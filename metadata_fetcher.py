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
        url = clean_url(url)

        # Extract paper_id
        paper_id = url.split("/")[-1]

        # Fetch data
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

        url = clean_url(url)

        # Extract repo full name from URL
        parsed_url = urlparse(url)
        repo_full_name = "/".join(parsed_url.path.strip("/").split("/")[:2])

        if not repo_full_name:
            raise ValueError("Invalid GitHub URL")

        repo = g.get_repo(repo_full_name)

        try:
            readme = repo.get_readme().decoded_content.decode()
            readme = process_markdown(readme)
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


def clean_url(url: str) -> str:
    """Cleans the URL to meet the requirements."""
    parsed_url = urlparse(url)

    if "github.com" in parsed_url.netloc:
        # Keep only the first two path segments (username and repo name)
        path = "/".join(parsed_url.path.strip("/").split("/")[:2])
        return urlunparse(
            parsed_url._replace(path=f"/{path}", params="", query="", fragment="")
        )

    elif "arxiv.org" in parsed_url.netloc:
        # Replace 'pdf' with 'abs' in the path and remove version number
        path = parsed_url.path.replace("/pdf/", "/abs/")
        path = re.sub(r"v\d+$", "", path)
        return urlunparse(
            parsed_url._replace(path=path, params="", query="", fragment="")
        )

    else:
        raise ValueError("Invalid URL. Must be an arXiv or GitHub URL.")


def process_markdown(markdown):
    # Remove HTML tags
    html_tag_pattern = r"<[^>]*>"
    markdown = re.sub(html_tag_pattern, "", markdown)

    # Remove markdown links
    md_link_pattern = r"\[(.*?)\]\(.*?\)"
    markdown = re.sub(md_link_pattern, r"\1", markdown)

    # Remove code blocks
    code_block_pattern = r"```.*?```"
    markdown = re.sub(code_block_pattern, "(code example)", markdown, flags=re.DOTALL)

    # Remove markdown tables
    md_table_pattern = r"\|.*?\|"
    markdown = re.sub(md_table_pattern, "(table)", markdown, flags=re.DOTALL)

    return markdown
