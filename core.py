# Core IFD Scoring Engine
# Implements Instruction Following Difficulty (IFD) metric from Cherry_LLM
# Paper: "From Quantity to Quality: Boosting LLM Performance with Self-Guided Data Selection"

import os
import math
import json
import time
import concurrent.futures
from typing import Dict, List, Tuple, Optional, Callable
from dotenv import load_dotenv
from openai import OpenAI
import difflib

load_dotenv(override=True)

# Configuration
BASE_URL = os.getenv("OPENAI_BASE_URL")
API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_SCORER = os.getenv("QWEN_SCORER_MODEL", "qwen/qwen3-next-80b-a3b-instruct")

if not API_KEY or not BASE_URL:
    client = None
else:
    client = OpenAI(base_url=BASE_URL, api_key=API_KEY)

# ===== IFD SCORING FUNCTIONS =====

def chat(model: str, system: str, user: str, temperature: float = 0.2) -> str:
    """Helper function to call LLM"""
    if not client:
        raise ValueError("OpenAI client not initialized. Check API credentials.")
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ],
            temperature=temperature,
        )
        return resp.choices[0].message.content or ""
    except Exception as e:
        error_msg = str(e)
        print(f"Error calling API: {error_msg}")
        if "429" in error_msg or "rate limit" in error_msg.lower():
            raise ValueError("API rate limit exceeded. Please try again later or upgrade your plan.")
        if "401" in error_msg or "unauthorized" in error_msg.lower():
            raise ValueError("Invalid API key. Please check your credentials.")
        raise ValueError(f"API error: {error_msg}")

def calculate_ifd_score(pair: Dict, source_text: str = "") -> Dict:
    """
    Calculate IFD (Instruction Following Difficulty) score for a Q&A pair
    
    IFD = sθ(A|Q) / sθ(A)
    where:
    - sθ(A|Q) = Conditioned Answer Score (how hard to generate answer given question)
    - sθ(A) = Direct Answer Score (how hard to generate answer without question)
    
    High IFD = Model struggles to follow the instruction (valuable data)
    Low IFD = Model easily generates the answer (less valuable)
    
    Returns: {
        "ifd_score": 0.0-1.0,
        "conditioned_score": float,
        "direct_score": float,
        "tier": "easy" | "medium" | "hard",
        "value_category": "low" | "medium" | "high",
        "recommendation": str
    }
    """
    question = pair.get("question", "")
    answer = pair.get("answer", "")
    
    if not question or not answer:
        return {
            "ifd_score": 0.0,
            "conditioned_score": 0.0,
            "direct_score": 0.0,
            "tier": "medium",
            "value_category": "low",
            "recommendation": "Invalid pair - missing question or answer"
        }
    
    try:
        # Step 1: Calculate sθ(A|Q) - Answer complexity given question
        conditioned_prompt = f"""
Analyze the difficulty of generating this answer given the question:

Question: {question}
Answer: {answer}

Rate the difficulty on a scale 1-10:
1 = Very easy to generate (model can easily follow this instruction)
10 = Very hard to generate (model struggles to follow this instruction)

Provide only the number 1-10.
"""
        
        conditioned_response = chat(
            MODEL_SCORER,
            "You are an instruction difficulty analyzer.",
            conditioned_prompt,
            temperature=0.0
        )
        
        # Extract number
        conditioned_nums = [int(c) for c in conditioned_response if c.isdigit()]
        conditioned_difficulty = conditioned_nums[0] if conditioned_nums else 5
        conditioned_score = conditioned_difficulty / 10.0
        
        # Step 2: Calculate sθ(A) - Answer complexity without question
        direct_prompt = f"""
Analyze how difficult it is to generate this text independently:

Text: {answer}

Rate the intrinsic complexity on a scale 1-10:
1 = Very simple text
10 = Very complex text

Provide only the number 1-10.
"""
        
        direct_response = chat(
            MODEL_SCORER,
            "You are a text complexity analyzer.",
            direct_prompt,
            temperature=0.0
        )
        
        # Extract number
        direct_nums = [int(c) for c in direct_response if c.isdigit()]
        direct_difficulty = direct_nums[0] if direct_nums else 5
        direct_score = direct_difficulty / 10.0
        
        # Step 3: Calculate IFD = sθ(A|Q) / sθ(A)
        # Avoid division by zero
        if direct_score > 0:
            ifd_score = conditioned_score / direct_score
            # Normalize to 0-1
            # Cap at 2.0 ratio instead of 3.0 to get better distribution
            # Score of 1.0 = equal difficulty (neutral)
            # Score > 1.0 = question makes it harder (more instruction-following difficulty)
            # Score < 1.0 = question makes it easier (less instruction-following difficulty)
            ifd_score = min(1.0, max(0.0, (ifd_score - 0.5) / 1.5))  # Shift and scale
        else:
            ifd_score = conditioned_score
        
        # Step 4: Determine tier and category
        if ifd_score < 0.33:
            tier = "easy"
        elif ifd_score < 0.67:
            tier = "medium"
        else:
            tier = "hard"
        
        # Value category based on IFD score (higher IFD = higher value for training)
        if ifd_score > 0.7:
            value_category = "high"
            recommendation = "High value - prioritize for training"
        elif ifd_score > 0.4:
            value_category = "medium"
            recommendation = "Medium value - useful data"
        else:
            value_category = "low"
            recommendation = "Low value - less useful for training"
        
    except Exception as e:
        print(f"Error calculating IFD: {e}")
        # Fallback to heuristic
        ifd_score = estimate_ifd_heuristic(answer, question)
        conditioned_score = 0.0
        direct_score = 0.0
        tier = "medium"
        value_category = "medium"
        recommendation = f"Heuristic scoring: {str(e)}"
    
    return {
        "ifd_score": round(ifd_score, 3),
        "conditioned_score": round(conditioned_score, 3),
        "direct_score": round(direct_score, 3),
        "tier": tier,
        "value_category": value_category,
        "recommendation": recommendation
    }

