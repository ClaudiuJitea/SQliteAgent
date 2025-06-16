// Database Management Module
class DatabaseManager {
    constructor() {
        this.databases = new Map();
        this.currentDatabase = null;
        this.connectionPool = new Map();
    }
    
    // Database loading and management
    async loadDatabase(file) {
        const formData = new FormData();
        formData.append('database', file);
        
        try {
            const response = await fetch('/api/databases/load', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (result.success) {
                const dbInfo = result.data;
                this.databases.set(dbInfo.database_id, dbInfo);
                return dbInfo;
            } else {
                throw new Error(result.error || 'Failed to load database');
            }
        } catch (error) {
            console.error('Database loading error:', error);
            throw error;
        }
    }
    
    async openDatabase(filePath) {
        try {
            const response = await fetch('/api/databases/load', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ file_path: filePath })
            });
            
            const result = await response.json();
            
            if (result.success) {
                const dbInfo = result.data;
                this.databases.set(dbInfo.database_id, dbInfo);
                return dbInfo;
            } else {
                throw new Error(result.error || 'Failed to open database');
            }
        } catch (error) {
            console.error('Database opening error:', error);
            throw error;
        }
    }
    
    async getDatabaseList() {
        try {
            const response = await fetch('/api/databases/');
            const result = await response.json();
            
            if (result.success) {
                // Update local database map
                this.databases.clear();
                (result.data || []).forEach(db => {
                    this.databases.set(db.database_id, db);
                });
                
                return result.data || [];
            } else {
                throw new Error(result.error || 'Failed to get database list');
            }
        } catch (error) {
            console.error('Error getting database list:', error);
            throw error;
        }
    }
    
    async getDatabaseInfo(databaseId) {
        try {
            const response = await fetch(`/api/databases/${databaseId}/info`);
            const result = await response.json();
            
            if (result.success) {
                return result.data;
            } else {
                throw new Error(result.error || 'Failed to get database info');
            }
        } catch (error) {
            console.error('Error getting database info:', error);
            throw error;
        }
    }
    
    async getDatabaseSchema(databaseId) {
        try {
            const response = await fetch(`/api/databases/${databaseId}/schema`);
            const result = await response.json();
            
            if (result.success) {
                return result.data;
            } else {
                throw new Error(result.error || 'Failed to get database schema');
            }
        } catch (error) {
            console.error('Error getting database schema:', error);
            throw error;
        }
    }
    
    /**
     * Create a new database from natural language description
     * @param {string} description - Natural language description of the database
     * @param {string} databaseName - Name for the new database
     * @returns {Promise<Object>} Response from the server
     */
    async createDatabase(description, databaseName) {
        try {
            const response = await fetch('/api/databases/create', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    description: description,
                    database_name: databaseName
                })
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Failed to create database');
            }
            
            return data;
        } catch (error) {
            console.error('Error creating database:', error);
            throw error;
        }
    }

    /**
     * Close a database connection
     * @param {string} databaseId - The database ID to close
     * @returns {Promise<Object>} Response from the server
     */
    async closeDatabase(databaseId) {
        try {
            const response = await fetch(`/api/databases/${databaseId}/close`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Failed to close database');
            }
            
            return data;
        } catch (error) {
            console.error('Error closing database:', error);
            throw error;
        }
    }
    
    // Query execution
    async executeQuery(databaseId, query) {
        try {
            const response = await fetch(`/api/databases/${databaseId}/query`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    query: query
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                return result.data;
            } else {
                throw new Error(result.error || 'Query execution failed');
            }
        } catch (error) {
            console.error('Query execution error:', error);
            throw error;
        }
    }
    
    async validateQuery(databaseId, query) {
        try {
            const response = await fetch('/api/databases/validate', {
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
                throw new Error(result.error || 'Query validation failed');
            }
        } catch (error) {
            console.error('Query validation error:', error);
            throw error;
        }
    }
    
    // Table operations
    async getTableData(databaseId, tableName, options = {}) {
        try {
            const params = new URLSearchParams();
            
            if (options.limit) params.append('limit', options.limit);
            if (options.offset) params.append('offset', options.offset);
            if (options.sortBy) params.append('sort_by', options.sortBy);
            if (options.sortOrder) params.append('sort_order', options.sortOrder);
            
            // Add filters
            if (options.filters) {
                Object.entries(options.filters).forEach(([key, value]) => {
                    params.append(`filter_${key}`, value);
                });
            }
            
            const url = `/api/tables/${databaseId}/${tableName}${params.toString() ? '?' + params.toString() : ''}`;
            const response = await fetch(url);
            const result = await response.json();
            
            if (result.success) {
                return result.data;
            } else {
                throw new Error(result.error || 'Failed to get table data');
            }
        } catch (error) {
            console.error('Error getting table data:', error);
            throw error;
        }
    }
    
    async getTableSchema(databaseId, tableName) {
        try {
            const response = await fetch(`/api/tables/${databaseId}/${tableName}/schema`);
            const result = await response.json();
            
            if (result.success) {
                return result.data;
            } else {
                throw new Error(result.error || 'Failed to get table schema');
            }
        } catch (error) {
            console.error('Error getting table schema:', error);
            throw error;
        }
    }
    
    async insertRecord(databaseId, tableName, data) {
        try {
            const response = await fetch(`/api/tables/${databaseId}/${tableName}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ data })
            });
            
            const result = await response.json();
            
            if (result.success) {
                return result.data;
            } else {
                throw new Error(result.error || 'Failed to insert record');
            }
        } catch (error) {
            console.error('Error inserting record:', error);
            throw error;
        }
    }
    
    async updateRecord(databaseId, tableName, recordId, data, idColumn = 'id') {
        try {
            const response = await fetch(`/api/tables/${databaseId}/${tableName}/${recordId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ 
                    data,
                    id_column: idColumn
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                return result.data;
            } else {
                throw new Error(result.error || 'Failed to update record');
            }
        } catch (error) {
            console.error('Error updating record:', error);
            throw error;
        }
    }
    
    async deleteRecord(databaseId, tableName, recordId, idColumn = 'id') {
        try {
            const params = new URLSearchParams();
            if (idColumn !== 'id') {
                params.append('id_column', idColumn);
            }
            
            const url = `/api/tables/${databaseId}/${tableName}/${recordId}${params.toString() ? '?' + params.toString() : ''}`;
            const response = await fetch(url, {
                method: 'DELETE'
            });
            
            const result = await response.json();
            
            if (result.success) {
                return result.data;
            } else {
                throw new Error(result.error || 'Failed to delete record');
            }
        } catch (error) {
            console.error('Error deleting record:', error);
            throw error;
        }
    }
    
    async exportTableData(databaseId, tableName, format = 'json', limit = 1000) {
        try {
            const params = new URLSearchParams({
                format: format,
                limit: limit.toString()
            });
            
            const response = await fetch(`/api/tables/${databaseId}/${tableName}/export?${params.toString()}`);
            const result = await response.json();
            
            if (result.success) {
                return result.data;
            } else {
                throw new Error(result.error || 'Failed to export table data');
            }
        } catch (error) {
            console.error('Error exporting table data:', error);
            throw error;
        }
    }
    
    // Utility methods
    getCurrentDatabase() {
        return this.currentDatabase;
    }
    
    setCurrentDatabase(databaseId) {
        if (this.databases.has(databaseId)) {
            this.currentDatabase = databaseId;
            return true;
        }
        return false;
    }
    
    getDatabaseById(databaseId) {
        return this.databases.get(databaseId);
    }
    
    getAllDatabases() {
        return Array.from(this.databases.values());
    }
    
    // Database file validation
    validateDatabaseFile(file) {
        const validExtensions = ['.db', '.sqlite', '.sqlite3'];
        const maxSize = 100 * 1024 * 1024; // 100MB
        
        // Check file extension
        const fileName = file.name.toLowerCase();
        const hasValidExtension = validExtensions.some(ext => fileName.endsWith(ext));
        
        if (!hasValidExtension) {
            throw new Error('Invalid file type. Please select a SQLite database file (.db, .sqlite, .sqlite3)');
        }
        
        // Check file size
        if (file.size > maxSize) {
            throw new Error('File size too large. Maximum size is 100MB.');
        }
        
        // Check if file is empty
        if (file.size === 0) {
            throw new Error('File is empty.');
        }
        
        return true;
    }
    
    // Connection management
    async testConnection(databaseId) {
        try {
            const info = await this.getDatabaseInfo(databaseId);
            return info !== null;
        } catch (error) {
            return false;
        }
    }
    
    // Query history management
    getQueryHistory() {
        try {
            const history = localStorage.getItem('queryHistory');
            return history ? JSON.parse(history) : [];
        } catch (error) {
            console.error('Error loading query history:', error);
            return [];
        }
    }
    
    saveQueryToHistory(query, result, type, databaseId) {
        try {
            const history = this.getQueryHistory();
            const entry = {
                id: Date.now().toString(),
                query,
                result,
                type,
                databaseId,
                timestamp: new Date().toISOString()
            };
            
            history.unshift(entry);
            
            // Keep only last 100 queries
            if (history.length > 100) {
                history.splice(100);
            }
            
            localStorage.setItem('queryHistory', JSON.stringify(history));
            return entry;
        } catch (error) {
            console.error('Error saving query to history:', error);
            return null;
        }
    }
    
    clearQueryHistory() {
        try {
            localStorage.removeItem('queryHistory');
            return true;
        } catch (error) {
            console.error('Error clearing query history:', error);
            return false;
        }
    }
    
    // Database statistics
    async getDatabaseStats(databaseId) {
        try {
            const schema = await this.getDatabaseSchema(databaseId);
            const info = await this.getDatabaseInfo(databaseId);
            
            const stats = {
                tableCount: Object.keys(schema.tables || {}).length,
                totalRows: 0,
                totalSize: info.file_size || 0,
                tables: []
            };
            
            // Calculate total rows and table stats
            Object.entries(schema.tables || {}).forEach(([tableName, tableInfo]) => {
                stats.totalRows += tableInfo.row_count || 0;
                stats.tables.push({
                    name: tableName,
                    rowCount: tableInfo.row_count || 0,
                    columnCount: tableInfo.columns ? tableInfo.columns.length : 0
                });
            });
            
            // Sort tables by row count
            stats.tables.sort((a, b) => b.rowCount - a.rowCount);
            
            return stats;
        } catch (error) {
            console.error('Error getting database stats:', error);
            throw error;
        }
    }
    
    // Backup and restore
    async createBackup(databaseId) {
        try {
            // This would typically create a backup file
            // For now, we'll just export the database info
            const info = await this.getDatabaseInfo(databaseId);
            const schema = await this.getDatabaseSchema(databaseId);
            
            const backup = {
                timestamp: new Date().toISOString(),
                database: info,
                schema: schema
            };
            
            return backup;
        } catch (error) {
            console.error('Error creating backup:', error);
            throw error;
        }
    }
    
    // Performance monitoring
    startPerformanceMonitoring(databaseId) {
        if (!this.performanceMonitors) {
            this.performanceMonitors = new Map();
        }
        
        const monitor = {
            databaseId,
            startTime: Date.now(),
            queryCount: 0,
            totalExecutionTime: 0,
            errors: 0
        };
        
        this.performanceMonitors.set(databaseId, monitor);
        return monitor;
    }
    
    recordQueryPerformance(databaseId, executionTime, success = true) {
        if (!this.performanceMonitors) return;
        
        const monitor = this.performanceMonitors.get(databaseId);
        if (monitor) {
            monitor.queryCount++;
            monitor.totalExecutionTime += executionTime;
            if (!success) {
                monitor.errors++;
            }
        }
    }
    
    getPerformanceStats(databaseId) {
        if (!this.performanceMonitors) return null;
        
        const monitor = this.performanceMonitors.get(databaseId);
        if (!monitor) return null;
        
        const duration = Date.now() - monitor.startTime;
        const avgExecutionTime = monitor.queryCount > 0 ? monitor.totalExecutionTime / monitor.queryCount : 0;
        const errorRate = monitor.queryCount > 0 ? (monitor.errors / monitor.queryCount) * 100 : 0;
        
        return {
            databaseId,
            duration,
            queryCount: monitor.queryCount,
            avgExecutionTime,
            totalExecutionTime: monitor.totalExecutionTime,
            errorRate,
            errors: monitor.errors
        };
    }
    
    stopPerformanceMonitoring(databaseId) {
        if (this.performanceMonitors) {
            this.performanceMonitors.delete(databaseId);
        }
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DatabaseManager;
} else {
    window.DatabaseManager = DatabaseManager;
}