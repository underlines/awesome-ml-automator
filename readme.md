# awesome-ml-automator

Trying to automate the indexing, structuring and generation of the github.com/underlines/awesome-ml repository.

## Working

- Fetch arxiv paper and github repository metadata
- Use ollama or OpenAI to generate a summary
- Save as `metadata.json`
- Basic dupe check

## Work in progress

- Create a basic taxonomy to structure the papers and repositories

## Planned

- Extend functionality to the whole repo, instead of only llm-tools.md generation
- Dynamic Table of Contents generation
- Sort entries by most stars or chronologically by last change date
- Create a GUI similar to extractum's llm explorer to explore entries more dynamically
- Add tagging system
- Represent everything in graphs
