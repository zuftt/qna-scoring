# Quick Reference Card

## 🎯 Project Overview

Two separate web apps for Bahasa Melayu Q&A pair generation and scoring.

| Aspect | Generator | Scorer |
|--------|-----------|--------|
| **Purpose** | Generate Q&A pairs from text | Score pairs using IFD metric |
| **Port** | 8080 | 8081 |
| **Input** | `.txt` files | JSON/CSV files |
| **Output** | Q&A pairs + CSV | Scored pairs + IFD metrics |
| **Metric** | Heuristic | IFD-based |

## 🚀 Quick Start (5 minutes)

### Generator
```bash
cd QnA_Pair_Generator
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python web.py
# Open http://localhost:8080
```

### Scorer
```bash
cd QnA_Scoring_Interface
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# Add API credentials to .env
python app.py
# Open http://localhost:8081
```

## 📁 Directory Structure

```
UKM/
├── QnA_Pair_Generator/     ← Generate Q&A pairs
├── QnA_Scoring_Interface/  ← Score Q&A pairs (NEW!)
├── docs/                   ← All documentation
├── README.md               ← Main project README
├── SETUP_GUIDE.md          ← Detailed setup
└── QUICK_REFERENCE.md      ← This file
```

## 🔑 API Setup (One-time)

1. Get key: https://openrouter.ai/
2. Create `.env` in both folders:
```dotenv
OPENAI_API_KEY=your_key
OPENAI_BASE_URL=https://openrouter.ai/api/v1
QWEN_SCORER_MODEL=qwen/qwen3-next-80b-a3b-thinking
```

## 📊 IFD Score Ranges

| Score | Tier | Value | Use |
|-------|------|-------|-----|
| 0.0-0.33 | Easy | Low | Sparingly |
| 0.33-0.67 | Medium | Medium | Standard |
| 0.67-1.0 | Hard | High | Prioritize |

## 🎬 Typical Workflow

```
1. Generator (8080)
   ├─ Upload .txt
   ├─ Preview content
   ├─ Generate
   └─ Download JSON

2. Scorer (8081)
   ├─ Upload JSON
   ├─ Score pairs
   ├─ View metrics
   ├─ Filter
   └─ Download CSV
```

## 📚 Documentation

| File | Content |
|------|---------|
| **CHERRY_LLM_QUICK_SUMMARY.md** | 5-min overview |
| **CHERRY_LLM_INTEGRATION_ANALYSIS.md** | Detailed concepts |
| **SCORING_IMPLEMENTATION_GUIDE.md** | Code examples |
| **ADVANCED_SCORING_TECHNIQUES.md** | Advanced features |
| **SCORING_ARCHITECTURE.md** | System design |

All in: `docs/` folder

## 🔧 Common Commands

### Generator
```bash
cd QnA_Pair_Generator
python web.py                    # Run
python -m venv .venv            # Create venv
pip install -r requirements.txt # Install deps
```

### Scorer
```bash
cd QnA_Scoring_Interface
python app.py                    # Run
python -m venv .venv            # Create venv
pip install -r requirements.txt # Install deps
```

## 🐛 Quick Troubleshooting

| Issue | Solution |
|-------|----------|
| "API not configured" | Check .env exists with credentials |
| Port in use | Kill process or change port in code |
| Import error | `pip install --force-reinstall -r requirements.txt` |
| Slow scoring | Try smaller batch, check API quota |
| Connection failed | Verify internet + API key |

## 🌐 Web Interfaces

### Generator (Port 8080)
- Upload `.txt` files
- Preview content
- Generate Q&A pairs
- Review results
- Export CSV/JSON

### Scorer (Port 8081)
- Upload JSON/CSV pairs
- Score with IFD metric
- View difficulty tiers
- Filter by score/tier
- Download scored pairs

## 📝 File Formats

### Input to Scorer (JSON)
```json
[
  {"question": "...", "answer": "...", "source": "..."}
]
```

### Input to Scorer (CSV)
```csv
question,answer,source
"Q1","A1","Source1"
"Q2","A2","Source2"
```

### Output from Scorer (CSV)
```csv
Question,Answer,IFD Score,Tier,Value,Recommendation
```

## 🎯 Key Concepts

**IFD** = Instruction Following Difficulty
- High IFD = Difficult for model = Valuable data
- Low IFD = Easy for model = Less valuable

**Tier** = Difficulty classification
- Easy (0.0-0.33)
- Medium (0.33-0.67)
- Hard (0.67-1.0)

**Value** = Training value category
- High (prioritize)
- Medium (useful)
- Low (sparingly)

## 📞 Support Resources

- **Cherry_LLM Paper**: https://github.com/tianyi-lab/Cherry_LLM
- **API**: https://openrouter.ai/
- **Documentation**: `docs/` folder
- **Setup Guide**: `SETUP_GUIDE.md`

## ✅ Initialization Checklist

- [ ] API key obtained
- [ ] .env files created in both folders
- [ ] Dependencies installed
- [ ] Generator runs on 8080
- [ ] Scorer runs on 8081
- [ ] Test with sample data
- [ ] Documentation reviewed

---

**For detailed setup**: See `SETUP_GUIDE.md`
**For all docs**: See `docs/` folder
**For API help**: See `QnA_Scoring_Interface/README.md`

