// AI Service Module
class AIService {
    constructor() {
        this.queryHistory = [];
        this.suggestions = [];
        this.isProcessing = false;
    }
    
    // Natural language query processing
    async processNaturalLanguageQuery(databaseId, query) {
        this.isProcessing = true;
        
        try {
            const response = await fetch('/api/ai/query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    database_id: databaseId,
                    query: query
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                // Store in history
                this.addToHistory({
                    type: 'natural_language',
                    query: query,
                    result: result.data,
                    timestamp: new Date().toISOString(),
                    databaseId: databaseId
                });
                
                return result.data;
            } else {
                throw new Error(result.error || 'Failed to process natural language query');
            }
        } catch (error) {
            console.error('Natural language query error:', error);
            throw error;
        } finally {
            this.isProcessing = false;
        }
    }
    
    // Parse natural language to understand intent
    async parseNaturalLanguage(query, databaseId = null) {
        try {
            const response = await fetch('/api/ai/parse', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    query: query,
                    database_id: databaseId
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                return result.data;
            } else {
                throw new Error(result.error || 'Failed to parse natural language');
            }
        } catch (error) {
            console.error('Natural language parsing error:', error);
            throw error;
        }
    }
    
    // Explain query results
    async explainResults(databaseId, query, results) {
        try {
            const response = await fetch('/api/ai/explain', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    database_id: databaseId,
                    query: query,
                    results: results
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                return result.data;
            } else {
                throw new Error(result.error || 'Failed to explain results');
            }
        } catch (error) {
            console.error('Results explanation error:', error);
            throw error;
        }
    }
    
    // Suggest query optimizations
    async suggestOptimizations(databaseId, query) {
        try {
            const response = await fetch('/api/ai/optimize', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    database_id: databaseId,
                    query: query
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                return result.data;
            } else {
                throw new Error(result.error || 'Failed to suggest optimizations');
            }
        } catch (error) {
            console.error('Optimization suggestion error:', error);
            throw error;
        }
    }
    
    // Validate query safety
    async validateQuerySafety(databaseId, query) {
        try {
            const response = await fetch('/api/ai/validate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    database_id: databaseId,
                    query: query
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                return result.data;
            } else {
                throw new Error(result.error || 'Failed to validate query safety');
            }
        } catch (error) {
            console.error('Query safety validation error:', error);
            throw error;
        }
    }
    
    // Get related query suggestions
    async getRelatedQueries(databaseId, query) {
        try {
            const response = await fetch('/api/ai/related', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    database_id: databaseId,
                    query: query
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.suggestions = result.data.suggestions || [];
                return result.data;
            } else {
                throw new Error(result.error || 'Failed to get related queries');
            }
        } catch (error) {
            console.error('Related queries error:', error);
            throw error;
        }
    }
    
    // Get insights from query history
    async getHistoryInsights(databaseId) {
        try {
            const response = await fetch('/api/ai/insights', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    database_id: databaseId
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                return result.data;
            } else {
                throw new Error(result.error || 'Failed to get history insights');
            }
        } catch (error) {
            console.error('History insights error:', error);
            throw error;
        }
    }
    
    // Check AI service health
    async checkHealth() {
        try {
            const response = await fetch('/api/ai/health');
            const result = await response.json();
            
            if (result.success) {
                return result.data;
            } else {
                throw new Error(result.error || 'AI service health check failed');
            }
        } catch (error) {
            console.error('AI health check error:', error);
            throw error;
        }
    }
    
    // Query suggestion and auto-completion
    generateQuerySuggestions(input, schema) {
        const suggestions = [];
        const inputLower = input.toLowerCase();
        
        // Basic query starters
        const starters = [
            'SELECT * FROM',
            'SELECT COUNT(*) FROM',
            'SHOW TABLES',
            'DESCRIBE',
            'INSERT INTO',
            'UPDATE',
            'DELETE FROM'
        ];
        
        // Add starter suggestions
        starters.forEach(starter => {
            if (starter.toLowerCase().includes(inputLower)) {
                suggestions.push({
                    text: starter,
                    type: 'keyword',
                    description: 'SQL keyword'
                });
            }
        });
        
        // Add table suggestions
        if (schema && schema.tables) {
            Object.keys(schema.tables).forEach(tableName => {
                if (tableName.toLowerCase().includes(inputLower)) {
                    suggestions.push({
                        text: tableName,
                        type: 'table',
                        description: `Table: ${tableName}`
                    });
                }
                
                // Add column suggestions
                const table = schema.tables[tableName];
                if (table.columns) {
                    table.columns.forEach(column => {
                        if (column.name.toLowerCase().includes(inputLower)) {
                            suggestions.push({
                                text: column.name,
                                type: 'column',
                                description: `Column: ${column.name} (${column.type})`
                            });
                        }
                    });
                }
            });
        }
        
        // Natural language suggestions
        const nlSuggestions = [
            'Show me all records from',
            'Count the number of',
            'Find records where',
            'Get the average of',
            'List all unique',
            'Show the top 10',
            'Find the maximum',
            'Find the minimum'
        ];
        
        nlSuggestions.forEach(suggestion => {
            if (suggestion.toLowerCase().includes(inputLower)) {
                suggestions.push({
                    text: suggestion,
                    type: 'natural_language',
                    description: 'Natural language query'
                });
            }
        });
        
        return suggestions.slice(0, 10); // Limit to 10 suggestions
    }
    
