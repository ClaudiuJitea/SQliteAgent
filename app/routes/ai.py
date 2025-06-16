from flask import Blueprint, request, jsonify, current_app
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging
from typing import Dict, Any
from app.models.database import DatabaseModel
from app.models.ai_service import AIService
from app.models.schemas import (
    NaturalLanguageQueryRequest, APIResponse, ErrorResponse
)
from pydantic import ValidationError

# Create blueprint
ai_bp = Blueprint('ai', __name__)

# Import shared database model from database routes
from app.routes.database import db_model
ai_service = AIService(db_model)
logger = logging.getLogger(__name__)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

@ai_bp.route('/query', methods=['POST'])
@limiter.limit("30 per hour")
def process_natural_language_query():
    """Process a natural language query and return SQL + results"""
    try:
        # Log incoming request data for debugging
        logger.info(f"Received request data: {request.json}")
        
        # Validate request data
        try:
            request_data = NaturalLanguageQueryRequest(**request.json)
        except ValidationError as e:
            logger.error(f"Validation error: {e.errors()}")
            error_response = ErrorResponse(
                error="Invalid request data",
                error_code="VALIDATION_ERROR",
                details={"validation_errors": e.errors()}
            )
            return jsonify(error_response.dict()), 400
        
        # Process the natural language query
        ai_response = ai_service.process_natural_language_query(
            request_data.prompt,
            request_data.database_id,
            request_data.include_explanation,
            request_data.model
        )
        
        # Convert to JSON-serializable format
        response_data = {
            'success': ai_response.success,
            'sql_query': ai_response.sql_query,
            'original_prompt': ai_response.original_prompt,
            'explanation': ai_response.explanation,
            'processing_time': ai_response.processing_time,
            'error': ai_response.error
        }
        
        # Add parsed info if available
        if ai_response.parsed_info:
            response_data['parsed_info'] = {
                'original_query': ai_response.parsed_info.original_query,
                'query_type': ai_response.parsed_info.query_type.value,
                'tables': ai_response.parsed_info.tables,
                'columns': ai_response.parsed_info.columns,
                'filters': ai_response.parsed_info.filters,
                'aggregations': ai_response.parsed_info.aggregations,
                'sorting': ai_response.parsed_info.sorting,
                'limit': ai_response.parsed_info.limit,
                'confidence': ai_response.parsed_info.confidence,
                'suggestions': ai_response.parsed_info.suggestions
            }
        
        # Add query result if available
        if ai_response.query_result:
            response_data['query_result'] = {
                'success': ai_response.query_result.success,
                'data': ai_response.query_result.data,
                'columns': ai_response.query_result.columns,
                'row_count': ai_response.query_result.row_count,
                'rows_affected': ai_response.query_result.rows_affected,
                'message': ai_response.query_result.message,
                'error': ai_response.query_result.error,
                'execution_time': ai_response.query_result.execution_time
            }
        
        response = APIResponse(
            success=ai_response.success,
            data=response_data
        )
        
        status_code = 200 if ai_response.success else 400
        return jsonify(response.dict()), status_code
        
    except Exception as e:
        logger.error(f"Error processing natural language query: {str(e)}")
        error_response = ErrorResponse(
            error=str(e),
            error_code="AI_QUERY_ERROR"
        )
        return jsonify(error_response.dict()), 500

@ai_bp.route('/explain', methods=['POST'])
@limiter.limit("50 per hour")
def explain_query_results():
    """Generate explanation for query results"""
    try:
        request_data = request.json
        
        # Validate required fields
        required_fields = ['query_result', 'original_prompt', 'sql_query']
        for field in required_fields:
            if field not in request_data:
                error_response = ErrorResponse(
                    error=f"Missing required field: {field}",
                    error_code="MISSING_FIELD"
                )
                return jsonify(error_response.dict()), 400
        
        # Create QueryResult object from request data
        from app.models.schemas import QueryResult
        query_result = QueryResult(**request_data['query_result'])
        
        # Generate explanation
        explanation_result = ai_service.explain_query_results(
            query_result,
            request_data['original_prompt'],
            request_data['sql_query']
        )
        
        response = APIResponse(
            success=explanation_result['success'],
            data=explanation_result
        )
        
        status_code = 200 if explanation_result['success'] else 400
        return jsonify(response.dict()), status_code
        
    except Exception as e:
        logger.error(f"Error explaining query results: {str(e)}")
        error_response = ErrorResponse(
            error=str(e),
            error_code="EXPLANATION_ERROR"
        )
        return jsonify(error_response.dict()), 500

