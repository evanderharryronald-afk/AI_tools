# AI_tools/code_companion/core/diff_extractor.py

import subprocess


class DiffExtractor:

    @staticmethod
    def get_git_diff() -> str:
        try:
            result = subprocess.run(
                ["git", "diff"],
                capture_output=True,
                text=True,
                check=False
            )
            return result.stdout
        except Exception:
            return ""

    @staticmethod
    def get_changed_files() -> list[str]:
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only"],
                capture_output=True,
                text=True,
                check=False
            )
            files = result.stdout.strip().splitlines()
            return [f for f in files if f.strip()]
        except Exception:
            return []
