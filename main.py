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
TX_ENDPOINT = os.getenv("TX_ENDPOINT")
LOGFILE_NAME = os.getenv("LOGFILENAME")

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

@app.route('/')
def index():
    """Main page displaying all ECL expressions"""
    ecl_files = read_ecl_files()
    return render_template('index.html', ecl_files=ecl_files, tx_endpoint=TX_ENDPOINT)

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
        
        if not ecl_expression:
            return jsonify({
                'success': False,
                'error': 'ECL expression is required'
            }), 400
        
        logger.info(f'Testing ECL expression from {filename}')
        
        # Call the fetcher function
        result = fetcher.expand_valueset(TX_ENDPOINT, ecl_expression, 25)
        
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
    app.run(debug=True, host='0.0.0.0', port=5001)
   