# Advanced Scoring Techniques (Inspired by Cherry_LLM)

## For When You Want to Go Deeper

This document covers advanced techniques from Cherry_LLM research that you can implement for sophisticated scoring.

---

## 1. Perplexity-Based Difficulty Scoring (Cherry_LLM Core)

### Concept
Instead of heuristics, use the language model's **perplexity** as an objective measure of text complexity.

**Lower perplexity** = More predictable = Easier content
**Higher perplexity** = Less predictable = Harder content

### Implementation

```python
import math
from typing import List, Tuple

def calculate_perplexity(text: str, model_name: str = None) -> float:
    """
    Calculate perplexity of text using your Qwen model.
    
    Perplexity = exp(mean(negative log probabilities))
    
    You already have a chat() function that calls the model.
    We can use logit outputs if available from API, or estimate it.
    
    Args:
        text: Input text to calculate perplexity for
        model_name: Which model to use (default: your configured MODEL_GEN)
    
    Returns:
        Perplexity score (typically 1-1000+)
    """
    if model_name is None:
        model_name = MODEL_GEN
    
    # Method 1: Using model logprobs (if API supports it)
    # Most LLM APIs don't expose logprobs directly
    # So we use Method 2 instead
    
    # Method 2: Estimate via repeated sampling + scoring
    # Create a scoring prompt that asks model to rate the text's predictability
    scoring_prompt = f"""
    Teks berikut:
    {text}
    
    Pada skala 1-10, seberapa MUDAH (dapat diprediksi) teks ini?
    1 = Sangat sukar diprediksi (perplexity tinggi)
    10 = Sangat mudah diprediksi (perplexity rendah)
    
    Berikan hanya nomor 1-10.
    """
    
    try:
        response = chat(
            model_name,
            "You are a text complexity analyzer. Rate predictability 1-10.",
            scoring_prompt,
            temperature=0.0
        )
        # Extract number from response
        numbers = [int(c) for c in response if c.isdigit()]
        if numbers:
            # Convert predictability (1-10) to perplexity-like score (1-100)
            predictability = numbers[0]
            estimated_perplexity = 100 / predictability  # Inverse: high predictability = low perplexity
            return estimated_perplexity
    except:
        pass
    
    # Fallback: Use text statistics
    return estimate_perplexity_heuristic(text)


def estimate_perplexity_heuristic(text: str) -> float:
    """
    Fallback heuristic for estimating perplexity without calling model.
    
    Based on:
    - Vocabulary diversity (unique words / total words)
    - Sentence length variation
    - Word length distribution
    """
    import statistics
    
    words = text.lower().split()
    if not words:
        return 10.0
    
    # Vocabulary diversity (higher = more complex)
    unique_words = len(set(words))
    vocab_diversity = unique_words / len(words)  # 0.0-1.0
    
    # Word length distribution
    word_lengths = [len(w) for w in words]
    avg_word_length = statistics.mean(word_lengths) / 10  # Normalize
    
    # Sentence count and variation
    sentences = text.split('.')
    sentence_lengths = [len(s.split()) for s in sentences if s.strip()]
    
    if sentence_lengths:
        avg_sentence_length = statistics.mean(sentence_lengths) / 20  # Normalize
        try:
            sentence_variance = statistics.stdev(sentence_lengths) / 20  # Normalize
        except:
            sentence_variance = 0
    else:
        avg_sentence_length = 0
        sentence_variance = 0
    
    # Combine factors into perplexity estimate
    # Formula: perplexity ~ 10^(vocab_diversity + avg_word_length + avg_sentence_length)
    complexity_score = (
        vocab_diversity * 3 +
        avg_word_length * 2 +
        avg_sentence_length * 1 +
        sentence_variance * 0.5
    )
    
    perplexity = math.exp(complexity_score)
    
    return perplexity


def difficulty_score_from_perplexity(perplexity: float, min_pp: float = 5.0, max_pp: float = 500.0) -> float:
    """
    Convert perplexity to difficulty score (0.0-1.0)
    
    Args:
        perplexity: Perplexity value (typically 1-1000+)
        min_pp: Perplexity for "easy" (e.g., 5.0)
        max_pp: Perplexity for "hard" (e.g., 500.0)
    
    Returns:
        Difficulty score 0.0-1.0
    """
    # Use logarithmic scale for better distribution
    log_pp = math.log(max(perplexity, 1.0))
    log_min = math.log(min_pp)
    log_max = math.log(max_pp)
    
    difficulty = (log_pp - log_min) / (log_max - log_min)
    
    return max(0.0, min(1.0, difficulty))


# Example usage:
# pp = calculate_perplexity("Apakah itu arkeologi?")
# difficulty = difficulty_score_from_perplexity(pp)
# print(f"Perplexity: {pp}, Difficulty: {difficulty}")
```

---

## 2. Multi-Dimensional Quality Scoring (Like Cherry_LLM)

### Concept
Score pairs on multiple independent dimensions, then combine them.

```python
class QAPairQualityScorer:
    """Comprehensive scorer inspired by Cherry_LLM evaluation methodology"""
    
    def __init__(self, model_name: str = None):
        self.model = model_name or MODEL_GEN
        self.cache = {}  # Cache expensive calculations
    
    def score_factual_accuracy(self, pair: Dict, source_text: str) -> Tuple[float, str]:
        """
        Check if answer is factually accurate to source.
        Uses LLM as judge.
        
        Returns: (score: 0.0-1.0, reasoning: str)
        """
        q = pair.get("question", "")
        a = pair.get("answer", "")
        
        judge_prompt = f"""
        Soalan: {q}
        Jawapan: {a}
        
        Sumber teks:
        {source_text[:500]}  # First 500 chars of source
        
        Adakah jawapan TEPAT dan DISOKONG oleh sumber? Jawab: "YA" atau "TIDAK"
        """
        
        try:
            response = chat(
                self.model,
                "Anda adalah penilai ketepatan fakta. Jawab YA atau TIDAK.",
                judge_prompt,
                temperature=0.0
            )
            
            is_accurate = "ya" in response.lower() or "yes" in response.lower()
            score = 1.0 if is_accurate else 0.5
            
            return score, "Accurate" if is_accurate else "Questionable"
        except Exception as e:
            return 0.5, f"Error: {str(e)}"
    
    def score_completeness(self, pair: Dict) -> float:
        """
        Check if answer completely addresses the question.
        Uses heuristics.
        
        Returns: score 0.0-1.0
        """
        q = pair.get("question", "").lower()
        a = pair.get("answer", "").lower()
        
        # Extract question type
        q_type = self._extract_question_type(q)
        
        # Check for required elements
        completeness_score = 0.5  # Base score
        
        if q_type == "what":
            # "What" questions need definition or clear answer
            if len(a.split()) > 15:  # Substantial answer
                completeness_score = 0.9
            elif len(a.split()) > 8:
                completeness_score = 0.7
        elif q_type == "how":
            # "How" questions need steps/process
            has_steps = any(word in a for word in ["pertama", "kedua", "ketiga", "langkah", "kemudian"])
            completeness_score = 0.85 if has_steps else 0.65
        elif q_type == "why":
            # "Why" questions need explanation/cause
            has_cause = any(word in a for word in ["karena", "sebab", "disebabkan", "akibat"])
            completeness_score = 0.85 if has_cause else 0.65
        
        return completeness_score
    
    def score_clarity_and_fluency(self, pair: Dict) -> Tuple[float, str]:
        """
        Check if Q&A is clear and well-written in Bahasa Melayu.
        Uses LLM as judge.
        
        Returns: (score: 0.0-1.0, reasoning: str)
        """
        q = pair.get("question", "")
        a = pair.get("answer", "")
        
        clarity_prompt = f"""
        Soalan: {q}
        Jawapan: {a}
        
        Adakah soalan dan jawapan ini JELAS dan FASIH dalam Bahasa Melayu?
        Berikan skor: 1-5 (1=sangat buruk, 5=sangat baik)
        Berikan hanya angka.
        """
        
        try:
            response = chat(
                self.model,
                "Anda adalah penilai kejelasan bahasa.",
                clarity_prompt,
                temperature=0.0
            )
            
            # Extract score 1-5
            numbers = [int(c) for c in response if c.isdigit()]
            if numbers:
                score = numbers[0] / 5.0  # Convert 1-5 to 0.0-1.0
                reasons = {1: "Very unclear", 2: "Unclear", 3: "Acceptable", 4: "Clear", 5: "Very clear"}
                return score, reasons.get(numbers[0], "Unknown")
        except:
            pass
        
        # Fallback heuristic
        heuristic_score = self._clarity_heuristic(pair)
        return heuristic_score, "Heuristic"
    
    def _extract_question_type(self, question: str) -> str:
        """Extract question type: what, how, why, who, when, where"""
        q_lower = question.lower()
        
        if q_lower.startswith(("apa ", "apakah")):
            return "what"
        elif q_lower.startswith(("bagaimana", "bagaimanakah", "gimana")):
            return "how"
        elif q_lower.startswith(("mengapa", "kenapa", "kenapa", "sebab")):
            return "why"
        elif q_lower.startswith(("siapa", "siapakah")):
            return "who"
        elif q_lower.startswith(("bila", "bilakah", "kapan", "kailan")):
            return "when"
        elif q_lower.startswith(("di mana", "dimana")):
            return "where"
        else:
            return "other"
    
    def _clarity_heuristic(self, pair: Dict) -> float:
        """Heuristic for clarity when LLM call fails"""
        q = pair.get("question", "")
        a = pair.get("answer", "")
        
        # Check for basic clarity issues
        issues = 0.0
        
        # Long and potentially confusing
        if len(q.split()) > 50:
            issues += 0.1
        if len(a.split()) > 300:
            issues += 0.1
        
        # Check for unclear pronouns without antecedent
        unclear_pronouns = ["ini", "itu", "ia", "mereka", "nya"]
        unclear_count = sum(q.count(p) + a.count(p) for p in unclear_pronouns)
        if unclear_count > 5:
            issues += 0.15
        
        return max(0.0, 1.0 - issues)
    
    def comprehensive_score(self, pair: Dict, source_text: str) -> Dict:
        """
        Compute comprehensive quality score combining all dimensions.
        
        Returns: {
            "overall": 0.0-1.0,
            "dimensions": {
                "accuracy": 0.0-1.0,
                "completeness": 0.0-1.0,
                "clarity": 0.0-1.0,
                "difficulty": 0.0-1.0
            },
            "insights": [str, ...]
        }
        """
        accuracy, acc_reason = self.score_factual_accuracy(pair, source_text)
        completeness = self.score_completeness(pair)
        clarity, clarity_reason = self.score_clarity_and_fluency(pair)
        difficulty = estimate_answer_difficulty(pair.get("answer", ""))
        
        # Weighted combination (based on Cherry_LLM's approach)
        overall = (
            0.30 * accuracy +        # Most important: must be accurate
            0.25 * completeness +    # Important: must answer the question
            0.25 * clarity +         # Important: must be clear
            0.20 * (1 - abs(difficulty - 0.5) * 0.5)  # Prefer medium difficulty
        )
        
        insights = [
            f"Accuracy: {acc_reason}",
            f"Clarity: {clarity_reason}",
            f"Completeness: {'Complete' if completeness > 0.7 else 'Partial'}",
            f"Difficulty: {'Easy' if difficulty < 0.33 else 'Medium' if difficulty < 0.67 else 'Hard'}"
        ]
        
        return {
            "overall": round(overall, 3),
            "dimensions": {
                "accuracy": round(accuracy, 3),
                "completeness": round(completeness, 3),
                "clarity": round(clarity, 3),
                "difficulty": round(difficulty, 3)
            },
            "insights": insights
        }
```

