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
    instruction = """
    Write a very short technical summary for this arxiv paper, capturing the main points, methods and technology used.
    Exclude Title.
    Avoid full sentences, articles, subject pronouns and auxiliary verbs.
    Compress as much as possible in two or less sentences maintaining brevity.
    
    Examples:
    "scaling LLMs with effective Depth Up-Scaling to increase parameter count and continue pre-training"
    "Half-Quadratic Quantization for LLMs significantly accelerating quantization speed without requiring calibration data, outperforming existing methods in processing speed and memory efficiency"
    "creating a flexible and scalable platform for LLM-based multi-agent collaboration using an agent integration protocol, an instant-messaging-like architecture, and dynamic mechanisms for agent teaming and conversation flow control, code available"
    """
    text = f"Title:\n{paper.title}\n\nAbstract:\n{paper.abstract}"
    return summarize(text, instruction)


def summarize_github_project(repo: GithubRepo) -> str:
    instruction = """
    Write a very short technical summary for this github repository, capturing the main points, methods and technology used.
    Exclude Title.
    Avoid full sentences, articles, subject pronouns and auxiliary verbs.
    Compress as much as possible in two or less sentences maintaining brevity.
    
    Examples:
    "framework for autonomous Language Agents. Provides LSTM, Tool Usage, Web Navigation, Multi Agent Communication and Human-Agent interaction"
    "open source 'Perplexity' clone to answer questions via RAG and web search built with Next.js, Groq, Mixtral, Langchain, OpenAI"
    "high-speed Model Inference Serving on Consumer GPU/CPU using activation locality for hot/cold neurons"
    """
    text = f"Title:\n{repo.title}\n\nAbout:\n{repo.about}"
    if repo.readme:
        text += f"\n\nReadme:\n{repo.readme}"
    return summarize(text, instruction)
