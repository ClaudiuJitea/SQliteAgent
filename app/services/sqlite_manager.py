import sqlite3
import os
import json
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import logging
import threading

class SQLiteManager:
    """Manages SQLite database connections and operations"""
    
    def __init__(self):
        self.database_paths = {}  # Store paths instead of connections
        self.logger = logging.getLogger(__name__)
        self._lock = threading.Lock()
    
    def _get_connection(self, db_name: str) -> sqlite3.Connection:
        """Get a new connection for the specified database"""
        if db_name not in self.database_paths:
            raise ValueError(f"Database {db_name} not loaded")
        
        file_path = self.database_paths[db_name]
        conn = sqlite3.connect(file_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    
    def load_database(self, file_path: str) -> Dict[str, Any]:
        """Load a SQLite database and return connection info"""
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Database file not found: {file_path}")
            
            # Test connection
            conn = sqlite3.connect(file_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            
            # Get database info
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            conn.close()  # Close test connection
            
            # Store database path
            db_id = os.path.basename(file_path)
            with self._lock:
                self.database_paths[db_id] = file_path
            
            return {
                'id': db_id,
                'path': file_path,
                'tables': tables,
                'size': os.path.getsize(file_path),
                'status': 'connected'
            }
            
        except Exception as e:
            self.logger.error(f"Error loading database {file_path}: {str(e)}")
            raise
    
    def create_database(self, file_path: str, schema_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new SQLite database with the given schema"""
        try:
            # Create new database connection
            conn = sqlite3.connect(file_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Execute CREATE TABLE statements
            tables = []
            for table_info in schema_data.get('tables', []):
                table_name = table_info['name']
                create_sql = table_info['create_sql']
                
                # Execute CREATE TABLE
                cursor.execute(create_sql)
                tables.append(table_name)
                
                # Insert sample data if provided
                sample_data = table_info.get('sample_data', [])
                for insert_sql in sample_data:
                    try:
                        cursor.execute(insert_sql)
                    except Exception as e:
                        self.logger.warning(f"Failed to insert sample data: {str(e)}")
            
            # Create indexes if provided
            for index_sql in schema_data.get('indexes', []):
                try:
                    cursor.execute(index_sql)
                except Exception as e:
                    self.logger.warning(f"Failed to create index: {str(e)}")
            
            # Commit changes
            conn.commit()
            conn.close()  # Close creation connection
            
            # Store database path
            db_id = os.path.basename(file_path)
            with self._lock:
                self.database_paths[db_id] = file_path
            
            return {
                'id': db_id,
                'path': file_path,
                'tables': tables,
                'size': os.path.getsize(file_path),
                'status': 'connected'
            }
            
        except Exception as e:
            # Clean up file if creation failed
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except:
                    pass
            self.logger.error(f"Error creating database {file_path}: {str(e)}")
            raise
    
    def list_databases(self) -> List[Dict[str, Any]]:
        """List all loaded databases"""
        databases = []
        with self._lock:
            for db_id, file_path in self.database_paths.items():
                # Get tables for each database
                tables = []
                try:
                    conn = self._get_connection(db_id)
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                    tables = [row[0] for row in cursor.fetchall()]
                    conn.close()
                except Exception as e:
                    self.logger.error(f"Error getting tables for {db_id}: {str(e)}")
                
                databases.append({
                    'id': db_id,
                    'path': file_path,
                    'tables': tables,
                    'size': os.path.getsize(file_path) if os.path.exists(file_path) else 0,
                    'status': 'connected' if os.path.exists(file_path) else 'disconnected'
                })
        return databases
    
    def get_database_schema(self, db_name: str) -> Dict[str, Any]:
        """Get detailed schema information for a database"""
        conn = self._get_connection(db_name)
        cursor = conn.cursor()
        
        try:
            schema = {'tables': {}}
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            for table in tables:
                table_name = table[0]
                
                # Get table info
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                
                # Get row count
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                row_count = cursor.fetchone()[0]
                
                schema['tables'][table_name] = {
                    'columns': [
                        {
                            'name': col[1],
                            'type': col[2],
                            'not_null': bool(col[3]),
                            'default_value': col[4],
                            'primary_key': bool(col[5])
                        } for col in columns
                    ],
                    'row_count': row_count
                }
            
            return schema
        finally:
            conn.close()
    
    def execute_query(self, query: str, db_name: str, params: Optional[Tuple] = None) -> Dict[str, Any]:
        """Execute a SQL query and return results"""
        conn = self._get_connection(db_name)
        cursor = conn.cursor()
        
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # Check if it's a SELECT query
            if query.strip().upper().startswith('SELECT'):
                results = cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                
                return {
                    'success': True,
                    'data': [dict(zip(columns, row)) for row in results],
                    'columns': columns,
                    'row_count': len(results)
                }
            else:
                # For INSERT, UPDATE, DELETE
                conn.commit()
                return {
                    'success': True,
                    'message': f"Query executed successfully. {cursor.rowcount} rows affected.",
                    'rows_affected': cursor.rowcount
                }
                
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Error executing query: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
        finally:
            conn.close()
    
    def get_table_data(self, table_name: str, db_name: str, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """Get paginated data from a specific table"""
        query = f"SELECT * FROM {table_name} LIMIT {limit} OFFSET {offset}"
        return self.execute_query(query, db_name)
    
    def close_database(self, db_name: str) -> bool:
        """Remove a database from the manager"""
        with self._lock:
            if db_name in self.database_paths:
                del self.database_paths[db_name]
                return True
        return False
    
    def close_all_databases(self):
        """Remove all databases from the manager"""
        with self._lock:
            self.database_paths.clear()
    
    def validate_query_safety(self, query: str) -> Dict[str, Any]:
        """Basic SQL injection and safety validation"""
        dangerous_keywords = [
            'DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'CREATE', 'INSERT', 'UPDATE'
        ]
        
        query_upper = query.upper().strip()
        
        # Check for dangerous operations
        for keyword in dangerous_keywords:
            if keyword in query_upper:
                return {
                    'safe': False,
                    'warning': f"Query contains potentially dangerous operation: {keyword}",
                    'requires_confirmation': True
                }
        
        return {
            'safe': True,
            'warning': None,
            'requires_confirmation': False
        }