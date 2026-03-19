# AI_tools/code_companion/core/token_estimator.py

class TokenEstimator:
    """
    Rough token estimator.
    Approximation: 1 token ≈ 4 characters (safe side)
    """

    @staticmethod
    def estimate(text: str) -> int:
        if not text:
            return 0
        return max(1, len(text) // 4)

    @staticmethod
    def estimate_many(texts: list[str]) -> int:
        return sum(TokenEstimator.estimate(t) for t in texts)