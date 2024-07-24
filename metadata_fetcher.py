import re
from dotenv import load_dotenv
from datetime import datetime
from typing import Union, List
from pydantic import BaseModel, Field
import arxiv
from github import Github, GithubException
from urllib.parse import urlparse, urlunparse

# Load environment variables
load_dotenv()


class ArxivPaper(BaseModel):
    """Represents an arXiv paper."""

    title: str
    abstract: str = Field(exclude=True)  # This field won't be included in serialization
    authors: List[str]
    publish_date: datetime
    arxiv_url: str
    fetch_date: datetime = Field(default_factory=datetime.now)
    summary: str


class GithubRepo(BaseModel):
    """Represents a GitHub repository."""

    title: str
    about: str
    readme: str = Field(exclude=True)  # This field won't be included in serialization
    author: str
    last_commit_date: datetime
    stars: int
    license: Union[str, None]
    github_url: str
    fetch_date: datetime = Field(default_factory=datetime.now)
    summary: str


def fetch_arxiv_data(url: str) -> ArxivPaper:
    """Fetch data for an arXiv paper."""
    try:
        # Step 1: Convert /pdf/ to /abs/
        parsed_url = urlparse(url)
        path_parts = parsed_url.path.split("/")
        if "pdf" in path_parts:
            path_parts[path_parts.index("pdf")] = "abs"
            url = urlunparse(parsed_url._replace(path="/".join(path_parts)))

        # Step 2: Remove version number
        url = re.sub(r"v\d+$", "", url)

        # Extract paper_id
        paper_id = url.split("/")[-1]

        # Step 3: Fetch data
        search = arxiv.Search(id_list=[paper_id])
        paper = next(search.results())

        return ArxivPaper(
            title=paper.title,
            abstract=paper.summary,
            authors=[author.name for author in paper.authors],
            publish_date=paper.published,
            arxiv_url=url,
            summary="",
        )
    except StopIteration:
        raise ValueError(f"No paper found for the given URL: {url}")
    except Exception as e:
        raise RuntimeError(f"Error fetching arXiv data: {str(e)}")


def fetch_github_data(url: str) -> GithubRepo:
    """Fetch data for a GitHub repository."""
    try:
        g = Github()

        # Extract repo full name from URL
        parsed_url = urlparse(url)
        repo_full_name = "/".join(parsed_url.path.strip("/").split("/")[:2])

        if not repo_full_name:
            raise ValueError("Invalid GitHub URL")

        repo = g.get_repo(repo_full_name)

        try:
            readme = repo.get_readme().decoded_content.decode()
        except GithubException:
            readme = "No README available"

        return GithubRepo(
            title=repo.name,
            about=repo.description or "No description available",
            readme=readme,
            author=repo.owner.login,
            last_commit_date=repo.pushed_at,
            stars=repo.stargazers_count,
            license=repo.license.name if repo.license else None,
            github_url=url,
            summary="",
        )
    except GithubException as e:
        if e.status == 404:
            raise ValueError(f"GitHub repository not found: {url}")
        else:
            raise RuntimeError(f"GitHub API error: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Error fetching GitHub data: {str(e)}")
