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
gemini_api_key = "AIzaSyBznMBg8a3XGhzSr0bOJIs7ppKxZqtiNwg"
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

def summarize_and_validate_results(user_question: str, sql_query: str, results: list) -> Tuple[bool, dict, str]:
    """
    Use Gemini to summarize query results in plain English
    and validate if results match user expectations
    
    Returns: (success, response_dict, error_message)
    response_dict contains:
    {
        "summary": "Plain English explanation of results",
        "matches_expectation": true/false,
        "confidence": 0-100,
        "key_insights": ["insight1", "insight2"],
        "raw_data_count": number
    }
    """
    try:
        # Convert results to JSON string for Gemini
        results_json = json.dumps(results, default=str, indent=2)
        
        # Limit results shown to Gemini to avoid token limits
        if len(results) > 20:
            display_results = results[:20]
            results_note = f"\n\n[Note: Showing first 20 of {len(results)} results. Full dataset has {len(results)} records.]"
        else:
            display_results = results
            results_note = ""
        
        results_json = json.dumps(display_results, default=str, indent=2)
        
        summarization_prompt = f"""You are a data analyst helping a non-technical user understand their database query results.

Original User Question: "{user_question}"

Generated SQL Query: {sql_query}

Query Results:
{results_json}{results_note}

Please analyze these results and respond with ONLY valid JSON in this format:
{{
    "summary": "A clear, non-technical explanation of what these results show. Use simple language to describe the findings.",
    "matches_expectation": true or false,
    "confidence": A number from 0-100 indicating how confident you are that these results answer the original question,
    "key_insights": ["Key insight 1", "Key insight 2", "Key insight 3"],
    "raw_data_count": {len(results)},
    "recommendation": "If matches_expectation is false, suggest what query might better answer the question"
}}

IMPORTANT:
1. If matches_expectation is false, explain why in the recommendation field
2. key_insights should contain up to 3 important findings from the data
3. summary should be written for non-technical business users
4. confidence should reflect whether the data answers the original question"""
        
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=summarization_prompt
        )
        
        # Parse the response
        response_text = response.text.strip()
        
        # Try to extract JSON if it's wrapped in markdown
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        response_dict = json.loads(response_text)
        
        return True, response_dict, ""
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse summarization response: {e}")
        return False, {}, f"Failed to parse AI response: {str(e)}"
    except Exception as e:
        logger.error(f"AI summarization error: {e}")
        return False, {}, str(e)

