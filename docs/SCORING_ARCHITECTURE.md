# QNA Pair Scoring System - Architecture & Design

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      Frontend (index.html)                       │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Upload Text → Preview Text → View Extracted Blocks        │  │
│  │      ↓                                              ↓      │  │
│  │  [Extract]  → [Generate Q&A] → [Score Pairs]  → [Filter]  │  │
│  │      ↓           ↓                 ↓ NEW          ↓        │  │
│  │  /api/extract  /api/generate   /api/score-pairs /filter   │  │
│  └────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓↑
        ┌─────────────────────────────────────────────────┐
        │          Backend (web.py + core.py)             │
        │                                                 │
        │  API Endpoints:                                │
        │  ├── /api/extract          (existing)          │
        │  ├── /api/generate         (existing)          │
        │  ├── /api/score-pairs      ← NEW               │
        │  ├── /api/filter-pairs     ← NEW               │
        │  └── /api/download-csv     (existing)          │
        │                                                 │
        │  Core Functions:                               │
        │  ├── score_qa_pair()       ← NEW               │
        │  ├── batch_score_pairs()   ← NEW               │
        │  ├── calculate_clarity()   ← NEW               │
        │  ├── calculate_grounding() ← NEW               │
        │  └── estimate_difficulty() ← NEW               │
        └─────────────────────────────────────────────────┘
                              ↓↑
        ┌─────────────────────────────────────────────────┐
        │        External AI Model (Qwen via API)         │
        │                                                 │
        │  Used for:                                     │
        │  ├── Generate Q&A pairs                        │
        │  ├── Review Q&A pairs                          │
        │  ├── (Optional) Score clarity/accuracy         │
        │  └── (Optional) Compare pairs                  │
        └─────────────────────────────────────────────────┘
```

---

## Scoring Pipeline

### Phase 1: Basic Scoring (Heuristic-based)

```
Input: Q&A Pair + Source Text
    ↓
┌──────────────────────────────────────────┐
│  Heuristic Scoring (No API Calls)       │
├──────────────────────────────────────────┤
│                                          │
│  1. Question Clarity Score               │
│     - Starts with question word?         │
│     - Has punctuation?                   │
│     - Optimal length (5-30 words)?       │
│     - Not too vague?                     │
│     → Output: 0.0-1.0                    │
│                                          │
│  2. Answer Grounding Score               │
│     - Word overlap with source?          │
│     - Key entities mentioned?            │
│     - Not hallucinating?                 │
│     → Output: 0.0-1.0                    │
│                                          │
│  3. Answer Length Score                  │
│     - Too short? (<10 words)             │
│     - Optimal length? (20-100 words)     │
│     - Too long? (>200 words)             │
│     → Output: 0.0-1.0                    │
│                                          │
│  4. Difficulty Score                     │
│     - Technical term density?            │
│     - Sentence complexity?               │
│     - Answer length?                     │
│     → Output: 0.0-1.0 (0=easy, 1=hard)   │
│                                          │
│  5. Diversity Score                      │
│     - Similar to existing questions?     │
│     - Unique phrasing?                   │
│     → Output: 0.0-1.0 (1=unique)         │
│                                          │
└──────────────────────────────────────────┘
    ↓
Combine Scores (Weighted Average)
    ↓
Overall Score = 0.20×clarity + 0.25×grounding + 0.20×difficulty 
              + 0.20×length + 0.15×diversity
    ↓
Output: Overall Score + Tier (Easy/Medium/Hard) + Recommendation (Keep/Review/Flag)
```

### Phase 2: Advanced Scoring (Optional - Uses API Calls)

```
Input: Q&A Pair + Source Text + Budget for API Calls
    ↓
┌──────────────────────────────────────────┐
│  LLM-Based Scoring (Uses Qwen API)      │
├──────────────────────────────────────────┤
│                                          │
│  1. Factual Accuracy Check               │
│     - Is answer factually correct?       │
│     - Is it supported by source?         │
│     Call: chat() with judge prompt       │
│     → Output: 0.0-1.0                    │
│                                          │
│  2. Completeness Check                   │
│     - Does answer fully address Q?       │
│     - Missing any key elements?          │
│     Logic: Based on question type        │
│     → Output: 0.0-1.0                    │
│                                          │
│  3. Clarity & Fluency Check              │
│     - Clear in Bahasa Melayu?            │
│     - Grammar errors?                    │
│     Call: chat() with clarity prompt     │
│     → Output: 0.0-1.0                    │
│                                          │
└──────────────────────────────────────────┘
    ↓
