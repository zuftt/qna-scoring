# QNA Pair Scoring System - Implementation Guide

## Quick Start: Add Scoring to Your System in 3 Steps

---

## Step 1: Basic Scoring Functions (Add to `core.py`)

```python
# Add these imports at the top of core.py
import math
from typing import Dict, Tuple
from collections import Counter
import re

# Add these functions to core.py (after existing functions)

def calculate_answer_length_score(answer: str) -> float:
    """
    Score based on answer length - avoid too short or too long answers
    Returns: 0.0-1.0 (1.0 = optimal length)
    """
    words = len(answer.split())
    # Optimal: 20-100 words
    # Penalize if too short (<10) or too long (>200)
    if words < 10:
        return max(0.0, words / 10 * 0.5)  # Too short
    elif words > 200:
        return max(0.0, 1.0 - (words - 200) / 200 * 0.5)  # Too long
    elif words < 20:
        return 0.5 + (words - 10) / 10 * 0.5
    elif words > 100:
        return 1.0 - (words - 100) / 100 * 0.3
    else:
        return 1.0  # Optimal range


def calculate_question_clarity_score(question: str) -> float:
    """
    Score based on question structure - good questions are clear and focused
    Returns: 0.0-1.0 (1.0 = clear question)
    
    Heuristics:
    - Starts with question word (Siapa, Apa, Bagaimana, Mengapa, etc.)
    - Contains punctuation (?, or .)
    - Not too long (>30 words is often unclear)
    - Not too short (<5 words is usually too vague)
    """
    q_words = len(question.split())
    q_lower = question.lower()
    
    score = 0.0
    
    # Check for question word start (BM)
    question_words = ['siapa', 'apa', 'bagaimana', 'mengapa', 'berapa', 'di', 'ke', 'yang mana', 'adakah']
    starts_with_q = any(q_lower.startswith(qw) for qw in question_words)
    score += 0.3 if starts_with_q else 0.0
    
    # Check for proper punctuation
    has_punctuation = '?' in question or '。' in question  # . or full-width period
    score += 0.2 if has_punctuation else 0.0
    
    # Check length (optimal: 5-30 words)
    if 5 <= q_words <= 30:
        score += 0.3
    elif 5 <= q_words <= 50:
        score += 0.2
    else:
        score += 0.0
    
    # Penalize very vague patterns
    vague_patterns = [r'\bits\b', r'\bini\b\s*\?', r'\bitu\b\s*\?', r'apa\s*ini', r'apa\s*itu']
    is_vague = any(re.search(pattern, q_lower) for pattern in vague_patterns)
    score -= 0.2 if is_vague else 0.0
    
    return max(0.0, min(1.0, score + 0.2))  # Normalize to 0-1


def calculate_grounding_score(answer: str, source_text: str) -> float:
    """
    Score how well the answer is grounded in source text
    Returns: 0.0-1.0 (1.0 = well grounded)
    
    Heuristics:
    - Check word overlap between answer and source
    - Named entities should appear in source
    """
    # Tokenize and normalize
    answer_tokens = set(answer.lower().split())
    source_tokens = set(source_text.lower().split())
    
    # Remove common stop words
    stop_words = {'yang', 'dan', 'di', 'ke', 'dari', 'untuk', 'adalah', 'ada', 'ini', 'itu', 'atau', 'akan', 'sudah', 'telah'}
    answer_tokens = answer_tokens - stop_words
    source_tokens = source_tokens - stop_words
    
    # Calculate overlap
    if not answer_tokens:
        return 0.5  # Empty answer, neutral score
    
    overlap = len(answer_tokens & source_tokens)
    coverage = overlap / len(answer_tokens)
    
    # Coverage > 50% = well grounded
    # Coverage > 30% = acceptable
    # Coverage < 30% = poorly grounded
    if coverage > 0.5:
        return 0.9
    elif coverage > 0.3:
        return 0.6
    else:
        return 0.3


def calculate_diversity_score(question: str, all_questions: List[str], threshold: float = 0.75) -> float:
    """
    Score based on how unique this question is compared to existing questions
    Returns: 0.0-1.0 (1.0 = very unique, 0.0 = very similar)
    """
    if not all_questions:
        return 1.0
    
    q_lower = question.lower().strip()
    max_similarity = 0.0
    
    for existing_q in all_questions:
        existing_lower = existing_q.lower().strip()
        similarity = difflib.SequenceMatcher(None, q_lower, existing_lower).ratio()
        max_similarity = max(max_similarity, similarity)
    
    # Convert similarity to diversity score (inverse)
    diversity = max(0.0, 1.0 - max_similarity)
    
    return diversity


def estimate_answer_difficulty(answer: str) -> float:
    """
    Estimate answer difficulty based on:
    - Vocabulary complexity (technical terms)
    - Sentence structure
    - Answer length
    
    Returns: 0.0-1.0 (1.0 = hardest)
    """
    words = answer.lower().split()
    word_count = len(words)
    
    # Count technical/complex terms (BM)
    technical_terms = [
        'arkeologi', 'interpretasi', 'analisis', 'metodologi', 
        'sinergis', 'fenomenologi', 'epistemologi', 'ontologi',
        'deskriptif', 'kualitatif', 'kuantitatif', 'empiris',
        'hipotesis', 'teori', 'kerangka', 'paradigma'
    ]
    
    technical_count = sum(1 for term in technical_terms if term in answer.lower())
    technical_density = technical_count / max(len(words), 1)
    
    # Sentence complexity (by punctuation)
    sentences = re.split(r'[。.!?!！？]', answer)
    avg_sentence_length = word_count / max(len([s for s in sentences if s.strip()]), 1)
    
    # Calculate difficulty score
    # Longer answers tend to be more complex
    length_factor = min(word_count / 200, 1.0) * 0.3  # Max 0.3
    
    # Technical density
    technical_factor = min(technical_density * 3, 1.0) * 0.3  # Max 0.3
    
    # Sentence complexity
    complexity_factor = min(avg_sentence_length / 30, 1.0) * 0.4  # Max 0.4
    
    difficulty = length_factor + technical_factor + complexity_factor
    
    return min(1.0, max(0.0, difficulty))


def score_qa_pair(pair: Dict, source_text: str, all_questions: List[str] = None) -> Dict:
    """
    Comprehensive scoring function for a Q&A pair
    
    Args:
        pair: {"question": str, "answer": str, "source": str}
        source_text: Original text chunk the pair came from
        all_questions: List of existing questions for diversity checking
    
    Returns: {
        "question": str,
        "answer": str,
        "scores": {
            "clarity": 0.0-1.0,
            "grounding": 0.0-1.0,
            "diversity": 0.0-1.0,
            "difficulty": 0.0-1.0,
            "length": 0.0-1.0,
            "overall": 0.0-1.0
        },
        "tier": "easy" | "medium" | "hard",
        "recommendation": "keep" | "review" | "flag"
    }
    """
    if all_questions is None:
        all_questions = []
    
    question = pair.get("question", "")
    answer = pair.get("answer", "")
    
    # Calculate individual scores
    clarity_score = calculate_question_clarity_score(question)
    grounding_score = calculate_grounding_score(answer, source_text)
    diversity_score = calculate_diversity_score(question, all_questions)
    difficulty_score = estimate_answer_difficulty(answer)
    length_score = calculate_answer_length_score(answer)
    
    # Weighted overall score
    overall = (
        0.20 * clarity_score +        # Clear questions are important
        0.25 * grounding_score +      # Grounding is critical
        0.15 * diversity_score +      # Avoid duplicates
        0.20 * difficulty_score +     # Balanced difficulty
        0.20 * length_score           # Appropriate length
    )
    
    # Determine difficulty tier
    if difficulty_score < 0.33:
        tier = "easy"
    elif difficulty_score < 0.67:
        tier = "medium"
    else:
        tier = "hard"
    
    # Recommendation logic
    if overall >= 0.75 and grounding_score >= 0.6:
        recommendation = "keep"
    elif overall >= 0.6 or grounding_score < 0.4:
        recommendation = "review"
    else:
        recommendation = "flag"
    
    return {
        "question": question,
        "answer": answer,
        "scores": {
            "clarity": round(clarity_score, 3),
            "grounding": round(grounding_score, 3),
            "diversity": round(diversity_score, 3),
            "difficulty": round(difficulty_score, 3),
            "length": round(length_score, 3),
            "overall": round(overall, 3)
        },
        "tier": tier,
        "recommendation": recommendation
    }


def batch_score_pairs(pairs: List[Dict], source_text: str) -> List[Dict]:
    """Score multiple pairs and include diversity scores"""
    questions = [p.get("question", "") for p in pairs]
    scored = []
    
    for pair in pairs:
        scored_pair = score_qa_pair(pair, source_text, questions)
        scored.append(scored_pair)
    
    return scored
```

