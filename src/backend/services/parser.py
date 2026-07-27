"""
File Parser and Graph Extraction Service for CodePulse.
Integrates Tree-sitter for deterministic AST import extraction across Python and JS/TS,
constructs NetworkX DiGraph, detects circular dependencies, and computes folder clusters.
"""

import os
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import networkx as nx
import tree_sitter
import tree_sitter_python
import tree_sitter_javascript
import tree_sitter_typescript

from src.backend.config import settings
from src.backend.models.schemas import RepositoryContext, ParsedRepository, FileMetrics, ImportEdge


class TreeSitterParserService:
    """Parser service that converts a RepositoryContext into a ParsedRepository using Tree-sitter & NetworkX."""

    def __init__(self, repo_context: RepositoryContext):
        self.context = repo_context
        self.repo_root = Path(repo_context.repository_path).resolve()

        # Instantiate Tree-sitter parsers
        self.py_lang = tree_sitter.Language(tree_sitter_python.language())
        self.js_lang = tree_sitter.Language(tree_sitter_javascript.language())
        self.ts_lang = tree_sitter.Language(tree_sitter_typescript.language_typescript())
        self.tsx_lang = tree_sitter.Language(tree_sitter_typescript.language_tsx())

        self.py_parser = tree_sitter.Parser(self.py_lang)
        self.js_parser = tree_sitter.Parser(self.js_lang)
        self.ts_parser = tree_sitter.Parser(self.ts_lang)
        self.tsx_parser = tree_sitter.Parser(self.tsx_lang)

    def parse_python_imports(self, code_bytes: bytes) -> List[str]:
        """Extract import module strings from Python AST."""
        imports = []
        tree = self.py_parser.parse(code_bytes)

        def traverse(node):
            if node.type == "import_statement":
                for child in node.children:
                    if child.type in ("dotted_name", "aliased_import"):
                        target = child.child_by_field_name("name") if child.type == "aliased_import" else child
                        if target:
                            imports.append(code_bytes[target.start_byte:target.end_byte].decode("utf-8").strip())
            elif node.type == "import_from_statement":
                module_str = None
                imported_names = []
                after_import = False
                for child in node.children:
                    if child.type == "import":
                        after_import = True
                        continue
                    if not after_import:
                        if child.type in ("relative_import", "dotted_name"):
                            module_str = code_bytes[child.start_byte:child.end_byte].decode("utf-8").strip()
                    else:
                        if child.type in ("dotted_name", "aliased_import", "import_list", "identifier"):
                            text = code_bytes[child.start_byte:child.end_byte].decode("utf-8").strip()
                            text = text.strip("() \n\r\t")
                            for item in text.split(","):
                                item_clean = item.strip().split(" as ")[0].strip()
                                if item_clean:
                                    imported_names.append(item_clean)

                if module_str:
                    imports.append(module_str)
                    for name in imported_names:
                        if module_str in (".", "..", "..."):
                            imports.append(f"{module_str}{name}")
                        else:
                            imports.append(f"{module_str}.{name}")

            for child in node.children:
                traverse(child)

        traverse(tree.root_node)
        return imports

    def parse_jsts_imports(self, code_bytes: bytes, ext: str) -> List[str]:
        """Extract import strings from JS/TS AST."""
        imports = []
        if ext == ".tsx":
            tree = self.tsx_parser.parse(code_bytes)
        elif ext == ".ts":
            tree = self.ts_parser.parse(code_bytes)
        else:
            tree = self.js_parser.parse(code_bytes)

        def traverse(node):
            if node.type in ("import_statement", "export_statement"):
                source_node = node.child_by_field_name("source")
                if source_node and source_node.type == "string":
                    raw_str = code_bytes[source_node.start_byte:source_node.end_byte].decode("utf-8").strip("'\"")
                    imports.append(raw_str)
            elif node.type == "call_expression":
                fn_node = node.child_by_field_name("function")
                if fn_node and code_bytes[fn_node.start_byte:fn_node.end_byte] in (b"require", b"import"):
                    args = node.child_by_field_name("arguments")
                    if args and args.children:
                        for arg in args.children:
                            if arg.type == "string":
                                raw_str = code_bytes[arg.start_byte:arg.end_byte].decode("utf-8").strip("'\"")
                                imports.append(raw_str)

            for child in node.children:
                traverse(child)

        traverse(tree.root_node)
        return imports

    def resolve_python_import(self, source_rel: str, raw_target: str, manifest: set) -> Tuple[Optional[str], bool]:
        """Resolve Python import target to local manifest path."""
        source_dir = Path(source_rel).parent

        if raw_target.startswith("."):
            dots = 0
            while dots < len(raw_target) and raw_target[dots] == ".":
                dots += 1
            remainder = raw_target[dots:]
            target_dir = source_dir
            for _ in range(dots - 1):
                target_dir = target_dir.parent

            if remainder:
                sub = remainder.replace(".", "/")
                candidates = [
                    (target_dir / f"{sub}.py").as_posix(),
                    (target_dir / sub / "__init__.py").as_posix()
                ]
            else:
                candidates = [(target_dir / "__init__.py").as_posix()]

            for cand in candidates:
                norm = os.path.normpath(cand).replace("\\", "/")
                if norm in manifest:
                    return norm, False
            return None, False

        mod_path = raw_target.replace(".", "/")
        candidates = [
            f"{mod_path}.py",
            f"{mod_path}/__init__.py",
            f"src/{mod_path}.py",
            f"src/{mod_path}/__init__.py"
        ]
        for cand in candidates:
            norm = os.path.normpath(cand).replace("\\", "/")
            if norm in manifest:
                return norm, False

        return None, True

    def parse(self) -> ParsedRepository:
        """Run complete AST parsing and graph extraction pipeline."""
        start_time = time.time()
        source_metrics: Dict[str, FileMetrics] = {}
        manifest_set = set(self.context.file_manifest)
        raw_imports: Dict[str, List[str]] = {}

        for rel_path in self.context.file_manifest:
            full_path = self.repo_root / rel_path
            ext = full_path.suffix.lower()

            try:
                with open(full_path, "rb") as f:
                    code_bytes = f.read()

                lines = code_bytes.decode("utf-8", errors="ignore").splitlines()
                line_count = len(lines)
                fn_count = sum(1 for line in lines if line.strip().startswith(("def ", "function ", "const ", "let ")) and ("(" in line or "=>" in line))
                cls_count = sum(1 for line in lines if line.strip().startswith(("class ", "interface ", "type ")))
                doc_count = sum(1 for line in lines if line.strip().startswith(('"""', "'''", "/**", "/*", "//")))

                source_metrics[rel_path] = FileMetrics(
                    relative_path=rel_path,
                    line_count=line_count,
                    function_count=fn_count,
                    class_count=cls_count,
                    docstring_count=doc_count
                )

                if ext == ".py":
                    raw_imports[rel_path] = self.parse_python_imports(code_bytes)
                else:
                    raw_imports[rel_path] = self.parse_jsts_imports(code_bytes, ext)

            except Exception:
                source_metrics[rel_path] = FileMetrics(relative_path=rel_path, line_count=0)
                raw_imports[rel_path] = []

        # Graph assembly
        G = nx.DiGraph()
        for rel_path in manifest_set:
            G.add_node(rel_path)

        edges: List[ImportEdge] = []
        for source_rel, raw_list in raw_imports.items():
            ext = Path(source_rel).suffix.lower()
            seen = set()
            for target_raw in raw_list:
                if ext == ".py":
                    resolved, is_third = self.resolve_python_import(source_rel, target_raw, manifest_set)
                else:
                    resolved, is_third = None, True  # Simplified JS fallback for vertical slice

                is_res = resolved is not None
                target_str = resolved if is_res else target_raw

                if (source_rel, target_str) not in seen:
                    seen.add((source_rel, target_str))
                    edges.append(ImportEdge(
                        source_file=source_rel,
                        target_file=target_str,
                        is_resolved=is_res,
                        is_third_party=is_third
                    ))
                    if is_res and source_rel != target_str:
                        G.add_edge(source_rel, target_str)

        in_degrees = dict(G.in_degree())
        top_imported = sorted(in_degrees.items(), key=lambda x: x[1], reverse=True)[:5]

        try:
            cycles = list(nx.simple_cycles(G))
        except Exception:
            cycles = []

        folder_counts: Dict[str, int] = {}
        for rel_path in manifest_set:
            top_folder = Path(rel_path).parts[0] if len(Path(rel_path).parts) > 1 else "root"
            folder_counts[top_folder] = folder_counts.get(top_folder, 0) + 1

        duration = round(time.time() - start_time, 4)

        return ParsedRepository(
            source_files=source_metrics,
            import_edges=edges,
            circular_dependencies=cycles,
            most_imported_files=top_imported,
            folder_structure=folder_counts,
            parse_duration_seconds=duration
        )
