import os
from dotenv import load_dotenv
from llm import LLMManager
from metadata_fetcher import ArxivPaper, GithubRepo

# Load environment variables
load_dotenv()


def summarize(text: str, instruction: str) -> str:
    # Get the LLM backend from environment variable
    llm_backend = os.getenv("SUMMARIZER_LLM_BACKEND", "ollama")

    # Create LLMManager instance
    llm_manager = LLMManager(default_client=llm_backend)

    # Send message and get summary
    summary = llm_manager.send_message(system_prompt=instruction, user_prompt=text)

    return summary


def summarize_arxiv_paper(paper: ArxivPaper) -> str:
    instruction = "Write a technical summary for this arxiv paper, capturing the main points, methods and technology used as well as the novel ideas in two sentences:"
    text = f"Title:\n{paper.title}\n\nAbstract:\n{paper.abstract}"
    return summarize(text, instruction)


def summarize_github_project(repo: GithubRepo) -> str:
    instruction = "Write a technical summary for this github project, capturing the main points, methods and technology used:"
    text = f"Title:\n{repo.title}\n\nAbout:\n{repo.about}"
    if repo.readme:
        text += f"\n\nReadme:\n{repo.readme}"
    return summarize(text, instruction)
