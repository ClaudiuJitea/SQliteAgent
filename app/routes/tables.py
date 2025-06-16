from flask import Blueprint, request, jsonify, current_app
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging
import os
from typing import Dict, Any
from app.models.database import DatabaseModel
from app.models.schemas import (
    TableDataRequest, RecordInsertRequest, RecordUpdateRequest, 
    RecordDeleteRequest, APIResponse, ErrorResponse
)
from pydantic import ValidationError

# Create blueprint
tables_bp = Blueprint('tables', __name__)

# Initialize database model
db_model = DatabaseModel()
logger = logging.getLogger(__name__)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

@tables_bp.route('/<database_id>/<table_name>', methods=['GET'])
@limiter.limit("200 per hour")
def get_table_data(database_id: str, table_name: str):
    """Get paginated data from a specific table"""
    try:
        # Get query parameters
        limit = min(int(request.args.get('limit', 100)), 1000)  # Max 1000 rows
        offset = max(int(request.args.get('offset', 0)), 0)
        sort_by = request.args.get('sort_by')
        sort_order = request.args.get('sort_order', 'ASC').upper()
        
        # Validate sort order
        if sort_order not in ['ASC', 'DESC']:
            sort_order = 'ASC'
        
        # Parse filters from query parameters
        filters = {}
        for key, value in request.args.items():
            if key.startswith('filter_'):
                column_name = key[7:]  # Remove 'filter_' prefix
                filters[column_name] = value
        
        # Validate database exists
        if not db_model.get_database_info(database_id):
            error_response = ErrorResponse(
                error=f"Database not found: {database_id}",
                error_code="DATABASE_NOT_FOUND"
            )
            return jsonify(error_response.dict()), 404
        
        # Validate table exists
        if not db_model.validate_table_exists(database_id, table_name):
            error_response = ErrorResponse(
                error=f"Table not found: {table_name}",
                error_code="TABLE_NOT_FOUND"
            )
            return jsonify(error_response.dict()), 404
        
        # Get table data
        result = db_model.get_table_data(
            database_id=database_id,
            table_name=table_name,
            limit=limit,
            offset=offset,
            filters=filters if filters else None,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        if result['success']:
            response_data = {
                'table_name': table_name,
                'data': result['data'],
                'columns': result['columns'],
                'row_count': result['row_count'],
                'page_info': result.get('page_info'),
                'execution_time': result.get('execution_time')
            }
            
            response = APIResponse(
                success=True,
                data=response_data
            )
            
            return jsonify(response.dict()), 200
        else:
            error_response = ErrorResponse(
                error=result.get('error', 'Unknown error'),
                error_code="TABLE_DATA_ERROR"
            )
            return jsonify(error_response.dict()), 500
        
    except ValueError as e:
        error_response = ErrorResponse(
            error=str(e),
            error_code="INVALID_PARAMETER"
        )
        return jsonify(error_response.dict()), 400
        
    except Exception as e:
        logger.error(f"Error getting table data: {str(e)}")
        error_response = ErrorResponse(
            error=str(e),
            error_code="TABLE_DATA_ERROR"
        )
        return jsonify(error_response.dict()), 500

@tables_bp.route('/<database_id>/<table_name>', methods=['POST'])
@limiter.limit("100 per hour")
def insert_record(database_id: str, table_name: str):
    """Insert a new record into the specified table"""
    try:
        # Validate request data
        request_data = request.json
        if not request_data or 'data' not in request_data:
            error_response = ErrorResponse(
                error="Missing record data",
                error_code="MISSING_DATA"
            )
            return jsonify(error_response.dict()), 400
        
        # Create request object for validation
        try:
            insert_request = RecordInsertRequest(
                table_name=table_name,
                database_id=database_id,
                data=request_data['data']
            )
        except ValidationError as e:
            error_response = ErrorResponse(
                error="Invalid request data",
                error_code="VALIDATION_ERROR",
                details=e.errors()
            )
            return jsonify(error_response.dict()), 400
        
        # Validate database exists
        if not db_model.get_database_info(database_id):
            error_response = ErrorResponse(
                error=f"Database not found: {database_id}",
                error_code="DATABASE_NOT_FOUND"
            )
            return jsonify(error_response.dict()), 404
        
        # Validate table exists
        if not db_model.validate_table_exists(database_id, table_name):
            error_response = ErrorResponse(
                error=f"Table not found: {table_name}",
                error_code="TABLE_NOT_FOUND"
            )
            return jsonify(error_response.dict()), 404
        
        # Insert record
        result = db_model.insert_record(
            database_id=database_id,
            table_name=table_name,
            data=insert_request.data
        )
        
        if result['success']:
            response = APIResponse(
                success=True,
                message=f"Record inserted successfully into {table_name}",
                data=result
            )
            return jsonify(response.dict()), 201
        else:
            error_response = ErrorResponse(
                error=result.get('error', 'Unknown error'),
                error_code="INSERT_ERROR"
            )
            return jsonify(error_response.dict()), 500
        
    except Exception as e:
        logger.error(f"Error inserting record: {str(e)}")
        error_response = ErrorResponse(
            error=str(e),
            error_code="INSERT_ERROR"
        )
        return jsonify(error_response.dict()), 500

@tables_bp.route('/<database_id>/<table_name>/<record_id>', methods=['PUT'])
@limiter.limit("100 per hour")
def update_record(database_id: str, table_name: str, record_id: str):
    """Update an existing record in the specified table"""
    try:
        # Validate request data
        request_data = request.json
        if not request_data or 'data' not in request_data:
            error_response = ErrorResponse(
                error="Missing record data",
                error_code="MISSING_DATA"
            )
            return jsonify(error_response.dict()), 400
        
        # Get ID column name (default to 'id')
        id_column = request_data.get('id_column', 'id')
        
        # Create request object for validation
        try:
            update_request = RecordUpdateRequest(
                table_name=table_name,
                database_id=database_id,
                record_id=record_id,
                data=request_data['data'],
                id_column=id_column
            )
        except ValidationError as e:
            error_response = ErrorResponse(
                error="Invalid request data",
                error_code="VALIDATION_ERROR",
                details=e.errors()
            )
            return jsonify(error_response.dict()), 400
        
        # Validate database exists
        if not db_model.get_database_info(database_id):
            error_response = ErrorResponse(
                error=f"Database not found: {database_id}",
                error_code="DATABASE_NOT_FOUND"
            )
            return jsonify(error_response.dict()), 404
        
        # Validate table exists
        if not db_model.validate_table_exists(database_id, table_name):
            error_response = ErrorResponse(
                error=f"Table not found: {table_name}",
                error_code="TABLE_NOT_FOUND"
            )
            return jsonify(error_response.dict()), 404
        
        # Update record
        result = db_model.update_record(
            database_id=database_id,
            table_name=table_name,
            record_id=record_id,
            data=update_request.data,
            id_column=update_request.id_column
        )
        
        if result['success']:
            if result.get('rows_affected', 0) == 0:
                error_response = ErrorResponse(
                    error=f"Record not found: {record_id}",
                    error_code="RECORD_NOT_FOUND"
                )
                return jsonify(error_response.dict()), 404
            
            response = APIResponse(
                success=True,
                message=f"Record updated successfully in {table_name}",
                data=result
            )
            return jsonify(response.dict()), 200
        else:
            error_response = ErrorResponse(
                error=result.get('error', 'Unknown error'),
                error_code="UPDATE_ERROR"
            )
            return jsonify(error_response.dict()), 500
        
    except Exception as e:
        logger.error(f"Error updating record: {str(e)}")
        error_response = ErrorResponse(
            error=str(e),
            error_code="UPDATE_ERROR"
        )
        return jsonify(error_response.dict()), 500

@tables_bp.route('/<database_id>/<table_name>/<record_id>', methods=['DELETE'])
@limiter.limit("50 per hour")
def delete_record(database_id: str, table_name: str, record_id: str):
    """Delete a record from the specified table"""
    try:
        # Get ID column name from query parameters (default to 'id')
        id_column = request.args.get('id_column', 'id')
        
        # Create request object for validation
        try:
            delete_request = RecordDeleteRequest(
                table_name=table_name,
                database_id=database_id,
                record_id=record_id,
                id_column=id_column
            )
        except ValidationError as e:
            error_response = ErrorResponse(
                error="Invalid request data",
                error_code="VALIDATION_ERROR",
                details=e.errors()
            )
            return jsonify(error_response.dict()), 400
        
        # Validate database exists
        if not db_model.get_database_info(database_id):
            error_response = ErrorResponse(
                error=f"Database not found: {database_id}",
                error_code="DATABASE_NOT_FOUND"
            )
            return jsonify(error_response.dict()), 404
        
        # Validate table exists
        if not db_model.validate_table_exists(database_id, table_name):
            error_response = ErrorResponse(
                error=f"Table not found: {table_name}",
                error_code="TABLE_NOT_FOUND"
            )
            return jsonify(error_response.dict()), 404
        
        # Delete record
        result = db_model.delete_record(
            database_id=database_id,
            table_name=table_name,
            record_id=record_id,
            id_column=delete_request.id_column
        )
        
        if result['success']:
            if result.get('rows_affected', 0) == 0:
                error_response = ErrorResponse(
                    error=f"Record not found: {record_id}",
                    error_code="RECORD_NOT_FOUND"
                )
                return jsonify(error_response.dict()), 404
            
            response = APIResponse(
                success=True,
                message=f"Record deleted successfully from {table_name}",
                data=result
            )
            return jsonify(response.dict()), 200
        else:
            error_response = ErrorResponse(
                error=result.get('error', 'Unknown error'),
                error_code="DELETE_ERROR"
            )
            return jsonify(error_response.dict()), 500
        
    except Exception as e:
        logger.error(f"Error deleting record: {str(e)}")
        error_response = ErrorResponse(
            error=str(e),
            error_code="DELETE_ERROR"
        )
        return jsonify(error_response.dict()), 500

@tables_bp.route('/<database_id>/<table_name>/schema', methods=['GET'])
@limiter.limit("100 per hour")
def get_table_schema(database_id: str, table_name: str):
    """Get schema information for a specific table"""
    try:
        # Debug logging
        logger.info(f"Getting schema for database: {database_id}, table: {table_name}")
        
        # Check if database exists in registry
        db_info = db_model.get_database_info(database_id)
        logger.info(f"Database info from registry: {db_info}")
        
        # If not in registry, try to load it
        if not db_info:
            logger.info(f"Database {database_id} not in registry, checking if file exists")
            # Try to find the database file in upload folder
            upload_folder = current_app.config['UPLOAD_FOLDER']
            db_path = os.path.join(upload_folder, database_id)
            
            if os.path.exists(db_path):
                logger.info(f"Found database file at {db_path}, loading it")
                try:
                    db_info = db_model.load_database(db_path)
                    logger.info(f"Successfully loaded database: {db_info}")
                except Exception as load_error:
                    logger.error(f"Failed to load database: {load_error}")
                    error_response = ErrorResponse(
                        error=f"Failed to load database: {database_id}",
                        error_code="DATABASE_LOAD_ERROR"
                    )
                    return jsonify(error_response.dict()), 500
            else:
                logger.error(f"Database file not found: {db_path}")
                error_response = ErrorResponse(
                    error=f"Database not found: {database_id}",
                    error_code="DATABASE_NOT_FOUND"
                )
                return jsonify(error_response.dict()), 404
        
        # Validate table exists
        if not db_model.validate_table_exists(database_id, table_name):
            error_response = ErrorResponse(
                error=f"Table not found: {table_name}",
                error_code="TABLE_NOT_FOUND"
            )
            return jsonify(error_response.dict()), 404
        
        # Get database schema
        schema = db_model.get_database_schema(database_id)
        
        if table_name not in schema['tables']:
            error_response = ErrorResponse(
                error=f"Table schema not found: {table_name}",
                error_code="TABLE_SCHEMA_NOT_FOUND"
            )
            return jsonify(error_response.dict()), 404
        
        table_info = schema['tables'][table_name]
        
        # Convert to JSON-serializable format
        table_schema = {
            'table_name': table_name,
            'row_count': table_info.row_count,
            'columns': [
                {
                    'name': col.name,
                    'type': col.type,
                    'not_null': col.not_null,
                    'default_value': col.default_value,
                    'primary_key': col.primary_key
                } for col in table_info.columns
            ]
        }
        
        response = APIResponse(
            success=True,
            data=table_schema
        )
        
        return jsonify(response.dict()), 200
        
    except Exception as e:
        logger.error(f"Error getting table schema: {str(e)}")
        error_response = ErrorResponse(
            error=str(e),
            error_code="TABLE_SCHEMA_ERROR"
        )
        return jsonify(error_response.dict()), 500

@tables_bp.route('/<database_id>/<table_name>/export', methods=['GET'])
@limiter.limit("10 per hour")
def export_table_data(database_id: str, table_name: str):
    """Export table data in various formats"""
    try:
        # Get export format from query parameters
        export_format = request.args.get('format', 'json').lower()
        limit = min(int(request.args.get('limit', 1000)), 10000)  # Max 10k rows for export
        
        # Validate format
        if export_format not in ['json', 'csv']:
            error_response = ErrorResponse(
                error="Unsupported export format. Use 'json' or 'csv'",
                error_code="INVALID_FORMAT"
            )
            return jsonify(error_response.dict()), 400
        
        # Validate database exists
        if not db_model.get_database_info(database_id):
            error_response = ErrorResponse(
                error=f"Database not found: {database_id}",
                error_code="DATABASE_NOT_FOUND"
            )
            return jsonify(error_response.dict()), 404
        
        # Validate table exists
        if not db_model.validate_table_exists(database_id, table_name):
            error_response = ErrorResponse(
                error=f"Table not found: {table_name}",
                error_code="TABLE_NOT_FOUND"
            )
            return jsonify(error_response.dict()), 404
        
        # Get table data
        result = db_model.get_table_data(
            database_id=database_id,
            table_name=table_name,
            limit=limit,
            offset=0
        )
        
        if not result['success']:
            error_response = ErrorResponse(
                error=result.get('error', 'Unknown error'),
                error_code="EXPORT_ERROR"
            )
            return jsonify(error_response.dict()), 500
        
        export_data = {
            'table_name': table_name,
            'export_format': export_format,
            'row_count': result['row_count'],
            'data': result['data'],
            'columns': result['columns']
        }
        
        response = APIResponse(
            success=True,
            message=f"Table data exported successfully in {export_format} format",
            data=export_data
        )
        
        return jsonify(response.dict()), 200
        
    except ValueError as e:
        error_response = ErrorResponse(
            error=str(e),
            error_code="INVALID_PARAMETER"
        )
        return jsonify(error_response.dict()), 400
        
    except Exception as e:
        logger.error(f"Error exporting table data: {str(e)}")
        error_response = ErrorResponse(
            error=str(e),
            error_code="EXPORT_ERROR"
        )
        return jsonify(error_response.dict()), 500

# Error handlers for the blueprint
@tables_bp.errorhandler(404)
def not_found(error):
    error_response = ErrorResponse(
        error="Table or resource not found",
        error_code="NOT_FOUND"
    )
    return jsonify(error_response.dict()), 404

@tables_bp.errorhandler(500)
def internal_error(error):
    error_response = ErrorResponse(
        error="Internal table service error",
        error_code="INTERNAL_ERROR"
    )
    return jsonify(error_response.dict()), 500