    // Query formatting and beautification
    formatSQL(query) {
        if (!query) return '';
        
        // Basic SQL formatting
        let formatted = query
            .replace(/\s+/g, ' ') // Normalize whitespace
            .replace(/,/g, ',\n    ') // Add line breaks after commas
            .replace(/\bFROM\b/gi, '\nFROM')
            .replace(/\bWHERE\b/gi, '\nWHERE')
            .replace(/\bGROUP BY\b/gi, '\nGROUP BY')
            .replace(/\bHAVING\b/gi, '\nHAVING')
            .replace(/\bORDER BY\b/gi, '\nORDER BY')
            .replace(/\bLIMIT\b/gi, '\nLIMIT')
            .replace(/\bJOIN\b/gi, '\nJOIN')
            .replace(/\bLEFT JOIN\b/gi, '\nLEFT JOIN')
            .replace(/\bRIGHT JOIN\b/gi, '\nRIGHT JOIN')
            .replace(/\bINNER JOIN\b/gi, '\nINNER JOIN')
            .replace(/\bOUTER JOIN\b/gi, '\nOUTER JOIN')
            .replace(/\bUNION\b/gi, '\nUNION')
            .replace(/\bAND\b/gi, '\n    AND')
            .replace(/\bOR\b/gi, '\n    OR');
        
        // Clean up extra whitespace
        formatted = formatted
            .split('\n')
            .map(line => line.trim())
            .filter(line => line.length > 0)
            .join('\n');
        
        return formatted;
    }
    
    // Query analysis
    analyzeQuery(query) {
        const analysis = {
            type: 'unknown',
            tables: [],
            columns: [],
            operations: [],
            complexity: 'low',
            estimatedRows: null,
            warnings: []
        };
        
        const queryUpper = query.toUpperCase();
        
        // Determine query type
        if (queryUpper.includes('SELECT')) {
            analysis.type = 'select';
        } else if (queryUpper.includes('INSERT')) {
            analysis.type = 'insert';
        } else if (queryUpper.includes('UPDATE')) {
            analysis.type = 'update';
        } else if (queryUpper.includes('DELETE')) {
            analysis.type = 'delete';
        } else if (queryUpper.includes('CREATE')) {
            analysis.type = 'create';
        } else if (queryUpper.includes('DROP')) {
            analysis.type = 'drop';
        }
        
        // Extract table names (basic regex)
        const tableMatches = query.match(/(?:FROM|JOIN|INTO|UPDATE)\s+([a-zA-Z_][a-zA-Z0-9_]*)/gi);
        if (tableMatches) {
            tableMatches.forEach(match => {
                const tableName = match.split(/\s+/)[1];
                if (tableName && !analysis.tables.includes(tableName)) {
                    analysis.tables.push(tableName);
                }
            });
        }
        
        // Detect operations
        const operations = {
            'JOIN': /\bJOIN\b/gi,
            'GROUP BY': /\bGROUP\s+BY\b/gi,
            'ORDER BY': /\bORDER\s+BY\b/gi,
            'HAVING': /\bHAVING\b/gi,
            'SUBQUERY': /\([^)]*SELECT[^)]*\)/gi,
            'AGGREGATE': /\b(COUNT|SUM|AVG|MIN|MAX)\s*\(/gi,
            'UNION': /\bUNION\b/gi
        };
        
        Object.entries(operations).forEach(([op, regex]) => {
            if (regex.test(query)) {
                analysis.operations.push(op);
            }
        });
        
        // Determine complexity
        let complexityScore = 0;
        complexityScore += analysis.tables.length;
        complexityScore += analysis.operations.length * 2;
        
        if (complexityScore <= 2) {
            analysis.complexity = 'low';
        } else if (complexityScore <= 6) {
            analysis.complexity = 'medium';
        } else {
            analysis.complexity = 'high';
        }
        
        // Add warnings
        if (queryUpper.includes('SELECT *')) {
            analysis.warnings.push('Using SELECT * may impact performance');
        }
        
