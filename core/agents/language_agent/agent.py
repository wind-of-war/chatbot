from core.utils.language_detection import detect_language


class LanguageAgent:
    def run(self, state: dict) -> dict:
        query = state.get("question", "")
        if not query:
            state["language"] = "en"
            return state

        state["language"] = detect_language(query)
        return state
