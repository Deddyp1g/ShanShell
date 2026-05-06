"""ShanShell AI 候选排序器。"""


class Ranker:
    def rank(self, candidates: list, max_results=3) -> list:
        if not candidates:
            return []

        for c in candidates:
            if hasattr(c, "risk") and c.risk == "high":
                c.confidence = 0.0

        sorted_candidates = sorted(
            candidates,
            key=lambda c: c.confidence if hasattr(c, "confidence") else 0,
            reverse=True
        )

        top = sorted_candidates[:max_results]

        return top
