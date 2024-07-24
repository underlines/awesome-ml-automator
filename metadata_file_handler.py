import json
from metadata_fetcher import ArxivPaper, GithubRepo


def load_metadata() -> dict:
    """Load existing metadata from file."""
    try:
        with open("metadata.json", "r") as f:
            content = f.read().strip()
            if content:
                return json.loads(content)
            else:
                return {}
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        print("Warning: metadata.json is corrupted. Starting with empty metadata.")
        return {}


def save_metadata(metadata: dict):
    """Save metadata to file."""
    serializable_metadata = {}
    for url, data in metadata.items():
        if isinstance(data, (ArxivPaper, GithubRepo)):
            serializable_metadata[url] = data.dict(exclude={"abstract", "readme"})
        else:
            # If it's already a dict (loaded from JSON), use it as is
            serializable_metadata[url] = data

    with open("metadata.json", "w") as f:
        json.dump(serializable_metadata, f, default=str, indent=2)
