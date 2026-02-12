# AI_tools/code_companion/core/prompt_builder.py

class PromptBuilder:

    def __init__(self):
        self.modes = {
            "Debug": self._debug_prompt,
            "Refactor": self._refactor_prompt,
            "Explain": self._explain_prompt,
        }

    def build(self, mode, merged_code, git_diff=None, user_instruction=""):
        if mode not in self.modes:
            mode = "Explain"

        return self.modes[mode](merged_code, git_diff, user_instruction)

    # ================= Mode Templates =================

    def _debug_prompt(self, code, diff, instruction):
        return f"""
You are a senior backend engineer.

TASK: Debug the following project.

Focus on:
- Potential logic errors
- Runtime risks
- Design flaws
- Concurrency or state issues

{self._diff_section(diff)}

==== PROJECT CODE START ====
{code}
==== PROJECT CODE END ====

User Question:
{instruction}
""".strip()

    def _refactor_prompt(self, code, diff, instruction):
        return f"""
You are a senior software architect.

TASK: Refactor and improve the structure.

Focus on:
- Clean architecture
- Decoupling
- Maintainability
- Naming improvements

{self._diff_section(diff)}

==== PROJECT CODE START ====
{code}
==== PROJECT CODE END ====

User Requirement:
{instruction}
""".strip()

    def _explain_prompt(self, code, diff, instruction):
        return f"""
You are a senior engineer.

TASK: Explain this project clearly.

Focus on:
- Architecture
- Core logic
- Execution flow
- Key modules

{self._diff_section(diff)}

==== PROJECT CODE START ====
{code}
==== PROJECT CODE END ====

User Question:
{instruction}
""".strip()

    def _diff_section(self, diff):
        if not diff:
            return ""

        return f"""
==== GIT DIFF START ====
{diff}
==== GIT DIFF END ====
"""
