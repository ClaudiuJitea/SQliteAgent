import logging
import os
from typing import Dict, Any, Optional
from datetime import datetime
from app.services.ai_query_processor import AIQueryProcessor
from app.services.natural_language_parser import NaturalLanguageParser
from app.models.database import DatabaseModel
from app.models.schemas import (
    AIQueryResponse, ParsedQuery, QueryResult, QuerySafetyAnalysis, 
    QueryOptimization, RiskLevel
)

class AIService:
    """AI service that provides natural language processing and query assistance"""
    
    def __init__(self, database_model: DatabaseModel):
        self.ai_processor = AIQueryProcessor()
        self.nl_parser = NaturalLanguageParser()
        self.database_model = database_model
        self.logger = logging.getLogger(__name__)
    
    def process_natural_language_query(self, prompt: str, database_id: str, 
                                     include_explanation: bool = False, model: Optional[str] = None) -> AIQueryResponse:
        """Process a natural language query and return structured results"""
        start_time = datetime.now()
        
        try:
            self.logger.info(f"Starting AI query processing for database: {database_id}")
            self.logger.info(f"Prompt: {prompt}")
            self.logger.info(f"Include explanation: {include_explanation}")
            
            # Validate database exists
            if not self.database_model.get_database_info(database_id):
                self.logger.error(f"Database not found: {database_id}")
                return AIQueryResponse(
                    success=False,
                    original_prompt=prompt,
                    error="Database not found"
                )
            
            # Parse natural language query
            parsed_info = self.nl_parser.parse_query(prompt)
            parsed_query = ParsedQuery(**parsed_info)
            
            # Get database schema for AI context
            self.logger.info(f"Retrieving schema for database: {database_id}")
            schema = self.database_model.get_database_schema(database_id)
            if not schema:
                self.logger.error(f"Could not retrieve schema for database: {database_id}")
                return AIQueryResponse(
                    success=False,
                    original_prompt=prompt,
                    error="Could not retrieve database schema"
                )
            
            self.logger.info(f"Schema retrieved successfully, tables: {list(schema.keys()) if isinstance(schema, dict) else 'schema object'}")

            # Convert natural language to SQL using AI
            self.logger.info(f"Calling AI processor to convert prompt to SQL")
            ai_result = self.ai_processor.natural_language_to_sql(prompt, schema, model=model)
            self.logger.info(f"AI processor returned: {ai_result}")
            
            if not ai_result['success']:
                return AIQueryResponse(
                    success=False,
                    original_prompt=prompt,
                    parsed_info=parsed_query,
                    error=ai_result['error']
                )
            
            sql_query = ai_result['sql_query']
            
            # Validate query safety
            safety_check = self.validate_query_safety(sql_query, model=model)
            if not safety_check.safe and safety_check.risk_level == RiskLevel.HIGH:
                return AIQueryResponse(
                    success=False,
                    original_prompt=prompt,
                    sql_query=sql_query,
                    parsed_info=parsed_query,
                    error="Query rejected due to high security risk"
                )
            
            # Execute the generated SQL query
            query_result = self.database_model.execute_query(database_id, sql_query)
            
            # Convert to QueryResult schema
            structured_result = QueryResult(**query_result)
            
            # Generate explanation if requested and query was successful
            explanation = None
            if include_explanation and structured_result.success and structured_result.data:
                explanation_result = self.ai_processor.explain_query_results(
                    structured_result.data, prompt, sql_query, model=model
                )
                if explanation_result['success']:
                    explanation = explanation_result['explanation']
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return AIQueryResponse(
                success=True,
                sql_query=sql_query,
                original_prompt=prompt,
                parsed_info=parsed_query,
                query_result=structured_result,
                explanation=explanation,
                processing_time=processing_time
            )
            
        except Exception as e:
            self.logger.error(f"Error processing natural language query: {str(e)}")
            self.logger.error(f"Exception type: {type(e).__name__}")
            import traceback
            self.logger.error(f"Full traceback: {traceback.format_exc()}")
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return AIQueryResponse(
                success=False,
                original_prompt=prompt,
                error=str(e),
                processing_time=processing_time
            )
    
    def validate_query_safety(self, sql_query: str, model: Optional[str] = None) -> QuerySafetyAnalysis:
        """Validate the safety of a SQL query using AI and rule-based checks"""
        try:
            # First, use rule-based validation from SQLite manager
            basic_validation = self.database_model.sqlite_manager.validate_query_safety(sql_query)
            
            # Then use AI-powered validation
            ai_validation = self.ai_processor.validate_query_safety(sql_query, model=model)
            
            if ai_validation['success']:
                ai_analysis = ai_validation['analysis']
                
                # Combine both analyses
                combined_warnings = []
                combined_recommendations = []
                
                # Add basic validation warnings
                if not basic_validation['safe']:
                    combined_warnings.append(basic_validation['warning'])
                
                # Add AI analysis
                if 'warnings' in ai_analysis:
                    combined_warnings.extend(ai_analysis['warnings'])
                
                if 'recommendations' in ai_analysis:
                    combined_recommendations.extend(ai_analysis['recommendations'])
                
                # Determine overall safety
                is_safe = basic_validation['safe'] and ai_analysis.get('safe', True)
                risk_level = RiskLevel(ai_analysis.get('risk_level', 'medium'))
                
                return QuerySafetyAnalysis(
                    safe=is_safe,
                    risk_level=risk_level,
                    warnings=combined_warnings,
                    recommendations=combined_recommendations
                )
            else:
                # Fallback to basic validation only
                return QuerySafetyAnalysis(
                    safe=basic_validation['safe'],
                    risk_level=RiskLevel.MEDIUM,
                    warnings=[basic_validation.get('warning', 'Unknown safety issue')],
                    recommendations=['Manual review recommended']
                )
                
        except Exception as e:
            self.logger.error(f"Error validating query safety: {str(e)}")
            return QuerySafetyAnalysis(
                safe=False,
                risk_level=RiskLevel.HIGH,
                warnings=[f"Validation error: {str(e)}"],
                recommendations=['Manual review required']
            )
    
    def create_database_from_description(self, description: str, database_name: str, upload_folder: str) -> Dict[str, Any]:
        """Create a new database from natural language description"""
        start_time = datetime.now()
        
        try:
            # Generate schema using AI
            schema_result = self.ai_processor.generate_database_schema(description)
            
            if not schema_result['success']:
                return {
                    'success': False,
                    'error': schema_result['error'],
                    'description': description
                }
            
            # Create file path
            file_path = os.path.join(upload_folder, database_name)
            
            # Create the database
            database_info = self.database_model.create_database(file_path, schema_result['schema'])
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return {
                'success': True,
                'database_info': {
                    'id': database_info.id,
                    'path': database_info.path,
                    'tables': database_info.tables,
                    'size': database_info.size,
                    'status': database_info.status.value,
                    'created_at': database_info.created_at.isoformat() if database_info.created_at else None
                },
                'schema': schema_result['schema'],
                'description': description,
                'processing_time': processing_time
            }
            
        except Exception as e:
            self.logger.error(f"Error creating database from description: {str(e)}")
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return {
                'success': False,
                'error': str(e),
                'description': description,
                'processing_time': processing_time
            }
    
    def get_query_optimization_suggestions(self, sql_query: str, database_id: str, model: Optional[str] = None) -> QueryOptimization:
        """Get AI-powered optimization suggestions for a SQL query"""
        try:
            # Validate database exists
            if not self.database_model.get_database_info(database_id):
                return QueryOptimization(
                    success=False,
                    original_query=sql_query,
                    error="Database not found or not loaded"
                )
            
            # Get database schema for context
            schema = self.database_model.get_database_schema(database_id)
            
            # Get AI optimization suggestions
            optimization_result = self.ai_processor.suggest_optimizations(sql_query, schema, model=model)
            
            if optimization_result['success']:
                return QueryOptimization(
                    success=True,
                    original_query=sql_query,
                    suggestions=optimization_result['suggestions']
                )
            else:
                return QueryOptimization(
                    success=False,
                    original_query=sql_query,
                    error=optimization_result['error']
                )
                
        except Exception as e:
            self.logger.error(f"Error getting optimization suggestions: {str(e)}")
            return QueryOptimization(
                success=False,
                original_query=sql_query,
                error=str(e)
            )
    
    def explain_query_results(self, query_result: QueryResult, original_prompt: str, 
                            sql_query: str) -> Dict[str, Any]:
        """Generate human-readable explanation of query results"""
        try:
            if not query_result.success or not query_result.data:
                return {
                    'success': False,
                    'error': 'No data to explain'
                }
            
            explanation_result = self.ai_processor.explain_query_results(
                query_result.data, original_prompt, sql_query
            )
            
            return explanation_result
            
        except Exception as e:
            self.logger.error(f"Error explaining query results: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def suggest_related_queries(self, original_query: str, database_id: str) -> Dict[str, Any]:
        """Suggest related queries based on the original query and database schema"""
        try:
            # Get database schema
            schema = self.database_model.get_database_schema(database_id)
            
            # Parse the original query to understand intent
            parsed_info = self.nl_parser.parse_query(original_query)
            
            suggestions = []
            
            # Generate suggestions based on parsed information
            if parsed_info['tables']:
                table_name = parsed_info['tables'][0]
                
                # Suggest count query
                suggestions.append(f"How many records are in {table_name}?")
                
                # Suggest column exploration
                if table_name in schema['tables']:
                    table_info = schema['tables'][table_name]
                    for column in table_info.columns[:3]:  # Limit to first 3 columns
                        suggestions.append(f"Show unique values in {column.name} from {table_name}")
                
                # Suggest filtering
                if not parsed_info['filters']:
                    suggestions.append(f"Show {table_name} with specific conditions")
                
                # Suggest aggregation
                if parsed_info['query_type'].value != 'count':
                    suggestions.append(f"Get statistics for {table_name}")
            
            return {
                'success': True,
                'suggestions': suggestions[:5]  # Limit to 5 suggestions
            }
            
        except Exception as e:
            self.logger.error(f"Error generating related query suggestions: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_query_history_insights(self, query_history: list) -> Dict[str, Any]:
        """Analyze query history and provide insights"""
        try:
            if not query_history:
                return {
                    'success': False,
                    'error': 'No query history available'
                }
            
            insights = {
                'total_queries': len(query_history),
                'most_common_tables': {},
                'query_types': {},
                'performance_insights': []
            }
            
            # Analyze query patterns
            for query_info in query_history:
                # Count query types
                if 'query_type' in query_info:
                    query_type = query_info['query_type']
                    insights['query_types'][query_type] = insights['query_types'].get(query_type, 0) + 1
                
                # Count table usage
                if 'tables' in query_info:
                    for table in query_info['tables']:
                        insights['most_common_tables'][table] = insights['most_common_tables'].get(table, 0) + 1
                
                # Performance insights
                if 'execution_time' in query_info and query_info['execution_time'] > 1.0:
                    insights['performance_insights'].append({
                        'query': query_info.get('sql_query', 'Unknown'),
                        'execution_time': query_info['execution_time'],
                        'suggestion': 'Consider optimizing this slow query'
                    })
            
            return {
                'success': True,
                'insights': insights
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing query history: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }