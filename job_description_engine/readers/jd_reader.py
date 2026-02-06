from pathlib import Path

def read_jd(file_path: Path) -> str:
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"The file {file_path} does not exist.")

    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()