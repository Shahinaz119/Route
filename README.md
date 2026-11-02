# Smart Career Path Agent

An AI-assisted career planning tool that compares a candidate's CV with a target role, identifies skill gaps, and recommends relevant courses from a course catalog. The project includes a Streamlit user interface, a LangGraph agent, deterministic validation logic, semantic course search, and offline tests.

## Contents

- [How it works](#how-it-works)
- [Project structure](#project-structure)
- [Requirements](#requirements)
- [Private data files](#private-data-files)
- [Configuration](#configuration)
- [Build course embeddings](#build-course-embeddings)
- [Run the web application](#run-the-web-application)
- [Run from the command line](#run-from-the-command-line)
- [Generate course skill tags](#generate-course-skill-tags)
- [Tests](#tests)
- [Data formats](#data-formats)
- [Safety and recommendation rules](#safety-and-recommendation-rules)
- [Known limitations](#known-limitations)
- [Troubleshooting](#troubleshooting)

## How it works

1. The user selects a target role and uploads a CV.
2. The agent reads the CV and extracts skills, experience, education, and projects. CV contents are treated as untrusted input.
3. Extracted skills are checked against exact quotes from the CV. Skills without supporting quotes are discarded.
4. The candidate profile is compared with the selected role's requirements. Requirements are classified as missing, underdeveloped, unverified, or demonstrated at the required level.
5. Semantic embeddings rank relevant published courses. A similarity score is useful for ranking, but is not accepted as proof that a course teaches a skill.
6. Course recommendations are checked against reviewed skill tags or exact skill phrases in course metadata.
7. The agent produces a report with the candidate's skills, gaps, recommended courses, uncovered gaps, and an Arabic summary.

The Streamlit app is the primary user experience. The LangGraph agent coordinates model calls and tools; deterministic Python code performs profile grounding, gap analysis, catalog validation, and recommendation checks.

## Project structure

```text
.
|-- src/
|   |-- app.py                 Streamlit web interface
|   |-- deep_agent.py          LangGraph agent and CLI entry point
|   |-- agent_tools.py         Agent tools, session state, and report validation
|   |-- cv_extractor.py        CV reading, profile validation, and evidence grounding
|   |-- gap_analyzer.py        Deterministic role-to-candidate gap analysis
|   |-- course_search.py       Embedding-based course ranking
|   |-- course_matcher.py      Deterministic reviewed-tag matching utility
|   |-- catalog.py             Excel/JSON catalog loading and validation
|   |-- embeddings.py          Build and load catalog embeddings
|   |-- tag_courses.py         Generate draft course skill tags
|   |-- models.py              Pydantic data models
|   |-- skills.py              Skill normalization and aliases
|   |-- pipeline.py            Shared role loading and deterministic pipeline
|   |-- config.py              Load project environment settings
|   |-- llm_gemini.py          Gemini provider adapter
|   `-- llm_openrouter.py      OpenRouter provider adapter
|-- tests/
|   |-- test_agent.py          Gap, matching, and CV-grounding tests
|   `-- test_agent_tools.py    Agent-tool behavior tests
|-- requirements.txt           Base Python dependencies
|-- pytest.ini                 Pytest configuration
`-- .gitignore                 Excludes secrets, datasets, and generated files
```

## Requirements

- Python 3.10 or later
- A Gemini or OpenRouter API key for LLM-backed analysis
- A local course catalog, role definitions, skill tags, and embedding file (see [Private data files](#private-data-files))
- Internet access the first time the sentence-transformers embedding model is downloaded

Create and activate a virtual environment from the project root on Windows:

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

The current `requirements.txt` does not yet list every application runtime package. Install the packages used by the app and agent:

```powershell
pip install streamlit sentence-transformers langgraph langchain-google-genai
```

For OpenRouter support, also install:

```powershell
pip install langchain-openai
```

## Private data files

The repository intentionally does not include `data/`, `assets/`, CVs, spreadsheets, embeddings, `.env`, or generated reports. These paths and file types are excluded by `.gitignore`; they must be supplied locally before running the application.

The default app and CLI expect:

```text
data/
|-- roles_sample.json          Role definitions
|-- courses.xlsx               Course catalog (or a supported JSON catalog for the CLI)
|-- course_skill_tags.json     Course skill tags; reviewed tags can support recommendations
|-- catalog_embeddings.npz     Precomputed course vectors and corresponding slugs
`-- CVs/                       Optional local CV files for testing
```

The web app uses `data/roles_sample.json` and `data/courses.xlsx` relative to the project root. Do not commit real CVs, API credentials, private company catalogs, or generated reports to a public repository.

## Configuration

Create a `.env` file in the project root. `src/config.py` loads it automatically.

For Gemini:

```dotenv
AGENT_MODEL=google_genai:gemini-3.8-flash
GOOGLE_API_KEY=replace_with_your_gemini_api_key
```

For OpenRouter:

```dotenv
AGENT_MODEL=openrouter:openrouter/free
OPENROUTER_API_KEY=replace_with_your_openrouter_api_key
```

Use one provider configuration at a time. Never commit `.env` or paste a real key into source code, issues, or logs. The Streamlit app defaults to the Gemini model shown above when `AGENT_MODEL` is not set; the command-line agent requires `AGENT_MODEL` to be set.

## Build course embeddings

Generate the embedding file after providing the catalog. Run this from the project root:

```powershell
python src/embeddings.py --catalog data/courses.xlsx
```

The default output is `data/catalog_embeddings.npz`. Rebuild it when the course catalog changes so its course slugs and vectors remain aligned with the catalog. The embedding model is multilingual and runs locally after it has been downloaded.

## Run the web application

With the required data files and provider configuration in place:

```powershell
streamlit run src/app.py
```

Choose a target role, upload a CV, and start the analysis. Reports can be downloaded from the results view. Run the command from the project root because the app's data paths are relative to that directory.

## Run from the command line

The CLI agent accepts a role ID, CV path, role file, catalog path, and optional output path:

```powershell
python src/deep_agent.py `
  --role junior_ai_engineer `
  --cv data/CVs/example.pdf `
  --roles data/roles_sample.json `
  --catalog data/courses.xlsx `
  --out report.json
```

The command writes a JSON report. The output path defaults to `report.json`. The role ID must exist in the roles JSON file. The CV reader currently extracts text from PDF, TXT, and Markdown files; scanned PDFs need OCR before analysis.

`src/pipeline.py` also provides role loading and a deterministic profile-based pipeline for development. Its current report builder does not create the agent's course roadmap; use `src/deep_agent.py` for the full agent workflow.

## Generate course skill tags

Draft skill tags for courses using Gemini:

```powershell
python src/tag_courses.py --catalog data/courses.xlsx --batch-size 10 --delay 20
```

The script saves progress to `data/course_skill_tags.json` and skips entries that already exist. Generated tags are marked unreviewed. Review them before setting `reviewed` to `true`; unreviewed tags do not establish course coverage.

## Tests

Run the offline unit tests from the project root:

```powershell
pytest
```

`pytest.ini` configures pytest to collect tests from `tests/`. The unit tests use mocks for embeddings and do not require API keys or network access. The root-level `test_*.py` scripts are manual integration/search checks and are not included in the configured default test path; some require provider credentials or the private local data files.

## Data formats

### Roles

The roles file is a JSON list. Each role has a unique `role_id`, a display `title`, and a list of requirements. Each requirement contains a skill name, minimum level (`none`, `beginner`, `intermediate`, or `advanced`), and an optional `mandatory` flag.

```json
[
  {
    "role_id": "junior_ai_engineer",
    "title": "Junior AI Engineer",
    "requirements": [
      {"skill": "python", "min_level": "beginner", "mandatory": true}
    ]
  }
]
```

### Course catalog

Catalogs can be Excel (`.xlsx` or `.xlsm`) or a JSON list. Required columns/keys are `Slug`, `Title (EN)`, `Delivery Type`, and `Status`. Supported optional metadata includes Arabic and English descriptions, overview, instructor, category, stage, duration, certificate hours, and quiz type. Only courses with `Status` set to `published` are available for recommendations.

### Course tags

`course_skill_tags.json` maps course slugs to tag records:

```json
{
  "course-slug": {
    "skills": ["python", "data analysis"],
    "reviewed": false
  }
}
```

Reviewed tags can support recommendations. Unreviewed tags are retained for review but are not treated as evidence.

## Safety and recommendation rules

- CV text is untrusted data; instructions inside a CV must not be followed.
- A candidate skill is retained only when its supporting quote appears in the CV text.
- A skill absent from a CV is reported as not evidenced; it is not proof the candidate lacks that skill.
- Listed-only skills that meet the required level are reported as unverified, not demonstrated.
- Unverified skills do not trigger course recommendations.
- Semantic similarity ranks course candidates but does not prove that a course covers a skill.
- A course can be recommended only when a reviewed skill tag or exact skill phrase in its metadata supports the match. The agent is instructed to require a similarity score of at least 0.35 as an additional ranking threshold.
- The final report validates course slugs and each claimed skill-to-course relationship before accepting a roadmap.

## Known limitations

- The example role requirements are placeholders and need validation against sourced job descriptions.
- The course catalog and role data are not included in this repository; results depend on the local files supplied by the user.
- Untagged or unreviewed course data limits recommendation coverage.
- Exact normalized skill names and conservative metadata evidence can miss semantically related skills.
- The app's file uploader currently lists DOCX, but the CV text reader does not parse DOCX yet. Use PDF or TXT for the app; Markdown is supported by the CLI reader.
- Course stage, duration, and certificate hours are informational and do not affect matching or learning sequence.

## Troubleshooting

- **Missing `AGENT_MODEL`:** Add `AGENT_MODEL` to `.env`; the CLI agent requires it.
- **Missing provider key:** Set `GOOGLE_API_KEY` for Gemini or `OPENROUTER_API_KEY` for OpenRouter.
- **Missing roles/catalog files:** Supply the local files under `data/`; they are not published in the repository.
- **Missing embeddings:** Run `python src/embeddings.py --catalog data/courses.xlsx` and confirm `data/catalog_embeddings.npz` exists.
- **No extracted CV text:** Use a text-based PDF or TXT file. Scanned PDFs require OCR.
- **No course recommendations:** Check that published catalog entries exist, embedding slugs match course slugs, and reviewed tags or exact skill phrases support the gaps.
- **Provider quota/rate limit:** Wait for the provider limit to reset or configure another supported model/provider. The agent stops rather than retrying a quota failure.