        if (!queryUpper.includes('LIMIT') && analysis.type === 'select') {
            analysis.warnings.push('Consider adding LIMIT clause for large tables');
        }
        
        if (queryUpper.includes('DELETE') && !queryUpper.includes('WHERE')) {
            analysis.warnings.push('DELETE without WHERE clause will remove all records');
        }
        
        if (queryUpper.includes('UPDATE') && !queryUpper.includes('WHERE')) {
            analysis.warnings.push('UPDATE without WHERE clause will modify all records');
        }
        
        return analysis;
    }
    
    // History management
    addToHistory(entry) {
        this.queryHistory.unshift(entry);
        
        // Keep only last 50 entries
        if (this.queryHistory.length > 50) {
            this.queryHistory = this.queryHistory.slice(0, 50);
        }
        
        // Save to localStorage
        try {
            localStorage.setItem('aiQueryHistory', JSON.stringify(this.queryHistory));
        } catch (error) {
            console.error('Error saving query history:', error);
        }
    }
    
    loadHistory() {
        try {
            const saved = localStorage.getItem('aiQueryHistory');
            if (saved) {
                this.queryHistory = JSON.parse(saved);
            }
        } catch (error) {
            console.error('Error loading query history:', error);
            this.queryHistory = [];
        }
    }
    
    clearHistory() {
        this.queryHistory = [];
        try {
            localStorage.removeItem('aiQueryHistory');
        } catch (error) {
            console.error('Error clearing query history:', error);
        }
    }
    
    getHistory() {
        return this.queryHistory;
    }
    
    // Utility methods
    isProcessing() {
        return this.isProcessing;
    }
    
    getSuggestions() {
        return this.suggestions;
    }
    
    // Query templates
    getQueryTemplates() {
        return {
            basic_select: {
                name: 'Basic Select',
                template: 'SELECT * FROM {table} LIMIT 10',
                description: 'Select all columns from a table'
            },
            count_records: {
                name: 'Count Records',
                template: 'SELECT COUNT(*) FROM {table}',
                description: 'Count total number of records'
            },
            filter_records: {
                name: 'Filter Records',
                template: 'SELECT * FROM {table} WHERE {column} = "{value}"',
                description: 'Filter records by condition'
            },
            group_by: {
                name: 'Group By',
                template: 'SELECT {column}, COUNT(*) FROM {table} GROUP BY {column}',
                description: 'Group records and count'
            },
            order_by: {
                name: 'Order By',
                template: 'SELECT * FROM {table} ORDER BY {column} DESC LIMIT 10',
                description: 'Sort records by column'
            },
            join_tables: {
                name: 'Join Tables',
                template: 'SELECT * FROM {table1} JOIN {table2} ON {table1}.{key} = {table2}.{key}',
                description: 'Join two tables'
            },
            aggregate: {
                name: 'Aggregate Functions',
                template: 'SELECT AVG({column}), MIN({column}), MAX({column}) FROM {table}',
                description: 'Calculate aggregate values'
            }
        };
    }
    
    // Natural language examples
    getNaturalLanguageExamples() {
        return [
            'Show me all customers from New York',
            'Count how many orders were placed last month',
            'Find the top 10 products by sales',
            'What is the average price of products in electronics category?',
            'List all employees hired after 2020',
            'Show me customers who have never placed an order',
            'Find the most expensive product in each category',
            'What are the total sales by region?',
            'Show me all orders with a value greater than $1000',
            'List products that are out of stock'
        ];
    }
    
    // Error handling and recovery
    handleError(error, context = {}) {
        const errorInfo = {
            message: error.message || 'Unknown error',
            timestamp: new Date().toISOString(),
            context: context,
            stack: error.stack
        };
        
        console.error('AI Service Error:', errorInfo);
        
        // Store error for debugging
        try {
            const errors = JSON.parse(localStorage.getItem('aiErrors') || '[]');
            errors.unshift(errorInfo);
            
            // Keep only last 10 errors
            if (errors.length > 10) {
                errors.splice(10);
            }
            
            localStorage.setItem('aiErrors', JSON.stringify(errors));
        } catch (storageError) {
            console.error('Error storing error info:', storageError);
        }
        
        return errorInfo;
    }
    
    getErrorHistory() {
        try {
            return JSON.parse(localStorage.getItem('aiErrors') || '[]');
        } catch (error) {
            console.error('Error loading error history:', error);
            return [];
        }
    }
    
    clearErrorHistory() {
        try {
            localStorage.removeItem('aiErrors');
        } catch (error) {
            console.error('Error clearing error history:', error);
        }
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AIService;
} else {
    window.AIService = AIService;
}