def estimate_ifd_heuristic(answer: str, question: str = "") -> float:
    """
    Estimate IFD score using heuristics when API call fails
    
    Based on:
    - Answer length and complexity
    - Vocabulary diversity
    - Sentence structure variation
    """
    words = answer.lower().split()
    if not words:
        return 0.0
    
    # Vocabulary diversity
    unique_words = len(set(words))
    vocab_diversity = unique_words / len(words)
    
    # Technical term density
    technical_terms = [
        'arkeologi', 'interpretasi', 'analisis', 'metodologi',
        'sinergis', 'fenomenologi', 'epistemologi', 'ontologi',
        'deskriptif', 'kualitatif', 'kuantitatif', 'empiris'
    ]
    technical_count = sum(1 for term in technical_terms if term in answer.lower())
    technical_density = technical_count / max(len(words), 1)
    
    # Length factor
    length_factor = min(len(words) / 200, 1.0)
    
    # Combine factors
    ifd_heuristic = (vocab_diversity * 0.3 + technical_density * 0.3 + length_factor * 0.4)
    
    return min(1.0, max(0.0, ifd_heuristic))

def batch_score_pairs_ifd(pairs: List[Dict], source_text: str = "") -> List[Dict]:
    """
    Score multiple Q&A pairs with IFD metric
    
    Returns: List of pairs with IFD scores added
    """
    scored_pairs = []
    
    for idx, pair in enumerate(pairs):
        print(f"Scoring pair {idx+1}/{len(pairs)}...")
        
        # Add IFD scores
        ifd_result = calculate_ifd_score(pair, source_text)
        
        # Combine original pair with scores
        scored_pair = pair.copy()
        scored_pair.update(ifd_result)
        
        scored_pairs.append(scored_pair)
    
    return scored_pairs