@ai_bp.route('/optimize', methods=['POST'])
@limiter.limit("20 per hour")
def get_optimization_suggestions():
    """Get AI-powered optimization suggestions for a SQL query"""
    try:
        request_data = request.json
        
        # Validate required fields
        if 'sql_query' not in request_data or 'database_id' not in request_data:
            error_response = ErrorResponse(
                error="Missing required fields: sql_query, database_id",
                error_code="MISSING_FIELDS"
            )
            return jsonify(error_response.dict()), 400
        
        # Get optimization suggestions
        optimization_result = ai_service.get_query_optimization_suggestions(
            request_data['sql_query'],
            request_data['database_id'],
            model=request_data.get('model')
        )
        
        # Convert to JSON-serializable format
        response_data = {
            'success': optimization_result.success,
            'original_query': optimization_result.original_query,
            'suggestions': optimization_result.suggestions,
            'optimized_query': optimization_result.optimized_query,
            'performance_notes': optimization_result.performance_notes,
            'error': optimization_result.error
        }
        
        response = APIResponse(
            success=optimization_result.success,
            data=response_data
        )
        
        status_code = 200 if optimization_result.success else 400
        return jsonify(response.dict()), status_code
        
    except Exception as e:
        logger.error(f"Error getting optimization suggestions: {str(e)}")
        error_response = ErrorResponse(
            error=str(e),
            error_code="OPTIMIZATION_ERROR"
        )
        return jsonify(error_response.dict()), 500

@ai_bp.route('/validate', methods=['POST'])
@limiter.limit("100 per hour")
def validate_query_safety():
    """Validate SQL query safety using AI"""
    try:
        request_data = request.json
        
        # Validate required field
        if 'sql_query' not in request_data:
            error_response = ErrorResponse(
                error="Missing required field: sql_query",
                error_code="MISSING_FIELD"
            )
            return jsonify(error_response.dict()), 400
        
        # Validate query safety
        safety_analysis = ai_service.validate_query_safety(
            request_data['sql_query'],
            model=request_data.get('model')
        )
        
        # Convert to JSON-serializable format
        response_data = {
            'safe': safety_analysis.safe,
            'risk_level': safety_analysis.risk_level.value,
            'warnings': safety_analysis.warnings,
            'recommendations': safety_analysis.recommendations
        }
        
        response = APIResponse(
            success=True,
            data=response_data
        )
        
        return jsonify(response.dict()), 200
        
    except Exception as e:
        logger.error(f"Error validating query safety: {str(e)}")
        error_response = ErrorResponse(
            error=str(e),
            error_code="SAFETY_VALIDATION_ERROR"
        )
        return jsonify(error_response.dict()), 500

@ai_bp.route('/suggest-queries', methods=['POST'])
@limiter.limit("30 per hour")
def suggest_related_queries():
    """Suggest related queries based on the original query"""
    try:
        request_data = request.json
        
        # Validate required fields
        required_fields = ['original_query', 'database_id']
        for field in required_fields:
            if field not in request_data:
                error_response = ErrorResponse(
                    error=f"Missing required field: {field}",
                    error_code="MISSING_FIELD"
                )
                return jsonify(error_response.dict()), 400
        
        # Get query suggestions
        suggestions_result = ai_service.suggest_related_queries(
            request_data['original_query'],
            request_data['database_id']
        )
        
        response = APIResponse(
            success=suggestions_result['success'],
            data=suggestions_result
        )
        
        status_code = 200 if suggestions_result['success'] else 400
        return jsonify(response.dict()), status_code
        
    except Exception as e:
        logger.error(f"Error suggesting related queries: {str(e)}")
        error_response = ErrorResponse(
            error=str(e),
            error_code="QUERY_SUGGESTION_ERROR"
        )
        return jsonify(error_response.dict()), 500

@ai_bp.route('/parse', methods=['POST'])
@limiter.limit("100 per hour")
def parse_natural_language():
    """Parse natural language query and extract structured information"""
    try:
        request_data = request.json
        
        # Validate required field
        if 'query' not in request_data:
            error_response = ErrorResponse(
                error="Missing required field: query",
                error_code="MISSING_FIELD"
            )
            return jsonify(error_response.dict()), 400
        
        # Parse the query
        parsed_info = ai_service.nl_parser.parse_query(request_data['query'])
        
        # Convert enum to string for JSON serialization
        parsed_info['query_type'] = parsed_info['query_type'].value
        
        response = APIResponse(
            success=True,
            data=parsed_info
        )
        
        return jsonify(response.dict()), 200
        
    except Exception as e:
        logger.error(f"Error parsing natural language query: {str(e)}")
        error_response = ErrorResponse(
            error=str(e),
            error_code="PARSING_ERROR"
        )
        return jsonify(error_response.dict()), 500

