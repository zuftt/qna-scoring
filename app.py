# IFD-Based Q&A Scoring Interface
# Uses Instruction Following Difficulty (IFD) metric to score Q&A pairs
# Based on Cherry_LLM methodology

from flask import Flask, render_template, request, jsonify, send_file
import os
import csv
import json
import tempfile
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
import core

# Load environment variables
load_dotenv(override=True)

# Initialize Flask app
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()

# Allowed file extensions
ALLOWED_EXTENSIONS = {'json', 'csv', 'txt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def map_column_names(csv_dict_row):
    """
    Automatically map Bahasa Melayu column names to English.
    Supports both English and Bahasa Melayu column names.
    """
    # Mapping of Bahasa Melayu to English columns
    column_mapping = {
        'Soalan': 'question',
        'Jawapan': 'answer',
        'Sumber': 'source',
    }
    
    mapped_row = {}
    for key, value in csv_dict_row.items():
        # Check if column needs mapping
        mapped_key = column_mapping.get(key, key)
        mapped_row[mapped_key] = value
    
    return mapped_row

@app.route('/')
def index():
    """Render main scoring interface"""
    return render_template('index.html')

@app.route('/api/health', methods=['GET'])
def health_check():
    """Check if API is properly configured"""
    has_config = bool(core.API_KEY and core.BASE_URL)
    return jsonify({
        'configured': has_config,
        'model': core.MODEL_SCORER,
        'status': 'ready' if has_config else 'not_configured'
    })

@app.route('/api/upload-pairs', methods=['POST'])
def upload_pairs():
    """Upload and parse Q&A pairs from JSON/CSV"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Only JSON, CSV, or TXT files are supported'}), 400
        
        filename = secure_filename(file.filename)
        file_content = file.read().decode('utf-8')
        
        # Parse based on file type
        pairs = []
        if filename.endswith('.json'):
            pairs = json.loads(file_content)
            if not isinstance(pairs, list):
                pairs = [pairs]
        elif filename.endswith('.csv'):
            import io
            reader = csv.DictReader(io.StringIO(file_content))
            for row in reader:
                # Map Bahasa Melayu columns to English
                mapped_row = map_column_names(row)
                if mapped_row.get('question') and mapped_row.get('answer'):
                    pairs.append({
                        'question': mapped_row['question'],
                        'answer': mapped_row['answer'],
                        'source': mapped_row.get('source', '')
                    })
        else:
            # Plain text - not a valid format for pairs
            return jsonify({'error': 'Plain text format not supported. Use JSON or CSV.'}), 400
        
        # Validate pairs
        validated = []
        for pair in pairs:
            if isinstance(pair, dict) and 'question' in pair and 'answer' in pair:
                validated.append({
                    'question': str(pair['question']).strip(),
                    'answer': str(pair['answer']).strip(),
                    'source': str(pair.get('source', ''))
                })
        
        if not validated:
            return jsonify({'error': 'No valid Q&A pairs found in file'}), 400
        
        return jsonify({
            'filename': filename,
            'count': len(validated),
            'pairs': validated
        })
    
    except json.JSONDecodeError:
        return jsonify({'error': 'Invalid JSON format'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/score-pairs', methods=['POST'])
def score_pairs():
    """Score Q&A pairs using IFD metric (BATCH MODE - FAST!)"""
    import time
    try:
        data = request.json
        pairs = data.get('pairs', [])
        batch_size = data.get('batch_size', 10)  # Score 10 pairs per batch
        
        if not pairs:
            return jsonify({'error': 'No pairs provided'}), 400
        
        start_time = time.time()
        scored_pairs = []
        
        # Define progress callback to track timing
        timing_info = {
            'start_time': start_time,
            'last_progress': start_time,
            'last_count': 0
        }
        
        def progress_callback(progress_data):
            """Called during scoring to track progress"""
            now = time.time()
            elapsed = now - timing_info['start_time']
            pairs_done = progress_data['pairs_done']
            total_pairs = progress_data['total_pairs']
            
            # Estimate time remaining
            if pairs_done > 0:
                time_per_pair = elapsed / pairs_done
                remaining_pairs = total_pairs - pairs_done
                estimated_remaining = time_per_pair * remaining_pairs
            else:
                estimated_remaining = 0
            
            # Store timing info
            progress_data['elapsed'] = elapsed
            progress_data['estimated_remaining'] = estimated_remaining
            progress_data['estimated_total'] = elapsed + estimated_remaining
            
            print(f"{progress_data['status']} - "
                  f"Elapsed: {elapsed:.1f}s, Est. Remaining: {estimated_remaining:.1f}s")
        
        # Score using BATCH mode (10x faster!)
        scored_pairs = core.calculate_batch_ifd_scores(
            pairs,
            batch_size=batch_size,
            progress_callback=progress_callback
        )
        
        total_time = time.time() - start_time
        
        # Calculate statistics
        overall_scores = [p['ifd_score'] for p in scored_pairs]
        
        stats = {
            'total': len(scored_pairs),
            'avg_ifd_score': round(sum(overall_scores) / len(overall_scores), 3) if overall_scores else 0,
            'min_ifd_score': round(min(overall_scores), 3) if overall_scores else 0,
            'max_ifd_score': round(max(overall_scores), 3) if overall_scores else 0,
            'difficulty_distribution': {
                'easy': sum(1 for p in scored_pairs if p['tier'] == 'easy'),
                'medium': sum(1 for p in scored_pairs if p['tier'] == 'medium'),
                'hard': sum(1 for p in scored_pairs if p['tier'] == 'hard')
            },
            'high_value': sum(1 for p in scored_pairs if p['value_category'] == 'high'),
            'medium_value': sum(1 for p in scored_pairs if p['value_category'] == 'medium'),
            'low_value': sum(1 for p in scored_pairs if p['value_category'] == 'low')
        }
        
        return jsonify({
            'pairs': scored_pairs,
            'statistics': stats,
            'timing': {
                'total_time_seconds': round(total_time, 2),
                'time_per_pair_ms': round((total_time / len(scored_pairs)) * 1000, 2) if scored_pairs else 0,
                'batch_size': batch_size,
                'method': 'batch_scoring'
            }
        })
    
    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500

@app.route('/api/filter-pairs', methods=['POST'])
def filter_pairs():
    """Filter pairs by IFD score or difficulty tier"""
    try:
        data = request.json
        pairs = data.get('pairs', [])
        min_ifd_score = data.get('min_ifd_score', 0.0)
        max_ifd_score = data.get('max_ifd_score', 1.0)
        tiers = data.get('tiers', ['easy', 'medium', 'hard'])
        value_categories = data.get('value_categories', ['low', 'medium', 'high'])
        
        filtered = []
        for pair in pairs:
            ifd_score = pair.get('ifd_score', 0)
            tier = pair.get('tier', 'medium')
            category = pair.get('value_category', 'medium')
            
            # Apply filters
            if ifd_score < min_ifd_score or ifd_score > max_ifd_score:
                continue
            if tier not in tiers:
                continue
            if category not in value_categories:
                continue
            
            filtered.append(pair)
        
        return jsonify({
            'filtered_pairs': filtered,
            'count': len(filtered),
            'original_count': len(pairs)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download-scored-pairs', methods=['POST'])
def download_scored_pairs():
    """Export scored pairs to CSV"""
    try:
        data = request.json
        pairs = data.get('pairs', [])
        filename = data.get('filename', 'scored_pairs')
        
        if not pairs:
            return jsonify({'error': 'No pairs to export'}), 400
        
        # Create temporary CSV file
        base_name = filename.replace('.json', '').replace('.csv', '')
        csv_filename = f"{base_name}_scored.csv"
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', newline='', encoding='utf-8')
        
        writer = csv.writer(temp_file)
        # Write header
        writer.writerow([
            'Question', 'Answer', 'Source',
            'IFD Score', 'Difficulty Tier', 'Value Category',
            'Conditioned Score', 'Direct Score',
            'Recommendation'
        ])
        
        # Write data
        for pair in pairs:
            writer.writerow([
                pair.get('question', ''),
                pair.get('answer', ''),
                pair.get('source', ''),
                round(pair.get('ifd_score', 0), 3),
                pair.get('tier', ''),
                pair.get('value_category', ''),
                round(pair.get('conditioned_score', 0), 3),
                round(pair.get('direct_score', 0), 3),
                pair.get('recommendation', '')
            ])
        
        temp_file.close()
        
        return send_file(
            temp_file.name,
            mimetype='text/csv',
            as_attachment=True,
            download_name=csv_filename
        )
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/verify-connection', methods=['GET'])
def verify_connection():
    """Verify AI API connection"""
    try:
        if not core.API_KEY or not core.BASE_URL:
            return jsonify({
                'connected': False,
                'error': 'API credentials not configured'
            })
        
        # Make a simple test call
        test_response = core.chat(
            core.MODEL_SCORER,
            "You are a helpful assistant.",
            "Say 'OK' if you can read this.",
            temperature=0.1
        )
        
        if test_response and len(test_response) > 0:
            return jsonify({
                'connected': True,
                'model': core.MODEL_SCORER,
                'message': 'Successfully connected to AI API'
            })
        else:
            return jsonify({
                'connected': False,
                'error': 'No response from API'
            })
    except ValueError as e:
        error_msg = str(e)
        return jsonify({
            'connected': False,
            'error': error_msg,
            'is_rate_limit': 'rate limit' in error_msg.lower(),
            'is_auth_error': 'invalid api key' in error_msg.lower()
        }), 200
    except Exception as e:
        return jsonify({
            'connected': False,
            'error': str(e)
        }), 200

if __name__ == '__main__':
    # Check if API is configured
    if not core.API_KEY or not core.BASE_URL:
        print("\n" + "="*60)
        print("WARNING: API credentials not configured!")
        print("Please set OPENAI_API_KEY and OPENAI_BASE_URL in your .env file")
        print("="*60 + "\n")
    
    # Start server
    port = 8081  # Use 8081 to avoid conflict with generator (8080)
    print("Starting QNA Scoring Interface...")
    print(f"Open your browser and navigate to: http://localhost:{port}")
    app.run(debug=True, host='0.0.0.0', port=port)

