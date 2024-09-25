import os
from dotenv import load_dotenv
from llm import LLMManager
from metadata_fetcher import ArxivPaper, GithubRepo

# Load environment variables
load_dotenv()


def summarize(text: str, instruction: str, llm: str) -> str:
    # Create LLMManager instance with the specified client
    llm_manager = LLMManager(default_client=llm)

    # Send message and get summary
    summary = llm_manager.send_message(system_prompt=instruction, user_prompt=text)

    return summary


def summarize_arxiv_paper(paper: ArxivPaper, llm: str) -> str:
    instruction = """
    Summarize the arXiv paper's key points, methods, and technology used. 
    Do not include the paper title in your summary, omit the name and title!
    Max 2 sentences, be brief.
    Good examples:
    "improves <usage> to <benefit> using <technology>"
    "enables <outcome> for <application>, without <limitation>, surpassing <previous methods>"
    """
    text = f"Title:\n{paper.title}\n\nAbstract:\n{paper.abstract}"
    return summarize(text, instruction, llm)


def summarize_github_project(repo: GithubRepo, llm: str) -> str:
    instruction = """
    Summarize the GitHub repository's key points, methods, and technology used.
    Do not include the project name in your summary, omit the name and title!
    Max 2 sentences, be brief.
    Good examples:
    "is a <description> for <usage> using <technology> to <benefit>"
    "provides <functionality> for <application>, built with <technologies>"
    """
    text = f"Title:\n{repo.title}\n\nAbout:\n{repo.about}"
    if repo.readme:
        text += f"\n\nReadme:\n{repo.readme}"
    return summarize(text, instruction, llm)
