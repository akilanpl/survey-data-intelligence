from typing import Any, Protocol


class AIProvider(Protocol):
    def complete_json(self, *, system: str, user: str) -> dict[str, Any]:
        """Return a parsed JSON object. Must not log secrets or record payloads."""
        ...
