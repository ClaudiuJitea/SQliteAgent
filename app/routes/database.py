from flask import Blueprint, request, jsonify, current_app
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.utils import secure_filename
import os
import logging
from typing import Dict, Any
from app.models.database import DatabaseModel
from app.models.ai_service import AIService
from app.models.schemas import (
    DatabaseLoadRequest, DatabaseCreateRequest, QueryRequest, APIResponse, ErrorResponse
)
from pydantic import ValidationError

# Create blueprint
database_bp = Blueprint('database', __name__)

# Initialize database model and AI service
db_model = DatabaseModel()
ai_service = AIService(db_model)
logger = logging.getLogger(__name__)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

@database_bp.route('/', methods=['GET'])
@limiter.limit("100 per hour")
def list_databases():
    """Get list of all loaded databases"""
    try:
        databases = db_model.get_database_list()
        
        # Convert to dict format for JSON response
        database_list = []
        for db in databases:
            database_list.append({
                'id': db.id,
                'path': db.path,
                'tables': db.tables,
                'size': db.size,
                'status': db.status.value,
                'created_at': db.created_at.isoformat() if db.created_at else None,
                'last_accessed': db.last_accessed.isoformat() if db.last_accessed else None
            })
        
        response = APIResponse(
            success=True,
            message=f"Found {len(database_list)} databases",
            data=database_list
        )
        
        return jsonify(response.dict()), 200
        
    except Exception as e:
        logger.error(f"Error listing databases: {str(e)}")
        error_response = ErrorResponse(
            error=str(e),
            error_code="DATABASE_LIST_ERROR"
        )
        return jsonify(error_response.dict()), 500

@database_bp.route('/create', methods=['POST'])
@limiter.limit("10 per hour")
def create_database():
    """Create a new database from natural language description"""
    try:
        # Validate request data
        try:
            request_data = DatabaseCreateRequest(**request.json)
        except ValidationError as e:
            error_response = ErrorResponse(
                error=f"Invalid request data: {str(e)}",
                error_code="VALIDATION_ERROR"
            )
            return jsonify(error_response.dict()), 400
        
        # Get upload folder from config
        upload_folder = current_app.config['UPLOAD_FOLDER']
        
        # Create database using AI service
        result = ai_service.create_database_from_description(
            request_data.description,
            request_data.database_name,
            upload_folder
        )
        
        if result['success']:
            response = APIResponse(
                success=True,
                message=f"Database '{request_data.database_name}' created successfully",
                data=result
            )
            return jsonify(response.dict()), 201
        else:
            error_response = ErrorResponse(
                error=result['error'],
                error_code="DATABASE_CREATION_ERROR"
            )
            return jsonify(error_response.dict()), 500
            
    except Exception as e:
        logger.error(f"Error creating database: {str(e)}")
        error_response = ErrorResponse(
            error=str(e),
            error_code="DATABASE_CREATION_ERROR"
        )
        return jsonify(error_response.dict()), 500

