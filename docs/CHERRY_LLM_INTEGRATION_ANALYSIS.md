# Cherry_LLM Integration Analysis for QNA Pair Scoring System

## Executive Summary
Your QnA Pair Generator can leverage Cherry_LLM's **perplexity-based difficulty scoring** and **evaluation methodology** to implement a sophisticated QNA pair scoring system. This document outlines what you can use and how to integrate it.

---

## 1. Key Components from Cherry_LLM You Can Use

### 1.1 **Perplexity-Based Difficulty Scoring** (Core Innovation)
**Source**: Cherry_LLM NAACL'24 paper - "Self-data filtering of LLM instruction-tuning data using a novel perplexity-based difficulty score"

**What it does**:
- Scores each Q&A pair based on difficulty/complexity without using other external models
- Uses language model perplexity as a metric for data quality
- Lower perplexity = more predictable/easier content
- Higher perplexity = more complex/harder content

**How to use in your system**:
```
Your current flow: Generate → Review → Accept/Reject
Enhanced flow:    Generate → Review → Accept/Reject → Score (difficulty/quality)
```

**Advantages**:
- Single model inference (no need for multiple evaluators)
- Objective, quantifiable metric
- Can filter/rank your Q&A pairs by difficulty level
- No external API calls needed beyond your existing Qwen model

### 1.2 **LLM-based Evaluation Protocol** (GPT-4/ChatGPT Evaluation)
**Source**: Cherry_LLM evaluation scripts (`scripts/do_eval_*.sh`)

**What it does**:
- Uses GPT-4 or ChatGPT as judges to compare pairs
- Eliminates position bias when comparing two models/sets
- Provides side-by-side comparison scoring

**Potential applications in your system**:
- Compare "before review" vs "after review" Q&A pairs
- Score pair quality on multiple dimensions (factuality, clarity, relevance)
- A/B test different generation models

**Output format** (from their evaluation):
```json
{
  "question": "...",
  "model_a_response": "...",
  "model_b_response": "...",
  "winner": "model_a|model_b|tie",
  "score_a": 8.5,
  "score_b": 7.2,
  "reasoning": "..."
}
```

---

## 2. Scoring Dimensions You Can Implement

Based on Cherry_LLM's approach and your current review system, here are scoring metrics:

### **A. Difficulty Score** (Perplexity-based)
```python
def calculate_difficulty_score(question: str, answer: str, model) -> float:
    """
    Calculate perplexity-based difficulty score
    Returns: 0.0 (easiest) to 1.0 (hardest)
    """
    # Get perplexity from model
    # Normalize and return as difficulty score
```

### **B. Quality Score** (Multi-dimensional)
- **Relevance**: Is answer directly related to question?
- **Clarity**: Is the pair easy to understand?
- **Completeness**: Does answer fully address the question?
- **Grounding**: Is answer supported by source text? ✓ (Already in your reviewer)
- **Metadata-freeness**: No disallowed metadata? ✓ (Already in your reviewer)

### **C. Diversity Score**
- Semantic similarity to other questions (avoid duplicates)
- Different difficulty levels in your dataset
- Different question types (factual, analytical, creative)

### **D. Pedagogical Value Score** (Ranking-based)
- Difficulty appropriate for target audience
- Supports learning objectives
- Builds on prior knowledge

---

## 3. Implementation Options for Your System

### **Option A: Lightweight Scoring** (Recommended for MVP)
Add a simple scoring endpoint to your web app:

```python
# In core.py
def score_qa_pair(question: str, answer: str, source_text: str) -> Dict:
    """Score a single Q&A pair on multiple dimensions"""
    return {
        "difficulty": calculate_difficulty_score(answer),
        "clarity": score_clarity(question, answer),
        "relevance": score_relevance(question, answer, source_text),
        "grounding": score_grounding(answer, source_text),
        "overall": average_scores(...)
    }
```

**Location in flow**:
```
User uploads → Generate pairs → Review pairs → Score pairs → Preview+Download
                                                    ↑ NEW
```

### **Option B: Full Evaluation Pipeline** (Cherry_LLM inspired)
Implement full GPT-4 evaluation for comparing different generation strategies:

```python
def evaluate_pair_quality(pair_set_a: List[Dict], pair_set_b: List[Dict]) -> Dict:
    """Use LLM as judge to compare two sets of pairs"""
    # Implement Cherry_LLM's evaluation logic
    # Score each pair in both sets
    # Determine winner/ranking
```

### **Option C: Hybrid Approach** (Recommended)
1. **Fast local scoring** for every pair (difficulty, clarity, relevance)
2. **Optional GPT-4 scoring** for quality assurance or dataset curation
3. **User can enable/disable** full evaluation in settings

---

## 4. What NOT to Use from Cherry_LLM

❌ **Data selection filtering algorithms** - Your use case is different (generation vs. selection)
❌ **Training scripts** - Not needed for scoring
❌ **WizardLM/Alpaca training** - Your focus is Bahasa Melayu Q&A generation

---

## 5. Specific Code Patterns from Cherry_LLM