---

## Step 2: Add Scoring Endpoint to Web App (Add to `web.py`)

```python
# Add this endpoint to web.py (after existing routes)

@app.route('/api/score-pairs', methods=['POST'])
def score_qa_pairs():
    """Score a batch of Q&A pairs"""
    try:
        data = request.json
        pairs = data.get('pairs', [])
        source_text = data.get('source_text', '')
        
        if not pairs:
            return jsonify({'error': 'No pairs provided'}), 400
        
        # Score all pairs
        scored_pairs = core.batch_score_pairs(pairs, source_text)
        
        # Calculate statistics
        overall_scores = [p['scores']['overall'] for p in scored_pairs]
        difficulty_dist = {'easy': 0, 'medium': 0, 'hard': 0}
        
        for p in scored_pairs:
            difficulty_dist[p['tier']] += 1
        
        stats = {
            'total': len(scored_pairs),
            'avg_score': round(sum(overall_scores) / len(overall_scores), 3) if overall_scores else 0,
            'min_score': round(min(overall_scores), 3) if overall_scores else 0,
            'max_score': round(max(overall_scores), 3) if overall_scores else 0,
            'difficulty_distribution': difficulty_dist,
            'high_quality': sum(1 for s in overall_scores if s >= 0.75),
            'flagged': sum(1 for p in scored_pairs if p['recommendation'] == 'flag')
        }
        
        return jsonify({
            'pairs': scored_pairs,
            'statistics': stats
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/filter-pairs', methods=['POST'])
def filter_pairs_by_score():
    """Filter pairs by difficulty tier or score threshold"""
    try:
        data = request.json
        pairs = data.get('pairs', [])
        min_score = data.get('min_score', 0.6)  # Default: filter low-quality
        tiers = data.get('tiers', ['easy', 'medium', 'hard'])  # Which tiers to keep
        recommendation = data.get('recommendation', None)  # Filter by recommendation
        
        filtered = []
        for pair in pairs:
            scores = pair.get('scores', {})
            overall = scores.get('overall', 0)
            tier = pair.get('tier', 'medium')
            rec = pair.get('recommendation', 'review')
            
            # Apply filters
            if overall < min_score:
                continue
            if tier not in tiers:
                continue
            if recommendation and rec != recommendation:
                continue
            
            filtered.append(pair)
        
        return jsonify({'filtered_pairs': filtered, 'count': len(filtered)})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

---

## Step 3: Update HTML UI to Display Scores (Update `templates/index.html`)

Add this section to display scores in your preview table:

```html
<!-- Add to the table headers in index.html -->
<th>Soalan</th>
<th>Jawapan</th>
<th>Kesukaran</th>
<th>Kejelasan</th>
<th>Skor Keseluruhan</th>
<th>Status</th>

