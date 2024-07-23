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
from uuid import uuid4
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from uuid import UUID

load_dotenv()

class Header(BaseModel):
    id: UUID
    url: str
    first_fetched_at: datetime
    last_fetched_at: datetime
    last_published_at: datetime
    title: str
    generated_summary: str

class GithubDetail(BaseModel):
    about_text: str
    readme_text: str
    author: str
    license: str
    repository_stars: int

class ArxivDetail(BaseModel):
    authors: List[str]
    abstract: str

class GithubEntry(BaseModel):
    header: Header
    detail: GithubDetail

class ArxivEntry(BaseModel):
    header: Header
    detail: ArxivDetail

class Data(BaseModel):
    github: List[GithubEntry] = Field(default_factory=list)
    arxiv: List[ArxivEntry] = Field(default_factory=list)

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
                "about_text": data['description'],
                "readme_text": readme_content,
                "author": data['owner']['login'],
                "license": data['license']['name'] if data['license'] else '',
                "repository_stars": data['stargazers_count'],
            }
        return None

class ArxivMetadataGatherer(MetadataGatherer):
    def gather(self, url: str) -> Dict:
        paper_id = url.split('/')[-1]
        search = arxiv.Search(id_list=[paper_id])
        result = next(search.results(), None)
        
        if result:
            return {
                "authors": [author.name for author in result.authors],
                "paper_title": result.title,
                "publish_date": result.published,
                "abstract": result.summary,
            }
        return None

class JSONDataHandler:
    def __init__(self, metadata_filename: str):
        self.metadata_filename = metadata_filename

    def load_data(self) -> Data:
        try:
            with open(self.metadata_filename, 'r') as f:
                metadata_data = Data.parse_raw(f.read())
        except FileNotFoundError:
            metadata_data = Data()
        return metadata_data

    def save_data(self, metadata_data: Data):
        with open(self.metadata_filename, 'w') as f:
            f.write(metadata_data.json(indent=2))

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

class EntryManager:
    def __init__(self, json_handler: JSONDataHandler, summarizer: Summarizer):
        self.json_handler = json_handler
        self.summarizer = summarizer

    def add_or_update_entry(self, url: str, entry_type: str, metadata: Dict):
        data = self.json_handler.load_data()
        
        entry_list = getattr(data, entry_type)
        for existing_entry in entry_list:
            if existing_entry.header.url == url:
                existing_entry.header.last_fetched_at = datetime.now()
                existing_entry.header.last_published_at = datetime.fromisoformat(metadata['last_commit_date' if entry_type == "github" else 'publish_date'])
                existing_entry.header.generated_summary = self.summarizer.summarize(existing_entry.header.title, entry_type)
                existing_entry.detail = metadata
                break
        else:
            uuid = uuid4()
            header = Header(id=uuid, url=url, first_fetched_at=datetime.now(), last_fetched_at=datetime.now(), 
                            last_published_at=datetime.fromisoformat(metadata['last_commit_date' if entry_type == "github" else 'publish_date']), 
                            title=metadata['project_title' if entry_type == "github" else 'paper_title'], 
                            generated_summary=self.summarizer.summarize(metadata['project_title' if entry_type == "github" else 'paper_title'], entry_type))
            entry = GithubEntry(header=header, detail=metadata) if entry_type == "github" else ArxivEntry(header=header, detail=metadata)
            entry_list.append(entry)

        self.json_handler.save_data(data)

def is_valid_url(url: str) -> bool:
    github_pattern = r'^https?://github\.com/[\w-]+/[\w.-]+/?$'
    arxiv_pattern = r'^https?://arxiv\.org/abs/\d+\.\d+(v\d+)?$'
    return bool(re.match(github_pattern, url)) or bool(re.match(arxiv_pattern, url))

def main():
    llm_manager = LLMManager()
    json_handler = JSONDataHandler("metadata.json")
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
            entry_manager.add_or_update_entry(url, entry_type, metadata)
            print(f"Metadata for {url} has been updated in the JSON file.")
        else:
            print(f"Failed to retrieve metadata for {url}.")

if __name__ == "__main__":
    main()
