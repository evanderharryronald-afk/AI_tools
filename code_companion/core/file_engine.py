# AI_tools/code_companion/core/file_engine.py

import os

class FileEngine:

    @staticmethod
    def merge_files_with_relative_paths(files, root_dir):
        """
        Backward compatible merge method.
        """
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

    # ✅ 新增：结构化读取（推荐以后用这个）
    @staticmethod
    def read_files_as_dict(files, root_dir=None):
        """
        Return:
        {
            "relative/path.py": "file content"
        }
        """
        result = {}

        for file in files:
            try:
                with open(file, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read().rstrip()

                if not content.strip():
                    continue  # skip empty files

                if root_dir:
                    rel = os.path.relpath(file, root_dir).replace("\\", "/")
                else:
                    rel = file

                result[rel] = content

            except Exception:
                continue

        return result
