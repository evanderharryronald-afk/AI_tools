# AI_tools/code_companion/core/file_engine.py
import os

def merge_files_with_relative_paths(files, root_dir):
    merged_code = []

    for file in files:
        rel = os.path.relpath(file, root_dir).replace("\\", "/")
        merged_code.append(f"# ===== File: {rel} =====\n")

        try:
            with open(file, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read().rstrip()
                merged_code.append(content + "\n\n")
        except Exception as e:
            merged_code.append(f"# ERROR reading file: {e}\n\n")

    return "".join(merged_code)
