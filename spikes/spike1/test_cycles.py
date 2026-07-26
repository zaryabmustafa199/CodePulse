import os
from pathlib import Path
from extract_graph import TreeSitterGraphExtractor

def test_circular_dependency():
    test_dir = Path("spikes/spike1/repos/circular_test").resolve()
    test_dir.mkdir(parents=True, exist_ok=True)
    
    file_a = test_dir / "module_a.py"
    file_b = test_dir / "module_b.py"
    
    with open(file_a, "w") as f:
        f.write("from .module_b import func_b\ndef func_a():\n    pass\n")
        
    with open(file_b, "w") as f:
        f.write("from .module_a import func_a\ndef func_b():\n    pass\n")
        
    extractor = TreeSitterGraphExtractor(str(test_dir))
    extractor.inventory_files()
    extractor.extract_all_ast_imports()
    print("Source files:", list(extractor.source_files.keys()))
    print("Raw imports:", extractor.raw_imports)
    extractor.build_import_edges()
    print("Import edges:", extractor.import_edges)
    G, metrics = extractor.build_networkx_graph()
    
    print("Circular test metrics:")
    print("  Cycle Count:", metrics["circular_cycle_count"])
    print("  Cycles:", metrics["circular_cycles"])
    
    # Cleanup synthetic files
    file_a.unlink()
    file_b.unlink()
    test_dir.rmdir()

if __name__ == "__main__":
    test_circular_dependency()
