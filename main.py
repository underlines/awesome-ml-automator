import argparse
import metadata_file_handler
import metadata_fetcher
from summarizer import summarize_arxiv_paper, summarize_github_project
from typing import Optional
from dotenv import load_dotenv

load_dotenv(override=True)

def main(url: str, overwrite: Optional[str] = None, llm: str = "ollama"):
    """
    Main function to process the URL with optional overwrite behavior.

    Args:
        url (str): The arXiv or GitHub URL to process.
        overwrite (Optional[str]): Overwrite behavior. Can be 'all', 'nollm', or 'llm'.
        llm (str): The LLM backend to use. Can be 'ollama' or 'openai'.
    """
    url = metadata_fetcher.clean_url(url)
    metadata = metadata_file_handler.load_metadata()

    if url in metadata:
        if not overwrite:
            print("URL already processed. Use an overwrite option to reindex.")
            return
        else:
            if overwrite == "all":
                print("Overwriting all metadata for the existing URL.")
                del metadata[url]  # Remove existing entry to reprocess
            elif overwrite == "nollm":
                print("Overwriting metadata without updating the summary.")
                existing_data = metadata[url]
            elif overwrite == "llm":
                print("Overwriting only the LLM-generated summary.")
                existing_data = metadata[url]
            else:
                raise ValueError("Invalid overwrite option.")
    else:
        existing_data = None

    # Fetch and process data based on URL type
    if "arxiv.org" in url:
        data = metadata_fetcher.fetch_arxiv_data(url)
        if overwrite in [None, "all"]:
            summary = summarize_arxiv_paper(data, llm)
            data.summary = summary
        elif overwrite == "llm":
            # Preserve existing metadata and update summary
            data = existing_data
            data = metadata_fetcher.fetch_arxiv_data(url)
            data.summary = summarize_arxiv_paper(data, llm)
    elif "github.com" in url:
        data = metadata_fetcher.fetch_github_data(url)
        if overwrite in [None, "all"]:
            summary = summarize_github_project(data, llm)
            data.summary = summary
        elif overwrite == "llm":
            # Preserve existing metadata and update summary
            data = existing_data
            data = metadata_fetcher.fetch_github_data(url)
            data.summary = summarize_github_project(data, llm)
    else:
        raise ValueError("Invalid URL. Must be an arXiv or GitHub URL.")

    metadata[url] = data
    metadata_file_handler.save_metadata(metadata)
    print("Data fetched and saved successfully.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Automate indexing, structuring, and generation of the awesome-ml repository."
    )
    parser.add_argument(
        "--url",
        type=str,
        required=True,
        help="arXiv paper or GitHub repository URL to process.",
    )
    parser.add_argument(
        "--overwrite",
        type=str,
        choices=["all", "nollm", "llm"],
        help=(
            "Overwrite behavior:\n"
            "  all   - Reindex and update all metadata.\n"
            "  nollm - Reindex and update metadata without changing the summary.\n"
            "  llm   - Reindex and update only the LLM-generated summary."
        ),
    )
    parser.add_argument(
        "--llm",
        type=str,
        choices=["ollama", "openai"],
        default="openai",
        help="Specify which LLM to use for summarization: 'ollama' or 'openai'.",
    )

    args = parser.parse_args()
    main(url=args.url, overwrite=args.overwrite, llm=args.llm)
