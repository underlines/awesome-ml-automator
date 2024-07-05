import re
import json
import requests
import os
import arxiv
from datetime import datetime
from urllib.parse import urlparse
from dotenv import load_dotenv
from llm import LLMManager

# Load environment variables
load_dotenv()

# Initialize LLMManager
llm_manager = LLMManager()

def is_valid_url(url):
    """Check if the URL is a valid GitHub repository or arXiv paper link."""
    github_pattern = r'^https?://github\.com/[\w-]+/[\w.-]+/?$'
    arxiv_pattern = r'^https?://arxiv\.org/abs/\d+\.\d+(v\d+)?$'
    return re.match(github_pattern, url) or re.match(arxiv_pattern, url)

def get_github_metadata(url):
    """Retrieve metadata for a GitHub repository."""
    api_url = f"https://api.github.com/repos/{urlparse(url).path.strip('/')}"
    response = requests.get(api_url)
    if response.status_code == 200:
        data = response.json()
        readme_url = f"{api_url}/readme"
        readme_response = requests.get(readme_url)
        readme_content = ""
        if readme_response.status_code == 200:
            readme_data = readme_response.json()
            readme_content = requests.get(readme_data['download_url']).text

        return {
            "url": url,
            "fetch_date": datetime.now().isoformat(),
            "repository_stars": data['stargazers_count'],
            "last_commit_date": data['pushed_at'],
            "about_text": data['description'],
            "readme_md_text": readme_content,
            "project_title": data['name']
        }
    return None

def get_arxiv_metadata(url):
    """Retrieve metadata for an arXiv paper."""
    paper_id = url.split('/')[-1]
    search = arxiv.Search(id_list=[paper_id])
    result = next(search.results(), None)
    
    if result:
        return {
            "url": url,
            "fetch_date": datetime.now().isoformat(),
            "abstract_text": result.summary,
            "publish_date": result.published.isoformat(),
            "author_names": [author.name for author in result.authors],
            "paper_title": result.title
        }
    return None

def summarize_content(content: str, url_type: str) -> str:
    system_prompt = f"""
    # Instruction
    - You are a computer scientist in the field of AI and ML.
    - Read the following {url_type} description and summarize it in one sentence, highlighting what's mind blowing or revolutionary.
    - Focus on the main benefits or USPs and what it solves or improves and how.
    - If certain technologies and methods have an important role, mention them in the summary.
    - Don't mention the title or name of the project, as it will already be in the summary.
    - Don't mention other things, just the summary.
    """
    user_prompt = f"""
    # Description
    {content}
    """
    try:
        response = llm_manager.send_message(
            system_prompt=system_prompt,
            user_prompt=user_prompt
        )
        return response
    except Exception as e:
        return f"An error occurred: {str(e)}"

def update_json_files(metadata):
    """Update the JSON files with new metadata."""
    url_type_filename = "url_type.json"
    metadata_filename = "metadata.json"
    
    try:
        with open(url_type_filename, 'r') as f:
            url_data = json.load(f)
    except FileNotFoundError:
        url_data = {"github": [], "arxiv": []}

    try:
        with open(metadata_filename, 'r') as f:
            metadata_data = json.load(f)
    except FileNotFoundError:
        metadata_data = {}

    url_type = "github" if "github.com" in metadata["url"] else "arxiv"
    metadata_id = str(len(metadata_data) + 1)
    
    # Create or update the metadata entry
    summary = ""
    if url_type == "github":
        publisher_date_update = metadata["last_commit_date"]
        content = f"{url_type.capitalize()} Project Title: {metadata['project_title']}\nAbout: {metadata['about_text']}\nReadme: {metadata['readme_md_text'][:400]}"
        summary = summarize_content(content, url_type)
    else:
        publisher_date_update = metadata["publish_date"]
        content = f"{url_type.capitalize()} Paper Title: {metadata['paper_title']}\nAbstract: {metadata['abstract_text']}"
        summary = summarize_content(content, url_type)
    
    # Check if the URL already exists in the data
    url_exists = False
    for entry in url_data[url_type]:
        if entry["url"] == metadata["url"]:
            entry["fetch_date_update"] = metadata["fetch_date"]
            entry["publisher_date_update"] = publisher_date_update
            if not entry.get("summary"):
                entry["summary"] = summary
            metadata_data[entry["metadata_id"]].update(metadata)
            url_exists = True
            break
    
    if not url_exists:
        new_entry = {
            "id": len(url_data[url_type]) + 1,
            "url": metadata["url"],
            "fetch_date_first": metadata["fetch_date"],
            "fetch_date_update": metadata["fetch_date"],
            "publisher_date_update": publisher_date_update,
            "summary": summary,
            "metadata_id": metadata_id
        }
        url_data[url_type].append(new_entry)
        metadata_data[metadata_id] = metadata

    # Write the updated data back to the JSON files
    with open(url_type_filename, 'w') as f:
        json.dump(url_data, f, indent=2)
    
    with open(metadata_filename, 'w') as f:
        json.dump(metadata_data, f, indent=2)

def main():
    while True:
        url = input("Enter a GitHub repository or arXiv paper URL (or 'quit' to exit): ")
        if url.lower() == 'quit':
            break

        if not is_valid_url(url):
            print("Invalid URL. Please enter a valid GitHub repository or arXiv paper URL.")
            continue

        if "github.com" in url:
            metadata = get_github_metadata(url)
        else:
            metadata = get_arxiv_metadata(url)

        if metadata:
            update_json_files(metadata)
            print(f"Metadata for {url} has been updated in the JSON files.")
        else:
            print(f"Failed to retrieve metadata for {url}.")

if __name__ == "__main__":
    main()
