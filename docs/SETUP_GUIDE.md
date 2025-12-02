# Setup Guide - QnA Generator & Scoring System

## 📦 What You Have

Your project now has **two completely separate applications**:

```
/Users/muhdzafri/Documents/UKM/
├── QnA_Pair_Generator/          ← Existing app (generates Q&A pairs)
├── QnA_Scoring_Interface/       ← NEW app (scores Q&A pairs with IFD)
├── docs/                        ← Documentation (moved from generator folder)
└── README.md                    ← Main project README
```

## 🚀 Getting Started

### Step 1: Setup API Credentials

Both apps need the same API configuration. You only need to set this up once.

Get API key from: https://openrouter.ai/

### Step 2: Setup Generator (if not already done)

```bash
cd QnA_Pair_Generator

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure API credentials
cp ../ # (Create .env from your existing setup)

# Run on port 8080
python web.py
```

### Step 3: Setup Scorer (NEW)

```bash
cd QnA_Scoring_Interface

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure API credentials
cat > .env << 'EOF'
OPENAI_API_KEY=your_openrouter_key_here
OPENAI_BASE_URL=https://openrouter.ai/api/v1
QWEN_SCORER_MODEL=qwen/qwen3-next-80b-a3b-thinking
EOF

# Run on port 8081
python app.py
```

## 🎯 How to Use

### Typical Workflow

```
1. Generate Q&A Pairs (Generator)
   ├── Upload text file (.txt)
   ├── Click "Generate"
   ├── Review results
   └── Export as JSON/CSV
   
2. Score Q&A Pairs (Scorer)
   ├── Upload generated pairs (JSON/CSV)
   ├── Click "Score Pairs"
   ├── Review IFD scores and metrics
   ├── Filter high-value pairs
   └── Download scored pairs
```

### Port Reference

- **Generator**: http://localhost:8080 (Q&A generation)
- **Scorer**: http://localhost:8081 (Q&A evaluation)

## 📚 Documentation

Read these in order:

1. **docs/CHERRY_LLM_QUICK_SUMMARY.md** 
   - 5-minute overview of scoring system
   
2. **docs/CHERRY_LLM_INTEGRATION_ANALYSIS.md**
   - Deep dive into Cherry_LLM and IFD concepts
   
3. **docs/SCORING_IMPLEMENTATION_GUIDE.md**
   - Step-by-step implementation details
   
4. **docs/ADVANCED_SCORING_TECHNIQUES.md**
   - Advanced features and optimization
   
5. **docs/SCORING_ARCHITECTURE.md**
   - System design and architecture

## 🔧 Key Files

### Scorer App Structure

```
QnA_Scoring_Interface/
├── app.py                  # Flask application + routes
├── core.py                 # IFD scoring logic
├── requirements.txt        # Dependencies
├── .env.example           # Environment template
├── README.md              # Scorer-specific README
└── templates/
    └── index.html         # Web interface
```

### Main Functions in core.py

```python
def calculate_ifd_score(pair, source_text)
    # Calculate IFD score for a single pair
    # Returns: ifd_score, tier, value_category

def batch_score_pairs_ifd(pairs, source_text)
    # Score multiple pairs
    # Returns: List of scored pairs

def rank_pairs_by_ifd(pairs, reverse=True)
    # Rank pairs by IFD score

def filter_high_value_pairs(pairs, min_ifd=0.6)
    # Filter to keep only high-value pairs
```

### API Routes in app.py

```python
GET  /api/health              # Check configuration
GET  /api/verify-connection   # Test API connection
POST /api/upload-pairs        # Upload Q&A file
POST /api/score-pairs         # Score pairs with IFD
POST /api/filter-pairs        # Filter by criteria
POST /api/download-scored-pairs  # Export as CSV
```

## 📊 IFD Scoring Explained

**What is IFD?**
Measures how difficult it is for an LLM to follow an instruction (question) when generating a response (answer).

**High IFD** = Model struggles = Valuable for training
**Low IFD** = Model easily generates = Less valuable

**Example**:
- Easy question: "What is X?" → Low IFD → Low training value
- Complex question: "Analyze the implications of X in context Y..." → High IFD → High training value

## 🔄 Workflow Example

### Generate Q&A Pairs

1. Open Generator: http://localhost:8080
2. Upload your text file (Malay language)
3. Review extracted content
4. Click "Generate"
5. Wait for processing
6. Download CSV with generated pairs
7. Export as JSON for scorer

### Score Q&A Pairs

1. Open Scorer: http://localhost:8081
2. Upload JSON from generator
3. Set filters:
   - Min IFD Score: 0.4
   - Difficulty: Easy, Medium, Hard
4. Click "Score Pairs"
5. Review results:
   - IFD scores
   - Difficulty distribution
   - Value categories
6. Apply filters if needed
7. Download scored pairs as CSV

## ⚠️ Important Notes

### API Rate Limits
- Scoring is API-intensive (calls Qwen for each pair)
- 100 pairs ~ 5-10 minutes
- May hit rate limits
- Consider batching if scoring large datasets

### Separate Configuration
- Generator and Scorer can use different models
- Both need same API credentials setup
- Edit .env in each folder separately

### Port Conflicts
- If port 8080/8081 already in use:
  - Generator: Edit `web.py` line ~402
  - Scorer: Edit `app.py` line ~262

## 🆘 Troubleshooting

### "API credentials not configured"
```bash
# Check .env file exists in both folders
ls -la QnA_Pair_Generator/.env
ls -la QnA_Scoring_Interface/.env

# Should see both files with API key and URL
```

### Scoring times out
```bash
# Try with smaller batch or longer timeout
# Reduce number of pairs
# Check API status at openrouter.ai
```

### Port already in use
```bash
# Find process using port
lsof -i :8080
lsof -i :8081

# Kill if needed (macOS/Linux)
kill -9 <PID>
```

### Import errors
```bash
# Reinstall dependencies
pip install --force-reinstall -r requirements.txt
```

## 📋 Checklist

- [ ] API credentials obtained from OpenRouter
- [ ] Both .env files created with credentials
- [ ] Both apps have virtual environments
- [ ] Dependencies installed in both apps
- [ ] Generator running on port 8080
- [ ] Scorer running on port 8081
- [ ] Sample Q&A pairs generated
- [ ] Pairs scored successfully
- [ ] Results filtered and downloaded
- [ ] Documentation reviewed

## 🔗 Resources

- **OpenRouter**: https://openrouter.ai/
- **Cherry_LLM**: https://github.com/tianyi-lab/Cherry_LLM
- **Qwen Models**: https://qwen.alibaba.com/
- **Flask Docs**: https://flask.palletsprojects.com/

## 📞 Support

If issues arise:
1. Check `.env` files for correct credentials
2. Verify API key has remaining quota
3. Review error messages in console
4. Check documentation in `docs/` folder
5. Try with small batch first

---

**You're all set!** 🚀

Next: Open http://localhost:8080 to generate or http://localhost:8081 to score!

