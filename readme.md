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

- Use markdown tables in the .md files for better readability
- Extend functionality to the whole repo, instead of only `llm-tools.md` generation
- Dynamic Table of Contents generation
- Sort entries by most stars or chronologically by last change date
- Create a GUI similar to extractum's llm explorer to explore entries more dynamically, instead of github's .md files
- Add tagging system
- Represent everything in graphs
- Auto fetch new arXiv papers and github repos of interest
- Add vote / like functionality

## Development

### Set up the environment
1. Install Conda, Mamba, MiniConda, Micromamba or similar
1. `conda env create -f environment.yml`
1. `conda activate awesome-ml-automator`
1. `pip install -r requirements.txt`

### Save changes
If you installed additional packages in conda or pip, update the environment.yml and requirements.txt:
1. `conda env export --no-builds > environment.yml`
   Remove the pip: section manually, because this is handled by requirements.txt and would lead to conflicts
1. `pip freeze > requirements.txt`
   This includes all installed packages, including transitive dependencies, which is not ideal for a clean requirements.txt.
   Best practices suggest listing only the core packages you directly depend on via imports, and letting those packages manage their own dependencies.
   Therefore remove all transitive dependencies from the requirements.txt and leave only the core packages.