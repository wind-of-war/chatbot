import json

import httpx

from configs.settings import settings


class OpenAIService:
    def __init__(self) -> None:
        self.api_key = settings.openai_api_key.strip()
        self.model = settings.openai_model.strip()
        self.base_url = settings.openai_base_url.rstrip("/")
        self.timeout_seconds = settings.openai_timeout_seconds
        self.ollama_enabled = settings.ollama_enabled
        self.ollama_model = settings.ollama_model.strip()
        self.ollama_base_url = settings.ollama_base_url.rstrip("/")
        self.ollama_num_predict = settings.ollama_num_predict
        self.ollama_num_ctx = settings.ollama_num_ctx
        self.ollama_temperature = settings.ollama_temperature

    def enabled(self) -> bool:
        return bool((self.api_key and self.model and self.base_url) or (self.ollama_enabled and self.ollama_model and self.ollama_base_url))

    def _build_prompt(self, question: str, docs: list[dict], language: str, max_docs: int = 4, max_chars: int = 1200) -> str:
        lang_instruction = "Answer in English."
        if language == "vi":
            lang_instruction = "Tra loi bang tieng Viet ro rang, ngan gon, dung trong tam."

        context_items = []
        for d in docs[:max_docs]:
            context_items.append(
                {
                    "source": d.get("source", "unknown"),
                    "section": d.get("section"),
                    "text": (d.get("text") or "")[:max_chars],
                }
            )

        context_json = json.dumps(context_items, ensure_ascii=False)
        return (
            "You are a GMP/GDP compliance assistant.\n"
            "Use only provided context.\n"
            "If context is insufficient, say so briefly.\n"
            f"{lang_instruction}\n\n"
            f"Question:\n{question}\n\n"
            f"Context JSON:\n{context_json}\n"
        )

    def _build_compact_prompt_for_ollama(self, question: str, docs: list[dict], language: str) -> str:
        base = self._build_prompt(question=question, docs=docs, language=language, max_docs=2, max_chars=650)
        return (
            "Answer in at most 4 short bullet points.\n"
            "Keep answer concise and practical.\n\n"
            f"{base}"
        )

    def _generate_openai(self, prompt: str) -> str | None:
        if not (self.api_key and self.model and self.base_url):
            return None

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a precise pharma compliance assistant."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return content.strip() if isinstance(content, str) else None

    def _generate_ollama(self, prompt: str) -> str | None:
        if not (self.ollama_enabled and self.ollama_model and self.ollama_base_url):
            return None

        payload = {
            "model": self.ollama_model,
            "stream": False,
            "messages": [
                {"role": "system", "content": "You are a precise pharma compliance assistant."},
                {"role": "user", "content": prompt},
            ],
            "options": {
                "num_predict": self.ollama_num_predict,
                "num_ctx": self.ollama_num_ctx,
                "temperature": self.ollama_temperature,
            },
        }

        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.post(f"{self.ollama_base_url}/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()
            message = data.get("message") or {}
            content = message.get("content")
            return content.strip() if isinstance(content, str) else None

    def generate(self, question: str, docs: list[dict], language: str) -> str | None:
        if not self.enabled():
            return None

        if self.ollama_enabled:
            try:
                answer = self._generate_ollama(
                    self._build_compact_prompt_for_ollama(question=question, docs=docs, language=language)
                )
                if answer:
                    return answer
            except Exception:
                pass

        try:
            return self._generate_openai(self._build_prompt(question=question, docs=docs, language=language))
        except Exception:
            return None
