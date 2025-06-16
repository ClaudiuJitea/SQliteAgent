import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from app.models.schemas import QueryType

class NaturalLanguageParser:
    """Parses natural language queries and extracts intent and entities"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._init_patterns()
    
    def _init_patterns(self):
        """Initialize regex patterns for query parsing"""
        self.patterns = {
            'select_keywords': [
                r'\b(show|display|list|get|find|select|retrieve)\b',
                r'\b(what|which|how many)\b',
                r'\b(all|every)\s+\w+'
            ],
            'count_keywords': [
                r'\b(count|number of|how many|total)\b',
                r'\b(sum|average|avg|max|min)\b'
            ],
            'filter_keywords': [
                r'\bwhere\b',
                r'\b(with|having|contains|includes)\b',
                r'\b(greater than|less than|equal to|equals)\b',
                r'\b(>|<|=|>=|<=|!=)\b'
            ],
            'insert_keywords': [
                r'\b(add|insert|create|new)\b',
                r'\b(record|entry|row)\b'
            ],
            'update_keywords': [
                r'\b(update|modify|change|edit)\b',
                r'\b(set|to)\b'
            ],
            'delete_keywords': [
                r'\b(delete|remove|drop)\b'
            ],
            'table_indicators': [
                r'\b(table|from)\s+(\w+)\b',
                r'\b(in|on)\s+(\w+)\s+(table)?\b'
            ],
            'column_indicators': [
                r'\b(column|field)\s+(\w+)\b',
                r'\b(\w+)\s+(column|field)\b'
            ],
            'sort_keywords': [
                r'\b(sort|order)\s+by\b',
                r'\b(ascending|descending|asc|desc)\b'
            ],
            'limit_keywords': [
                r'\b(limit|top|first)\s+(\d+)\b',
                r'\b(\d+)\s+(rows?|records?)\b'
            ]
        }
    
    def parse_query(self, query: str) -> Dict[str, Any]:
        """Parse natural language query and extract structured information"""
        query_lower = query.lower().strip()
        
        result = {
            'original_query': query,
            'query_type': self._determine_query_type(query_lower),
            'tables': self._extract_tables(query_lower),
            'columns': self._extract_columns(query_lower),
            'filters': self._extract_filters(query_lower),
            'aggregations': self._extract_aggregations(query_lower),
            'sorting': self._extract_sorting(query_lower),
            'limit': self._extract_limit(query_lower),
            'confidence': 0.0,
            'suggestions': []
        }
        
        # Calculate confidence score
        result['confidence'] = self._calculate_confidence(result)
        
        # Generate suggestions for improvement
        result['suggestions'] = self._generate_suggestions(result)
        
        return result
    
    def _determine_query_type(self, query: str) -> QueryType:
        """Determine the type of query based on keywords"""
        # Check for count/aggregate operations first
        for pattern in self.patterns['count_keywords']:
            if re.search(pattern, query, re.IGNORECASE):
                return QueryType.COUNT
        
        # Check for CRUD operations
        for pattern in self.patterns['select_keywords']:
            if re.search(pattern, query, re.IGNORECASE):
                return QueryType.SELECT
        
        for pattern in self.patterns['insert_keywords']:
            if re.search(pattern, query, re.IGNORECASE):
                return QueryType.INSERT
        
        for pattern in self.patterns['update_keywords']:
            if re.search(pattern, query, re.IGNORECASE):
                return QueryType.UPDATE
        
        for pattern in self.patterns['delete_keywords']:
            if re.search(pattern, query, re.IGNORECASE):
                return QueryType.DELETE
        
        return QueryType.UNKNOWN
    
    def _extract_tables(self, query: str) -> List[str]:
        """Extract table names from the query"""
        tables = []
        
        for pattern in self.patterns['table_indicators']:
            matches = re.finditer(pattern, query, re.IGNORECASE)
            for match in matches:
                if len(match.groups()) > 0:
                    table_name = match.group(1)
                    if table_name and table_name not in ['table', 'from', 'in', 'on']:
                        tables.append(table_name)
        
        # Also look for common table names without indicators
        common_table_words = ['users', 'products', 'orders', 'customers', 'items', 'data']
        for word in common_table_words:
            if word in query and word not in tables:
                tables.append(word)
        
        return list(set(tables))
    
    def _extract_columns(self, query: str) -> List[str]:
        """Extract column names from the query"""
        columns = []
        
        # Look for explicit column mentions
        for pattern in self.patterns['column_indicators']:
            matches = re.finditer(pattern, query, re.IGNORECASE)
            for match in matches:
                if len(match.groups()) > 0:
                    column_name = match.group(1)
                    if column_name and column_name not in ['column', 'field']:
                        columns.append(column_name)
        
        # Look for SELECT-like patterns
        select_pattern = r'\b(show|get|display)\s+(\w+(?:,\s*\w+)*)\b'
        matches = re.finditer(select_pattern, query, re.IGNORECASE)
        for match in matches:
            if len(match.groups()) > 1:
                column_list = match.group(2)
                columns.extend([col.strip() for col in column_list.split(',')])
        
        return list(set(columns))
    
    def _extract_filters(self, query: str) -> List[Dict[str, Any]]:
        """Extract filter conditions from the query"""
        filters = []
        
        # Look for WHERE-like conditions
        where_patterns = [
            r'\bwhere\s+(\w+)\s*(=|>|<|>=|<=|!=|like)\s*([\w\s\'"]+)',
            r'\b(\w+)\s+(is|equals?|contains?)\s+([\w\s\'"]+)',
            r'\b(\w+)\s+(greater than|less than|equal to)\s+([\w\s\'"]+)'
        ]
        
        for pattern in where_patterns:
            matches = re.finditer(pattern, query, re.IGNORECASE)
            for match in matches:
                if len(match.groups()) >= 3:
                    filters.append({
                        'column': match.group(1),
                        'operator': match.group(2),
                        'value': match.group(3).strip()
                    })
        
        return filters
    
    def _extract_aggregations(self, query: str) -> List[Dict[str, Any]]:
        """Extract aggregation functions from the query"""
        aggregations = []
        
        agg_patterns = [
            r'\b(count|sum|average|avg|max|min)\s+(?:of\s+)?(\w+)',
            r'\b(total|number of)\s+(\w+)',
            r'\bhow many\s+(\w+)'
        ]
        
        for pattern in agg_patterns:
            matches = re.finditer(pattern, query, re.IGNORECASE)
            for match in matches:
                func = match.group(1).lower()
                if func in ['total', 'number of', 'how many']:
                    func = 'count'
                elif func == 'average':
                    func = 'avg'
                
                aggregations.append({
                    'function': func,
                    'column': match.group(2) if len(match.groups()) > 1 else '*'
                })
        
        return aggregations
    
    def _extract_sorting(self, query: str) -> Optional[Dict[str, Any]]:
        """Extract sorting information from the query"""
        sort_patterns = [
            r'\border\s+by\s+(\w+)\s*(asc|desc|ascending|descending)?',
            r'\bsort\s+by\s+(\w+)\s*(asc|desc|ascending|descending)?'
        ]
        
        for pattern in sort_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                direction = 'ASC'
                if len(match.groups()) > 1 and match.group(2):
                    direction = 'DESC' if match.group(2).lower() in ['desc', 'descending'] else 'ASC'
                
                return {
                    'column': match.group(1),
                    'direction': direction
                }
        
        return None
    
    def _extract_limit(self, query: str) -> Optional[int]:
        """Extract limit/top N information from the query"""
        limit_patterns = [
            r'\blimit\s+(\d+)',
            r'\btop\s+(\d+)',
            r'\bfirst\s+(\d+)',
            r'\b(\d+)\s+rows?'
        ]
        
        for pattern in limit_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return int(match.group(1))
        
        return None
    
    def _calculate_confidence(self, parsed_result: Dict[str, Any]) -> float:
        """Calculate confidence score for the parsed query"""
        score = 0.0
        
        # Base score for query type identification
        if parsed_result['query_type'] != QueryType.UNKNOWN:
            score += 0.3
        
        # Score for table identification
        if parsed_result['tables']:
            score += 0.2
        
        # Score for column identification
        if parsed_result['columns']:
            score += 0.2
        
        # Score for filters
        if parsed_result['filters']:
            score += 0.15
        
        # Score for aggregations
        if parsed_result['aggregations']:
            score += 0.1
        
        # Score for sorting
        if parsed_result['sorting']:
            score += 0.05
        
        return min(score, 1.0)
    
    def _generate_suggestions(self, parsed_result: Dict[str, Any]) -> List[str]:
        """Generate suggestions to improve query clarity"""
        suggestions = []
        
        if not parsed_result['tables']:
            suggestions.append("Consider specifying which table you want to query")
        
        if parsed_result['query_type'] == QueryType.UNKNOWN:
            suggestions.append("Try using clearer action words like 'show', 'find', 'count', etc.")
        
        if parsed_result['confidence'] < 0.5:
            suggestions.append("Your query might be ambiguous. Try being more specific about tables and columns")
        
        if not parsed_result['columns'] and parsed_result['query_type'] == QueryType.SELECT:
            suggestions.append("Specify which columns you want to see, or use 'all columns'")
        
        return suggestions
    
    def suggest_sql_structure(self, parsed_result: Dict[str, Any]) -> str:
        """Suggest a basic SQL structure based on parsed information"""
        query_type = parsed_result['query_type']
        
        if query_type == QueryType.SELECT or query_type == QueryType.COUNT:
            columns = ', '.join(parsed_result['columns']) if parsed_result['columns'] else '*'
            
            if parsed_result['aggregations']:
                agg_parts = []
                for agg in parsed_result['aggregations']:
                    agg_parts.append(f"{agg['function'].upper()}({agg['column']})")
                columns = ', '.join(agg_parts)
            
            sql = f"SELECT {columns}"
            
            if parsed_result['tables']:
                sql += f" FROM {parsed_result['tables'][0]}"
            
            if parsed_result['filters']:
                where_parts = []
                for filter_item in parsed_result['filters']:
                    where_parts.append(f"{filter_item['column']} {filter_item['operator']} '{filter_item['value']}'")
                sql += f" WHERE {' AND '.join(where_parts)}"
            
            if parsed_result['sorting']:
                sort_info = parsed_result['sorting']
                sql += f" ORDER BY {sort_info['column']} {sort_info['direction']}"
            
            if parsed_result['limit']:
                sql += f" LIMIT {parsed_result['limit']}"
            
            return sql
        
        return "-- Unable to generate SQL structure for this query type"