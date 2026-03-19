# AI_tools/code_companion/core/context_manager.py

from .token_estimator import TokenEstimator


class ContextManager:

    def __init__(self, max_tokens: int = 6000):
        self.max_tokens = max_tokens

    def build_context(
        self,
        file_contents: dict[str, str],
        diff_text: str | None = None,
    ) -> dict:
        """
        Return:
        {
            "context": str,
            "stats": {...}
        }
        """

        sections = []
        total_tokens = 0
        truncated = False

        # 1️⃣ 优先加入 diff
        if diff_text:
            diff_tokens = TokenEstimator.estimate(diff_text)

            if diff_tokens < self.max_tokens:
                sections.append("==== GIT DIFF START ====\n")
                sections.append(diff_text)
                sections.append("\n==== GIT DIFF END ====\n\n")
                total_tokens += diff_tokens
            else:
                # diff 过大，截断
                allowed_chars = self.max_tokens * 4
                diff_text = diff_text[:allowed_chars]
                sections.append("==== GIT DIFF (TRUNCATED) ====\n")
                sections.append(diff_text)
                sections.append("\n==== END ====\n\n")
                total_tokens = self.max_tokens
                truncated = True

        # 2️⃣ 加文件内容
        for path, content in file_contents.items():

            header = f"\n==== FILE: {path} ====\n"
            section_text = header + content

            section_tokens = TokenEstimator.estimate(section_text)

            if total_tokens + section_tokens > self.max_tokens:
                remaining_chars = (self.max_tokens - total_tokens) * 4

                if remaining_chars > 0:
                    truncated_content = section_text[:remaining_chars]
                    sections.append(truncated_content)
                    truncated = True

                break

            sections.append(section_text)
            total_tokens += section_tokens

        context_text = "".join(sections)

        return {
            "context": context_text,
            "stats": {
                "total_tokens_estimated": total_tokens,
                "file_count": len(file_contents),
                "truncated": truncated,
                "max_tokens": self.max_tokens,
            },
        }
