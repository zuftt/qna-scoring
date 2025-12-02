# QnA Scoring Interface - Context & Project State

## 🎯 Project Overview

This is a **standalone web application for scoring Bahasa Melayu Q&A pairs** using the IFD (Instruction Following Difficulty) metric from the Cherry_LLM research paper.

### Separation of Concerns
- **Generator** (`QnA_Pair_Generator/`) - Generates Q&A pairs from text
- **Scorer** (this folder) - Scores already-generated Q&A pairs
- **Independent**: Run on separate ports (8080 vs 8081), different codebase

## 📂 Project Structure

```
QnA_Scoring_Interface/
├── app.py                              (Flask app - 260 lines)
├── core.py                             (IFD scoring engine - 320 lines)
├── requirements.txt                    (Dependencies)
├── .env.example                        (Config template)
├── README.md                           (App documentation)
├── templates/
│   └── index.html                      (Web UI - 716 lines)
├── docs/                               (Folder with more docs)
└── [Other docs]
    ├── CHERRY_LLM_QUICK_SUMMARY.md
    ├── CHERRY_LLM_INTEGRATION_ANALYSIS.md
    ├── SCORING_IMPLEMENTATION_GUIDE.md
    ├── ADVANCED_SCORING_TECHNIQUES.md
    ├── SCORING_ARCHITECTURE.md
    ├── SETUP_GUIDE.md
    └── QUICK_REFERENCE.md
```

## 🔧 Core Files & Responsibilities

### `app.py` - Flask Application
**Purpose**: HTTP API server
**Routes**:
- `GET /api/health` - Check configuration
- `GET /api/verify-connection` - Test API connection
- `POST /api/upload-pairs` - Upload JSON/CSV with Q&A pairs
- `POST /api/score-pairs` - Score uploaded pairs using IFD
- `POST /api/filter-pairs` - Filter by criteria
- `POST /api/download-scored-pairs` - Export results to CSV

**Key Functions**:
- `upload_pairs()` - Parse JSON/CSV files
- `score_pairs()` - Call core.batch_score_pairs_ifd()
- `filter_pairs()` - Filter by score/tier
- `download_scored_pairs()` - Generate CSV export

**Port**: 8081

### `core.py` - IFD Scoring Engine
**Purpose**: Calculate IFD scores for Q&A pairs

**Key Functions**:
- `calculate_ifd_score(pair, source_text)` - Main scoring function
  - Calculates `sθ(A|Q)` - Conditioned answer score
  - Calculates `sθ(A)` - Direct answer score
  - Returns `IFD = sθ(A|Q) / sθ(A)` (normalized 0-1)
  - Falls back to heuristic if API fails

- `batch_score_pairs_ifd(pairs, source_text)` - Score multiple pairs

- `estimate_ifd_heuristic()` - Fallback scoring without API

- `compare_pairs_by_ifd()` - Analyze dataset distribution

- `rank_pairs_by_ifd()` - Sort by IFD score

- `filter_high_value_pairs()` - Keep only high IFD pairs

**API Integration**:
- Uses `chat()` helper to call Qwen LLM
- 2 API calls per pair (conditioned + direct)
- ~2-5 seconds per pair

### `templates/index.html` - Web UI
**Purpose**: User interface for scoring
**Features**:
- Drag-and-drop file upload
- Real-time scoring progress
- Interactive statistics dashboard
- Difficulty tier badges (Easy/Medium/Hard)
- IFD score visualization
- Filtering controls
- CSV export
- Responsive design

**Key Sections**:
- Header with status indicator
- Upload card with drag-drop area
- Settings card for filter configuration
- Results section with:
  - Statistics grid (totals, avg, distribution)
  - Data table with scores
  - Insights panel

## 🎯 IFD Scoring Explained

### Formula
```
IFD = sθ(A|Q) / sθ(A)
```

### Calculation Process
1. **Conditioned Score** `sθ(A|Q)`:
   - Ask LLM: "How hard is it to generate this answer given the question?"
   - Scale 1-10, convert to 0-1

2. **Direct Score** `sθ(A)`:
   - Ask LLM: "How hard is it to generate this text independently?"
   - Scale 1-10, convert to 0-1

3. **IFD Score**:
   - Divide conditioned by direct
   - Normalize to 0-1 range
   - Higher = more valuable for training

### Score Interpretation
| Range | Tier | Value | Recommendation |
|-------|------|-------|---|
| 0.0-0.33 | Easy | Low | Use sparingly |
| 0.33-0.67 | Medium | Medium | Useful data |
| 0.67-1.0 | Hard | High | Prioritize for training |

**Key Insight**: High IFD = Model struggles to follow instruction = Valuable for instruction tuning

## 🚀 How It Works

