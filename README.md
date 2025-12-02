# QNA Scoring Interface - IFD Based Evaluation

A standalone web-based Q&A pair scoring system using **Instruction Following Difficulty (IFD)** metric from the Cherry_LLM research paper.

## What is IFD Scoring?

IFD (Instruction Following Difficulty) measures how difficult it is for a language model to follow an instruction (question) when generating a response (answer).

**Formula**: `IFD = sθ(A|Q) / sθ(A)`

Where:
- `sθ(A|Q)` = Difficulty of generating answer given the question
- `sθ(A)` = Difficulty of generating answer without the question

**High IFD scores indicate high-value training data** (the model struggles to follow the instruction, so learning from this data is valuable).

## Features

✅ **IFD-Based Scoring** - Objective difficulty metrics for Q&A pairs
✅ **Batch Processing** - Score multiple pairs at once
✅ **Flexible Filtering** - Filter by difficulty tier or IFD score range
✅ **Dataset Analytics** - View distribution and insights
✅ **Export Results** - Download scored pairs as CSV
✅ **Web Interface** - Beautiful, responsive UI
✅ **Standalone** - Completely separate from generator

## Setup

### 1. Install Dependencies

```bash
cd QnA_Scoring_Interface
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and add your API credentials:

```bash
cp .env.example .env
```

Edit `.env`:
```dotenv
OPENAI_API_KEY=your_key_here
OPENAI_BASE_URL=https://openrouter.ai/api/v1
QWEN_SCORER_MODEL=qwen/qwen3-next-80b-a3b-instruct
```

### 3. Run the Application

```bash
python app.py
```

Open your browser and navigate to: `http://localhost:8081`

## Usage

### Step 1: Upload Q&A Pairs

Supported formats:
- **JSON**: Array of objects with `question`, `answer`, `source` fields
- **CSV**: Columns: `question`, `answer`, `source`

Example JSON:
```json
[
  {
    "question": "What is arkeology?",
    "answer": "Arkeology is the study of human history...",
    "source": "Document 1"
  },
  {
    "question": "How do arkeologists work?",
    "answer": "Arkeologists use various excavation techniques...",
    "source": "Document 1"
  }
]
```

Example CSV:
```csv
question,answer,source
"What is arkeology?","Arkeology is the study of human history...","Document 1"
"How do arkeologists work?","Arkeologists use various excavation techniques...","Document 1"
```

### Step 2: Configure Settings

- **Minimum IFD Score**: Lower threshold for valuable data
- **Maximum IFD Score**: Upper threshold (usually 1.0)
- **Difficulty Tiers**: Select which tiers to include (Easy/Medium/Hard)

### Step 3: Score Pairs

Click "Score Pairs" to analyze all uploaded Q&A pairs using the IFD metric.

### Step 4: Review Results

View:
- **IFD Scores**: Raw scores (0.0-1.0)
- **Difficulty Tiers**: Easy/Medium/Hard classification
- **Value Category**: High/Medium/Low training value
- **Dataset Statistics**: Distribution and insights

### Step 5: Filter & Export

- Apply filters to find specific pairs
- Download scored pairs as CSV
- Use for further training or curation

## IFD Score Interpretation

| IFD Range | Difficulty | Value Category | Recommendation |
|-----------|------------|---|---|
| 0.0 - 0.33 | Easy | Low | Use sparingly |
| 0.33 - 0.67 | Medium | Medium | Useful data |
| 0.67 - 1.0 | Hard | High | Prioritize for training |

## API Endpoints

### GET `/api/health`
Check API configuration status.

### GET `/api/verify-connection`
Verify connection to LLM API.

### POST `/api/upload-pairs`
Upload Q&A pairs file.

**Request**:
```json
{
  "file": <binary file>
}
```

**Response**:
```json
{
  "filename": "pairs.json",
  "count": 10,
  "pairs": [...]
}
```

### POST `/api/score-pairs`
Score Q&A pairs using IFD metric.

**Request**:
```json
{
  "pairs": [...],
  "source_text": ""
}
```

**Response**:
```json
{
  "pairs": [
    {
      "question": "...",
      "answer": "...",
      "source": "...",
      "ifd_score": 0.65,
      "conditioned_score": 0.8,
      "direct_score": 0.65,
      "tier": "medium",
      "value_category": "medium",
      "recommendation": "..."
    }
  ],
  "statistics": {...}
}
```

### POST `/api/filter-pairs`
Filter scored pairs by criteria.

### POST `/api/download-scored-pairs`
Export scored pairs to CSV.

## File Structure

```
QnA_Scoring_Interface/
├── app.py                  # Flask application
├── core.py                 # IFD scoring logic
├── requirements.txt        # Python dependencies
├── .env.example           # Environment template
├── README.md              # This file
├── templates/
│   └── index.html         # Web interface
└── static/
    ├── css/
    └── js/
```

## Performance

- **Fast Scoring**: ~2-5 seconds per pair (depends on API)
- **Batch Processing**: Score 100 pairs in ~3-5 minutes
- **Memory**: Minimal (processes streamed responses)

## Requirements

- Python 3.8+
- Flask 3.0+
- OpenAI Python SDK
- Active API credentials (OpenRouter or similar)

## Troubleshooting

### "API credentials not configured"
- Ensure `.env` file exists with valid credentials
- Check `OPENAI_API_KEY` and `OPENAI_BASE_URL`

### Scoring takes too long
- API rate limits may be in effect
- Consider using a faster model or upgrading API tier
- Process in smaller batches

### Connection errors
- Verify internet connection
- Check API endpoint URL
- Ensure API key is valid and has remaining quota

## Differences from Generator

| Aspect | Generator | Scorer |
|--------|-----------|--------|
| Purpose | Generate Q&A pairs | Score existing pairs |
| Input | Raw text documents | Q&A pairs |
| Output | Q&A pairs + metadata | Scored pairs + metrics |
| Port | 8080 | 8081 |
| Scoring Metric | Heuristic-based | IFD-based |

## Research Background

Based on the Cherry_LLM paper:
- **Title**: "From Quantity to Quality: Boosting LLM Performance with Self-Guided Data Selection for Instruction Tuning"
- **Venue**: NAACL 2024
- **Key Concept**: Perplexity and difficulty-based data selection
- **GitHub**: https://github.com/tianyi-lab/Cherry_LLM

## License

MIT License - Feel free to use and modify

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review API documentation
3. Check Cherry_LLM paper for methodology details

---

**Happy Scoring!** 🎯

