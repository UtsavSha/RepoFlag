import subprocess
import json
import os
from typing import Dict


def analyze_complexity(repo_path: str) -> Dict[str, float]:
    """
    Analyzes Cyclomatic Complexity using Radon. 
    Returns a dictionary mapping file paths to their average complexity score.
    """
    print(f"Analyzing code complexity for {repo_path}...")

    # -j for JSON output, -a for average complexity
    cmd = ["radon", "cc", "-j", "-a", repo_path]

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=False)

        if not result.stdout:
            return {}

        raw_output = json.loads(result.stdout)
        file_complexities = {}

        for file_path, blocks in raw_output.items():
            # Radon outputs the absolute path. We need to make it relative to the repo root.
            relative_path = file_path.replace(repo_path, "").lstrip("/\\")

            # If it's a valid Python file with parsed blocks
            if isinstance(blocks, list) and len(blocks) > 0:
                # Calculate the average complexity of all functions/classes in the file
                total_complexity = sum(
                    [block.get("complexity", 1) for block in blocks])
                avg_complexity = total_complexity / len(blocks)
                file_complexities[relative_path] = round(avg_complexity, 2)
            elif isinstance(blocks, dict) and "error" in blocks:
                continue

        return file_complexities

    except Exception as e:
        print(f"Error analyzing complexity: {e}")
        return {}
