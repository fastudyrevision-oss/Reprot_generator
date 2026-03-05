"""
Enhanced Backend API for Gemini Report Generator
Features:
- Database connectivity (MySQL)
- AI-powered SQL query generation
- Query validation and security checks
- Report generation and analytics
"""
from flask import Flask, request, jsonify, render_template
from google import genai
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
from datetime import datetime
import json
import logging
import os
from typing import Tuple
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import custom modules
from sql_validator import QueryValidator, validate_ai_generated_query

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, template_folder=".", static_folder="static")
CORS(app)

# Initialize Gemini client with API key from environment variable
gemini_api_key = os.getenv('GEMINI_API_KEY')
if not gemini_api_key:
    logger.warning("⚠️ GEMINI_API_KEY not found in .env file!")
    raise ValueError("GEMINI_API_KEY environment variable is required")

client = genai.Client(api_key=gemini_api_key)

# Database configuration from environment variables
DATABASE_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'gemini_reports')
}

def get_db_connection():
    """Get a database connection"""
    try:
        connection = mysql.connector.connect(**DATABASE_CONFIG)
        return connection
    except Error as err:
        logger.error(f"Database connection error: {err}")
        raise

def execute_sql_query(query: str):
    """
    Execute SQL query safely
    Returns: (success, data/error_message)
    """
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        logger.info(f"Executing query: {query}")
        cursor.execute(query)
        
        results = cursor.fetchall()
        cursor.close()
        connection.close()
        
        return True, results
        
    except Error as err:
        logger.error(f"Query execution error: {err}")
        return False, f"Database error: {str(err)}"
    except Exception as err:
        logger.error(f"Unexpected error: {err}")
        return False, f"Unexpected error: {str(err)}"

def generate_ai_sql_query(question: str) -> Tuple[bool, str, str]:
    """
    Use Gemini to generate SQL query from natural language
    Returns: (success, response, error_message)
    """
    try:
        # Create a prompt that ensures JSON output with SQL query
        system_prompt = """You are an expert SQL query generator. The user will ask questions about a database.

Database Schema:
- customers (customer_id, name, email, phone, country, registration_date, status)
- products (product_id, name, category, price, stock_quantity, created_date, status)
- sales (sale_id, customer_id, product_id, quantity, unit_price, total_amount, sale_date, payment_status)
- inventory_logs (log_id, product_id, quantity_change, transaction_type, log_date)
- reviews (review_id, customer_id, product_id, rating, review_text, review_date)

IMPORTANT: You must respond ONLY with valid JSON in this format:
{
    "query": "SELECT ... FROM ... WHERE ...",
    "explanation": "Brief explanation of what the query does"
}

Rules:
1. Generate ONLY SELECT statements
2. Use proper SQL syntax for MySQL
3. Include appropriate WHERE, JOIN, GROUP BY, ORDER BY, LIMIT clauses
4. Never include DROP, DELETE, INSERT, UPDATE, or any data-modifying statements
5. Return valid JSON that can be parsed
"""
        
        # Send request to Gemini
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=f"{system_prompt}\n\nUser question: {question}"
        )
        
        return True, response.text, ""
        
    except Exception as e:
        logger.error(f"AI query generation error: {e}")
        return False, "", str(e)

@app.route('/')
def index():
    """Serve the frontend"""
    return render_template('index.html')

@app.route('/api/ask', methods=['POST'])
def ask():
    """
    Original endpoint - Send question to Gemini for general response
    """
    try:
        data = request.get_json()
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({'error': 'Question cannot be empty'}), 400
        
        # Send request to Gemini
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=question
        )
        
        return jsonify({
            'success': True,
            'question': question,
            'response': response.text,
            'type': 'text'
        }), 200
        
    except Exception as e:
        logger.error(f"Error in /api/ask: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/report', methods=['POST'])
def generate_report():
    """
    NEW ENDPOINT - Generate report from database query
    Flow:
    1. Receive natural language question
    2. Generate SQL query using Gemini
    3. Validate query (security checks)
    4. Execute query
    5. Return formatted results
    """
    try:
        data = request.get_json()
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({
                'success': False,
                'error': 'Question cannot be empty'
            }), 400
        
        # Step 1: Generate SQL query using Gemini
        logger.info(f"Generating SQL query for: {question}")
        success, ai_response, error = generate_ai_sql_query(question)
        
        if not success:
            return jsonify({
                'success': False,
                'error': f"Failed to generate query: {error}"
            }), 500
        
        # Step 2: Extract and validate the SQL query
        logger.info(f"AI Response: {ai_response}")
        is_valid, query, validation_error = validate_ai_generated_query(ai_response)
        
        if not is_valid:
            return jsonify({
                'success': False,
                'error': f"Security validation failed: {validation_error}",
                'ai_response': ai_response
            }), 403
        
        # Step 3: Execute the validated query
        logger.info(f"Executing validated query: {query}")
        success, results = execute_sql_query(query)
        
        if not success:
            return jsonify({
                'success': False,
                'error': f"Query execution failed: {results}",
                'query': query
            }), 500
        
        # Step 4: Return formatted results
        return jsonify({
            'success': True,
            'question': question,
            'query': query,
            'data': results,
            'record_count': len(results),
            'timestamp': datetime.now().isoformat(),
            'type': 'report'
        }), 200
        
    except Exception as e:
        logger.error(f"Unexpected error in /api/report: {e}")
        return jsonify({
            'success': False,
            'error': f"Unexpected error: {str(e)}"
        }), 500

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    try:
        # Check database connection
        connection = get_db_connection()
        connection.close()
        db_status = "ok"
    except:
        db_status = "error"
    
    return jsonify({
        'status': 'ok',
        'database': db_status,
        'timestamp': datetime.now().isoformat()
    }), 200

@app.route('/api/schema', methods=['GET'])
def get_schema():
    """Get database schema information"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        schema_info = {}
        tables = ['customers', 'products', 'sales', 'inventory_logs', 'reviews']
        
        for table in tables:
            cursor.execute(f"DESCRIBE {table}")
            columns = cursor.fetchall()
            schema_info[table] = [
                {
                    'name': col[0],
                    'type': col[1],
                    'nullable': col[2] == 'YES',
                    'key': col[3],
                    'default': col[4]
                }
                for col in columns
            ]
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'success': True,
            'schema': schema_info
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting schema: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/table-stats', methods=['GET'])
def get_table_stats():
    """Get statistics about database tables"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        stats = {}
        tables = ['customers', 'products', 'sales', 'inventory_logs', 'reviews']
        
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
            count = cursor.fetchone()['count']
            stats[table] = {
                'record_count': count
            }
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'success': True,
            'stats': stats
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting table stats: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("""
    ╔════════════════════════════════════════════════╗
    ║  Gemini Report Generator - Backend Server      ║
    ║  Running on http://127.0.0.1:5000             ║
    ╚════════════════════════════════════════════════╝
    """)
    app.run(debug=True, host='127.0.0.1', port=5000)
