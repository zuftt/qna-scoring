#!/usr/bin/env python3
"""
Benchmark script to measure actual scoring time
Tests both thinking and instruct models
"""

import time
import sys
sys.path.insert(0, '/Users/muhdzafri/Documents/UKM/QnA_Scoring_Interface')

from dotenv import load_dotenv
import core

load_dotenv(override=True)

# Test Q&A pairs
test_pairs = [
    {
        "question": "Siapakah nama sebenar HAMKA?",
        "answer": "Nama sebenar HAMKA ialah Haji Abdul Malik bin Abdul Karim Amrullah, dan beliau dilahirkan di Nagari Sungai Batang, Maninjau, Sumatera Barat, Indonesia pada 17 Februari 1908."
    },
    {
        "question": "Apakah maksud jolokan 'Buya'?",
        "answer": "Jolokan 'Buya' ialah panggilan penghormatan masyarakat Minangkabau yang berasal daripada bahasa Arab, dan ia diperolehi semasa hayat HAMKA."
    },
    {
        "question": "Siapakah ayah HAMKA?",
        "answer": "Ayah HAMKA ialah Syeikh Abdul Karim bin Amrullah atau dikenali sebagai Haji Rasul, yang merupakan pelopor Gerakan Islah (tajdid) di Minangkabau."
    }
]

def benchmark_scoring(num_pairs=3):
    """Test actual scoring time"""
    print("🧪 SCORING BENCHMARK TEST")
    print("=" * 60)
    print(f"Model: {core.MODEL_SCORER}")
    print(f"Test Pairs: {num_pairs}")
    print("=" * 60)
    
    total_time = 0
    successful = 0
    failed = 0
    
    start_overall = time.time()
    
    for i, pair in enumerate(test_pairs[:num_pairs], 1):
        print(f"\n📍 Pair {i}/{num_pairs}")
        print(f"   Q: {pair['question'][:50]}...")
        
        try:
            pair_start = time.time()
            
            result = core.calculate_ifd_score(pair)
            
            pair_time = time.time() - pair_start
            total_time += pair_time
            successful += 1
            
            print(f"   ✅ Score: {result['ifd_score']:.2f} ({result['tier']})")
            print(f"   ⏱️  Time: {pair_time:.2f} seconds")
            
        except Exception as e:
            failed += 1
            print(f"   ❌ Error: {str(e)[:60]}")
    
    overall_time = time.time() - start_overall
    
    print("\n" + "=" * 60)
    print("📊 BENCHMARK RESULTS")
    print("=" * 60)
    print(f"✅ Successful: {successful}/{num_pairs}")
    print(f"❌ Failed: {failed}/{num_pairs}")
    
    if successful > 0:
        avg_time_per_pair = total_time / successful
        print(f"\n⏱️  Average time per pair: {avg_time_per_pair:.2f} seconds")
        print(f"⏱️  Total API time: {total_time:.2f} seconds")
        print(f"⏱️  Overall time (with overhead): {overall_time:.2f} seconds")
        
        # Extrapolate for 170 pairs
        print(f"\n📈 EXTRAPOLATION FOR 170 PAIRS:")
        print(f"   Estimated time: {avg_time_per_pair * 170:.0f} seconds")
        print(f"   = {avg_time_per_pair * 170 / 60:.1f} minutes")
        
        # Also show for different batch sizes
        print(f"\n📦 TIME ESTIMATES BY BATCH SIZE:")
        for batch_size in [10, 50, 100, 170]:
            est_time = avg_time_per_pair * batch_size
            print(f"   {batch_size:3d} pairs: {est_time:6.0f} sec ({est_time/60:5.1f} min)")

if __name__ == "__main__":
    # Test with 3 pairs first
    benchmark_scoring(num_pairs=3)
    
    print("\n" + "=" * 60)
    print("💡 NOTE: Real-world timing depends on:")
    print("   • OpenRouter API latency")
    print("   • Network speed")
    print("   • Rate limiting")
    print("   • Server load")
    print("=" * 60)