---

## 3. Batch Evaluation (Cherry_LLM Style)

### Concept
Instead of scoring pairs individually, compare and rank them together.

```python
def batch_compare_pairs(pairs: List[Dict], source_text: str, sample_size: int = 5) -> List[Dict]:
    """
    Compare pairs to each other and assign relative ranks.
    Like Cherry_LLM's comparative evaluation.
    
    Useful for:
    - Finding the top N pairs
    - Understanding relative quality
    - Dataset composition
    """
    
    if len(pairs) <= sample_size:
        sample = pairs
    else:
        # Sample randomly for efficiency
        import random
        sample = random.sample(pairs, sample_size)
    
    # Create comparison prompt
    pairs_text = "\n\n".join([
        f"Pasangan {i+1}:\nSoalan: {p.get('question', '')}\nJawapan: {p.get('answer', '')}"
        for i, p in enumerate(sample)
    ])
    
    comparison_prompt = f"""
    Berikut adalah {len(sample)} pasangan Q&A:
    
    {pairs_text}
    
    Sumber:
    {source_text[:300]}
    
    Ranking dari TERBAIK (1) hingga TERBURUK ({len(sample)}):
    Format: "1: Pasangan X, 2: Pasangan Y, ..."
    Berikan hanya ranking, tanpa penjelasan.
    """
    
    try:
        response = chat(
            MODEL_GEN,
            "Anda adalah penilai kualitas Q&A. Rank pasangan dari terbaik ke terburuk.",
            comparison_prompt,
            temperature=0.0
        )
        
        # Parse ranking
        # Expected: "1: Pasangan 2, 2: Pasangan 1, ..."
        ranking = {}
        for line in response.split('\n'):
            if ':' in line:
                parts = line.split(':')
                if len(parts) >= 2:
                    try:
                        rank = int(parts[0].strip())
                        pair_ref = parts[1].strip()
                        # Extract pair number
                        pair_num = int(''.join(filter(str.isdigit, pair_ref))) - 1
                        ranking[pair_num] = rank
                    except:
                        pass
        
        # Assign scores based on ranking
        scored_pairs = []
        for idx, pair in enumerate(sample):
            rank = ranking.get(idx, len(sample))
            score = 1.0 - (rank / len(sample))  # Higher rank = higher score
            pair_with_score = pair.copy()
            pair_with_score['comparative_score'] = round(score, 3)
            pair_with_score['rank'] = rank
            scored_pairs.append(pair_with_score)
        
        return sorted(scored_pairs, key=lambda x: x['rank'])
    
    except Exception as e:
        print(f"Error in batch comparison: {e}")
        return sample
```

