# # AI_tools/code_companion/core/prompt_builder.py
#
# from .token_estimator import TokenEstimator
#
#
# class PromptBuilder:
#
#     def __init__(self, max_tokens=6000):
#         self.max_tokens = max_tokens
#
#         self.modes = {
#             "Debug": self._debug_prompt,
#             "Refactor": self._refactor_prompt,
#             "Explain": self._explain_prompt,
#         }
#
#     # ===================== Public API =====================
#
#     def build(
#         self,
#         mode,
#         merged_code,
#         git_diff=None,
#         user_instruction="",
#     ):
#         if mode not in self.modes:
#             mode = "Explain"
#
#         context, stats = self._build_context(
#             merged_code,
#             git_diff
#         )
#
#         prompt = self.modes[mode](
#             context,
#             user_instruction
#         )
#
#         return {
#             "prompt": prompt,
#             "stats": stats
#         }
#
#     # ===================== Context Logic =====================
#
#     def _build_context(self, code, diff):
#
#         sections = []
#         total_tokens = 0
#         truncated = False
#
#         # 1️⃣ Diff 优先
#         if diff:
#             diff_tokens = TokenEstimator.estimate(diff)
#
#             if diff_tokens < self.max_tokens:
#                 sections.append("==== GIT DIFF START ====\n")
#                 sections.append(diff)
#                 sections.append("\n==== GIT DIFF END ====\n\n")
#                 total_tokens += diff_tokens
#             else:
#                 allowed_chars = self.max_tokens * 4
#                 sections.append("==== GIT DIFF (TRUNCATED) ====\n")
#                 sections.append(diff[:allowed_chars])
#                 sections.append("\n==== END ====\n\n")
#                 total_tokens = self.max_tokens
#                 truncated = True
#
#         # 2️⃣ Project Code
#         remaining_tokens = self.max_tokens - total_tokens
#
#         if remaining_tokens > 0 and code:
#             allowed_chars = remaining_tokens * 4
#
#             code_tokens = TokenEstimator.estimate(code)
#
#             if code_tokens > remaining_tokens:
#                 sections.append("==== PROJECT CODE (TRUNCATED) ====\n")
#                 sections.append(code[:allowed_chars])
#                 truncated = True
#             else:
#                 sections.append("==== PROJECT CODE START ====\n")
#                 sections.append(code)
#                 sections.append("\n==== PROJECT CODE END ====\n")
#
#             total_tokens = self.max_tokens if truncated else total_tokens + code_tokens
#
#         context = "".join(sections)
#
#         stats = {
#             "max_tokens": self.max_tokens,
#             "estimated_tokens": total_tokens,
#             "truncated": truncated,
#             "has_diff": bool(diff),
#         }
#
#         return context, stats
#
#     # ================= Mode Templates =================
#
#     def _debug_prompt(self, context, instruction):
#         return f"""
# You are a senior backend engineer.
#
# TASK: Debug the following project.
#
# Focus on:
# - Potential logic errors
# - Runtime risks
# - Design flaws
# - Concurrency or state issues
#
# {context}
#
# User Question:
# {instruction}
# """.strip()
#
#     def _refactor_prompt(self, context, instruction):
#         return f"""
# You are a senior software architect.
#
# TASK: Refactor and improve the structure.
#
# Focus on:
# - Clean architecture
# - Decoupling
# - Maintainability
# - Naming improvements
#
# {context}
#
# User Requirement:
# {instruction}
# """.strip()
#
#     def _explain_prompt(self, context, instruction):
#         return f"""
# You are a senior engineer.
#
# TASK: Explain this project clearly.
#
# Focus on:
# - Architecture
# - Core logic
# - Execution flow
# - Key modules
#
# {context}
#
# User Question:
# {instruction}
# """.strip()

# AI_tools/code_companion/core/prompt_builder.py

class PromptBuilder:

    def __init__(self, max_tokens=6000):
        self.max_tokens = max_tokens
        self.modes = {
            "Debug": self._debug_prompt,
            "Refactor": self._refactor_prompt,
            "Explain": self._explain_prompt,
        }

    # ============================================================
    # Public API
    # ============================================================

    def build(self, mode, merged_code, git_diff=None, user_instruction=""):
        if mode not in self.modes:
            mode = "Explain"

        # ===== 1. Token Estimate =====
        estimated_tokens = self._estimate_tokens(
            merged_code + (git_diff or "") + user_instruction
        )

        truncated = False

        # ===== 2. 自动截断（优先保留 diff）=====
        if estimated_tokens > self.max_tokens:
            truncated = True
            merged_code = self._truncate_code_keep_diff_first(
                merged_code,
                git_diff
            )

        # ===== 3. 构建 Prompt =====
        prompt = self.modes[mode](merged_code, git_diff, user_instruction)

        # ===== 4. 统计信息 =====
        stats = {
            "max_tokens": self.max_tokens,
            "estimated_tokens": estimated_tokens,
            "truncated": truncated,
            "has_diff": bool(git_diff)
        }

        return {
            "prompt": prompt,
            "stats": stats
        }

    # ============================================================
    # Token 估算
    # ============================================================

    def _estimate_tokens(self, text):
        # 简易估算：1 token ≈ 4 chars
        return int(len(text) / 4)

    # ============================================================
    # 截断逻辑（优先保留 diff）
    # ============================================================

    def _truncate_code_keep_diff_first(self, code, diff):
        if not code:
            return ""

        max_chars = self.max_tokens * 4

        # 如果有 diff，优先保留 diff
        diff_part = diff or ""
        diff_len = len(diff_part)

        if diff_len >= max_chars:
            return ""  # diff 太大，只留 diff（外部会拼）

        remain_chars = max_chars - diff_len

        return code[:remain_chars]

    # ============================================================
    # Mode Templates
    # ============================================================

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

    # ============================================================
    # Diff Section
    # ============================================================

    def _diff_section(self, diff):
        if not diff:
            return ""

        return f"""
==== GIT DIFF START ====
{diff}
==== GIT DIFF END ====
"""