### **Pattern 1: Scoring Architecture**
```python
# From Cherry_LLM structure
class DataScorer:
    def __init__(self, model_name: str):
        self.model = model_name
    
    def score(self, text: str) -> float:
        """Single responsibility: calculate one metric"""
        pass

# Your implementation
class QAPairScorer:
    def score_difficulty(self, pair: Dict) -> float:
        pass
    
    def score_clarity(self, pair: Dict) -> float:
        pass
    
    def score_relevance(self, pair: Dict, source: str) -> float:
        pass
```

### **Pattern 2: Multi-stage Pipeline**
Cherry_LLM uses: `Select → Score → Filter → Train`
Your system: `Generate → Review → Score → Export`

---

## 6. Integration Roadmap

### **Phase 1: Quick Win** (2-3 hours)
```python
# Add to core.py
def score_pair_simple(pair: Dict, source_text: str) -> Dict:
    """Quick scoring without heavy computation"""
    return {
        "length_score": calculate_length_score(pair["answer"]),
        "diversity_score": check_duplicate_questions(pair["question"]),
        "metadata_score": 1.0 if no_metadata(pair) else 0.0,
        "overall": average([...])
    }
```

### **Phase 2: Medium Effort** (1-2 days)
```python
# Add to web.py
@app.route('/api/score-pairs', methods=['POST'])
def score_pairs():
    """Score a batch of pairs"""
    pairs = request.json['pairs']
    scored = [score_pair(p, source_text) for p in pairs]
    return jsonify({'scored_pairs': scored})
```

### **Phase 3: Advanced** (3-5 days)
Implement full Cherry_LLM-style evaluation with GPT-4 comparison

---

## 7. Concrete Scoring Formulas

### **Difficulty Score** (Using model perplexity)
```
difficulty_score = min(log(perplexity) / log(max_expected_perplexity), 1.0)
- Easy Q&A: 0.2-0.4
- Medium Q&A: 0.4-0.6
- Hard Q&A: 0.6-0.9
```

### **Overall Quality Score**
```
overall_quality = (
    0.25 * difficulty_score +        # Avoid too-easy or too-hard
    0.25 * clarity_score +           # Easy to understand
    0.25 * relevance_score +         # Stays on topic
    0.25 * grounding_score           # Supported by source ✓
)
```

---

## 8. File Structure for Implementation

```
core.py
├── (existing) generate_pairs_for_chunk()
├── (existing) review_pair()
├── (NEW) score_pair()              ← Add scoring functions here
├── (NEW) calculate_difficulty()
└── (NEW) calculate_clarity()

web.py
├── (existing) /api/generate
├── (NEW) /api/score-pairs          ← New endpoint
└── (NEW) /api/evaluate-batch       ← Optional GPT-4 evaluation

templates/index.html
└── (update UI to show scores in preview)
```

---

## 9. Recommended Starting Point

Given your current architecture, I recommend:

```python
# In core.py, add this function:

def score_qa_pair(pair: Dict, source_text: str, *, title: str = "") -> Dict:
    """
    Score a Q&A pair on multiple dimensions (Cherry_LLM inspired)
    
    Returns: {
        "difficulty": 0.0-1.0,
        "clarity": 0.0-1.0,
        "relevance": 0.0-1.0,
        "grounding": 0.0-1.0,
        "overall": 0.0-1.0,
        "tier": "easy|medium|hard"
    }
    """
    # Implementation here
    pass
```

Add UI to display scores in your preview panel:
```html
<!-- In templates/index.html -->
<div class="score-display">
    <span>Difficulty: <meter value="0.7" min="0" max="1"></meter></span>
    <span>Clarity: <meter value="0.85" min="0" max="1"></meter></span>
    <span>Overall: <meter value="0.78" min="0" max="1"></meter></span>
</div>
```

---

## 10. References

- Cherry_LLM GitHub: https://github.com/tianyi-lab/Cherry_LLM
- Paper: "From Quantity to Quality: Boosting LLM Performance with Self-Guided Data Selection for Instruction Tuning" (NAACL'24)
- Key insight: Perplexity-based difficulty scoring requires only your existing model (Qwen), no external evaluators needed

---

## 11. Quick Decision Matrix

| Need | Use Cherry_LLM | Implementation Effort |
|------|---|---|
| Score difficulty | ✅ Perplexity-based | **Low** (1 function) |
| Score clarity | ⚠️ Partial (use prompt) | **Medium** (LLM call) |
| Score relevance | ⚠️ Partial (check similarity) | **Low** (similarity metric) |
| Score quality vs quality | ✅ GPT-4 evaluation | **High** (full pipeline) |
| Filter by threshold | ✅ Yes | **Low** (filtering logic) |
| Rank by difficulty | ✅ Yes | **Low** (sorting) |

---

## Conclusion

Cherry_LLM's **perplexity-based difficulty scoring** is directly applicable to your QNA pair scoring system without needing additional models. You can implement a 3-tier scoring system (Easy/Medium/Hard) in ~1-2 days, enabling better dataset curation and educational value ranking for your Bahasa Melayu Q&A pairs.

