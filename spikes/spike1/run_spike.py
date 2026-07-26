"""
Harness script for Spike 1: Cross-File Dependency Graph Extraction.
Runs TreeSitterGraphExtractor on Small, Medium, and Large benchmark repositories
and prints structured decision evidence.
"""

import sys
import json
from pathlib import Path
from extract_graph import TreeSitterGraphExtractor

REPOS = {
    "Small (Python - Bottle)": Path("spikes/spike1/repos/small_repo").resolve(),
    "Medium (TS/JS - React)": Path("spikes/spike1/repos/medium_repo").resolve(),
    "Large (Python - HTTPX)": Path("spikes/spike1/repos/large_repo").resolve(),
}

def main():
    print("==================================================")
    print("CODEPULSE — SPIKE 1 BENCHMARK EXECUTION")
    print("==================================================\n")
    
    results = {}

    for name, repo_path in REPOS.items():
        if not repo_path.exists():
            print(f"ERROR: Repository path not found: {repo_path}")
            continue

        print(f"Analyzing {name} at: {repo_path}")
        extractor = TreeSitterGraphExtractor(str(repo_path))
        metrics = extractor.run_pipeline()
        results[name] = metrics

        print("--------------------------------------------------")
        print(f"Files Analyzed:          {metrics['total_files']}")
        print(f"Lines of Code:           {metrics['total_lines']}")
        print(f"Total Raw Imports:       {metrics['total_raw_imports']}")
        print(f"Resolved Local Edges:    {metrics['resolved_local_edges']}")
        print(f"Unresolved Local:        {metrics['unresolved_local_imports']}")
        print(f"Third Party Imports:     {metrics['third_party_imports']}")
        print(f"Resolution Accuracy %:   {metrics['resolution_accuracy_pct']}%")
        print(f"Circular Cycles Found:   {metrics['circular_cycle_count']}")
        print(f"Top Imported Core Files: {metrics['top_imported_files']}")
        print(f"Execution Duration:      {metrics['execution_time_seconds']} seconds")
        print("--------------------------------------------------\n")

    # Output JSON summary for automated reporting
    summary_file = Path("spikes/spike1/spike1_benchmark_results.json")
    with open(summary_file, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"Benchmark results saved to: {summary_file.resolve()}")

if __name__ == "__main__":
    main()
