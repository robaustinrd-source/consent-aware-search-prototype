from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SAMPLE_DOCS = ROOT / "sampledocs"


def ensure_demo_data() -> None:
    SAMPLE_DOCS.mkdir(exist_ok=True)
    if not (SAMPLE_DOCS / "knowledge.md").exists():
        (SAMPLE_DOCS / "knowledge.md").write_text(
            "# Local Search Demo\n\n"
            "This knowledge base is designed for offline agent workflows.\n\n"
            "Consent-aware access keeps the system safe and auditable.\n",
            encoding="utf-8",
        )
    if not (SAMPLE_DOCS / "profile.txt").exists():
        (SAMPLE_DOCS / "profile.txt").write_text(
            "Name: Example User\n"
            "Role: Researcher\n"
            "Preference: Reliable local search and transparent consent logs.\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    ensure_demo_data()
    print(f"Demo content ready at: {SAMPLE_DOCS}")