<!-- Add to the table body rows -->
<tr>
    <td><%= question %></td>
    <td><%= answer %></td>
    <td>
        <span class="difficulty-badge" data-tier="<%= tier %>">
            <%= tier.toUpperCase() %>
        </span>
    </td>
    <td>
        <div class="score-bar">
            <div class="score-fill" style="width: <%= clarity * 100 %>%"></div>
        </div>
        <span class="score-value"><%= clarity.toFixed(2) %></span>
    </td>
    <td>
        <meter value="<%= overall %>" min="0" max="1"></meter>
        <span class="score-value"><%= overall.toFixed(2) %></span>
    </td>
    <td>
        <span class="recommendation-badge <%= recommendation %>">
            <%= recommendation.toUpperCase() %>
        </span>
    </td>
</tr>

<!-- Add CSS styling -->
<style>
.difficulty-badge {
    padding: 4px 8px;
    border-radius: 4px;
    font-weight: bold;
    font-size: 0.85em;
}

.difficulty-badge[data-tier="easy"] {
    background-color: #90EE90;
    color: #1a5d1a;
}

.difficulty-badge[data-tier="medium"] {
    background-color: #FFD700;
    color: #664d00;
}

.difficulty-badge[data-tier="hard"] {
    background-color: #FF6B6B;
    color: white;
}

.score-bar {
    display: inline-block;
    width: 80px;
    height: 6px;
    background-color: #e0e0e0;
    border-radius: 3px;
    overflow: hidden;
    margin-right: 8px;
}

.score-fill {
    height: 100%;
    background-color: #4CAF50;
    transition: width 0.3s ease;
}

.score-value {
    font-family: monospace;
    font-size: 0.9em;
    color: #666;
}

.recommendation-badge {
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 0.85em;
    font-weight: bold;
}

.recommendation-badge.keep {
    background-color: #c8e6c9;
    color: #2e7d32;
}

.recommendation-badge.review {
    background-color: #fff9c4;
    color: #f57f17;
}

.recommendation-badge.flag {
    background-color: #ffcccc;
    color: #c62828;
}

meter {
    width: 100%;
}
</style>
```

---

## Step 4: JavaScript to Call Scoring Endpoint

```javascript
// Add to your JavaScript in index.html

async function scoreGeneratedPairs(pairs, sourceText) {
    try {
        const response = await fetch('/api/score-pairs', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                pairs: pairs,
                source_text: sourceText
            })
        });
        
        if (!response.ok) throw new Error('Scoring failed');
        
        const data = await response.json();
        displayScoredPairs(data.pairs, data.statistics);
        return data.pairs;
    } catch (error) {
        console.error('Error scoring pairs:', error);
        showNotification('Error scoring pairs: ' + error.message, 'error');
    }
}

