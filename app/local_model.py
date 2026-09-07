"""Deterministic offline log classifier used by Worker log_inference jobs."""


_KEYWORD_RULES = {
    "disk": ("磁盘", "disk", "存储空间", "inode"),
    "memory": ("内存", "memory", "oom", "out of memory"),
    "cpu": ("cpu", "负载", "load average"),
    "network": ("网络", "连接超时", "timeout", "connection", "dns"),
}


def classify_log(text: str) -> dict:
    lowered = text.lower()
    for label, keywords in _KEYWORD_RULES.items():
        if any(keyword in lowered for keyword in keywords):
            return {
                "label": label,
                "confidence": 0.95,
                "matched_keywords": [kw for kw in keywords if kw in lowered],
            }
    return {"label": "normal", "confidence": 0.6, "matched_keywords": []}
