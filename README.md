# (fg-claude) PE Matcher

> AI-powered tool that analyzes SMB company websites and generates a shortlist of potential private equity fund buyers.

**Live Demo**: [https://deshaw-claude-casestudy-pe-match-ai-tpm-fg.streamlit.app](https://deshaw-claude-casestudy-pe-match-ai-tpm-fg.streamlit.app)

---

## Overview

PE Matcher solves a key challenge in PE deal sourcing: quickly identifying which funds might be interested in acquiring a specific SMB. Instead of manually researching fund portfolios and investment theses, this tool automates the matching process using LLM-powered analysis.

### How It Works

```
[User enters URL] → [Scrape website] → [Extract company profile via LLM] → [Match against PE funds] → [Ranked results + rationale]
```

---

## Features

- **Batch URL Processing**: Analyze up to 10 companies at once
- **AI-Powered Extraction**: Uses Claude API to extract structured company profiles from unstructured website content
- **Smart PE Matching**: Matches companies against 50+ PE funds based on sector, size, geography, and investment thesis
- **Deal Context**: Optional field to customize recommendations (e.g., "prefers growth equity over buyout")
- **Export Options**: PDF reports, Markdown, and JSON formats

---

## Technical Architecture

### Stack
| Component | Technology | Why |
|-----------|------------|-----|
| **Frontend** | Streamlit | Rapid prototyping, clean UI, no separate backend needed |
| **LLM** | Anthropic Claude API (Sonnet) | Strong reasoning, structured output, cost-effective |
| **Scraping** | requests + BeautifulSoup | Simple, handles most static sites |
| **Data** | Local JSON | No DB overhead for prototype |

### LLM Usage

The tool makes **2 API calls per company**:

1. **Extraction Call** (`claude-sonnet-4-20250514`)
   - Input: Raw website content (HTML → text)
   - Output: Structured JSON with company profile
   - Extracts: industry, location, size, products, customers, business model
   - Includes confidence scores for each field

2. **Matching Call** (`claude-sonnet-4-20250514`)
   - Input: Company profile + PE fund database + user context
   - Output: Ranked list of PE funds with fit scores and rationale
   - Applies reasoning about sector alignment, check size fit, thesis match

### Cost Optimization
- Uses Sonnet (not Opus) for speed and cost
- Truncates website content to avoid token bloat
- Single structured call per stage (not multi-turn chat)
- Estimated cost: ~$0.02-0.05 per company analyzed

---

## PE Fund Database

The tool includes a curated dataset of **50 PE funds** covering:

| Sector | Funds |
|--------|-------|
| Technology/Software | Vista, Thoma Bravo, Silver Lake, Francisco Partners, Insight, etc. |
| Healthcare | Welsh Carson, Linden, Cressey, etc. |
| Consumer | L Catterton, TSG Consumer, etc. |
| Business Services | Audax, Riverside, Alpine, etc. |
| Multi-sector | General Atlantic, Warburg Pincus, Advent, etc. |

Each fund record includes:
- AUM and check size range
- Sector focus and investment thesis keywords
- Geographic focus
- Recent deal examples

### Data Freshness Consideration
PE fund data is inherently dynamic (new funds raised, thesis shifts, recent deals). For a production system, this would integrate with:
- PitchBook or Crunchbase APIs
- SEC EDGAR filings (Form ADV)
- News aggregation for recent deal activity

---

## Project Structure

```
pe-matcher/
├── app.py              # Streamlit UI
├── scraper.py          # Website scraping module
├── extractor.py        # LLM-based profile extraction
├── matcher.py          # PE fund matching logic
├── output.py           # PDF/Markdown/JSON formatters
├── config.py           # Configuration and model settings
├── data/
│   └── pe_funds.json   # Curated PE fund dataset
├── requirements.txt
└── .env.example        # API key template
```

---

## Running Locally

### Prerequisites
- Python 3.9+
- Anthropic API key ([get one here](https://console.anthropic.com/))

### Setup

```bash
# Clone the repo
git clone https://github.com/FG-Baba/pe-matcher.git
cd pe-matcher

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure API key
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Run the app
streamlit run app.py
```

The app will open at `http://localhost:8501`

---

## Design Decisions & Trade-offs

### Why Streamlit over CLI?
The case study said UI doesn't matter, but a visual interface:
- Makes the demo more compelling
- Shows the full pipeline visually (progress bar, tabs, exports)
- Easier for interviewers to test without terminal setup

### Why a curated PE dataset over pure LLM knowledge?
- **Reliability**: LLM knowledge can be outdated or hallucinated
- **Transparency**: Can show exactly which funds are being matched against
- **Extensibility**: Easy to add new funds or update existing ones
- **Hybrid approach**: LLM handles fuzzy matching and rationale generation

### Why Claude Sonnet over GPT-4 or Claude Opus?
- **Speed**: Sonnet is faster for the demo experience
- **Cost**: ~10x cheaper than Opus for similar quality on this task
- **Sufficient capability**: Extraction and matching don't require frontier reasoning

### Challenges Encountered
1. **Website variability**: Some sites are JS-heavy, gated, or poorly structured
   - *Mitigation*: Graceful error handling, fallback scraping options

2. **LLM output consistency**: JSON parsing can fail on malformed responses
   - *Mitigation*: Robust parsing with fallbacks, retry logic

3. **PE data staleness**: Fund info changes frequently
   - *Mitigation*: Timestamps on data, designed for easy updates

---

## Future Improvements

With more time, I would add:

1. **Real-time PE data**: Integrate PitchBook/Crunchbase APIs
2. **Web search augmentation**: Query recent PE activity dynamically
3. **Confidence calibration**: Validate extraction accuracy against known companies
4. **User feedback loop**: Let users rate matches to improve over time
5. **Batch export**: Single PDF/report for multiple companies
6. **Authentication**: Secure API key management for multi-user deployment

---

## Demo Script

For the interview demo:

1. **Open the app** - show the clean, guided interface
2. **Single company analysis** - enter a SaaS company URL, walk through results
3. **Show context impact** - add "prefers growth equity" and show how rankings change
4. **Batch processing** - analyze 2-3 companies from different industries
5. **Export** - download PDF report
6. **Discuss architecture** - explain the pipeline and LLM usage

---

## Author

Built for D.E. Shaw AI Technical Product Manager case study.

**Tech**: Python, Streamlit, Anthropic Claude API, BeautifulSoup
