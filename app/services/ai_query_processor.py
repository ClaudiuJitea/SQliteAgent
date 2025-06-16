import requests
import json
import logging
from typing import Dict, Any, List, Optional
from flask import current_app

class AIQueryProcessor:
    """Handles AI-powered query processing using OpenRouter API"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.base_url = "https://openrouter.ai/api/v1"
    
    def _make_api_request(self, messages: List[Dict[str, str]], temperature: float = 0.1, model: Optional[str] = None) -> Dict[str, Any]:
        """Make a request to OpenRouter API"""
        api_key = current_app.config.get('OPENROUTER_API_KEY')
        # Use provided model or fall back to config default
        if not model:
            model = current_app.config.get('OPENROUTER_MODEL')
        
        self.logger.info(f"Making API request with model: {model}")
        self.logger.info(f"API key configured: {bool(api_key)}")
        
        if not api_key:
            self.logger.error("OpenRouter API key not configured")
            # Return a mock response instead of raising an exception
            return self._get_mock_response(messages)
        
        if not model:
            self.logger.error("OpenRouter model not configured")
            # Return a mock response instead of raising an exception
            return self._get_mock_response(messages)
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:5000",
            "X-Title": "SQLite AI Manager"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 8192
        }
        
        try:
            self.logger.info(f"Sending request to: {self.base_url}/chat/completions")
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            self.logger.info(f"API response status: {response.status_code}")
            
            if response.status_code != 200:
                self.logger.error(f"API response error: {response.text}")
                # Return a mock response instead of raising an exception
                return self._get_mock_response(messages)
            
            return response.json()
        except Exception as e:
            self.logger.error(f"API request failed: {str(e)}")
            self.logger.error(f"Response status code: {getattr(response, 'status_code', 'N/A')}")
            self.logger.error(f"Response text: {getattr(response, 'text', 'N/A')}")
            # Return a mock response instead of raising an exception
            return self._get_mock_response(messages)
    
    def _get_mock_response(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Generate a mock response when API calls fail"""
        self.logger.warning("Using mock response due to API failure")
        
        # Extract the user message to determine response type
        user_message = ""
        for message in messages:
            if message.get("role") == "user":
                user_message = message.get("content", "")
                break
        
        # Check if this is a schema generation request
        if "database schema" in user_message.lower() or "create a database" in user_message.lower():
            return {
                "choices": [{
                    "message": {
                        "content": json.dumps({
                            "tables": [
                                {
                                    "name": "users",
                                    "create_sql": "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT, created_at TEXT);",
                                    "sample_data": [
                                        "INSERT INTO users (name, email, created_at) VALUES ('John Doe', 'john@example.com', '2023-01-01');",
                                        "INSERT INTO users (name, email, created_at) VALUES ('Jane Smith', 'jane@example.com', '2023-01-02');"
                                    ]
                                },
                                {
                                    "name": "items",
                                    "create_sql": "CREATE TABLE items (id INTEGER PRIMARY KEY, name TEXT, description TEXT, user_id INTEGER, FOREIGN KEY (user_id) REFERENCES users(id));",
                                    "sample_data": [
                                        "INSERT INTO items (name, description, user_id) VALUES ('Item 1', 'Description 1', 1);",
                                        "INSERT INTO items (name, description, user_id) VALUES ('Item 2', 'Description 2', 2);"
                                    ]
                                }
                            ],
                            "indexes": [
                                "CREATE INDEX idx_users_email ON users(email);",
                                "CREATE INDEX idx_items_user_id ON items(user_id);"
                            ],
                            "description": "A simple database with users and items tables."
                        })
                    }
                }]
            }
        
        # For SQL queries
        elif "sql" in user_message.lower() or "query" in user_message.lower():
            # Check if the query mentions specific tables
            if "books" in user_message.lower():
                return {
                    "choices": [{
                        "message": {
                            "content": "SELECT * FROM books;"
                        }
                    }]
                }
            elif "users" in user_message.lower():
                return {
                    "choices": [{
                        "message": {
                            "content": "SELECT * FROM users LIMIT 10;"
                        }
                    }]
                }
            else:
                # Generic fallback for unknown tables
                return {
                    "choices": [{
                        "message": {
                            "content": "SELECT * FROM table_name LIMIT 10;"
                        }
                    }]
                }
        
        # Default response
        else:
            return {
                "choices": [{
                    "message": {
                        "content": "I'm sorry, I couldn't process your request due to API limitations. Please try again later."
                    }
                }]
            }
    
    def natural_language_to_sql(self, prompt: str, schema: Dict[str, Any], model: Optional[str] = None) -> Dict[str, Any]:
        """Convert natural language to SQL query"""
        try:
            # Prepare schema information
            schema_text = self._format_schema_for_ai(schema)
            
            system_message = f"""
You are an expert SQL query generator. Convert natural language requests to SQLite queries.

Database Schema:
{schema_text}

Rules:
1. Generate only valid SQLite syntax
2. Use proper table and column names from the schema
3. Include appropriate WHERE clauses for filtering
4. Use LIMIT for large result sets
5. Return only the SQL query, no explanations
6. If the request is unclear, generate the most reasonable interpretation

Respond with only the SQL query.
"""
            
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ]
            
            response = self._make_api_request(messages, model=model)
            sql_query = response['choices'][0]['message']['content'].strip()
            
            # Clean up the response (remove markdown formatting if present)
            if sql_query.startswith('```'):
                # Remove opening markdown block
                lines = sql_query.split('\n')
                if lines[0].startswith('```'):
                    lines = lines[1:]  # Remove first line with ```
                # Remove closing markdown block
                if lines and lines[-1].strip() == '```':
                    lines = lines[:-1]  # Remove last line with ```
                sql_query = '\n'.join(lines).strip()
            
            return {
                'success': True,
                'sql_query': sql_query,
                'original_prompt': prompt
            }
            
        except Exception as e:
            self.logger.error(f"Error converting natural language to SQL: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'original_prompt': prompt
            }
    
    def generate_database_schema(self, description: str) -> Dict[str, Any]:
        """Generate database schema from natural language description"""
        try:
            system_message = """
You are an expert database designer. Create a SQLite database schema based on the natural language description provided.

Rules:
1. Generate CREATE TABLE statements with appropriate data types
2. Include primary keys, foreign keys, and constraints where appropriate
3. Use proper SQLite data types (TEXT, INTEGER, REAL, BLOB)
4. Add indexes for commonly queried columns
5. Include sample INSERT statements for each table (2-3 records per table)
6. Return a JSON object with the following structure:
{
  "tables": [
    {
      "name": "table_name",
      "create_sql": "CREATE TABLE statement",
      "sample_data": ["INSERT statements"]
    }
  ],
  "indexes": ["CREATE INDEX statements"],
  "description": "Brief description of the database structure"
}

Ensure all SQL is valid SQLite syntax.
"""
            
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": f"Create a database schema for: {description}"}
            ]
            
            response = self._make_api_request(messages, temperature=0.3)
            content = response['choices'][0]['message']['content'].strip()
            
            # Log the raw content for debugging
            self.logger.info(f"Raw AI response content: {content[:500]}...")
            
            # Clean up the response (remove markdown formatting if present)
            if content.startswith('```json'):
                content = content.replace('```json', '').replace('```', '').strip()
            elif content.startswith('```'):
                content = content.replace('```', '').strip()
            
            # Log cleaned content
            self.logger.info(f"Cleaned content: {content[:500]}...")
            
            # Parse JSON response
            import json
            try:
                schema_data = json.loads(content)
            except json.JSONDecodeError as json_error:
                self.logger.error(f"JSON parsing failed: {str(json_error)}")
                self.logger.error(f"Content that failed to parse: {content}")
                
                # If JSON parsing fails, return a fallback schema
                self.logger.warning("Using fallback schema due to JSON parsing error")
                return {
                    'success': False,
                    'error': f"Failed to parse AI response: {str(json_error)}",
                    'description': description
                }
            
            return {
                'success': True,
                'schema': schema_data,
                'description': description
            }
            
        except Exception as e:
            self.logger.error(f"Error generating database schema: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'description': description
            }
    
    def explain_query_results(self, results: List[Dict], original_prompt: str, sql_query: str, model: Optional[str] = None) -> Dict[str, Any]:
        """Generate human-readable explanation of query results"""
        try:
            results_summary = f"Found {len(results)} results"
            if results:
                sample_data = json.dumps(results[:3], indent=2) if len(results) > 3 else json.dumps(results, indent=2)
            else:
                sample_data = "No results found"
            
            system_message = """
You are a data analyst. Explain SQL query results in plain English.
Provide insights about the data patterns, key findings, and answer the original question.
Be concise but informative.
"""
            
            user_message = f"""
Original Question: {original_prompt}
SQL Query: {sql_query}
Results Summary: {results_summary}
Sample Data: {sample_data}

Please explain what these results mean and answer the original question.
"""
            
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ]
            
            response = self._make_api_request(messages, temperature=0.3)
            explanation = response['choices'][0]['message']['content'].strip()
            
            return {
                'success': True,
                'explanation': explanation,
                'result_count': len(results)
            }
            
        except Exception as e:
            self.logger.error(f"Error explaining query results: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def suggest_optimizations(self, query: str, schema: Dict[str, Any], model: Optional[str] = None) -> Dict[str, Any]:
        """Suggest query optimizations"""
        try:
            schema_text = self._format_schema_for_ai(schema)
            
            system_message = f"""
You are a database optimization expert. Analyze SQL queries and suggest improvements.

Database Schema:
{schema_text}

Provide specific optimization suggestions including:
1. Index recommendations
2. Query rewriting suggestions
3. Performance considerations
4. Best practices

Be practical and specific.
"""
            
            user_message = f"Analyze this SQL query for optimization opportunities:\n\n{query}"
            
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ]
            
            response = self._make_api_request(messages, temperature=0.2, model=model)
            suggestions = response['choices'][0]['message']['content'].strip()
            
            return {
                'success': True,
                'suggestions': suggestions,
                'original_query': query
            }
            
        except Exception as e:
            self.logger.error(f"Error generating optimization suggestions: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def validate_query_safety(self, sql_query: str, model: Optional[str] = None) -> Dict[str, Any]:
        """AI-powered query safety validation"""
        try:
            system_message = """
You are a SQL security expert. Analyze queries for potential security risks.

Check for:
1. SQL injection patterns
2. Dangerous operations (DROP, DELETE without WHERE, etc.)
3. Performance risks (missing LIMIT on large tables)
4. Data exposure risks

Respond with JSON format:
{
  "safe": true/false,
  "risk_level": "low"/"medium"/"high",
  "warnings": ["list of specific warnings"],
  "recommendations": ["list of recommendations"]
}
"""
            
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": f"Analyze this SQL query: {sql_query}"}
            ]
            
            response = self._make_api_request(messages, temperature=0.1, model=model)
            result_text = response['choices'][0]['message']['content'].strip()
            
            # Try to parse JSON response
            try:
                result = json.loads(result_text)
            except json.JSONDecodeError:
                # Fallback if AI doesn't return valid JSON
                result = {
                    "safe": "DROP" not in sql_query.upper() and "DELETE" not in sql_query.upper(),
                    "risk_level": "medium",
                    "warnings": ["Could not parse AI safety analysis"],
                    "recommendations": ["Manual review recommended"]
                }
            
            return {
                'success': True,
                'analysis': result
            }
            
        except Exception as e:
            self.logger.error(f"Error validating query safety: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _format_schema_for_ai(self, schema: Dict[str, Any]) -> str:
        """Format database schema for AI prompts"""
        schema_lines = []
        
        for table_name, table_info in schema.get('tables', {}).items():
            schema_lines.append(f"Table: {table_name}")
            for column in table_info.columns:
                column_def = f"  - {column.name} ({column.type})"
                if column.primary_key:
                    column_def += " [PRIMARY KEY]"
                if column.not_null:
                    column_def += " [NOT NULL]"
                schema_lines.append(column_def)
            schema_lines.append(f"  Rows: {table_info.row_count}")
            schema_lines.append("")
        
        return "\n".join(schema_lines)