@database_bp.route('/load', methods=['POST'])
@limiter.limit("20 per hour")
def load_database():
    """Load a new database from file upload or existing path"""
    try:
        # Check if loading from existing file path
        if request.is_json:
            data = request.get_json()
            if 'file_path' in data:
                file_path = data['file_path']
                
                # Handle relative paths by converting to absolute paths
                if not os.path.isabs(file_path):
                    upload_folder = current_app.config['UPLOAD_FOLDER']
                    # If path starts with 'uploads/', remove it to avoid duplication
                    if file_path.startswith('uploads/'):
                        file_path = file_path[8:]  # Remove 'uploads/' prefix
                    elif file_path.startswith('uploads\\'):
                        file_path = file_path[8:]  # Remove 'uploads\' prefix
                    # Convert to absolute path relative to upload folder
                    file_path = os.path.join(upload_folder, file_path)
                
                # Validate file exists
                if not os.path.exists(file_path):
                    error_response = ErrorResponse(
                        error=f"Database file not found: {file_path}",
                        error_code="FILE_NOT_FOUND"
                    )
                    return jsonify(error_response.dict()), 404
                
                # Validate file extension
                if not file_path.lower().endswith(('.db', '.sqlite', '.sqlite3')):
                    error_response = ErrorResponse(
                        error="Invalid file type. Only .db, .sqlite, and .sqlite3 files are allowed",
                        error_code="INVALID_FILE_TYPE"
                    )
                    return jsonify(error_response.dict()), 400
                
                # Load database directly from original location
                database_info = db_model.load_database(file_path)
            else:
                error_response = ErrorResponse(
                    error="No file_path provided in JSON request",
                    error_code="NO_FILE_PATH_PROVIDED"
                )
                return jsonify(error_response.dict()), 400
        else:
            # Handle file upload (original behavior)
            if 'database' not in request.files:
                error_response = ErrorResponse(
                    error="No database file provided",
                    error_code="NO_FILE_PROVIDED"
                )
                return jsonify(error_response.dict()), 400
            
            file = request.files['database']
            if file.filename == '':
                error_response = ErrorResponse(
                    error="No file selected",
                    error_code="NO_FILE_SELECTED"
                )
                return jsonify(error_response.dict()), 400
            
            # Validate file extension
            if not file.filename.lower().endswith(('.db', '.sqlite', '.sqlite3')):
                error_response = ErrorResponse(
                    error="Invalid file type. Only .db, .sqlite, and .sqlite3 files are allowed",
                    error_code="INVALID_FILE_TYPE"
                )
                return jsonify(error_response.dict()), 400
            
            # Save uploaded file
            upload_folder = current_app.config['UPLOAD_FOLDER']
            filename = secure_filename(file.filename)
            file_path = os.path.join(upload_folder, filename)
            
            # Check if file already exists
            if os.path.exists(file_path):
                # Check if this database is already loaded
                existing_databases = db_model.get_database_list()
                for db in existing_databases:
                    if db.path == file_path:
                        # Database already loaded, return existing info
                        response_data = {
                            'database_id': db.id,
                            'path': db.path,
                            'tables': db.tables,
                            'size': db.size,
                            'status': db.status.value,
                            'created_at': db.created_at.isoformat() if db.created_at else None,
                            'last_accessed': db.last_accessed.isoformat() if db.last_accessed else None
                        }
                        
                        response = APIResponse(
                            success=True,
                            message=f"Database already loaded: {db.id}",
                            data=response_data
                        )
                        
                        return jsonify(response.dict()), 200
                
                # File exists but not loaded, use existing file directly
                # This prevents creating unnecessary duplicates
                pass
            else:
                # File doesn't exist, save the uploaded file
                file.save(file_path)
                
                # Verify file was saved
                if not os.path.exists(file_path):
                    error_response = ErrorResponse(
                        error="Failed to save uploaded file",
                        error_code="FILE_SAVE_ERROR"
                    )
                    return jsonify(error_response.dict()), 500
            
            # Check file size
            file_size = os.path.getsize(file_path)
            max_size = current_app.config.get('MAX_FILE_SIZE', 100 * 1024 * 1024)  # 100MB default
            
            if file_size > max_size:
                os.remove(file_path)  # Clean up
                error_response = ErrorResponse(
                    error=f"File too large. Maximum size is {max_size // (1024*1024)}MB",
                    error_code="FILE_TOO_LARGE"
                )
                return jsonify(error_response.dict()), 400
            
            # Load database
            database_info = db_model.load_database(file_path)
        
        # Convert to dict format for JSON response
        response_data = {
            'database_id': database_info.id,
            'path': database_info.path,
            'tables': database_info.tables,
            'size': database_info.size,
            'status': database_info.status.value,
            'created_at': database_info.created_at.isoformat() if database_info.created_at else None,
            'last_accessed': database_info.last_accessed.isoformat() if database_info.last_accessed else None
        }
        
        response = APIResponse(
            success=True,
            message=f"Database loaded successfully: {database_info.id}",
            data=response_data
        )
        
        return jsonify(response.dict()), 200
        
    except Exception as e:
        logger.error(f"Error loading database: {str(e)}")
        error_response = ErrorResponse(
            error=str(e),
            error_code="DATABASE_LOAD_ERROR"
        )
        return jsonify(error_response.dict()), 500