### User Workflow
```
1. User uploads Q&A pairs (JSON/CSV)
   ↓
2. App validates format
   ↓
3. User clicks "Score Pairs"
   ↓
4. app.py calls core.batch_score_pairs_ifd()
   ↓
5. For each pair:
   - calculate_ifd_score() is called
   - Makes 2 LLM API calls
   - Gets scores back
   ↓
6. Results displayed in UI:
   - IFD scores
   - Difficulty tiers
   - Value categories
   ↓
7. User can filter/export
```

### Data Flow
```
Frontend (index.html)
  ↓ (fetch POST request)
Backend (app.py)
  ↓
Core Engine (core.py)
  ↓ (2 API calls per pair)
Qwen LLM (via OpenRouter)
  ↓
Results (IFD scores)
  ↓ (JSON response)
Frontend (displays in table/stats)
```

## 📊 Input/Output Formats

### Input (Accepted Formats)

**JSON**:
```json
[
  {
    "question": "What is X?",
    "answer": "X is...",
    "source": "Document 1"
  }
]
```

**CSV**:
```csv
question,answer,source
"What is X?","X is...","Document 1"
"How does X work?","X works by...","Document 1"
```

### Output (CSV Export)

```csv
Question,Answer,Source,IFD Score,Difficulty Tier,Value Category,Conditioned Score,Direct Score,Recommendation
"What is X?","X is...","Doc1",0.654,medium,medium,0.75,0.65,"Medium value - useful data"
```

## 🔑 Configuration

### Environment (.env)
```dotenv
OPENAI_API_KEY=your_openrouter_key
OPENAI_BASE_URL=https://openrouter.ai/api/v1
QWEN_SCORER_MODEL=qwen/qwen3-next-80b-a3b-thinking
```

### Constants (in core.py)
- API timeout/retries
- Temperature for LLM calls (0.0 for consistency)
- Heuristic thresholds

## 🐛 Error Handling

**Current Strategy**:
1. Try API call
2. If API fails → Fallback to heuristic scoring
3. Log error but continue processing
4. Return result with note about scoring method

**Common Errors**:
- API rate limit → Try again later
- Invalid API key → Check .env
- Malformed input → Validate JSON/CSV
- Network timeout → Retry with longer timeout

## 📈 Performance

| Metric | Value |
|--------|-------|
| Score time per pair | 2-5 seconds |
| API calls per pair | 2 (conditioned + direct) |
| 100 pairs | ~5-10 minutes |
| Memory usage | Minimal |
| Concurrent requests | Limited by API tier |

**Bottleneck**: API calls (not local computation)

## 🔄 Research Context

**Based on**: Cherry_LLM paper (NAACL 2024)
- Title: "From Quantity to Quality: Boosting LLM Performance with Self-Guided Data Selection"
- Key Concept: IFD as difficulty metric
- Application: Data filtering for instruction tuning
- This app: Standalone implementation for scoring

## 📚 Documentation

Read these in order:
1. **QUICK_REFERENCE.md** - 2-minute overview
2. **CHERRY_LLM_QUICK_SUMMARY.md** - 5-minute intro
3. **SETUP_GUIDE.md** - How to set up
4. **README.md** - App-specific docs
5. **CHERRY_LLM_INTEGRATION_ANALYSIS.md** - Deep dive
6. **SCORING_IMPLEMENTATION_GUIDE.md** - Code examples
7. **ADVANCED_SCORING_TECHNIQUES.md** - Advanced features
8. **SCORING_ARCHITECTURE.md** - System design

## 🎯 Current State

✅ **Completed**:
- Flask backend with all endpoints
- IFD scoring engine (with heuristic fallback)
- Beautiful web UI
- File upload handling (JSON/CSV)
- Filtering system
- CSV export
- Error handling
- Documentation

⏳ **To Do** (as needed):
- Add database for storing results
- User authentication
- Batch scheduling
- Advanced visualizations
- Performance optimization
- Unit/integration tests

## 🚀 To Run

```bash
# Setup (one-time)
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Create .env with API credentials
echo "OPENAI_API_KEY=your_key" > .env
echo "OPENAI_BASE_URL=https://openrouter.ai/api/v1" >> .env

# Run
python app.py

# Visit
http://localhost:8081
```

## 📞 Quick Reference

| Task | File | Function |
|------|------|----------|
| Add new API endpoint | app.py | Add @app.route() |
| Change scoring logic | core.py | Modify calculate_ifd_score() |
| Update UI | templates/index.html | Edit HTML/CSS/JS |
| Adjust config | .env | Update variables |
| See performance | core.py | Check function signatures |

## 🎓 Key Learning Points

- **IFD**: Metric for instruction difficulty
- **Multi-step scoring**: Conditioned vs direct scores
- **Fallback strategy**: Always have heuristic backup
- **API efficiency**: Batch processing > individual calls
- **User experience**: Real-time feedback is critical

## 🔗 Related

- **Generator**: `/QnA_Pair_Generator/` - Creates pairs
- **Both**: Use same API (OpenRouter)
- **Workflow**: Generate → Score → Filter → Use

---

**Last Updated**: Dec 1, 2024

**For detailed technical info, see documentation files**

