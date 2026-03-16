from pathlib import Path


def generate_faq_entries(processed_dir: str) -> int:
    faq_path = Path("data/processed/faq_generated.md")
    entries = []

    for text_file in Path(processed_dir).glob("*.txt"):
        question = f"What does {text_file.stem} describe?"
        answer = "Auto-generated placeholder answer from processed compliance chunk."
        entries.append(f"## {question}\n\n{answer}\n")

    faq_path.write_text("\n".join(entries), encoding="utf-8")
    return len(entries)


if __name__ == "__main__":
    count = generate_faq_entries("data/processed")
    print(f"Generated {count} FAQ entries")