Combine All Scores (Advanced Weighting)
    ↓
Overall Score = 0.30×accuracy + 0.25×completeness + 0.25×clarity
              + 0.20×(medium_difficulty_bonus)
    ↓
Output: Multi-dimensional scores + Insights + Confidence level
```

### Phase 3: Comparative Evaluation (Optional - GPT-4 Judging)

```
Input: Multiple Q&A Pairs
    ↓
┌──────────────────────────────────────────┐
│  Batch Comparison (Cherry_LLM Style)    │
├──────────────────────────────────────────┤
│                                          │
│  1. Create comparison prompt              │
│     Include: All pairs + source snippet  │
│                                          │
│  2. Call LLM (or GPT-4) as judge        │
│     Prompt: "Rank these pairs best→worst│
│                                          │
│  3. Parse ranking response               │
│     Extract: "1: Pair 2, 2: Pair 1..."  │
│                                          │
│  4. Convert ranking to scores            │
│     Rank 1 → Score 1.0                   │
│     Rank 2 → Score 0.8                   │
│     Rank N → Score 0.1                   │
│                                          │
└──────────────────────────────────────────┘
    ↓
Output: Comparative rankings + pairwise scores
```

---

## Data Flow Diagram

### User's Perspective

```
         User's Browser (Frontend)
         ──────────────────────────
              1. Upload Text
                    ↓
         ┌──────────────────────┐
         │ Preview Extraction   │ (see TITLE/ABSTRACT/BODY)
         └──────────────────────┘
              2. Click "Generate"
                    ↓
         ┌──────────────────────┐
         │ Show Progress        │ (Generating Q&A...)
         └──────────────────────┘
              ↓ [After Generation]
         ┌──────────────────────┐
         │ Auto-Score Pairs     │ ← NEW FEATURE
         │ Show Scores/Tiers    │
         └──────────────────────┘
              3. View Results
                    ↓
         ┌──────────────────────┐
         │ Score Column Visible │
         │ Difficulty Badges    │
         │ Filter by Score      │
         └──────────────────────┘
              4. Download
                    ↓
         CSV with scores (optional)
```

### Backend's Perspective

```
Server-side Processing
─────────────────────

1. POST /api/generate
   ├─ Prefilter chunks
   ├─ Generate Q&A pairs (LLM call)
   ├─ Review pairs (LLM call)
   ├─ Deduplicate
   └─ Send 'complete' event with pairs
        ↓ NEW:
        └─ Trigger scoring in background

2. POST /api/score-pairs (NEW)
   ├─ Receive: pairs + source_text
   ├─ For each pair:
   │  ├─ score_qa_pair(pair, source_text)
   │  │  ├─ calculate_clarity()
   │  │  ├─ calculate_grounding()
   │  │  ├─ calculate_difficulty()
   │  │  ├─ calculate_length()
   │  │  └─ calculate_diversity()
   │  └─ Return scored pair
   ├─ Compute statistics
   └─ Return: scored_pairs + statistics

3. POST /api/filter-pairs (NEW)
   ├─ Receive: pairs + filters (min_score, tiers)
   ├─ Filter pairs
   └─ Return: filtered_pairs

4. POST /api/download-csv (existing)
   ├─ Include scores if available
   └─ Generate CSV
```

---

## Scoring Dimensions Explained

```
┌─────────────────────────────────────────────────────────────┐
│                   5 Dimensions of Quality                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. CLARITY (Question Quality)                             │
│     ┌─────────────────────────────────────────┐            │
│     │ Good:  "Apakah fungsi utama arkeologi?" │            │
│     │ Bad:   "Ini apa?"                       │            │
│     └─────────────────────────────────────────┘            │
│     Score 0.0 (confusing) → 1.0 (very clear)              │
│     Weight: 20% (important for usability)                  │
│                                                             │
│  2. GROUNDING (Factual Accuracy)                           │
│     ┌─────────────────────────────────────────┐            │
│     │ Good:  Answer uses words from source   │            │
│     │ Bad:   Answer is hallucination         │            │
│     └─────────────────────────────────────────┘            │
│     Score 0.0 (not supported) → 1.0 (well grounded)       │
│     Weight: 25% (critical for correctness)                 │
│                                                             │
│  3. DIFFICULTY (Complexity Level)                          │
│     ┌─────────────────────────────────────────┐            │
│     │ Easy:   Simple facts (0.0-0.33)        │            │
│     │ Medium: Concepts, explanations (0.33-0.67)          │
│     │ Hard:   Analysis, synthesis (0.67-1.0) │            │
│     └─────────────────────────────────────────┘            │
│     Score 0.0 (too simple) → 1.0 (too complex)            │
│     Weight: 20% (prefer balanced)                          │
│                                                             │
│  4. LENGTH (Answer Completeness)                           │
│     ┌─────────────────────────────────────────┐            │
│     │ Too short:   < 10 words     (score 0.5)│            │
│     │ Optimal:    20-100 words    (score 1.0)│            │
│     │ Too long:    > 200 words    (score 0.7)│            │
│     └─────────────────────────────────────────┘            │
│     Weight: 20% (ensures substantial answers)              │
│                                                             │
│  5. DIVERSITY (Uniqueness)                                 │
│     ┌─────────────────────────────────────────┐            │
│     │ Good:  Different from all other Qs  (1.0)           │
│     │ Bad:   Duplicate of existing Q     (0.0)            │
│     └─────────────────────────────────────────┘            │
│     Score 0.0 (duplicate) → 1.0 (unique)                  │
│     Weight: 15% (avoid redundancy)                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘

