import tree_sitter
import tree_sitter_python

py_lang = tree_sitter.Language(tree_sitter_python.language())
py_parser = tree_sitter.Parser(py_lang)

code = b"from .module_b import func_b\nfrom . import module_c\nimport foo.bar\nfrom foo.bar import baz\n"
tree = py_parser.parse(code)

def dump_tree(node, indent=0):
    text = code[node.start_byte:node.end_byte].decode("utf-8")
    print("  " * indent + f"{node.type} ({node.grammar_name}): {repr(text)}")
    for child in node.children:
        dump_tree(child, indent + 1)

dump_tree(tree.root_node)