@ai_bp.route('/history/insights', methods=['POST'])
@limiter.limit("10 per hour")
def get_query_history_insights():
    """Analyze query history and provide insights"""
    try:
        request_data = request.json
        
        # Validate required field
        if 'query_history' not in request_data:
            error_response = ErrorResponse(
                error="Missing required field: query_history",
                error_code="MISSING_FIELD"
            )
            return jsonify(error_response.dict()), 400
        
        # Get insights
        insights_result = ai_service.get_query_history_insights(
            request_data['query_history']
        )
        
        response = APIResponse(
            success=insights_result['success'],
            data=insights_result
        )
        
        status_code = 200 if insights_result['success'] else 400
        return jsonify(response.dict()), status_code
        
    except Exception as e:
        logger.error(f"Error getting query history insights: {str(e)}")
        error_response = ErrorResponse(
            error=str(e),
            error_code="INSIGHTS_ERROR"
        )
        return jsonify(error_response.dict()), 500

@ai_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for AI service"""
    try:
        # Test AI service availability
        test_result = {
            'ai_service_available': True,
            'openrouter_configured': bool(current_app.config.get('OPENROUTER_API_KEY')),
            'model': current_app.config.get('OPENROUTER_MODEL', 'Not configured')
        }
        
        response = APIResponse(
            success=True,
            message="AI service is healthy",
            data=test_result
        )
        
        return jsonify(response.dict()), 200
        
    except Exception as e:
        logger.error(f"AI service health check failed: {str(e)}")
        error_response = ErrorResponse(
            error=str(e),
            error_code="HEALTH_CHECK_ERROR"
        )
        return jsonify(error_response.dict()), 500

@ai_bp.route('/status', methods=['GET'])
def get_ai_status():
    """Get AI service status and configuration"""
    try:
        return jsonify({
            'success': True,
            'openrouter_configured': bool(current_app.config.get('OPENROUTER_API_KEY')),
            'model': current_app.config.get('OPENROUTER_MODEL', 'Not configured')
        })
    except Exception as e:
        current_app.logger.error(f"Error getting AI status: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_bp.route('/models', methods=['GET'])
def get_available_models():
    """Get available models from OpenRouter API"""
    try:
        import requests
        
        api_key = current_app.config.get('OPENROUTER_API_KEY')
        if not api_key:
            return jsonify({
                'success': False,
                'error': 'OpenRouter API key not configured'
            }), 400
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(
            "https://openrouter.ai/api/v1/models",
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        
        models_data = response.json()
        
        # Filter and format models for the dropdown
        formatted_models = []
        for model in models_data.get('data', []):
            formatted_models.append({
                'id': model['id'],
                'name': model.get('name', model['id']),
                'description': model.get('description', ''),
                'context_length': model.get('context_length', 0)
            })
        
        # Sort models by name for better UX
        formatted_models.sort(key=lambda x: x['name'])
        
        return jsonify({
            'success': True,
            'models': formatted_models
        })
        
    except requests.RequestException as e:
        current_app.logger.error(f"Error fetching models from OpenRouter: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to fetch models: {str(e)}'
        }), 500
    except Exception as e:
        current_app.logger.error(f"Error getting available models: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_bp.route('/natural-language', methods=['POST'])
@limiter.limit("30 per hour")
def process_natural_language_query_alias():
    """Alias for /query endpoint to maintain compatibility"""
    try:
        request_data = request.get_json()
        logger.info(f"Natural language alias called with data: {request_data}")
        logger.info(f"About to call AI service process_natural_language_query")
        response, status_code = process_natural_language_query()
        logger.info(f"AI service returned response with status: {status_code}")
        return response, status_code
    except Exception as e:
        logger.error(f"Error in natural language alias: {str(e)}")
        logger.error(f"Exception type: {type(e).__name__}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

# Error handlers for the blueprint
@ai_bp.errorhandler(429)
def rate_limit_exceeded(error):
    error_response = ErrorResponse(
        error="Rate limit exceeded. Please try again later.",
        error_code="RATE_LIMIT_EXCEEDED"
    )
    return jsonify(error_response.dict()), 429

@ai_bp.errorhandler(404)
def not_found(error):
    error_response = ErrorResponse(
        error="AI endpoint not found",
        error_code="NOT_FOUND"
    )
    return jsonify(error_response.dict()), 404

@ai_bp.errorhandler(500)
def internal_error(error):
    error_response = ErrorResponse(
        error="Internal AI service error",
        error_code="INTERNAL_ERROR"
    )
    return jsonify(error_response.dict()), 500