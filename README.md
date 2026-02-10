# Endee Resume Matcher

A production-ready semantic resume matching system built using [Endee](https://github.com/EndeeLabs/endee) vector database and `sentence-transformers`. This system allows recruiters to find the top candidates for a job description using natural language queries and metadata filters.

![Demo Screenshot](https://via.placeholder.com/800x400?text=Resume+Matcher+Demo+Screenshot)

## Features

- **Semantic Search**: Uses `all-MiniLM-L6-v2` to understand the meaning behind resumes and queries.
- **Metadata Filtering**: Supports complex filters including `$in` (skills), `$gte` (years of experience), and `$eq` (role).
- **Production Ready**: Clean code structure, type hinting, and robust error handling.
- **Edge Case Handling**: Verified against 8 common search scenarios including empty queries and partial matches.

## Quick Start

### Prerequisites

- Python 3.10+
- Endee API Key (if using Cloud) or Local Setup

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/resume-matcher.git
   cd resume-matcher
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment (optional):
   ```bash
   export ENDEE_API_KEY="your_api_key_here"
   ```

### Quick Start (Windows) 🪟

We provide a **one-click script** that handles everything (Docker, Python environment, dependencies, and UI launch).

1.  Double-click `setup_and_run.bat`
2.  The app will open in your browser automatically.

*(Prerequisites: Docker Desktop and Python 3.10+ must be installed)*

### Manual Setup (Mac/Linux) 🍎/🐧

1.  **Start Endee Server**:
    ```bash
    docker run -d -p 8080:8080 -v endee-data:/data --name endee-server endeeio/endee-server:latest
    ```
    *(If port 8080 is taken, see Troubleshooting below)*

2.  **Setup Environment**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

3.  **Run Application**:
    ```bash
    # Run interactive UI
    streamlit run app.py
    
    # Or run test suite
    python demo.py
    ```

## Usage Example

```python
from resume_matcher import ResumeMatcher

matcher = ResumeMatcher()
matcher.ingest("data/resumes.json")

# Semantic search with filters
results = matcher.query(
    "Senior React Developer", 
    filters={"years": {"$gte": 5}}
)

for r in results:
    print(f"{r['id']}: {r['role']} (Score: {r['score']})")
```

## Performance & Results

The system has been tested against a dataset of 20 realistic resumes.

| Test Case | Query | Filter | Result |
|-----------|-------|--------|--------|
| **Simple Search** | "React Developer" | None | ✅ Top 5 React candidates |
| **Complex Logic** | "Backend Engineer" | `role="Backend Developer", years>=4` | ✅ Matches senior backend devs only |
| **Edge Case** | [Empty String] | None | ✅ No matches found (Correct) |
| **Skill Filter** | "System Programmer" | `skills=["Rust"]` | ✅ Finds Rust expert specifically |

## Data Structure

The system expects JSON resume data in the following format:

```json
{
  "id": "res_001",
  "summary": "Full text summary...",
  "skills": ["Python", "AWS"],
  "years": 5,
  "role": "Software Engineer"
}
```

## Contributing

1. Fork the repo.
2. Create feature branch.
3. Submit PR.

---
Built for Endee Labs Evaluation.
