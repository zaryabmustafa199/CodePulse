import tree_sitter
import tree_sitter_python
import tree_sitter_javascript
import tree_sitter_typescript

print("Tree-sitter version:", tree_sitter.__version__ if hasattr(tree_sitter, '__version__') else "unknown")

# In tree-sitter >= 0.22, Language is instantiated via Language(module.language())
py_lang = tree_sitter.Language(tree_sitter_python.language())
js_lang = tree_sitter.Language(tree_sitter_javascript.language())
ts_lang = tree_sitter.Language(tree_sitter_typescript.language_typescript())

py_parser = tree_sitter.Parser(py_lang)
js_parser = tree_sitter.Parser(js_lang)
ts_parser = tree_sitter.Parser(ts_lang)

code = b"import os\nfrom .utils import helper\n"
tree = py_parser.parse(code)
print("Root node:", tree.root_node.type)
for child in tree.root_node.children:
    print("  Child node:", child.type, repr(code[child.start_byte:child.end_byte].decode("utf-8")))
