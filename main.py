import os
import glob
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import logging
import fetcher

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Configuration
TX_ENDPOINT = os.getenv("TX_ENDPOINT", "https://tx.ontoserver.csiro.au/fhir")
LOGFILE_NAME = os.getenv("LOGFILENAME", "./logs/ecl.log")

# Ensure logs directory exists
log_dir = os.path.dirname(LOGFILE_NAME)
if log_dir and not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Setup logging
logger = logging.getLogger(__name__)
logging.basicConfig(filename=LOGFILE_NAME, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger.info('Flask application started')

def read_ecl_files():
    """Read all ECL files from the ecl_library directory and extract expressions"""
    ecl_files = []
    
    # Find all .txt files in ecl_library subdirectories
    pattern = os.path.join('ecl_library', '**', '*.txt')
    files = glob.glob(pattern, recursive=True)
    
    for file_path in files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                
            # Extract the description (# line) and non-comment ECL expression
            lines = content.split('\n')
            description = ""
            ecl_expression = []
            
            for line in lines:
                line = line.strip()
                if line.startswith('#'):
                    # Extract description from comment line (remove the # and whitespace)
                    if not description:  # Only take the first comment line as description
                        description = line.lstrip('#').strip()
                elif line and not line.startswith('#'):
                    ecl_expression.append(line)
            
            if ecl_expression:
                ecl_files.append({
                    'filename': os.path.basename(file_path),
                    'path': file_path,
                    'description': description or "No description available",
                    'expression': '\n'.join(ecl_expression),
                    'category': os.path.basename(os.path.dirname(file_path))
                })
                
        except Exception as e:
            logger.error(f'Error reading file {file_path}: {e}')
    
    # Sort by category (folder) first, then by filename
    ecl_files.sort(key=lambda x: (x['category'], x['filename']))
    
    return ecl_files

@app.route('/favicon.ico')
def favicon():
    """Return empty response for favicon to prevent 404 errors"""
    return '', 204

@app.route('/')
def index():
    """Main page displaying all ECL expressions"""
    ecl_files = read_ecl_files()
    return render_template('index.html', ecl_files=ecl_files, tx_endpoint=TX_ENDPOINT)

@app.route('/search_ecl', methods=['GET'])
def search_ecl():
    """Search ECL expressions and return matching results"""
    query = request.args.get('q', '').strip().lower()
    
    if not query or len(query) < 2:
        return jsonify([])
    
    ecl_files = read_ecl_files()
    matching_results = []
    
    for ecl_file in ecl_files:
        # Search in filename, description, and expression
        searchable_text = f"{ecl_file['filename']} {ecl_file['description']} {ecl_file['expression']}".lower()
        
        if query in searchable_text:
            matching_results.append({
                'filename': ecl_file['filename'],
                'description': ecl_file['description'],
                'category': ecl_file['category'],
                'expression': ecl_file['expression'][:100] + ('...' if len(ecl_file['expression']) > 100 else ''),  # Truncate for preview
                'match_score': searchable_text.count(query)  # Simple relevance scoring
            })
    
    # Sort by relevance (match score) and then by filename
    matching_results.sort(key=lambda x: (-x['match_score'], x['filename']))
    
    # Limit results to prevent overwhelming the UI
    return jsonify(matching_results[:10])

@app.route('/test_ecl', methods=['POST'])
def test_ecl():
    """Test an ECL expression using the fetcher"""
    try:
        # Check if request has JSON data
        if not request.json:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400
            
        ecl_expression = request.json.get('expression')
        filename = request.json.get('filename')
        endpoint = request.json.get('endpoint', TX_ENDPOINT)  # Use custom endpoint if provided, otherwise use default
        
        if not ecl_expression:
            return jsonify({
                'success': False,
                'error': 'ECL expression is required'
            }), 400
        
        logger.info(f'Testing ECL expression from {filename} using endpoint: {endpoint}')
        
        # Call the fetcher function with the specified endpoint
        result = fetcher.expand_valueset(endpoint, ecl_expression, 25)
        
        logger.info(f'ECL test result for {filename}: {result}')
        
        return jsonify({
            'success': True,
            'total': result.get('total', -1),
            'concepts': result.get('concepts', []),
            'filename': filename,
            'error': result.get('error')
        })
        
    except Exception as e:
        logger.error(f'Error testing ECL expression: {e}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    # Use PORT from environment (for render.com) or default to 5001 for local development
    port = int(os.getenv('PORT', 5001))
    # Disable debug mode in production (when PORT is set by render.com)
    debug = os.getenv('PORT') is None
    
    print(f"\n{'='*60}")
    print(f"🚀 ECL Expression Tester is starting...")
    print(f"{'='*60}")
    print(f"📡 Listening on: http://0.0.0.0:{port}")
    print(f"🌐 Local access: http://localhost:{port}")
    print(f"🔧 Debug mode: {'ON' if debug else 'OFF'}")
    print(f"🔗 Terminology Server: {TX_ENDPOINT}")
    print(f"{'='*60}\n")
    
    app.run(debug=debug, host='0.0.0.0', port=port)
   