Final Overall Score = 0.20×C + 0.25×G + 0.20×D + 0.20×L + 0.15×D
                    = 0.0 (worst) to 1.0 (best)
```

---

## Difficulty Tier Classification

```
Difficulty Score Distribution

EASY (0.0 - 0.33)
├─ Simple definitions
├─ Direct facts from source
├─ Names, dates, places
└─ Example: "Siapa adalah arkeolog pertama?"

        |████
        |████
        |████
────────┼─────────────────────────
      0.0   0.33

MEDIUM (0.33 - 0.67)
├─ Conceptual questions
├─ Requires reasoning
├─ Connecting ideas
└─ Example: "Bagaimana arkeologi membantu memahami masa lalu?"

                    |████████
                    |████████
                    |████████
────────┼───────────┼─────────────────
      0.33        0.67

HARD (0.67 - 1.0)
├─ Analysis questions
├─ Synthesis required
├─ Multiple concepts combined
└─ Example: "Bagaimanakah temuan arkeologi di Bujang mengubah pemahaman?"

                                |████████
                                |████████
                                |████████
────────┼───────────┼───────────┼─────
      0.33        0.67       1.0

Dataset Goal: Balanced mix
└─ Ideal: 30% Easy, 40% Medium, 30% Hard
  OR depends on target audience
```

---

## Scoring Quality Levels

```
Overall Score Interpretation

0.0 - 0.2 | ❌ REJECT
├─ Major issues (accuracy, grounding, clarity)
└─ Recommendation: "flag" (needs manual review)

0.2 - 0.4 | ⚠️  POOR
├─ Multiple problems
└─ Recommendation: "flag" (likely remove)

0.4 - 0.6 | 🤔 QUESTIONABLE
├─ Some issues but potentially usable
└─ Recommendation: "review" (human decision)

0.6 - 0.75 | ✅ ACCEPTABLE
├─ Good enough for dataset
├─ Minor issues possible
└─ Recommendation: "review" (can keep)

0.75 - 0.9 | 👍 GOOD
├─ High quality
├─ Minimal issues
└─ Recommendation: "keep" (definitely include)

0.9 - 1.0 | 🌟 EXCELLENT
├─ Outstanding pair
├─ No issues found
└─ Recommendation: "keep" (premium quality)
```

---

## Implementation Timeline

### Week 1: Basic Scoring ⭐
```
Day 1: Set up scoring functions
│  └─ Add calculate_* functions to core.py
├─ Test with sample pairs
└─ Verify correctness

Day 2-3: Integrate with web app
│  ├─ Add /api/score-pairs endpoint
│  ├─ Add score display in UI
│  └─ Test end-to-end

Day 4: Polish & optimize
│  ├─ Add filtering UI
│  ├─ Add statistics display
│  └─ Performance tuning
└─ ✅ Basic scoring ready!

Result: Users see difficulty tiers + scores for each pair
```

### Week 2: Advanced Features ⭐⭐ (Optional)
```
Day 1: Advanced scoring class
│  └─ Create QAPairQualityScorer
├─ Implement LLM-based checks
└─ Test accuracy checking

Day 2-3: Batch comparison
│  ├─ Implement comparative ranking
│  ├─ Add confidence scores
│  └─ Test batch evaluation

Day 4: Dataset analytics
│  ├─ Compute statistics
│  ├─ Add visualization
│  └─ Export analysis
└─ ✅ Advanced features ready!