@database_bp.route('/<database_id>/info', methods=['GET'])
@limiter.limit("200 per hour")
def get_database_info(database_id):
    """Get detailed information about a specific database"""
    try:
        database_info = db_model.get_database_info(database_id)
        
        if not database_info:
            error_response = ErrorResponse(
                error=f"Database {database_id} not found",
                error_code="DATABASE_NOT_FOUND"
            )
            return jsonify(error_response.dict()), 404
        
        response = APIResponse(
            success=True,
            message=f"Database info retrieved: {database_id}",
            data=database_info
        )
        
        return jsonify(response.dict()), 200
        
    except Exception as e:
        logger.error(f"Error getting database info: {str(e)}")
        error_response = ErrorResponse(
            error=str(e),
            error_code="DATABASE_INFO_ERROR"
        )
        return jsonify(error_response.dict()), 500

@database_bp.route('/<database_id>/schema', methods=['GET'])
@limiter.limit("100 per hour")
def get_database_schema(database_id):
    """Get database schema information"""
    try:
        schema = db_model.get_database_schema(database_id)
        
        response = APIResponse(
            success=True,
            message=f"Schema retrieved for database: {database_id}",
            data=schema
        )
        
        return jsonify(response.dict()), 200
        
    except ValueError as e:
        error_response = ErrorResponse(
            error=str(e),
            error_code="DATABASE_NOT_FOUND"
        )
        return jsonify(error_response.dict()), 404
        
    except Exception as e:
        logger.error(f"Error getting database schema: {str(e)}")
        error_response = ErrorResponse(
            error=str(e),
            error_code="SCHEMA_ERROR"
        )
        return jsonify(error_response.dict()), 500

@database_bp.route('/<database_id>/query', methods=['POST'])
@limiter.limit("50 per hour")
def execute_query(database_id):
    """Execute a SQL query on a database"""
    try:
        # Validate request data
        try:
            request_data = QueryRequest(**request.json)
        except ValidationError as e:
            error_response = ErrorResponse(
                error=f"Invalid request data: {str(e)}",
                error_code="VALIDATION_ERROR"
            )
            return jsonify(error_response.dict()), 400
        
        # Execute query
        result = db_model.execute_query(database_id, request_data.query, request_data.params)
        
        response = APIResponse(
            success=True,
            message="Query executed successfully",
            data=result
        )
        
        return jsonify(response.dict()), 200
        
    except Exception as e:
        logger.error(f"Error executing query: {str(e)}")
        error_response = ErrorResponse(
            error=str(e),
            error_code="QUERY_EXECUTION_ERROR"
        )
        return jsonify(error_response.dict()), 500

@database_bp.route('/<database_id>/close', methods=['POST'])
@limiter.limit("10 per hour")
def close_database(database_id):
    """Close a database connection"""
    try:
        db_model.close_database(database_id)
        
        response = APIResponse(
            success=True,
            message=f"Database {database_id} closed successfully"
        )
        
        return jsonify(response.dict()), 200
        
    except Exception as e:
        logger.error(f"Error closing database: {str(e)}")
        error_response = ErrorResponse(
            error=str(e),
            error_code="DATABASE_CLOSE_ERROR"
        )
        return jsonify(error_response.dict()), 500

# Error handlers for the blueprint
@database_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found',
        'error_code': 'NOT_FOUND'
    }), 404

@database_bp.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        'success': False,
        'error': 'Method not allowed',
        'error_code': 'METHOD_NOT_ALLOWED'
    }), 405