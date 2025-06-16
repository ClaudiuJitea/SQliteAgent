import sqlite3
import os
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
from app.services.sqlite_manager import SQLiteManager
from app.models.schemas import DatabaseInfo, DatabaseStatus, TableInfo, ColumnInfo

class DatabaseModel:
    """Database model that provides high-level database operations"""
    
    # Class-level shared registry to ensure all instances share the same data
    _shared_registry = {}
    
    def __init__(self):
        self.sqlite_manager = SQLiteManager()
        self.logger = logging.getLogger(__name__)
        # Use the shared registry instead of instance-specific one
        self._database_registry = DatabaseModel._shared_registry
    
    def load_database(self, file_path: str) -> DatabaseInfo:
        """Load a database and return database information"""
        try:
            # Validate file path
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Database file not found: {file_path}")
            
            if not self._is_valid_sqlite_file(file_path):
                raise ValueError(f"Invalid SQLite database file: {file_path}")
            
            # Load database using SQLite manager
            db_info = self.sqlite_manager.load_database(file_path)
            
            # Create database info object
            database_info = DatabaseInfo(
                id=db_info['id'],
                path=db_info['path'],
                tables=db_info['tables'],
                size=db_info['size'],
                status=DatabaseStatus.CONNECTED,
                created_at=datetime.now(),
                last_accessed=datetime.now()
            )
            
            # Register in local registry
            self._database_registry[db_info['id']] = {
                'info': database_info,
                'loaded_at': datetime.now()
            }
            
            self.logger.info(f"Database loaded successfully: {file_path}")
            return database_info
            
        except Exception as e:
            self.logger.error(f"Error loading database {file_path}: {str(e)}")
            raise
    
    def create_database(self, file_path: str, schema_data: Dict[str, Any]) -> DatabaseInfo:
        """Create a new database with the given schema"""
        try:
            # Ensure the file doesn't already exist
            if os.path.exists(file_path):
                raise ValueError(f"Database file already exists: {file_path}")
            
            # Create the database file and execute schema
            db_info = self.sqlite_manager.create_database(file_path, schema_data)
            
            # Create database info object
            database_info = DatabaseInfo(
                id=db_info['id'],
                path=db_info['path'],
                tables=db_info['tables'],
                size=db_info['size'],
                status=DatabaseStatus.CONNECTED,
                created_at=datetime.now(),
                last_accessed=datetime.now()
            )
            
            # Register in local registry
            self._database_registry[db_info['id']] = {
                'info': database_info,
                'loaded_at': datetime.now()
            }
            
            self.logger.info(f"Database created successfully: {file_path}")
            return database_info
            
        except Exception as e:
            self.logger.error(f"Error creating database {file_path}: {str(e)}")
            raise
    
    def get_database_list(self) -> List[DatabaseInfo]:
        """Get list of all loaded databases"""
        try:
            databases = self.sqlite_manager.list_databases()
            database_list = []
            
            for db in databases:
                # Update last accessed time if in registry
                if db['id'] in self._database_registry:
                    self._database_registry[db['id']]['info'].last_accessed = datetime.now()
                    database_list.append(self._database_registry[db['id']]['info'])
                else:
                    # Create new database info if not in registry
                    db_info = DatabaseInfo(
                        id=db['id'],
                        path=db['path'],
                        tables=db['tables'],
                        size=db['size'],
                        status=DatabaseStatus(db['status']),
                        last_accessed=datetime.now()
                    )
                    # Add to registry for future lookups
                    self._database_registry[db['id']] = {
                        'info': db_info,
                        'loaded_at': datetime.now()
                    }
                    database_list.append(db_info)
            
            return database_list
            
        except Exception as e:
            self.logger.error(f"Error getting database list: {str(e)}")
            raise
    
    def get_database_schema(self, database_id: str) -> Dict[str, Any]:
        """Get database schema information"""
        try:
            if database_id not in self._database_registry:
                raise ValueError(f"Database {database_id} not loaded")
            
            # Ensure database is loaded in SQLiteManager
            db_info = self._database_registry[database_id]['info']
            if database_id not in self.sqlite_manager.database_paths:
                self.logger.info(f"Reloading database {database_id} in SQLiteManager")
                self.sqlite_manager.load_database(db_info.path)
            
            schema = self.sqlite_manager.get_database_schema(database_id)
            
            # Convert to structured format
            structured_schema = {
                'database_id': database_id,
                'tables': {},
                'total_tables': len(schema['tables']),
                'total_size': self._database_registry[database_id]['info'].size
            }
            
            for table_name, table_data in schema['tables'].items():
                columns = [
                    ColumnInfo(
                        name=col['name'],
                        type=col['type'],
                        not_null=col['not_null'],
                        default_value=col['default_value'],
                        primary_key=col['primary_key']
                    ) for col in table_data['columns']
                ]
                
                structured_schema['tables'][table_name] = TableInfo(
                    name=table_name,
                    columns=columns,
                    row_count=table_data['row_count']
                )
            
            return structured_schema
            
        except Exception as e:
            self.logger.error(f"Error getting schema for database {database_id}: {str(e)}")
            raise
    
    def execute_query(self, database_id: str, query: str, params: Optional[Tuple] = None) -> Dict[str, Any]:
        """Execute a SQL query on the specified database"""
        try:
            if database_id not in self._database_registry:
                raise ValueError(f"Database {database_id} not loaded")
            
            # Ensure database is loaded in SQLiteManager
            db_info = self._database_registry[database_id]['info']
            if database_id not in self.sqlite_manager.database_paths:
                self.logger.info(f"Reloading database {database_id} in SQLiteManager")
                self.sqlite_manager.load_database(db_info.path)
            
            # Update last accessed time
            self._database_registry[database_id]['info'].last_accessed = datetime.now()
            
            # Execute query
            start_time = datetime.now()
            result = self.sqlite_manager.execute_query(query, database_id, params)
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Add execution time to result
            result['execution_time'] = execution_time
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error executing query on database {database_id}: {str(e)}")
            raise
    
    def get_table_data(self, database_id: str, table_name: str, limit: int = 100, 
                      offset: int = 0, filters: Optional[Dict] = None, 
                      sort_by: Optional[str] = None, sort_order: str = "ASC") -> Dict[str, Any]:
        """Get paginated data from a specific table with optional filtering and sorting"""
        try:
            if database_id not in self._database_registry:
                raise ValueError(f"Database {database_id} not loaded")
            
            # Build query with filters and sorting
            query = f"SELECT * FROM {table_name}"
            params = []
            
            # Add filters
            if filters:
                where_conditions = []
                for column, value in filters.items():
                    # Use LIKE for text searches to enable partial matching
                    where_conditions.append(f"{column} LIKE ?")
                    params.append(f"%{value}%")
                
                if where_conditions:
                    query += f" WHERE {' AND '.join(where_conditions)}"
            
            # Add sorting
            if sort_by:
                query += f" ORDER BY {sort_by} {sort_order}"
            
            # Add pagination
            query += f" LIMIT {limit} OFFSET {offset}"
            
            # Execute query
            result = self.execute_query(database_id, query, tuple(params) if params else None)
            
            if result['success']:
                # Get total row count for pagination info
                count_query = f"SELECT COUNT(*) as total FROM {table_name}"
                if filters:
                    where_conditions = []
                    count_params = []
                    for column, value in filters.items():
                        # Use LIKE for text searches to enable partial matching
                        where_conditions.append(f"{column} LIKE ?")
                        count_params.append(f"%{value}%")
                    
                    if where_conditions:
                        count_query += f" WHERE {' AND '.join(where_conditions)}"
                    
                    count_result = self.execute_query(database_id, count_query, tuple(count_params))
                else:
                    count_result = self.execute_query(database_id, count_query)
                
                total_rows = count_result['data'][0]['total'] if count_result['success'] else 0
                
                # Add pagination info
                result['page_info'] = {
                    'current_page': (offset // limit) + 1,
                    'page_size': limit,
                    'total_rows': total_rows,
                    'total_pages': (total_rows + limit - 1) // limit,
                    'has_next': offset + limit < total_rows,
                    'has_previous': offset > 0
                }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error getting table data for {table_name} in database {database_id}: {str(e)}")
            raise
    
    def insert_record(self, database_id: str, table_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a new record into the specified table"""
        try:
            if database_id not in self._database_registry:
                raise ValueError(f"Database {database_id} not loaded")
            
            # Build INSERT query
            columns = list(data.keys())
            placeholders = ', '.join(['?' for _ in columns])
            query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
            
            # Execute query
            result = self.execute_query(database_id, query, tuple(data.values()))
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error inserting record into {table_name} in database {database_id}: {str(e)}")
            raise
    
    def update_record(self, database_id: str, table_name: str, record_id: Any, 
                     data: Dict[str, Any], id_column: str = "id") -> Dict[str, Any]:
        """Update an existing record in the specified table"""
        try:
            if database_id not in self._database_registry:
                raise ValueError(f"Database {database_id} not loaded")
            
            # Build UPDATE query
            set_clauses = [f"{column} = ?" for column in data.keys()]
            query = f"UPDATE {table_name} SET {', '.join(set_clauses)} WHERE {id_column} = ?"
            
            # Execute query
            params = list(data.values()) + [record_id]
            result = self.execute_query(database_id, query, tuple(params))
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error updating record in {table_name} in database {database_id}: {str(e)}")
            raise
    
    def delete_record(self, database_id: str, table_name: str, record_id: Any, 
                     id_column: str = "id") -> Dict[str, Any]:
        """Delete a record from the specified table"""
        try:
            if database_id not in self._database_registry:
                raise ValueError(f"Database {database_id} not loaded")
            
            # Build DELETE query
            query = f"DELETE FROM {table_name} WHERE {id_column} = ?"
            
            # Execute query
            result = self.execute_query(database_id, query, (record_id,))
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error deleting record from {table_name} in database {database_id}: {str(e)}")
            raise
    
    def close_database(self, database_id: str) -> bool:
        """Close a database connection"""
        try:
            success = self.sqlite_manager.close_database(database_id)
            
            if success and database_id in self._database_registry:
                del self._database_registry[database_id]
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error closing database {database_id}: {str(e)}")
            return False
    
    def close_all_databases(self):
        """Close all database connections"""
        try:
            self.sqlite_manager.close_all_databases()
            self._database_registry.clear()
            
        except Exception as e:
            self.logger.error(f"Error closing all databases: {str(e)}")
            raise
    
    def _is_valid_sqlite_file(self, file_path: str) -> bool:
        """Check if the file is a valid SQLite database"""
        try:
            # Check file extension
            allowed_extensions = {'.db', '.sqlite', '.sqlite3'}
            file_ext = Path(file_path).suffix.lower()
            
            if file_ext not in allowed_extensions:
                return False
            
            # Try to open and read the database
            conn = sqlite3.connect(file_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            cursor.fetchall()
            conn.close()
            
            return True
            
        except Exception:
            return False
    
    def get_database_info(self, database_id: str) -> Optional[DatabaseInfo]:
        """Get information about a specific database"""
        # Ensure registry is up to date by calling get_database_list
        self.get_database_list()
        
        self.logger.info(f"Looking for database_id: {database_id}")
        self.logger.info(f"Registry keys: {list(self._database_registry.keys())}")
        
        if database_id in self._database_registry:
            return self._database_registry[database_id]['info']
        return None
    
    def validate_table_exists(self, database_id: str, table_name: str) -> bool:
        """Check if a table exists in the database"""
        try:
            if database_id not in self._database_registry:
                return False
            
            query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
            result = self.execute_query(database_id, query, (table_name,))
            
            return result['success'] and len(result['data']) > 0
            
        except Exception:
            return False