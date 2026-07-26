"""
Spike 1: Cross-File Dependency Graph Extraction Engine.
Uses Tree-sitter for deterministic AST parsing of Python and TypeScript/JavaScript source files,
builds a NetworkX directed import graph, detects circular dependencies, and evaluates metrics.
"""

import os
import time
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
import networkx as nx
import tree_sitter
import tree_sitter_python
import tree_sitter_javascript
import tree_sitter_typescript

# ─────────────────────────────────────────────
# CONFIGURATION & FILE EXCLUSIONS
# ─────────────────────────────────────────────

EXCLUDED_PATHS = {
    "node_modules", "dist", "build", ".git", "__pycache__", ".venv", "venv", ".idea", ".vscode"
}

EXCLUDED_EXTENSIONS = {
    ".min.js", ".min.css", ".lock", ".snap", ".map", "_generated.py", "_generated.ts"
}

MAX_SINGLE_FILE_LINES = 2000


class TreeSitterGraphExtractor:
    def __init__(self, repo_root: str):
        self.repo_root = Path(repo_root).resolve()
        
        # Instantiate Tree-sitter parsers
        self.py_lang = tree_sitter.Language(tree_sitter_python.language())
        self.js_lang = tree_sitter.Language(tree_sitter_javascript.language())
        self.ts_lang = tree_sitter.Language(tree_sitter_typescript.language_typescript())
        self.tsx_lang = tree_sitter.Language(tree_sitter_typescript.language_tsx())
        
        self.py_parser = tree_sitter.Parser(self.py_lang)
        self.js_parser = tree_sitter.Parser(self.js_lang)
        self.ts_parser = tree_sitter.Parser(self.ts_lang)
        self.tsx_parser = tree_sitter.Parser(self.tsx_lang)
        
        # State tracking
        self.source_files: Dict[str, Path] = {}  # {relative_path_str: absolute_path}
        self.file_languages: Dict[str, str] = {}  # {relative_path_str: language}
        self.file_line_counts: Dict[str, int] = {}
        self.raw_imports: Dict[str, List[str]] = {}  # {relative_path_str: [raw_import_targets]}
        self.import_edges: List[Tuple[str, str, bool, bool]] = []  # [(source, target, is_resolved, is_third_party)]

    def is_excluded(self, path: Path) -> bool:
        """Check if a path or file should be skipped."""
        parts = path.parts
        for excluded in EXCLUDED_PATHS:
            if excluded in parts:
                return True
        name = path.name
        for ext in EXCLUDED_EXTENSIONS:
            if name.endswith(ext):
                return True
        return False

    def inventory_files(self) -> int:
        """Walk file tree, filter out exclusions, record source files and line counts."""
        total_lines = 0
        for root, dirs, files in os.walk(self.repo_root):
            # Prune excluded directories in-place
            dirs[:] = [d for d in dirs if d not in EXCLUDED_PATHS]
            
            for file_name in files:
                full_path = Path(root) / file_name
                if self.is_excluded(full_path):
                    continue
                
                ext = full_path.suffix.lower()
                lang = None
                if ext == ".py":
                    lang = "python"
                elif ext in (".js", ".jsx"):
                    lang = "javascript"
                elif ext in (".ts", ".tsx"):
                    lang = "typescript"
                
                if lang:
                    try:
                        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                            lines = f.readlines()
                            line_count = len(lines)
                        
                        if line_count > MAX_SINGLE_FILE_LINES:
                            continue  # Skip auto-generated / bundled files
                        
                        rel_path = full_path.relative_to(self.repo_root).as_posix()
                        self.source_files[rel_path] = full_path
                        self.file_languages[rel_path] = lang
                        self.file_line_counts[rel_path] = line_count
                        total_lines += line_count
                    except Exception as e:
                        pass
        return total_lines

    def parse_python_imports(self, code_bytes: bytes) -> List[str]:
        """Extract imported module strings from Python AST using Tree-sitter."""
        imports = []
        tree = self.py_parser.parse(code_bytes)
        
        def traverse(node):
            if node.type == "import_statement":
                # import foo, bar.baz as b
                for child in node.children:
                    if child.type in ("dotted_name", "aliased_import"):
                        target_node = child.child_by_field_name("name") if child.type == "aliased_import" else child
                        if target_node:
                            imports.append(code_bytes[target_node.start_byte:target_node.end_byte].decode("utf-8").strip())
            elif node.type == "import_from_statement":
                # from [module] import [names]
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
                            # Clean parenthesized import lists if any
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
        """Extract import/export module specifiers from JS/TS AST using Tree-sitter."""
        imports = []
        if ext == ".tsx":
            tree = self.tsx_parser.parse(code_bytes)
        elif ext == ".ts":
            tree = self.ts_parser.parse(code_bytes)
        else:
            tree = self.js_parser.parse(code_bytes)

        def traverse(node):
            if node.type in ("import_statement", "export_statement"):
                # import ... from 'source' OR export ... from 'source'
                source_node = node.child_by_field_name("source")
                if source_node and source_node.type == "string":
                    raw_str = code_bytes[source_node.start_byte:source_node.end_byte].decode("utf-8").strip("'\"")
                    imports.append(raw_str)
            elif node.type == "call_expression":
                # require('...')
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

    def extract_all_ast_imports(self):
        """Walk all source files and extract raw import targets via Tree-sitter AST."""
        for rel_path, full_path in self.source_files.items():
            lang = self.file_languages[rel_path]
            ext = full_path.suffix.lower()
            try:
                with open(full_path, "rb") as f:
                    code_bytes = f.read()
                
                if lang == "python":
                    raw = self.parse_python_imports(code_bytes)
                else:
                    raw = self.parse_jsts_imports(code_bytes, ext)
                
                self.raw_imports[rel_path] = raw
            except Exception as e:
                self.raw_imports[rel_path] = []

    def resolve_python_import(self, source_rel_path: str, raw_target: str) -> Tuple[Optional[str], bool]:
        """
        Resolve a Python import target string to a local project file relative path.
        Returns: (resolved_rel_path_or_None, is_third_party)
        """
        source_dir = Path(source_rel_path).parent

        # 1. Relative import (e.g. `.utils`, `..parent.module`, `.module_b`)
        if raw_target.startswith("."):
            dots = 0
            while dots < len(raw_target) and raw_target[dots] == ".":
                dots += 1
            remainder = raw_target[dots:]
            
            # Navigate up directory tree according to dot count
            target_dir = source_dir
            for _ in range(dots - 1):
                target_dir = target_dir.parent
            
            if remainder:
                sub_path = remainder.replace(".", "/")
                candidates = [
                    (target_dir / f"{sub_path}.py").as_posix(),
                    (target_dir / sub_path / "__init__.py").as_posix()
                ]
            else:
                candidates = [(target_dir / "__init__.py").as_posix()]

            for cand in candidates:
                norm_cand = os.path.normpath(cand).replace("\\", "/")
                if norm_cand in self.source_files:
                    return norm_cand, False

            return None, False  # Unresolved relative import

        # 2. Absolute project import (e.g., `import src.module` or `from app.routes import api`)
        module_as_path = raw_target.replace(".", "/")
        candidates = [
            f"{module_as_path}.py",
            f"{module_as_path}/__init__.py",
            f"src/{module_as_path}.py",
            f"src/{module_as_path}/__init__.py"
        ]
        
        for cand in candidates:
            norm_cand = os.path.normpath(cand).replace("\\", "/")
            if norm_cand in self.source_files:
                return norm_cand, False

        # Third party package if unresolved locally
        return None, True

    def resolve_jsts_import(self, source_rel_path: str, raw_target: str) -> Tuple[Optional[str], bool]:
        """
        Resolve a JS/TS import target string to a local project file relative path.
        Returns: (resolved_rel_path_or_None, is_third_party)
        """
        source_dir = Path(source_rel_path).parent

        # Relative imports start with ./ or ../
        if raw_target.startswith("./") or raw_target.startswith("../"):
            base_path = (source_dir / raw_target).as_posix()
            norm_base = os.path.normpath(base_path).replace("\\", "/")

            if norm_base in self.source_files:
                return norm_base, False

            possible_exts = [".ts", ".tsx", ".js", ".jsx"]
            for ext in possible_exts:
                cand = f"{norm_base}{ext}"
                if cand in self.source_files:
                    return cand, False

            for ext in possible_exts:
                cand = f"{norm_base}/index{ext}"
                if cand in self.source_files:
                    return cand, False

            return None, False

        # Check path aliases (e.g. `@/components/...` or `src/...`)
        if raw_target.startswith("@/"):
            clean_target = raw_target[2:]
            candidates = [
                f"src/{clean_target}",
                f"{clean_target}"
            ]
            for base in candidates:
                norm_base = os.path.normpath(base).replace("\\", "/")
                if norm_base in self.source_files:
                    return norm_base, False
                for ext in [".ts", ".tsx", ".js", ".jsx"]:
                    if f"{norm_base}{ext}" in self.source_files:
                        return f"{norm_base}{ext}", False

        return None, True

    def build_import_edges(self):
        """Resolve all extracted raw imports into structured edges."""
        self.import_edges.clear()
        
        for source_rel, raw_list in self.raw_imports.items():
            lang = self.file_languages[source_rel]
            seen_targets = set()
            for raw_target in raw_list:
                if lang == "python":
                    resolved, is_third = self.resolve_python_import(source_rel, raw_target)
                else:
                    resolved, is_third = self.resolve_jsts_import(source_rel, raw_target)
                
                is_resolved = resolved is not None
                target_str = resolved if is_resolved else raw_target
                
                # Avoid duplicate edges for same target in single file
                edge_key = (source_rel, target_str)
                if edge_key not in seen_targets:
                    seen_targets.add(edge_key)
                    self.import_edges.append((source_rel, target_str, is_resolved, is_third))

    def build_networkx_graph(self) -> Tuple[nx.DiGraph, Dict]:
        """
        Build directed graph from resolved internal imports and compute graph metrics.
        Returns: (DiGraph, metrics_dict)
        """
        G = nx.DiGraph()
        
        for rel_path in self.source_files.keys():
            G.add_node(rel_path, lines=self.file_line_counts[rel_path], lang=self.file_languages[rel_path])

        resolved_count = 0
        third_party_count = 0
        unresolved_local_count = 0

        for source, target, is_resolved, is_third in self.import_edges:
            if is_resolved:
                # Do not self-loop file
                if source != target:
                    G.add_edge(source, target)
                resolved_count += 1
            elif is_third:
                third_party_count += 1
            else:
                unresolved_local_count += 1

        total_local_attempts = resolved_count + unresolved_local_count
        resolution_accuracy = (resolved_count / total_local_attempts * 100.0) if total_local_attempts > 0 else 100.0

        in_degrees = dict(G.in_degree())
        top_imported = sorted(in_degrees.items(), key=lambda x: x[1], reverse=True)[:5]
        
        try:
            cycles = list(nx.simple_cycles(G))
        except Exception:
            cycles = []

        isolated = [node for node in G.nodes() if G.in_degree(node) == 0 and G.out_degree(node) == 0]

        folder_nodes: Dict[str, List[str]] = {}
        for node in G.nodes():
            top_folder = Path(node).parts[0] if len(Path(node).parts) > 1 else "root"
            folder_nodes.setdefault(top_folder, []).append(node)

        metrics = {
            "total_files": len(self.source_files),
            "total_lines": sum(self.file_line_counts.values()),
            "total_raw_imports": len(self.import_edges),
            "resolved_local_edges": resolved_count,
            "third_party_imports": third_party_count,
            "unresolved_local_imports": unresolved_local_count,
            "resolution_accuracy_pct": round(resolution_accuracy, 2),
            "top_imported_files": top_imported,
            "circular_cycles": cycles,
            "circular_cycle_count": len(cycles),
            "isolated_file_count": len(isolated),
            "folder_clusters": {k: len(v) for k, v in folder_nodes.items()}
        }

        return G, metrics

    def run_pipeline(self) -> Dict:
        """Run complete extraction pipeline and measure timing."""
        start_time = time.time()
        
        self.inventory_files()
        self.extract_all_ast_imports()
        self.build_import_edges()
        G, metrics = self.build_networkx_graph()
        
        metrics["execution_time_seconds"] = round(time.time() - start_time, 4)
        return metrics
