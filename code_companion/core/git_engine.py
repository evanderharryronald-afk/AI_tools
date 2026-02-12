# AI_tools/code_companion/core/git_engine.py
import subprocess


def get_git_diff(root_dir):
    try:
        result = subprocess.run(
            ["git", "diff"],
            cwd=root_dir,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            return ""

        return result.stdout.strip()

    except Exception:
        return ""
