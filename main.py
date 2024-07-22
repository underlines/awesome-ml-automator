import re
import json
import requests
import os
import arxiv
from datetime import datetime
from urllib.parse import urlparse
from dotenv import load_dotenv
from llm import LLMManager
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

load_dotenv()

class MetadataGatherer(ABC):
    @abstractmethod
    def gather(self, url: str) -> Dict:
        pass

class GitHubMetadataGatherer(MetadataGatherer):
    def gather(self, url: str) -> Dict:
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

class ArxivMetadataGatherer(MetadataGatherer):
    def gather(self, url: str) -> Dict:
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

class JSONDataHandler:
    def __init__(self, url_type_filename: str, metadata_filename: str):
        self.url_type_filename = url_type_filename
        self.metadata_filename = metadata_filename

    def load_data(self) -> tuple:
        try:
            with open(self.url_type_filename, 'r') as f:
                url_data = json.load(f)
        except FileNotFoundError:
            url_data = {"github": [], "arxiv": []}

        try:
            with open(self.metadata_filename, 'r') as f:
                metadata_data = json.load(f)
        except FileNotFoundError:
            metadata_data = {}

        return url_data, metadata_data

    def save_data(self, url_data: Dict, metadata_data: Dict):
        with open(self.url_type_filename, 'w') as f:
            json.dump(url_data, f, indent=2)
        
        with open(self.metadata_filename, 'w') as f:
            json.dump(metadata_data, f, indent=2)

class Summarizer:
    def __init__(self, llm_manager: LLMManager):
        self.llm_manager = llm_manager

    def summarize(self, content: str, url_type: str) -> str:
        system_prompt = f"""
        # Instructions
        1. Summarize in two sentences: What it does, then how.
        2. Focus on key tech aspects: main technologies, specific features, integrations.
        3. Avoid marketing speak. Assume expert audience.
        4. Start mid-sentence, as if "This project" is already written.
        5. Be concise: ~50-60 words total.
        6. Use specific, technical language. Avoid vague terms.
        Example: "Provides a self-improving memory layer for LLMs, enabling personalized experiences across applications. Utilizes multi-level memory retention (user, session, and agent-based), adaptive personalization, and a developer-friendly API, with support for vector stores like Qdrant for production environments and compatibility with different LLM providers and frameworks."
        """
        user_prompt = f"""
        # Description
        {content}
        """
        try:
            response = self.llm_manager.send_message(
                system_prompt=system_prompt,
                user_prompt=user_prompt
            )
            return response
        except Exception as e:
            return f"An error occurred: {str(e)}"

class Entry:
    def __init__(self, url: str, entry_type: str, metadata: Dict):
        self.url = url
        self.entry_type = entry_type
        self.metadata = metadata
        self.summary = ""

    def generate_summary(self, summarizer: Summarizer):
        if self.entry_type == "github":
            content = f"GitHub Project Title: {self.metadata['project_title']}\nAbout: {self.metadata['about_text']}\nReadme: {self.metadata['readme_md_text'][:400]}"
        else:
            content = f"arXiv Paper Title: {self.metadata['paper_title']}\nAbstract: {self.metadata['abstract_text']}"
        self.summary = summarizer.summarize(content, self.entry_type)

    def to_dict(self) -> Dict:
        return {
            "url": self.url,
            "entry_type": self.entry_type,
            "metadata": self.metadata,
            "summary": self.summary
        }

class EntryManager:
    def __init__(self, json_handler: JSONDataHandler, summarizer: Summarizer):
        self.json_handler = json_handler
        self.summarizer = summarizer

    def add_or_update_entry(self, entry: Entry):
        url_data, metadata_data = self.json_handler.load_data()
        
        url_type = entry.entry_type
        metadata_id = str(len(metadata_data) + 1)
        
        entry.generate_summary(self.summarizer)
        
        # Check if the URL already exists in the data
        url_exists = False
        for existing_entry in url_data[url_type]:
            if existing_entry["url"] == entry.url:
                existing_entry["fetch_date_update"] = entry.metadata["fetch_date"]
                existing_entry["publisher_date_update"] = entry.metadata["last_commit_date" if url_type == "github" else "publish_date"]
                if not existing_entry.get("summary"):
                    existing_entry["summary"] = entry.summary
                metadata_data[existing_entry["metadata_id"]].update(entry.metadata)
                url_exists = True
                break
        
        if not url_exists:
            new_entry = {
                "id": len(url_data[url_type]) + 1,
                "url": entry.url,
                "fetch_date_first": entry.metadata["fetch_date"],
                "fetch_date_update": entry.metadata["fetch_date"],
                "publisher_date_update": entry.metadata["last_commit_date" if url_type == "github" else "publish_date"],
                "summary": entry.summary,
                "metadata_id": metadata_id
            }
            url_data[url_type].append(new_entry)
            metadata_data[metadata_id] = entry.metadata

        self.json_handler.save_data(url_data, metadata_data)

import re

def is_valid_url(url: str) -> bool:
    github_pattern = r'^https?://github\.com/[\w-]+/[\w.-]+/?$'
    arxiv_pattern = r'^https?://arxiv\.org/abs/\d+\.\d+(v\d+)?$'
    return bool(re.match(github_pattern, url)) or bool(re.match(arxiv_pattern, url))

def main():
    llm_manager = LLMManager()
    json_handler = JSONDataHandler("links.json", "metadata.json")
    summarizer = Summarizer(llm_manager)
    entry_manager = EntryManager(json_handler, summarizer)

    github_gatherer = GitHubMetadataGatherer()
    arxiv_gatherer = ArxivMetadataGatherer()

    while True:
        url = input("Enter a GitHub repository or arXiv paper URL (or 'quit' to exit): ")
        if url.lower() == 'quit':
            break

        if not is_valid_url(url):
            print("Invalid URL. Please enter a valid GitHub repository or arXiv paper URL.")
            continue

        if "github.com" in url:
            metadata = github_gatherer.gather(url)
            entry_type = "github"
        else:
            metadata = arxiv_gatherer.gather(url)
            entry_type = "arxiv"

        if metadata:
            entry = Entry(url, entry_type, metadata)
            entry_manager.add_or_update_entry(entry)
            print(f"Metadata for {url} has been updated in the JSON files.")
        else:
            print(f"Failed to retrieve metadata for {url}.")

if __name__ == "__main__":
    main()