def regenerate_query_on_mismatch(user_question: str, previous_query: str, previous_results: list, feedback: str) -> Tuple[bool, str, str]:
    """
    If results don't match expectations, ask AI to generate a better query
    
    Returns: (success, new_query, error_message)
    """
    try:
        regeneration_prompt = f"""You are an expert SQL query generator. The previous query did not match the user's expectations.

Original User Question: "{user_question}"

Previous Query (which didn't work well):
{previous_query}

Previous Results Count: {len(previous_results)}

Feedback on why it didn't match: {feedback}

Please generate a NEW SQL query that better answers the user's original question.

Database Schema:
- customers (customer_id, name, email, phone, country, registration_date, status)
- products (product_id, name, category, price, stock_quantity, created_date, status)
- sales (sale_id, customer_id, product_id, quantity, unit_price, total_amount, sale_date, payment_status)
- inventory_logs (log_id, product_id, quantity_change, transaction_type, log_date)
- reviews (review_id, customer_id, product_id, rating, review_text, review_date)

Respond ONLY with valid JSON in this format:
{{
    "query": "SELECT ... FROM ... WHERE ...",
    "explanation": "Why this query is better and how it addresses the original question"
}}"""
        
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=regeneration_prompt
        )
        
        response_text = response.text.strip()
        
        # Extract JSON if wrapped in markdown
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        response_dict = json.loads(response_text)
        new_query = response_dict.get('query', '')
        
        return True, new_query, ""
        
    except Exception as e:
        logger.error(f"Query regeneration error: {e}")
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
    ENHANCED ENDPOINT - Generate user-friendly reports from database
    Flow:
    1. Receive natural language question
    2. Generate SQL query using Gemini
    3. Validate query (security checks)
    4. Execute query
    5. Summarize results in plain English & validate if they match expectations
    6. If mismatch, optionally regenerate query (with user awareness)
    7. Return human-readable report with AI insights
    """
    try:
        data = request.get_json()
        question = data.get('question', '').strip()
        auto_retry = data.get('retry', True)  # Allow auto-retry if results don't match
        
        if not question:
            return jsonify({
                'success': False,
                'error': 'Question cannot be empty'
            }), 400
        
        # Step 1: Generate SQL query using Gemini
        logger.info(f"[STEP 1] Generating SQL query for: {question}")
        success, ai_response, error = generate_ai_sql_query(question)
        
        if not success:
            return jsonify({
                'success': False,
                'error': f"Failed to generate query: {error}"
            }), 500
        
        # Step 2: Extract and validate the SQL query
        logger.info(f"[STEP 2] Validating generated query")
        is_valid, query, validation_error = validate_ai_generated_query(ai_response)
        
        if not is_valid:
            return jsonify({
                'success': False,
                'error': f"Security validation failed: {validation_error}",
                'ai_response': ai_response
            }), 403
        
        # Step 3: Execute the validated query
        logger.info(f"[STEP 3] Executing query: {query}")
        success, results = execute_sql_query(query)
        
        if not success:
            return jsonify({
                'success': False,
                'error': f"Query execution failed: {results}",
                'query': query
            }), 500
        
        # Step 4: Summarize results and validate if they match expectations
        logger.info(f"[STEP 4] Summarizing results for user (found {len(results)} records)")
        success, summary_response, summary_error = summarize_and_validate_results(
            question, query, results
        )
        
        if not success:
            logger.warning(f"Summarization failed: {summary_error}")
            # Fallback: return raw results if summarization fails
            return jsonify({
                'success': True,
                'question': question,
                'query': query,
                'data': results,
                'record_count': len(results),
                'summary': "Unable to generate summary, but raw data is shown above",
                'matches_expectation': True,
                'confidence': 0,
                'timestamp': datetime.now().isoformat(),
                'type': 'report',
                'warning': 'Summary generation failed, showing raw results'
            }), 200
        
        # Step 5: Check if results match expectations
        matches_expectation = summary_response.get('matches_expectation', False)
        confidence = summary_response.get('confidence', 0)
        
        logger.info(f"[STEP 5] Results validation - Matches: {matches_expectation}, Confidence: {confidence}%")
        
        # If results don't match and auto_retry is enabled, try to regenerate query
        attempt_count = 1
        max_attempts = 2
        
        while not matches_expectation and confidence < 70 and auto_retry and attempt_count < max_attempts:
            logger.info(f"[STEP 6] Attempting query regeneration (Attempt {attempt_count}/{max_attempts})")
            
            feedback = summary_response.get('recommendation', 'Results did not fully answer the question')
            success, new_query, regen_error = regenerate_query_on_mismatch(
                question, query, results, feedback
            )
            
            if not success:
                logger.warning(f"Query regeneration failed: {regen_error}")
                break
            
            # Validate new query
            is_valid, new_query, validation_error = validate_ai_generated_query(json.dumps({
                "query": new_query,
                "explanation": "Regenerated query"
            }))
            
            if not is_valid:
                logger.warning(f"New query validation failed: {validation_error}")
                break
            
            # Execute new query
            success, new_results = execute_sql_query(new_query)
            
            if not success:
                logger.warning(f"New query execution failed: {new_results}")
                break
            
            # Summarize new results
            success, new_summary, summary_error = summarize_and_validate_results(
                question, new_query, new_results
            )
            
            if not success:
                logger.warning(f"New summarization failed: {summary_error}")
                break
            
            # Update variables
            query = new_query
            results = new_results
            summary_response = new_summary
            matches_expectation = new_summary.get('matches_expectation', False)
            confidence = new_summary.get('confidence', 0)
            attempt_count += 1
            
            logger.info(f"[RETRY {attempt_count-1}] New confidence: {confidence}%")
        
        # Step 7: Return user-friendly report
        report_response = {
            'success': True,
            'question': question,
            'summary': summary_response.get('summary', 'No summary available'),
            'key_insights': summary_response.get('key_insights', []),
            'data': results,
            'record_count': len(results),
            'matches_expectation': matches_expectation,
            'confidence': confidence,
            'timestamp': datetime.now().isoformat(),
            'type': 'report',
            'query': query  # Include query for transparency
        }
        
        # Add retry information if query was regenerated
        if attempt_count > 1:
            report_response['retry_info'] = {
                'attempts': attempt_count,
                'improved': matches_expectation and confidence >= 70
            }
        
        # Add recommendation if results still don't match
        if not matches_expectation:
            report_response['recommendation'] = summary_response.get('recommendation', 'Consider refining your question')
        
        return jsonify(report_response), 200
        
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
