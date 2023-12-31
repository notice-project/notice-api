import string
from pathlib import Path
from typing import Sequence

from notice_api.note_completion import model


def generate_note(transcript: str | Sequence[str], usernote: str):
    outcome = model.generate_note_openai(transcript, usernote)
    return outcome


# for testing purpose
def generate_note_from_file(file_path: Path | str, usernote: str):
    transcript = Path(file_path).read_text().splitlines()
    transcript = [
        line for line in transcript if line.startswith(tuple(string.ascii_letters))
    ]
    outcome = generate_note(transcript, usernote)
    return outcome


if __name__ == "__main__":
    notice_api_path = Path(__file__).resolve().parent.parent
    result = generate_note_from_file(notice_api_path / "ml_vs_dl.txt", "test")
    for chunk in result:
        print(chunk, end="", flush=True)