function displayScoredPairs(scoredPairs, statistics) {
    // Display statistics
    document.querySelector('.stats-container').innerHTML = `
        <div class="stat">
            <strong>Jumlah:</strong> ${statistics.total}
        </div>
        <div class="stat">
            <strong>Skor Purata:</strong> ${statistics.avg_score.toFixed(3)}
        </div>
        <div class="stat">
            <strong>Berkualiti Tinggi:</strong> ${statistics.high_quality}/${statistics.total}
        </div>
        <div class="stat">
            <strong>Bendera:</strong> ${statistics.flagged}
        </div>
        <div class="stat">
            <strong>Kesukaran:</strong> 
            Mudah: ${statistics.difficulty_distribution.easy} | 
            Sederhana: ${statistics.difficulty_distribution.medium} | 
            Sukar: ${statistics.difficulty_distribution.hard}
        </div>
    `;
    
    // Display scored pairs table
    const tableBody = document.querySelector('#pairs-table tbody');
    tableBody.innerHTML = scoredPairs.map(pair => `
        <tr>
            <td>${escapeHtml(pair.question)}</td>
            <td>${escapeHtml(pair.answer)}</td>
            <td><span class="difficulty-badge" data-tier="${pair.tier}">${pair.tier.toUpperCase()}</span></td>
            <td><meter value="${pair.scores.clarity}" min="0" max="1"></meter> ${pair.scores.clarity.toFixed(2)}</td>
            <td><meter value="${pair.scores.overall}" min="0" max="1"></meter> ${pair.scores.overall.toFixed(2)}</td>
            <td><span class="recommendation-badge ${pair.recommendation}">${pair.recommendation.toUpperCase()}</span></td>
        </tr>
    `).join('');
}

function filterByScore() {
    const minScore = parseFloat(document.querySelector('#min-score-filter').value) || 0.6;
    const selectedTiers = Array.from(document.querySelectorAll('input[name="tier-filter"]:checked'))
        .map(el => el.value);
    
    fetch('/api/filter-pairs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            pairs: currentScoredPairs,
            min_score: minScore,
            tiers: selectedTiers
        })
    })
    .then(r => r.json())
    .then(data => {
        displayScoredPairs(data.filtered_pairs, {
            total: data.count,
            avg_score: data.filtered_pairs.reduce((s, p) => s + p.scores.overall, 0) / data.count,
            high_quality: data.filtered_pairs.filter(p => p.scores.overall >= 0.75).length
        });
    })
    .catch(err => console.error('Error filtering:', err));
}
```

---

## Integration with Your Current Flow

### **Current Flow:**
```
Upload → Generate → Review → Export CSV
```

### **With Scoring:**
```
Upload → Generate → Review → Score → Filter/Rank → Export CSV
                                            ↑
                                      NEW STEP
```

### **Modify `/api/generate` in web.py:**

```python
# After pairs are generated and reviewed, add scoring step:

# In generate_with_progress() function, before sending 'complete' event:
scored_pairs = core.batch_score_pairs(pairs, file_content)

progress_queue.put({
    'type': 'complete',
    'pairs': scored_pairs,  # Now includes scores
    'count': len(scored_pairs),
    'statistics': calculate_statistics(scored_pairs),  # Add stats
    ...
})
```

---

## Testing the Implementation

```python
# Quick test in Python shell
from core import score_qa_pair, batch_score_pairs

# Test single pair
pair = {
    "question": "Apakah yang dimaksudkan dengan arkeologi?",
    "answer": "Arkeologi adalah kajian saintifik tentang sisa-sisa manusia dan tamadun yang telah lalu melalui analisis artifak, struktur, dan bukti lain yang tertinggal."
}

source = "Arkeologi merupakan disiplin ilmu yang mengkaji kehidupan manusia masa lalu melalui studi sistematis terhadap benda-benda budaya dan sisa-sisa material. Para arkeolog menggunakan berbagai teknik penggalian, klasifikasi, dan analisis untuk memahami tahapan perkembangan peradaban."

result = score_qa_pair(pair, source)
print(result)

# Test batch
pairs = [pair1, pair2, pair3]
results = batch_score_pairs(pairs, source)
```

---

## Summary

You now have:
1. ✅ **Scoring functions** - Ready to add to core.py
2. ✅ **Web endpoints** - Ready to add to web.py
3. ✅ **UI components** - Ready to add to templates/index.html
4. ✅ **JavaScript** - Ready to call scoring and display results

**Estimated implementation time: 2-3 hours**

Next step: Run the code and test with your existing Q&A pairs!

