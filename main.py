import metadata_file_handler
import metadata_fetcher
from summarizer import summarize_arxiv_paper, summarize_github_project


def main(url: str):
    """Main function to process the URL."""
    metadata = metadata_file_handler.load_metadata()

    if url in metadata:
        print("URL already processed.")
        return

    if "arxiv.org" in url:
        data = metadata_fetcher.fetch_arxiv_data(url)
        summary = summarize_arxiv_paper(data)
        data.summary = summary
    elif "github.com" in url:
        data = metadata_fetcher.fetch_github_data(url)
        summary = summarize_github_project(data)
        data.summary = summary
    else:
        raise ValueError("Invalid URL. Must be an arXiv or GitHub URL.")

    metadata[url] = data
    metadata_file_handler.save_metadata(metadata)
    print("Data fetched and saved successfully.")


if __name__ == "__main__":
    url = input("Enter arXiv paper or GitHub repository URL: ")
    main(url)