def compare_pairs_by_ifd(pairs: List[Dict]) -> Dict:
    """
    Analyze pair distribution and provide insights
    
    Returns: {
        "total": int,
        "avg_ifd": float,
        "distribution": { "easy": int, "medium": int, "hard": int },
        "value_distribution": { "low": int, "medium": int, "high": int },
        "insights": [str]
    }
    """
    if not pairs:
        return {}
    
    ifd_scores = [p.get('ifd_score', 0) for p in pairs]
    tiers = [p.get('tier', 'medium') for p in pairs]
    categories = [p.get('value_category', 'medium') for p in pairs]
    
    insights = []
    
    # Calculate statistics
    avg_ifd = sum(ifd_scores) / len(ifd_scores) if ifd_scores else 0
    
    # Distribution analysis
    tier_dist = {
        'easy': tiers.count('easy'),
        'medium': tiers.count('medium'),
        'hard': tiers.count('hard')
    }
    
    value_dist = {
        'low': categories.count('low'),
        'medium': categories.count('medium'),
        'high': categories.count('high')
    }
    
    # Generate insights
    if value_dist['high'] > value_dist['low']:
        insights.append(f"✓ Good dataset quality: {value_dist['high']} high-value pairs")
    else:
        insights.append(f"⚠ Lower quality dataset: Only {value_dist['high']} high-value pairs")
    
    if tier_dist['medium'] > (len(pairs) * 0.5):
        insights.append("✓ Balanced difficulty distribution")
    else:
        insights.append(f"⚠ Unbalanced difficulty: {tier_dist['easy']} easy, {tier_dist['medium']} medium, {tier_dist['hard']} hard")
    
    if avg_ifd > 0.6:
        insights.append(f"✓ High average IFD score ({avg_ifd:.2f}): Good for instruction tuning")
    else:
        insights.append(f"⚠ Low average IFD score ({avg_ifd:.2f}): May need better data selection")
    
    return {
        "total": len(pairs),
        "avg_ifd": round(avg_ifd, 3),
        "min_ifd": round(min(ifd_scores), 3) if ifd_scores else 0,
        "max_ifd": round(max(ifd_scores), 3) if ifd_scores else 0,
        "distribution": tier_dist,
        "value_distribution": value_dist,
        "insights": insights
    }

def rank_pairs_by_ifd(pairs: List[Dict], reverse: bool = True) -> List[Dict]:
    """
    Rank pairs by IFD score (higher IFD = more valuable)
    
    Args:
        pairs: List of scored pairs
        reverse: If True, sort by descending IFD (highest first)
    
    Returns: Sorted list of pairs
    """
    return sorted(pairs, key=lambda x: x.get('ifd_score', 0), reverse=reverse)

def filter_high_value_pairs(pairs: List[Dict], min_ifd: float = 0.6) -> List[Dict]:
    """
    Filter to keep only high-value pairs (high IFD scores)
    
    Useful for curating training data
    """
    return [p for p in pairs if p.get('ifd_score', 0) >= min_ifd]

# ===== BATCH SCORING (FAST!) =====

