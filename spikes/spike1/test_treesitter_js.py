import tree_sitter
import tree_sitter_javascript
import tree_sitter_typescript

js_lang = tree_sitter.Language(tree_sitter_javascript.language())
ts_lang = tree_sitter.Language(tree_sitter_typescript.language_typescript())

js_parser = tree_sitter.Parser(js_lang)
ts_parser = tree_sitter.Parser(ts_lang)

code = b"import React from 'react';\nimport App from './components/App';\nexport { default } from './components/Header';\n"
tree = ts_parser.parse(code)
print("Root node:", tree.root_node.type)
for child in tree.root_node.children:
    print("  Child node:", child.type, repr(code[child.start_byte:child.end_byte].decode("utf-8")))