---

## 4. Dynamic Difficulty Calibration

### Concept
Calibrate difficulty levels based on your actual dataset distribution.

```python
def calibrate_difficulty_levels(pairs: List[Dict], source_text: str) -> Tuple[float, float]:
    """
    Calibrate what counts as "easy", "medium", "hard" for YOUR dataset.
    
    Returns: (medium_threshold, hard_threshold)
    
    Example:
    - Easy: difficulty < 0.4
    - Medium: 0.4 <= difficulty < 0.7
    - Hard: difficulty >= 0.7
    
    But after calibration:
    - Easy: difficulty < 0.3
    - Medium: 0.3 <= difficulty < 0.6
    - Hard: difficulty >= 0.6
    """
    if not pairs:
        return 0.5, 0.75
    
    # Calculate difficulty for all pairs
    difficulties = []
    for pair in pairs:
        d = estimate_answer_difficulty(pair.get("answer", ""))
        difficulties.append(d)
    
    difficulties.sort()
    
    # Use percentiles for calibration
    # 50th percentile = medium threshold (50% below, 50% above)
    # 75th percentile = hard threshold (75% below, 25% above)
    
    n = len(difficulties)
    medium_threshold = difficulties[n // 2]
    hard_threshold = difficulties[(3 * n) // 4]
    
    # Add some buffer
    buffer = (hard_threshold - medium_threshold) * 0.1
    
    return medium_threshold - buffer, hard_threshold + buffer
```

---

## 5. Confidence Scoring

### Concept
Estimate how confident the model is in each score.

```python
def add_confidence_scores(scored_pairs: List[Dict]) -> List[Dict]:
    """
    Add confidence metrics to scores.
    
    Confidence factors:
    - How consistent are individual dimension scores?
    - How well-grounded is the answer?
    - How clear is the question?
    """
    
    for pair in scored_pairs:
        scores = pair.get('scores', {})
        dimensions = [
            scores.get('clarity', 0.5),
            scores.get('grounding', 0.5),
            scores.get('difficulty', 0.5),
            scores.get('length', 0.5),
            scores.get('diversity', 0.5)
        ]
        
        # Calculate variance in scores
        import statistics
        if len(dimensions) > 1:
            variance = statistics.variance(dimensions)
            # Low variance = more consistent = higher confidence
            confidence = 1.0 - min(variance, 1.0)
        else:
            confidence = 0.5
        
        pair['confidence'] = round(confidence, 3)
        
        # Also add confidence reasoning
        if confidence > 0.8:
            pair['confidence_level'] = "High"
        elif confidence > 0.6:
            pair['confidence_level'] = "Medium"
        else:
            pair['confidence_level'] = "Low"
    
    return scored_pairs
```

