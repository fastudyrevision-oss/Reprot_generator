"""
SQL Query Validation Module
Ensures security and proper SQL query format
- Only allows SELECT statements
- Detects prompt injection attempts
- Validates query structure
"""
import re
import json
from typing import Dict, Tuple

class SQLValidationError(Exception):
    """Custom exception for SQL validation errors"""
    pass

class QueryValidator:
    """Validates and sanitizes SQL queries"""
    
    # Forbidden patterns that indicate injection attempts
    INJECTION_PATTERNS = [
        r"(\bDROP\b|\bDELETE\b|\bUPDATE\b|\bINSERT\b|\bCREATE\b|\bALTER\b|\bTRUNCATE\b)",
        r"(--|#|/\*|\*/)",  # SQL comments
        r"(;\s*\w)",  # Multiple statements (semicolon followed by word character)
        r"(\bOR\s+(1\s*=\s*1|'1'\s*=\s*'1'|true|false))",  # Classic injection patterns only
        r"(;\s*(DROP|DELETE|INSERT|UPDATE|CREATE))",  # Semicolon with dangerous keywords
        r"(\bUNION\b.*\bSELECT\b)",  # UNION injection
        r"(\bEXEC\b|\bEXECUTE\b)",  # Stored procedure execution
        r"(xp_|sp_)",  # Extended/stored procedures
        r"(SLEEP|BENCHMARK|WAITFOR)",  # Time-based injection
        r"(INTO\s+(OUTFILE|DUMPFILE))",  # File operations
    ]
    
    # Dangerous functions
    DANGEROUS_FUNCTIONS = [
        'LOAD_FILE', 'INTO_OUTFILE', 'INTO_DUMPFILE',
        'SYSTEM', 'EXEC', 'SHELL_EXEC', 'EVAL'
    ]
    
    # Allowed table names (whitelist)
    ALLOWED_TABLES = {
        'customers', 'products', 'sales', 
        'inventory_logs', 'reviews'
    }
    
    @staticmethod
    def is_select_only(query: str) -> bool:
        """Check if query is SELECT statement only"""
        # Remove leading/trailing whitespace and convert to uppercase
        clean_query = query.strip().upper()
        
        # Must start with SELECT
        if not clean_query.startswith('SELECT'):
            return False
        
        # Check for dangerous keywords that modify data
        dangerous_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'CREATE', 
                            'ALTER', 'TRUNCATE', 'EXEC', 'EXECUTE']
        
        for keyword in dangerous_keywords:
            if re.search(rf'\b{keyword}\b', clean_query):
                return False
        
        return True
    
    @staticmethod
    def detect_injection(query: str) -> Tuple[bool, str]:
        """Detect common injection patterns"""
        query_upper = query.upper()
        
        for pattern in QueryValidator.INJECTION_PATTERNS:
            if re.search(pattern, query_upper, re.IGNORECASE):
                return True, f"Detected potentially malicious pattern: {pattern}"
        
        # Check for dangerous functions
        for func in QueryValidator.DANGEROUS_FUNCTIONS:
            if re.search(rf'\b{func}\b', query_upper):
                return True, f"Dangerous function detected: {func}"
        
        return False, ""
    
    @staticmethod
    def validate_table_references(query: str) -> Tuple[bool, str]:
        """Validate that query only references allowed tables"""
        query_upper = query.upper()
        
        # Find all table references (simple regex, may need adjustment for complex queries)
        # Look for patterns like: FROM table, JOIN table, INTO table
        table_pattern = r'\b(FROM|JOIN|INNER\s+JOIN|LEFT\s+JOIN|RIGHT\s+JOIN|FULL\s+JOIN)\s+(\w+)'
        
        matches = re.findall(table_pattern, query_upper)
        
        for match in matches:
            table_name = match[1].lower()
            if table_name not in QueryValidator.ALLOWED_TABLES:
                return False, f"Access to table '{table_name}' is not allowed"
        
        return True, ""
    
    @staticmethod
    def validate_syntax(query: str) -> Tuple[bool, str]:
        """Basic syntax validation"""
        # Check for unmatched quotes
        single_quotes = query.count("'") % 2
        double_quotes = query.count('"') % 2
        
        if single_quotes != 0:
            return False, "Unmatched single quotes"
        
        if double_quotes != 0:
            return False, "Unmatched double quotes"
        
        # Check for unmatched parentheses
        if query.count('(') != query.count(')'):
            return False, "Unmatched parentheses"
        
        return True, ""
    
    @classmethod
    def validate_query(cls, query: str) -> Tuple[bool, str]:
        """
        Main validation method
        Returns: (is_valid, error_message)
        """
        if not query or not query.strip():
            return False, "Query cannot be empty"
        
        # Basic syntax check
        is_valid, error = cls.validate_syntax(query)
        if not is_valid:
            return False, error
        
        # Check if it's a SELECT statement
        if not cls.is_select_only(query):
            return False, "Only SELECT statements are allowed"
        
        # Detect injection attempts
        has_injection, injection_msg = cls.detect_injection(query)
        if has_injection:
            return False, f"Security check failed: {injection_msg}"
        
        # Validate table references
        is_valid, error = cls.validate_table_references(query)
        if not is_valid:
            return False, error
        
        return True, "Query is safe"
    
    @staticmethod
    def parse_ai_response(response_text: str) -> Tuple[bool, str, str]:
        """
        Parse AI response and extract SQL query
        Expects JSON format: {"query": "SELECT ...", "explanation": "..."}
        Returns: (success, query, error_message)
        """
        try:
            # Try to parse as JSON
            data = json.loads(response_text)
            
            if not isinstance(data, dict):
                return False, "", "Response is not a valid JSON object"
            
            if 'query' not in data:
                return False, "", "Response missing 'query' field"
            
            query = data.get('query', '').strip()
            
            if not query:
                return False, "", "Query field is empty"
            
            return True, query, ""
            
        except json.JSONDecodeError as e:
            return False, "", f"Invalid JSON response: {str(e)}"
        except Exception as e:
            return False, "", f"Error parsing response: {str(e)}"

def validate_ai_generated_query(ai_response: str) -> Tuple[bool, str, str]:
    """
    Complete validation pipeline for AI-generated queries
    Returns: (is_valid, query, error_message)
    """
    # First, parse the JSON response
    success, query, error = QueryValidator.parse_ai_response(ai_response)
    if not success:
        return False, "", error
    
    # Then validate the extracted query
    is_valid, validation_error = QueryValidator.validate_query(query)
    if not is_valid:
        return False, "", validation_error
    
    return True, query, ""
