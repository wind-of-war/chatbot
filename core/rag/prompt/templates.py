def build_prompt(question: str, docs: list[dict], language: str) -> str:
    instruction = "Answer in English."
    if language == "vi":
        instruction = "Tra loi bang tieng Viet."

    context = "\n".join(
        f"- source={doc.get('source')} section={doc.get('section')} text={doc.get('text')}" for doc in docs
    )
    if not context:
        context = "- no relevant context"

    return (
        f"{instruction}\n\n"
        "Use only the regulatory documents below.\n\n"
        f"Question:\n{question}\n\n"
        f"Context:\n{context}"
    )
