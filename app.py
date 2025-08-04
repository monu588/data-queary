import os
import logging
import pandas as pd
import json
import re
from flask import Flask, render_template, request, jsonify
from openai_service import generate_pandas_code

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# Load the sales data once at startup
try:
    # Try to load from same directory first, then parent directory
    csv_path = 'sales.csv'
    if not os.path.exists(csv_path):
        csv_path = os.path.join(os.path.dirname(__file__), 'sales.csv')
    
    sales_data = pd.read_csv(csv_path)
    sales_data['date'] = pd.to_datetime(sales_data['date'])
    logging.info(f"Loaded sales data with {len(sales_data)} rows from {csv_path}")
except Exception as e:
    logging.error(f"Failed to load sales.csv: {e}")
    sales_data = None

def is_safe_code(code):
    """
    Basic safety check for generated pandas code.
    Prevents dangerous operations like file system access, imports, etc.
    """
    dangerous_patterns = [
        r'import\s+(?!pandas|numpy|datetime)',
        r'from\s+(?!pandas|numpy|datetime)',
        r'open\s*\(',
        r'exec\s*\(',
        r'eval\s*\(',
        r'__import__',
        r'getattr',
        r'setattr',
        r'delattr',
        r'globals\s*\(',
        r'locals\s*\(',
        r'dir\s*\(',
        r'vars\s*\(',
        r'\.system',
        r'os\.',
        r'subprocess',
        r'shutil',
        r'pickle',
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, code, re.IGNORECASE):
            return False
    return True

def execute_pandas_code(code, df):
    """
    Safely execute pandas code on the dataframe.
    Returns the result and any error messages.
    """
    if not is_safe_code(code):
        return None, "Generated code contains unsafe operations"
    
    try:
        # Create a restricted namespace with only necessary modules
        namespace = {
            'df': df,
            'pd': pd,
            'datetime': __import__('datetime'),
        }
        
        # Execute the code
        exec(code, namespace)
        
        # The code should assign result to 'result' variable
        if 'result' in namespace:
            result = namespace['result']
            
            # Convert result to JSON-serializable format
            if isinstance(result, pd.DataFrame):
                return {
                    'type': 'dataframe',
                    'data': result.to_dict('records'),
                    'columns': result.columns.tolist()
                }, None
            elif isinstance(result, pd.Series):
                return {
                    'type': 'series',
                    'data': result.to_dict(),
                    'name': result.name
                }, None
            elif isinstance(result, (int, float, str, bool)):
                return {
                    'type': 'scalar',
                    'data': result
                }, None
            else:
                return {
                    'type': 'other',
                    'data': str(result)
                }, None
        else:
            return None, "Generated code did not produce a 'result' variable"
            
    except Exception as e:
        return None, f"Error executing code: {str(e)}"

@app.route('/')
def index():
    """Render the main dashboard page."""
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    """
    Process natural language query and return analytics result.
    """
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({'error': 'No query provided'}), 400
        
        query = data['query'].strip()
        if not query:
            return jsonify({'error': 'Empty query provided'}), 400
        
        if sales_data is None:
            return jsonify({'error': 'Sales data not available'}), 500
        
        logging.info(f"Processing query: {query}")
        
        # Generate pandas code using OpenAI
        code, error = generate_pandas_code(query, sales_data.columns.tolist())
        
        if error:
            return jsonify({'error': f'Failed to generate code: {error}'}), 500
        
        logging.info(f"Generated code: {code}")
        
        # Execute the generated code
        result, exec_error = execute_pandas_code(code, sales_data)
        
        if exec_error:
            return jsonify({'error': exec_error}), 500
        
        # Return successful result
        return jsonify({
            'success': True,
            'result': result,
            'generated_code': code,
            'query': query
        })
        
    except Exception as e:
        logging.error(f"Unexpected error in /ask endpoint: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/data-info')
def data_info():
    """Return information about the loaded dataset."""
    if sales_data is None:
        return jsonify({'error': 'Sales data not available'}), 500
    
    return jsonify({
        'columns': sales_data.columns.tolist(),
        'row_count': len(sales_data),
        'sample_data': sales_data.head(5).to_dict('records'),
        'date_range': {
            'start': sales_data['date'].min().isoformat(),
            'end': sales_data['date'].max().isoformat()
        },
        'regions': sales_data['region'].unique().tolist() if 'region' in sales_data.columns else []
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
