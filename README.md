# Strategy Room — short description

What it is
- A small Python project with workflow logic and example LLM modules.
- Main sources are in the `src` directory.

Requirements
- Python 3.10+ (tested on Python 3.12).

How to run (Windows)
1. Create and activate a virtual environment:
   - `python -m venv .venv`
   - `.venv\Scripts\activate`
2. Install dependencies (if any):
   - `pip install -r requirements.txt`
3. Run the application:
   - From project root: `python -m src`
   - Or directly: `python src\app.py`
4. In PyCharm: add a run configuration pointing to `src\app.py` or run the `src` module.

Useful files
- `src\app.py` — main application logic.
- `src\workflow.py` — workflow implementation.
- `src\base_llm.py` — base/abstraction for LLM.
- `src\strategy_flow_workflow.html` — auxiliary HTML (diagram).

Notes
- Repository ignores common build/IDE files (see `.gitignore`).
- If something fails, check Python version and virtual environment activation.