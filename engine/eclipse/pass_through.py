"""Prompts and media are never rewritten. Hardware refuse ≠ content policy."""


def unchanged(prompt: str) -> str:
    if not isinstance(prompt, str):
        raise TypeError("prompt must be str")
    return prompt
