from core.utils.query_translation import expand_multilingual_query, normalize_query_for_retrieval


class QueryAgent:
    def run(self, state: dict) -> dict:
        question = state.get("question", "")
        language = state.get("language", "en")

        normalized = normalize_query_for_retrieval(question, language)
        state["original_question"] = question
        state["normalized_question"] = normalized
        state["retrieval_queries"] = expand_multilingual_query(
            question=question,
            language=language,
            normalized_question=normalized,
        )
        return state