Result: Users see multi-dimensional analysis + confidence
```

### Week 3: LLM Evaluation (Optional) ⭐⭐⭐
```
Day 1: GPT-4 integration
│  └─ Set up GPT-4 API calls
├─ Implement comparative evaluation
└─ Test GPT-4 scoring

Day 2-3: Evaluation UI
│  ├─ Add evaluation endpoint
│  ├─ Show GPT-4 judgments
│  └─ Display reasoning

Day 4: Full evaluation pipeline
│  ├─ End-to-end testing
│  ├─ Cost analysis
│  └─ Optimization
└─ ✅ LLM evaluation ready!

Result: Expert-level evaluation using GPT-4
```

---

## Cherry_LLM Integration Points

```
Your System                 Cherry_LLM Concept
─────────────────          ──────────────────
Score Pairs             →   Data Selection Filter
                            (uses difficulty scores)

Difficulty Scoring     →   Perplexity-based IFD Score
                            (instruction following difficulty)

Multi-dimensional       →   Multiple evaluation dimensions
                            (accuracy, relevance, etc.)

LLM-as-judge           →   GPT-4 Evaluation Protocol
                            (compare models fairly)

Dataset Statistics     →   Data Quality Metrics
                            (distribution analysis)

Filtering by threshold →   Automatic filtering
                            (quality gates)
```

---

## Performance Considerations

```
Scoring Method          Speed        Cost         Quality
─────────────────────  ──────────  ────────────  ──────────
Basic Heuristic        ⚡⚡⚡ Fast    Free         Good
(no API calls)         ~100ms/pair              (70%)

Advanced LLM-based     ⚡ Slow       $$$          Very Good
(Qwen API calls)       ~2-5s/pair               (85%)

GPT-4 Evaluation       🐢 Very Slow  $$$$$       Excellent
(GPT-4 API calls)      ~5-10s/pair              (95%)

Batch Comparison       ⚡ Medium     $$           Excellent
(sample + compare)     ~1-2s/5 pairs            (90%)
```

**Recommendation**: Start with Basic Heuristic (free, fast), add others as needed

---

## File Organization

```
QnA_Pair_Generator/
│
├── core.py
│   ├── (existing) generate_pairs_for_chunk()
│   ├── (existing) review_pair()
│   ├── (existing) process_text_file()
│   │
│   ├── ✨ NEW SECTION: SCORING FUNCTIONS
│   ├─────────────────────────────────────
│   ├── calculate_question_clarity_score()
│   ├── calculate_grounding_score()
│   ├── calculate_answer_length_score()
│   ├── estimate_answer_difficulty()
│   ├── calculate_diversity_score()
│   ├── score_qa_pair()
│   └── batch_score_pairs()
│
├── web.py
│   ├── (existing) @app.route('/api/extract')
│   ├── (existing) @app.route('/api/generate')
│   ├── (existing) @app.route('/api/download-csv')
│   │
│   ├── ✨ NEW SECTION: SCORING ENDPOINTS
│   ├──────────────────────────────────────
│   ├── @app.route('/api/score-pairs')
│   └── @app.route('/api/filter-pairs')
│
├── templates/
│   └── index.html
│       ├── (existing) File upload UI
│       ├── (existing) Generation progress UI
│       ├── (existing) Preview UI
│       │
│       ├── ✨ NEW SECTION: SCORING UI
│       ├──────────────────────────────
│       ├── Score display columns
│       ├── Difficulty tier badges
│       ├── Score bars/meters
│       ├── Filter controls
│       ├── Statistics panel
│       └── CSS styling for scores
│
└── Documentation/
    ├── CHERRY_LLM_INTEGRATION_ANALYSIS.md
    ├── SCORING_IMPLEMENTATION_GUIDE.md
    ├── ADVANCED_SCORING_TECHNIQUES.md
    ├── CHERRY_LLM_QUICK_SUMMARY.md
    └── SCORING_ARCHITECTURE.md (this file)
```

---

## Next Steps

1. **Read** → `CHERRY_LLM_QUICK_SUMMARY.md` (overview)
2. **Read** → `CHERRY_LLM_INTEGRATION_ANALYSIS.md` (concepts)
3. **Implement** → `SCORING_IMPLEMENTATION_GUIDE.md` (code)
4. **Enhance** → `ADVANCED_SCORING_TECHNIQUES.md` (advanced features)
5. **Refer** → This file (architecture & design)

Start building! 🚀