---

## 6. Dataset-Level Metrics

### Concept
Analyze your entire dataset of Q&A pairs at once.

```python
def compute_dataset_statistics(pairs: List[Dict]) -> Dict:
    """
    Compute statistics about your entire dataset.
    Useful for understanding dataset balance and quality.
    """
    if not pairs:
        return {}
    
    scores = [p.get('scores', {}).get('overall', 0) for p in pairs]
    difficulties = [p.get('scores', {}).get('difficulty', 0) for p in pairs]
    clarities = [p.get('scores', {}).get('clarity', 0) for p in pairs]
    
    import statistics
    
    stats = {
        "total_pairs": len(pairs),
        "overall_quality": {
            "mean": round(statistics.mean(scores), 3),
            "median": round(statistics.median(scores), 3),
            "stdev": round(statistics.stdev(scores), 3) if len(scores) > 1 else 0,
        },
        "difficulty_distribution": {
            "easy": sum(1 for d in difficulties if d < 0.33),
            "medium": sum(1 for d in difficulties if 0.33 <= d < 0.67),
            "hard": sum(1 for d in difficulties if d >= 0.67),
        },
        "clarity_distribution": {
            "low": sum(1 for c in clarities if c < 0.4),
            "medium": sum(1 for c in clarities if 0.4 <= c < 0.7),
            "high": sum(1 for c in clarities if c >= 0.7),
        },
        "recommendations": {
            "keep": sum(1 for p in pairs if p.get('recommendation') == 'keep'),
            "review": sum(1 for p in pairs if p.get('recommendation') == 'review'),
            "flag": sum(1 for p in pairs if p.get('recommendation') == 'flag'),
        }
    }
    
    return stats
```

---

## Implementation Priority

### Quick Wins (< 1 hour):
1. Add heuristic perplexity estimation
2. Add completeness scoring
3. Add dataset statistics

### Medium Effort (1-2 hours):
1. LLM-based accuracy checking
2. Batch comparison scoring
3. Confidence scores

### Advanced (2-4 hours):
1. Full perplexity calculation from model
2. Complete quality scorer class
3. Difficulty calibration

---

## Integration Example

```python
# In web.py, create enhanced scoring endpoint:

@app.route('/api/advanced-score-pairs', methods=['POST'])
def advanced_score_pairs():
    """Advanced scoring using techniques from Cherry_LLM"""
    try:
        data = request.json
        pairs = data.get('pairs', [])
        source_text = data.get('source_text', '')
        use_llm_eval = data.get('use_llm_eval', False)  # Enable expensive LLM calls
        
        if use_llm_eval:
            # Use comprehensive scorer with LLM
            scorer = QAPairQualityScorer()
            scored_pairs = []
            for pair in pairs:
                result = scorer.comprehensive_score(pair, source_text)
                pair_with_score = pair.copy()
                pair_with_score.update(result)
                scored_pairs.append(pair_with_score)
        else:
            # Quick heuristic scoring
            scored_pairs = batch_score_pairs(pairs, source_text)
        
        # Add confidence scores
        scored_pairs = add_confidence_scores(scored_pairs)
        
        # Compute dataset statistics
        statistics = compute_dataset_statistics(scored_pairs)
        
        return jsonify({
            'pairs': scored_pairs,
            'statistics': statistics
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

---

## Conclusion

These advanced techniques give you:
- **Objective perplexity-based scoring** (like Cherry_LLM)
- **Multi-dimensional quality assessment**
- **Comparative evaluation** (like Cherry_LLM's GPT-4 judging)
- **Dataset-level insights**
- **Confidence estimates**

Start with the basic scoring (previous document), then add these advanced techniques as needed!