def calculate_batch_ifd_scores(
    pairs: List[Dict],
    batch_size: int = 10,
    progress_callback: Optional[Callable] = None
) -> List[Dict]:
    """
    Score pairs in BATCHES (10x faster than one-by-one)
    
    Instead of:
      - 2 API calls per pair × 170 pairs = 340 calls
    
    We do:
      - 2 API calls per batch × 17 batches = 34 calls
      - 10x fewer API calls!
    
    Args:
        pairs: List of Q&A pairs to score
        batch_size: How many pairs per batch (default 10)
        progress_callback: Function to report progress
    
    Returns:
        List of scored pairs with IFD metrics
    """
    start_time = time.time()
    results = []
    total_pairs = len(pairs)
    
    # Split into batches
    batches = [
        pairs[i:i+batch_size]
        for i in range(0, len(pairs), batch_size)
    ]
    
    total_batches = len(batches)
    
    # ===== PHASE 1: Conditioned Scores (A|Q) =====
    
    conditioned_scores = []
    
    for batch_idx, batch in enumerate(batches):
        # Report progress
        if progress_callback:
            elapsed = time.time() - start_time
            progress_callback({
                'phase': 'scoring_conditioned',
                'batch': batch_idx + 1,
                'total_batches': total_batches,
                'pairs_done': min((batch_idx + 1) * batch_size, total_pairs),
                'total_pairs': total_pairs,
                'elapsed': elapsed,
                'status': f'Phase 1: Scoring {batch_idx + 1}/{total_batches}...'
            })
        
        # Build batch prompt
        batch_text = "\n".join([
            f"{j+1}. Question: {p['question']}\n   Answer: {p['answer'][:200]}..."
            if len(p['answer']) > 200 else
            f"{j+1}. Question: {p['question']}\n   Answer: {p['answer']}"
            for j, p in enumerate(batch)
        ])
        
        batch_prompt = f"""Analyze the difficulty of generating each answer given its question.
Rate each on a scale 1-10 (1=easy, 10=hard).

{batch_text}

Return ONLY the scores separated by commas. Example: 7,6,8,9,5
"""
        
        try:
            response = chat(
                MODEL_SCORER,
                "You are an instruction difficulty analyzer. Rate each Q&A pair.",
                batch_prompt,
                temperature=0.0
            )
            
            # Parse scores
            score_strs = response.replace(' ', '').split(',')
            scores = []
            for s in score_strs:
                try:
                    num = int(''.join(c for c in s if c.isdigit()))
                    if 1 <= num <= 10:
                        scores.append(num / 10.0)
                    else:
                        scores.append(0.5)  # Default if out of range
                except:
                    scores.append(0.5)
            
            # Ensure we have right number of scores
            while len(scores) < len(batch):
                scores.append(0.5)
            
            conditioned_scores.extend(scores[:len(batch)])
            
        except Exception as e:
            print(f"Error in batch {batch_idx}: {e}")
            conditioned_scores.extend([0.5] * len(batch))
    
    # ===== PHASE 2: Direct Scores (A) =====
    
    direct_scores = []
    
    for batch_idx, batch in enumerate(batches):
        # Report progress
        if progress_callback:
            elapsed = time.time() - start_time
            progress_callback({
                'phase': 'scoring_direct',
                'batch': batch_idx + 1,
                'total_batches': total_batches,
                'pairs_done': total_pairs // 2 + min((batch_idx + 1) * batch_size, total_pairs) // 2,
                'total_pairs': total_pairs,
                'elapsed': elapsed,
                'status': f'Phase 2: Analyzing complexity {batch_idx + 1}/{total_batches}...'
            })
        
        # Build batch prompt for direct scoring
        batch_text = "\n".join([
            f"{j+1}. {p['answer'][:200]}..."
            if len(p['answer']) > 200 else
            f"{j+1}. {p['answer']}"
            for j, p in enumerate(batch)
        ])
        
        batch_prompt = f"""Analyze the intrinsic complexity of generating each text independently.
Rate each on a scale 1-10 (1=simple, 10=complex).

{batch_text}

Return ONLY the scores separated by commas. Example: 4,5,3,6,2
"""
        
        try:
            response = chat(
                MODEL_SCORER,
                "You are a text complexity analyzer.",
                batch_prompt,
                temperature=0.0
            )
            
            # Parse scores
            score_strs = response.replace(' ', '').split(',')
            scores = []
            for s in score_strs:
                try:
                    num = int(''.join(c for c in s if c.isdigit()))
                    if 1 <= num <= 10:
                        scores.append(num / 10.0)
                    else:
                        scores.append(0.5)
                except:
                    scores.append(0.5)
            
            while len(scores) < len(batch):
                scores.append(0.5)
            
            direct_scores.extend(scores[:len(batch)])
            
        except Exception as e:
            print(f"Error in batch {batch_idx}: {e}")
            direct_scores.extend([0.5] * len(batch))
    
    # ===== PHASE 3: Calculate IFD and Format Results =====
    
    for i, pair in enumerate(pairs):
        if progress_callback and i % 10 == 0:
            elapsed = time.time() - start_time
            progress_callback({
                'phase': 'finalizing',
                'pairs_done': i,
                'total_pairs': total_pairs,
                'elapsed': elapsed,
                'status': f'Finalizing results {i}/{total_pairs}...'
            })
        
        conditioned = conditioned_scores[i] if i < len(conditioned_scores) else 0.5
        direct = direct_scores[i] if i < len(direct_scores) else 0.5
        
        # Calculate IFD
        if direct > 0:
            ifd_score = conditioned / direct
            ifd_score = min(1.0, max(0.0, ifd_score / 3.0))  # Normalize to 0-1
        else:
            ifd_score = conditioned
        
        # Determine tier
        if ifd_score < 0.33:
            tier = "easy"
        elif ifd_score < 0.67:
            tier = "medium"
        else:
            tier = "hard"
        
        # Value category
        if ifd_score > 0.7:
            value_category = "high"
            recommendation = "High value - prioritize for training"
        elif ifd_score > 0.4:
            value_category = "medium"
            recommendation = "Medium value - useful data"
        else:
            value_category = "low"
            recommendation = "Low value - less useful for training"
        
        results.append({
            'question': pair.get('question', ''),
            'answer': pair.get('answer', ''),
            'source': pair.get('source', ''),
            'ifd_score': round(ifd_score, 3),
            'conditioned_score': round(conditioned, 3),
            'direct_score': round(direct, 3),
            'tier': tier,
            'value_category': value_category,
            'recommendation': recommendation
        })
    
    total_time = time.time() - start_time
    
    return results

