// Main Application JavaScript
class SQLiteAIManager {
    constructor() {
        this.currentDatabase = null;
        this.currentTable = null;
        this.settings = this.loadSettings();
        this.socket = null;
        this.queryHistory = [];
        this.databaseManager = new DatabaseManager();
        
        this.init();
    }
    
    init() {
        this.initializeEventListeners();
        this.initializeWebSocket();
        this.initializeUI();
        this.loadDatabases();
    }
    
    initializeEventListeners() {
        // Header events
        document.getElementById('settingsBtn').addEventListener('click', () => {
            this.openModal('settingsModal');
            this.loadSettingsToForm();
            this.loadAvailableModels();
        });
        
        // Database events
        document.getElementById('createDatabaseBtn').addEventListener('click', () => {
            this.openCreateDatabaseModal();
        });
        
        document.getElementById('loadDatabaseBtn').addEventListener('click', () => {
            document.getElementById('databaseFileInput').click();
        });
        
        document.getElementById('databaseFileInput').addEventListener('change', (e) => {
            this.handleDatabaseUpload(e.target.files[0]);
        });
        
        // Create database modal events
        document.getElementById('createDatabaseModalClose').addEventListener('click', () => {
            this.closeModal('createDatabaseModal');
        });
        
        document.getElementById('cancelCreateDatabase').addEventListener('click', () => {
            this.closeModal('createDatabaseModal');
        });
        
        // Database info modal events
        document.getElementById('databaseInfoModalClose').addEventListener('click', () => {
            this.closeModal('databaseInfoModal');
        });
        
        // Open database button
        const openDatabaseBtn = document.getElementById('openDatabaseBtn');
        if (openDatabaseBtn) {
            openDatabaseBtn.addEventListener('click', () => {
                this.openModal('openDatabaseModal');
            });
        }
        
        // Open database modal close
        const openDatabaseModalClose = document.getElementById('openDatabaseModalClose');
        if (openDatabaseModalClose) {
            openDatabaseModalClose.addEventListener('click', () => {
                this.closeModal('openDatabaseModal');
            });
        }
        
        // Cancel open database
        const cancelOpenDatabase = document.getElementById('cancelOpenDatabase');
        if (cancelOpenDatabase) {
            cancelOpenDatabase.addEventListener('click', () => {
                this.closeModal('openDatabaseModal');
            });
        }
        
        // Open database form submission
        const openDatabaseForm = document.getElementById('openDatabaseForm');
        if (openDatabaseForm) {
            openDatabaseForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleOpenDatabase();
            });
        }
        
        // Browse database file button
        const browseDatabaseFile = document.getElementById('browseDatabaseFile');
        if (browseDatabaseFile) {
            browseDatabaseFile.addEventListener('click', () => {
                document.getElementById('databaseFileInput').click();
            });
        }
        
        // Database file input change
        const databaseFileInput = document.getElementById('databaseFileInput');
        if (databaseFileInput) {
            databaseFileInput.addEventListener('change', (e) => {
                if (e.target.files.length > 0) {
                    const file = e.target.files[0];
                    document.getElementById('databaseFilePath').value = file.path || file.name;
                }
            });
        }
        
        document.getElementById('createDatabaseForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleCreateDatabase();
        });
        
        // Tab switching
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.switchTab(e.target.dataset.tab);
            });
        });
        
        // Query execution
        document.getElementById('executeNaturalBtn').addEventListener('click', () => {
            this.executeNaturalLanguageQuery();
        });
        
        document.getElementById('executeSqlBtn').addEventListener('click', () => {
            this.executeSQLQuery();
        });
        
        // Clear buttons
        document.getElementById('clearNaturalBtn').addEventListener('click', () => {
            document.getElementById('naturalLanguageInput').value = '';
        });
        
        document.getElementById('clearSqlBtn').addEventListener('click', () => {
            document.getElementById('sqlQueryInput').value = '';
        });
        
        // Format SQL button
        document.getElementById('formatSqlBtn').addEventListener('click', () => {
            this.formatSQL();
        });
        
        // Export results
        document.getElementById('exportResultsBtn').addEventListener('click', () => {
            this.exportResults();
        });
        
        // Settings modal
        document.getElementById('saveSettingsBtn').addEventListener('click', () => {
            this.saveSettings();
        });
        
        // Modal close events
        document.querySelectorAll('.modal-close, [data-modal]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const modalId = e.target.dataset.modal || e.target.closest('.modal').id;
                this.closeModal(modalId);
            });
        });
        
        // Toast close events
        document.querySelectorAll('.toast-close').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.target.closest('.toast').classList.remove('show');
            });
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            this.handleKeyboardShortcuts(e);
        });
        
        // Click outside modal to close
        document.querySelectorAll('.modal').forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.closeModal(modal.id);
                }
            });
        });
    }
    
    initializeWebSocket() {
        try {
            // Get Socket.IO URL based on current location
            const protocol = window.location.protocol;
            const host = window.location.host;
            const url = `${protocol}//${host}`; // Don't add /socket.io/ as path is configured on server
            
            console.log('Connecting to Socket.IO server:', url);
            
            // Close any existing connection
            if (this.socket) {
                this.socket.close();
                this.socket = null;
            }
            
            // Initialize Socket.IO with compatible configuration
            this.socket = io(url, {
                transports: ['polling', 'websocket'],  // Try polling first to avoid frame header issues
                reconnection: true,
                reconnectionAttempts: 10,
                reconnectionDelay: 1000,
                timeout: 60000,  // Change from 5000 to 60000 (60 seconds)
                autoConnect: true
            });
            
            // Setup event handlers with proper error handling
            this.socket.on('connect', () => {
                console.log('Connected to server');
                this.updateConnectionStatus('connected');
            });
            
            this.socket.on('connect_error', (error) => {
                console.error('Connection error:', error);
                this.updateConnectionStatus('error');
                this.showToast('Connection error. Please check your network.', 'error');
            });
            
            this.socket.on('disconnect', (reason) => {
                console.log('Disconnected from server:', reason);
                this.updateConnectionStatus('disconnected');
            });
            
            this.socket.on('reconnect_attempt', (attemptNumber) => {
                console.log(`Attempting to reconnect: ${attemptNumber}`);
            });
            
            this.socket.on('reconnect_failed', () => {
                console.error('Failed to reconnect');
                this.updateConnectionStatus('error');
                this.showToast('Failed to reconnect to server. Please refresh the page.', 'error');
            });
            
            this.socket.on('message', (data) => {
                this.handleWebSocketMessage(data);
            });
            
        } catch (error) {
            console.error('Failed to initialize WebSocket:', error);
            this.updateConnectionStatus('error');
        }
    }
    
    initializeUI() {
        // Set initial tab
        this.switchTab('natural');
        
        // Load settings into form
        this.loadSettingsToForm();
        
        // Initialize tooltips or other UI components if needed
        this.initializeTooltips();
    }
    
    initializeTooltips() {
        // Add tooltip functionality if needed
        // This is a placeholder for future tooltip implementation
    }
    
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    handleKeyboardShortcuts(e) {
        // Ctrl/Cmd + Enter to execute query
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            const activeTab = document.querySelector('.tab-content.active');
            if (activeTab.id === 'naturalTab') {
                this.executeNaturalLanguageQuery();
            } else {
                this.executeSQLQuery();
            }
        }
        
        // Escape to close modals
        if (e.key === 'Escape') {
            const activeModal = document.querySelector('.modal.active');
            if (activeModal) {
                this.closeModal(activeModal.id);
            }
        }
    }
    
    switchTab(tabName) {
        // Remove active class from all tabs and content
        document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
        
        // Add active class to selected tab and content
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
        document.getElementById(`${tabName}Tab`).classList.add('active');
    }
    
    async handleDatabaseUpload(file) {
        if (!file) return;
        
        // Validate file type
        const validExtensions = ['.db', '.sqlite', '.sqlite3'];
        const fileExtension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));
        
        if (!validExtensions.includes(fileExtension)) {
            this.showToast('Please select a valid SQLite database file (.db, .sqlite, .sqlite3)', 'error');
            return;
        }
        
        // Check file size (max 100MB)
        const maxSize = 100 * 1024 * 1024; // 100MB
        if (file.size > maxSize) {
            this.showToast('File size too large. Maximum size is 100MB.', 'error');
            return;
        }
        
        this.showLoading('Uploading database...');
        
        try {
            const formData = new FormData();
            formData.append('database', file);
            
            const response = await fetch('/api/databases/load', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showToast('Database loaded successfully!', 'success');
                await this.loadDatabases();
                
                // Auto-select the newly loaded database
                if (result.data && result.data.database_info && result.data.database_info.id) {
                    this.selectDatabase(result.data.database_info.id);
                }
            } else {
                this.showToast(result.error || 'Failed to load database', 'error');
            }
        } catch (error) {
            console.error('Database upload error:', error);
            this.showToast('Failed to upload database. Please try again.', 'error');
        } finally {
            this.hideLoading();
            // Clear the file input
            document.getElementById('databaseFileInput').value = '';
        }
    }
    
    openCreateDatabaseModal() {
        // Clear form
        document.getElementById('databaseName').value = '';
        document.getElementById('databaseDescription').value = '';
        
        // Open modal
        this.openModal('createDatabaseModal');
    }
    
    async handleCreateDatabase() {
        const databaseName = document.getElementById('databaseName').value.trim();
        const description = document.getElementById('databaseDescription').value.trim();
        
        if (!databaseName) {
            this.showToast('Please enter a database name', 'error');
            return;
        }
        
        if (!description) {
            this.showToast('Please enter a description for your database', 'error');
            return;
        }
        
        // Validate database name (basic validation)
        const nameRegex = /^[a-zA-Z0-9_-]+$/;
        if (!nameRegex.test(databaseName)) {
            this.showToast('Database name can only contain letters, numbers, underscores, and hyphens', 'error');
            return;
        }
        
        // Close modal immediately to show loading spinner
        this.closeModal('createDatabaseModal');
        this.showLoading('Creating database with AI...', 'database-creation');
        
        try {
            const response = await fetch('/api/databases/create', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    database_name: databaseName,
                    description: description
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showToast('Database created successfully!', 'success');
                await this.loadDatabases();
                
                // Auto-select the newly created database
                if (result.data && result.data.database_info && result.data.database_info.id) {
                    this.selectDatabase(result.data.database_info.id);
                }
            } else {
                this.showToast(result.error || 'Failed to create database', 'error');
            }
        } catch (error) {
            console.error('Database creation error:', error);
            this.showToast('Failed to create database. Please try again.', 'error');
        } finally {
            this.hideLoading();
        }
    }
    
    async loadDatabases() {
        try {
            const response = await fetch('/api/databases/');
            const result = await response.json();
            
            if (result.success) {
                this.renderDatabaseList(result.data || []);
            } else {
                console.error('Failed to load databases:', result.error);
            }
        } catch (error) {
            console.error('Error loading databases:', error);
        }
    }
    
    renderDatabaseList(databases) {
        const container = document.getElementById('databaseList');
        
        if (databases.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-database"></i>
                    <p>No databases loaded</p>
                    <small>Click "Open Database" to get started</small>
                </div>
            `;
            return;
        }
        
        container.innerHTML = databases.map(db => {
            // Extract database name from path
            const dbName = db.path ? db.path.split(/[\\/]/).pop().replace(/\.[^/.]+$/, '') : db.id;
            const dbPath = db.path || 'Unknown path';
            
            return `
                <div class="database-item" data-database-id="${db.id}">
                    <div class="database-info">
                        <div class="database-name">${dbName}</div>
                        <div class="database-path">${dbPath}</div>
                        <div class="database-meta">${db.tables ? db.tables.length : 0} tables • ${this.formatFileSize(db.size || 0)}</div>
                    </div>
                    <div class="database-actions">
                        <button class="action-btn" onclick="app.viewDatabaseInfo('${db.id}')" title="View Info">
                            <i class="fas fa-info-circle"></i>
                        </button>
                        <button class="action-btn" onclick="app.closeDatabase('${db.id}')" title="Close">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                </div>
            `;
        }).join('');
        
        // Add click events to database items
        container.querySelectorAll('.database-item').forEach(item => {
            item.addEventListener('click', (e) => {
                if (!e.target.closest('.database-actions')) {
                    this.selectDatabase(item.dataset.databaseId);
                }
            });
        });
    }
    
    async selectDatabase(databaseId) {
        // Update UI
        document.querySelectorAll('.database-item').forEach(item => {
            item.classList.remove('active');
        });
        
        const selectedItem = document.querySelector(`[data-database-id="${databaseId}"]`);
        if (selectedItem) {
            selectedItem.classList.add('active');
        }
        
        this.currentDatabase = databaseId;
        
        // Join database room for real-time updates
        if (this.socket) {
            this.socket.emit('join_database', { database_id: databaseId });
        }
        
        // Load tables
        await this.loadTables(databaseId);
    }
    
    async loadTables(databaseId) {
        try {
            const response = await fetch(`/api/databases/${databaseId}/schema`);
            const result = await response.json();
            
            if (result.success) {
                this.renderTableList(result.data.tables || {});
            } else {
                console.error('Failed to load tables:', result.error);
                this.renderTableList({});
            }
        } catch (error) {
            console.error('Error loading tables:', error);
            this.renderTableList({});
        }
    }
    
    renderTableList(tables) {
        const container = document.getElementById('tableList');
        const tableNames = Object.keys(tables);
        
        if (tableNames.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-table"></i>
                    <p>No tables found</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = tableNames.map(tableName => {
            const table = tables[tableName];
            return `
                <div class="table-item" data-table-name="${tableName}">
                    <div class="table-info">
                        <div class="table-name">${tableName}</div>
                        <div class="table-details">${table.row_count} rows, ${table.columns.length} columns</div>
                    </div>
                    <div class="table-actions">
                        <button class="action-btn" onclick="app.viewTableDetails('${tableName}')" title="View Details">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button class="action-btn" onclick="app.queryTable('${tableName}')" title="Query Table">
                            <i class="fas fa-search"></i>
                        </button>
                    </div>
                </div>
            `;
        }).join('');
        
        // Add click events to table items
        container.querySelectorAll('.table-item').forEach(item => {
            item.addEventListener('click', (e) => {
                if (!e.target.closest('.table-actions')) {
                    this.selectTable(item.dataset.tableName);
                }
            });
        });
    }
    
    selectTable(tableName) {
        // Update UI
        document.querySelectorAll('.table-item').forEach(item => {
            item.classList.remove('active');
        });
        
        const selectedItem = document.querySelector(`[data-table-name="${tableName}"]`);
        if (selectedItem) {
            selectedItem.classList.add('active');
        }
        
        this.currentTable = tableName;
    }
    
    async executeNaturalLanguageQuery() {
        const query = document.getElementById('naturalLanguageInput').value.trim();
        
        if (!query) {
            this.showToast('Please enter a question', 'error');
            return;
        }
        
        if (!this.currentDatabase) {
            this.showToast('Please select a database first', 'error');
            console.log('No database selected. Current database:', this.currentDatabase);
            return;
        }
        
        console.log('Executing natural language query with database:', this.currentDatabase);
        
        this.showLoading('Processing your question...');
        
        try {
            const response = await fetch('/api/ai/query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    database_id: this.currentDatabase,
                    prompt: query,
                    include_explanation: true,
                    model: this.settings.model
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.displayQueryResult(result.data, 'natural');
                this.addToHistory(query, result.data, 'natural');
            } else {
                console.error('Server returned error:', result);
                this.showToast(result.error || 'Failed to process query', 'error');
            }
        } catch (error) {
            console.error('Natural language query error:', error);
            if (error.response) {
                console.error('Response status:', error.response.status);
                console.error('Response data:', error.response.data);
            }
            this.showToast('Failed to process query. Please try again.', 'error');
        } finally {
            this.hideLoading();
        }
    }
    
    async executeSQLQuery() {
        const query = document.getElementById('sqlQueryInput').value.trim();
        
        if (!query) {
            this.showToast('Please enter a SQL query', 'error');
            return;
        }
        
        if (!this.currentDatabase) {
            this.showToast('Please select a database first', 'error');
            console.log('No database selected. Current database:', this.currentDatabase);
            return;
        }
        
        console.log('Executing natural language query with database:', this.currentDatabase);
        
        this.showLoading('Executing query...');
        
        try {
            const response = await fetch(`/api/databases/${this.currentDatabase}/query`, {
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
                this.displayQueryResult(result.data, 'sql');
                this.addToHistory(query, result.data, 'sql');
            } else {
                this.showToast(result.error || 'Query execution failed', 'error');
            }
        } catch (error) {
            console.error('SQL query error:', error);
            this.showToast('Failed to execute query. Please try again.', 'error');
        } finally {
            this.hideLoading();
        }
    }
    
    displayQueryResult(data, type) {
        const container = document.getElementById('resultsContent');
        const exportBtn = document.getElementById('exportResultsBtn');
        
        let html = '';
        
        if (type === 'natural' && data.explanation) {
            html += `
                <div class="ai-explanation">
                    <h4><i class="fas fa-robot"></i> AI Explanation</h4>
                    <p>${data.explanation}</p>
                </div>
            `;
        }
        
        if (data.sql_query) {
            html += `
                <div class="query-info">
                    <div class="query-text">${data.sql_query}</div>
                    <div class="query-meta">
                        <span>Execution time: ${data.query_result?.execution_time || 'N/A'}</span>
                        <span>Rows: ${data.query_result?.row_count || 0}</span>
                    </div>
                </div>
            `;
        }
        
        // For AI responses, data is nested under query_result
        const tableData = type === 'natural' ? data.query_result?.data : data.data;
        const tableColumns = type === 'natural' ? data.query_result?.columns : data.columns;
        
        if (tableData && tableData.length > 0) {
            html += this.createResultsTable(tableData, tableColumns);
            exportBtn.style.display = 'block';
            this.lastResults = type === 'natural' ? data.query_result : data;
        } else {
            html += `
                <div class="empty-state">
                    <i class="fas fa-search"></i>
                    <p>No results found</p>
                </div>
            `;
            exportBtn.style.display = 'none';
        }
        
        container.innerHTML = html;
        
        // Handle scroll navigation buttons
        this.setupScrollNavigation();
    }
    
    createResultsTable(data, columns) {
        if (!data || data.length === 0) return '';
        
        const headers = columns || Object.keys(data[0]);
        
        return `
            <div class="query-result">
                <div class="table-wrapper">
                    <table class="results-table">
                        <thead>
                            <tr>
                                ${headers.map(col => `<th title="${this.escapeHtml(col)}">${this.escapeHtml(col)}</th>`).join('')}
                            </tr>
                        </thead>
                        <tbody>
                            ${data.map(row => `
                                <tr>
                                    ${headers.map(col => {
                                        const cellValue = this.formatCellValue(row[col]);
                                        const rawValue = row[col];
                                        const tooltip = rawValue !== null && rawValue !== undefined ? this.escapeHtml(String(rawValue)) : 'NULL';
                                        return `<td title="${tooltip}">${cellValue}</td>`;
                                    }).join('')}
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    }
    
    formatCellValue(value) {
        if (value === null || value === undefined) {
            return '<em class="null-value">NULL</em>';
        }
        
        const stringValue = String(value);
        
        // Truncate long values for display
        if (stringValue.length > 50) {
            return this.escapeHtml(stringValue.substring(0, 50)) + '<span class="truncated">...</span>';
        }
        
        return this.escapeHtml(stringValue);
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    addToHistory(query, result, type) {
        this.queryHistory.unshift({
            query,
            result,
            type,
            timestamp: new Date().toISOString(),
            database: this.currentDatabase
        });
        
        // Keep only last 50 queries
        if (this.queryHistory.length > 50) {
            this.queryHistory = this.queryHistory.slice(0, 50);
        }
        
        // Save to localStorage
        localStorage.setItem('queryHistory', JSON.stringify(this.queryHistory));
    }
    
    formatSQL() {
        const textarea = document.getElementById('sqlQueryInput');
        const sql = textarea.value.trim();
        
        if (!sql) {
            this.showToast('No SQL to format', 'error');
            return;
        }
        
        // Basic SQL formatting
        const formatted = sql
            .replace(/\s+/g, ' ')
            .replace(/\s*,\s*/g, ',\n    ')
            .replace(/\s+(FROM|WHERE|GROUP BY|ORDER BY|HAVING|LIMIT)\s+/gi, '\n$1 ')
            .replace(/\s+(INNER|LEFT|RIGHT|FULL)\s+JOIN\s+/gi, '\n$1 JOIN ')
            .replace(/\s+(AND|OR)\s+/gi, '\n    $1 ')
            .trim();
        
        textarea.value = formatted;
    }
    
    setupScrollNavigation() {
        const scrollUpBtn = document.getElementById('scrollUpBtn');
        const scrollDownBtn = document.getElementById('scrollDownBtn');
        const tableWrapper = document.querySelector('.table-wrapper'); // This might be null if no results yet
        
        if (!scrollUpBtn || !scrollDownBtn) {
            console.log('Scroll buttons not found in DOM');
            return;
        }

        // Function to forcefully enable buttons
        const enableButtons = () => {
            if (scrollUpBtn) {
                scrollUpBtn.style.display = 'flex';
                scrollUpBtn.disabled = false;
                scrollUpBtn.removeAttribute('disabled');
                scrollUpBtn.classList.remove('disabled');
                scrollUpBtn.style.pointerEvents = 'auto'; // Ensure pointer events are on
                scrollUpBtn.style.cursor = 'pointer'; // Ensure cursor is pointer
                scrollUpBtn.style.opacity = '1'; // Ensure full opacity
            }
            if (scrollDownBtn) {
                scrollDownBtn.style.display = 'flex';
                scrollDownBtn.disabled = false;
                scrollDownBtn.removeAttribute('disabled');
                scrollDownBtn.classList.remove('disabled');
                scrollDownBtn.style.pointerEvents = 'auto'; // Ensure pointer events are on
                scrollDownBtn.style.cursor = 'pointer'; // Ensure cursor is pointer
                scrollDownBtn.style.opacity = '1'; // Ensure full opacity
            }
            console.log('Scroll buttons forcefully enabled and shown');
        };

        // Function to disable/hide buttons
        const disableButtons = () => {
            if (scrollUpBtn) {
                scrollUpBtn.style.display = 'none';
                // scrollUpBtn.disabled = true; // We don't want to disable, just hide
            }
            if (scrollDownBtn) {
                scrollDownBtn.style.display = 'none';
                // scrollDownBtn.disabled = true; // We don't want to disable, just hide
            }
            console.log('Scroll buttons hidden');
        };
        
        // Show/hide and enable/disable scroll buttons based on content
        const checkScrollable = () => {
            const hasResults = document.querySelector('.results-table');
            console.log('Checking scrollable - hasResults:', !!hasResults);
            
            if (hasResults) {
                enableButtons();
                // Update button states based on current scroll position immediately after enabling
                // Ensure the scroll container is available before calling
                setTimeout(() => {
                    const container = getScrollableContainer();
                    if (container) updateScrollButtonStates(container);
                }, 50); // Short delay to ensure DOM updates
                
            } else {
                disableButtons();
            }
        };
        
        // Update button states based on scroll position
        const updateScrollButtonStates = (scrollContainer) => {
            if (!scrollContainer) return; // Exit if no valid scroll container

            // First, ensure buttons are enabled (redundant if checkScrollable worked, but safe)
            enableButtons(); 

            const scrollTop = scrollContainer.scrollTop;
            const scrollHeight = scrollContainer.scrollHeight;
            const clientHeight = scrollContainer.clientHeight;
            
            // Keep buttons always enabled and visible - just update opacity for visual feedback
            if (scrollUpBtn) {
                // Always keep enabled, just adjust opacity slightly for visual feedback
                scrollUpBtn.disabled = false;
                scrollUpBtn.removeAttribute('disabled');
                scrollUpBtn.classList.remove('disabled');
                if (scrollTop <= 5) {
                    scrollUpBtn.style.opacity = '0.7'; // Slightly dimmed but still clearly visible
                } else {
                    scrollUpBtn.style.opacity = '1';
                }
            }
            
            if (scrollDownBtn) {
                // Always keep enabled, just adjust opacity slightly for visual feedback
                scrollDownBtn.disabled = false;
                scrollDownBtn.removeAttribute('disabled');
                scrollDownBtn.classList.remove('disabled');
                if (scrollTop >= scrollHeight - clientHeight - 5) {
                    scrollDownBtn.style.opacity = '0.7'; // Slightly dimmed but still clearly visible
                } else {
                    scrollDownBtn.style.opacity = '1';
                }
            }
        };

        // Helper function to get the current scrollable container
        const getScrollableContainer = () => {
            const dynamicTableWrapper = document.querySelector('.query-result .table-wrapper');
            const resultsContent = document.getElementById('resultsContent'); // Main content area for results
            const queryResultDiv = document.querySelector('.query-result'); // The direct parent of table-wrapper

            console.log('Checking containers:');
            console.log('dynamicTableWrapper:', dynamicTableWrapper, dynamicTableWrapper ? `scrollHeight: ${dynamicTableWrapper.scrollHeight}, clientHeight: ${dynamicTableWrapper.clientHeight}` : 'null');
            console.log('queryResultDiv:', queryResultDiv, queryResultDiv ? `scrollHeight: ${queryResultDiv.scrollHeight}, clientHeight: ${queryResultDiv.clientHeight}` : 'null');
            console.log('resultsContent:', resultsContent, resultsContent ? `scrollHeight: ${resultsContent.scrollHeight}, clientHeight: ${resultsContent.clientHeight}` : 'null');

            // Prioritize the most specific scrollable container, but be less strict about scrollable condition
            if (dynamicTableWrapper) {
                console.log('Using dynamicTableWrapper');
                return dynamicTableWrapper;
            }
            if (queryResultDiv) {
                console.log('Using queryResultDiv');
                return queryResultDiv;
            }
            if (resultsContent) {
                console.log('Using resultsContent');
                return resultsContent;
            }
            // Fallback to the initial tableWrapper if nothing else is found (though less likely to be the one)
            if (tableWrapper) {
                console.log('Using tableWrapper fallback');
                return tableWrapper;
            }
            console.log('No container found');
            return null;
        };
        
        // Check initially with multiple attempts to ensure DOM is ready
        const attemptCheck = (attempts = 0) => {
            const maxAttempts = 10;
            // Check if resultsContent exists and has children, or if results-table exists
            const resultsContentEl = document.getElementById('resultsContent');
            const hasContent = resultsContentEl && (resultsContentEl.querySelector('.results-table') || resultsContentEl.children.length > 0);
            
            if (hasContent || attempts >= maxAttempts) {
                checkScrollable();
            } else {
                setTimeout(() => attemptCheck(attempts + 1), 100); // Increased delay slightly
            }
        };
        
        // Start checking immediately and also after a delay
        attemptCheck();
        // setTimeout(checkScrollable, 200); // attemptCheck should cover this
        
        // Check on resize
        window.addEventListener('resize', () => {
            checkScrollable(); // Re-check scrollability
            const container = getScrollableContainer();
            if (container) updateScrollButtonStates(container); // Then update opacity
        });
        
        // Scroll to top
        scrollUpBtn.addEventListener('click', () => {
            console.log('Scroll up button clicked');
            const container = getScrollableContainer();
            console.log('Found container for scroll up:', container);
            
            if (container) {
                container.scrollTo({
                    top: 0,
                    behavior: 'smooth'
                });
                console.log('Scrolled to top');
            } else {
                // Fallback: try to scroll the main results content or window
                const resultsContent = document.getElementById('resultsContent');
                if (resultsContent) {
                    resultsContent.scrollTo({ top: 0, behavior: 'smooth' });
                    console.log('Fallback: Scrolled results content to top');
                } else {
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                    console.log('Fallback: Scrolled window to top');
                }
            }
        });
        
        // Scroll to bottom
        scrollDownBtn.addEventListener('click', () => {
            console.log('Scroll down button clicked');
            const container = getScrollableContainer();
            console.log('Found container for scroll down:', container);
            
            if (container) {
                container.scrollTo({
                    top: container.scrollHeight,
                    behavior: 'smooth'
                });
                console.log('Scrolled to bottom');
            } else {
                // Fallback: try to scroll the main results content or window
                const resultsContent = document.getElementById('resultsContent');
                if (resultsContent) {
                    resultsContent.scrollTo({ top: resultsContent.scrollHeight, behavior: 'smooth' });
                    console.log('Fallback: Scrolled results content to bottom');
                } else {
                    window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
                    console.log('Fallback: Scrolled window to bottom');
                }
            }
        });
        
        // Update button states on scroll - add listeners to all potential containers
        const addScrollListeners = () => {
            const container = getScrollableContainer();
            if (container) {
                // Remove existing listener to avoid duplicates if this is called multiple times
                container.removeEventListener('scroll', () => updateScrollButtonStates(container)); 
                container.addEventListener('scroll', () => updateScrollButtonStates(container));
            } else {
                // If no specific container, try adding to resultsContent as a fallback
                const resultsContentEl = document.getElementById('resultsContent');
                if (resultsContentEl) {
                    resultsContentEl.removeEventListener('scroll', () => updateScrollButtonStates(resultsContentEl));
                    resultsContentEl.addEventListener('scroll', () => updateScrollButtonStates(resultsContentEl));
                }
            }
        };
        
        // Initial setup
        addScrollListeners();
        
        // Re-add listeners and check scrollability when new content is added
        const observer = new MutationObserver((mutationsList, observerInstance) => {
            // We only care if child nodes were added/removed or subtree changed significantly
            for (const mutation of mutationsList) {
                if (mutation.type === 'childList' || mutation.type === 'subtree') {
                    console.log('Mutation observed, re-checking scroll and listeners.');
                    checkScrollable(); // This will enable/disable buttons and call updateScrollButtonStates
                    addScrollListeners(); // Re-attach scroll listeners to the potentially new/changed container
                    break; // No need to check other mutations if one relevant is found
                }
            }
        });
        
        // Observe changes to results content
        const resultsContentEl = document.getElementById('resultsContent');
        if (resultsContentEl) {
            observer.observe(resultsContentEl, { childList: true, subtree: true });
        }
    }
    
    async exportResults() {
        if (!this.lastResults) {
            this.showToast('No results to export', 'error');
            return;
        }
        
        try {
            const csv = this.convertToCSV(this.lastResults.data, this.lastResults.columns);
            
            const blob = new Blob([csv], { type: 'text/csv' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `query_results_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.csv`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            
            this.showToast('Results exported successfully!', 'success');
        } catch (error) {
            console.error('Export error:', error);
            this.showToast('Failed to export results', 'error');
        }
    }
    
    convertToCSV(data, columns) {
        const headers = columns || Object.keys(data[0]);
        const csvContent = [
            headers.join(','),
            ...data.map(row => 
                headers.map(col => {
                    const value = row[col];
                    if (value === null || value === undefined) return '';
                    const stringValue = String(value);
                    // Escape quotes and wrap in quotes if contains comma or quote
                    if (stringValue.includes(',') || stringValue.includes('"') || stringValue.includes('\n')) {
                        return '"' + stringValue.replace(/"/g, '""') + '"';
                    }
                    return stringValue;
                }).join(',')
            )
        ].join('\n');
        
        return csvContent;
    }
    
    // Modal functions
    openModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('active');
            document.body.style.overflow = 'hidden';
        }
    }
    
    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('active');
            document.body.style.overflow = '';
        }
    }
    
    // Settings functions
    loadSettings() {
        const defaultSettings = {
            apiKey: '',
            model: 'google/gemini-2.5-flash-preview-05-20',
            maxRows: 100
        };
        
        try {
            const saved = localStorage.getItem('sqliteAISettings');
            return saved ? { ...defaultSettings, ...JSON.parse(saved) } : defaultSettings;
        } catch (error) {
            console.error('Error loading settings:', error);
            return defaultSettings;
        }
    }
    
    loadSettingsToForm() {
        document.getElementById('apiKeyInput').value = this.settings.apiKey || '';
        document.getElementById('modelSelect').value = this.settings.model || 'google/gemini-2.5-flash-preview-05-20';
        document.getElementById('maxRowsInput').value = this.settings.maxRows || 100;
    }
    
    async loadAvailableModels() {
        const modelSelect = document.getElementById('modelSelect');
        const currentValue = modelSelect.value;
        
        try {
            const response = await fetch('/api/ai/models');
            const data = await response.json();
            
            if (data.success && data.models) {
                // Clear existing options
                modelSelect.innerHTML = '';
                
                // Add models from API
                data.models.forEach(model => {
                    const option = document.createElement('option');
                    option.value = model.id;
                    option.textContent = model.name;
                    if (model.description) {
                        option.title = model.description;
                    }
                    modelSelect.appendChild(option);
                });
                
                // Restore previous selection if it exists in the new list
                if (currentValue) {
                    const optionExists = Array.from(modelSelect.options).some(option => option.value === currentValue);
                    if (optionExists) {
                        modelSelect.value = currentValue;
                    } else {
                        // If previous model doesn't exist, select the first available model
                        if (modelSelect.options.length > 0) {
                            modelSelect.value = modelSelect.options[0].value;
                        }
                    }
                }
            } else {
                // Fallback to hardcoded option if API fails
                this.addFallbackModelOption(modelSelect, currentValue);
            }
        } catch (error) {
            console.error('Error loading models:', error);
            // Fallback to hardcoded option if API fails
            this.addFallbackModelOption(modelSelect, currentValue);
        }
    }
    
    addFallbackModelOption(modelSelect, currentValue) {
        modelSelect.innerHTML = '';
        const fallbackOption = document.createElement('option');
        fallbackOption.value = 'google/gemini-2.5-flash-preview-05-20';
        fallbackOption.textContent = 'Gemini 2.5 Flash Preview';
        modelSelect.appendChild(fallbackOption);
        
        if (currentValue === 'google/gemini-2.5-flash-preview-05-20') {
            modelSelect.value = currentValue;
        }
    }
    
    saveSettings() {
        const newSettings = {
            apiKey: document.getElementById('apiKeyInput').value.trim(),
            model: document.getElementById('modelSelect').value,
            maxRows: parseInt(document.getElementById('maxRowsInput').value) || 100
        };
        
        this.settings = { ...this.settings, ...newSettings };
        localStorage.setItem('sqliteAISettings', JSON.stringify(this.settings));
        
        this.closeModal('settingsModal');
        this.showToast('Settings saved successfully!', 'success');
    }
    
    // UI utility functions
    showLoading(message = 'Loading...', type = 'default') {
        const overlay = document.getElementById('loadingOverlay');
        const text = overlay.querySelector('.loading-text');
        text.textContent = message;
        
        // Remove any existing type classes
        overlay.classList.remove('database-creation');
        
        // Add specific type class if provided
        if (type === 'database-creation') {
            overlay.classList.add('database-creation');
        }
        
        overlay.style.display = 'flex';
    }
    
    hideLoading() {
        const overlay = document.getElementById('loadingOverlay');
        overlay.style.display = 'none';
        // Clean up classes
        overlay.classList.remove('database-creation');
    }
    
    showToast(message, type = 'info') {
        const toastId = type === 'error' ? 'errorToast' : 'successToast';
        const toast = document.getElementById(toastId);
        const messageEl = toast.querySelector('.toast-message');
        
        messageEl.textContent = message;
        toast.classList.add('show');
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            toast.classList.remove('show');
        }, 5000);
    }
    
    showError(message) {
        this.showToast(message, 'error');
    }
    
    showSuccess(message) {
        this.showToast(message, 'success');
    }
    
    updateConnectionStatus(status) {
        const statusEl = document.getElementById('connectionStatus');
        const indicator = document.getElementById('status-indicator');
        const text = document.getElementById('status-text');
        
        if (!statusEl || !indicator || !text) {
            console.warn('Connection status elements not found');
            return;
        }
        
        // Remove all status classes
        indicator.classList.remove('connected', 'connecting', 'error', 'disconnected');
        indicator.classList.add(status);
        
        switch (status) {
            case 'connected':
                text.textContent = 'Connected';
                break;
            case 'connecting':
                text.textContent = 'Connecting...';
                break;
            case 'disconnected':
                text.textContent = 'Disconnected';
                break;
            case 'error':
                text.textContent = 'Connection Error';
                break;
            default:
                text.textContent = 'Unknown Status';
                break;
        }
    }
    
    handleWebSocketMessage(data) {
        console.log('WebSocket message:', data);
        
        switch (data.type) {
            case 'connection':
                // Handle connection confirmation
                console.log('Connection confirmed:', data.data);
                break;
            case 'query_result':
                // Handle real-time query results if needed
                break;
            case 'database_update':
                // Handle database updates
                this.loadDatabases();
                break;
            case 'error':
                this.showToast(data.data.error, 'error');
                break;
            case 'nl_query_result':
                // Handle natural language query results
                console.log('Natural language query result:', data.data);
                break;
            case 'nl_query_error':
                // Handle natural language query errors
                this.showToast(data.data.error, 'error');
                break;
            case 'nl_processing_started':
                // Handle processing started notification
                console.log('Natural language processing started:', data.data);
                break;
            case 'room_joined':
                // Handle room joined confirmation
                console.log('Joined database room:', data.data);
                break;
            default:
                console.log('Unhandled message type:', data.type);
        }
    }
    
    // Database management functions
    async viewDatabaseInfo(databaseId) {
        try {
            const response = await fetch(`/api/databases/${databaseId}/info`);
            const result = await response.json();
            
            if (result.success) {
                const info = result.data;
                this.showDatabaseInfoModal(info);
            } else {
                this.showToast('Failed to load database information', 'error');
            }
        } catch (error) {
            console.error('Error getting database info:', error);
            this.showToast('Error loading database information', 'error');
        }
    }
    
    showDatabaseInfoModal(info) {
        const content = document.getElementById('databaseInfoContent');
        content.innerHTML = `
            <div class="database-info-details">
                <div class="info-section">
                    <h4><i class="fas fa-database"></i> Database Details</h4>
                    <div class="info-grid">
                        <div class="info-item">
                            <label>Name:</label>
                            <span>${info.name || 'Unknown'}</span>
                        </div>
                        <div class="info-item">
                            <label>File Path:</label>
                            <span class="file-path" title="${info.path || 'Unknown'}">${info.path || 'Unknown'}</span>
                        </div>
                        <div class="info-item">
                            <label>File Size:</label>
                            <span>${this.formatFileSize(info.size || 0)}</span>
                        </div>
                        <div class="info-item">
                            <label>Tables:</label>
                            <span>${info.table_count || 0}</span>
                        </div>
                        <div class="info-item">
                            <label>Last Accessed:</label>
                            <span>${info.last_accessed ? new Date(info.last_accessed).toLocaleString() : 'Never'}</span>
                        </div>
                        <div class="info-item">
                            <label>Status:</label>
                            <span class="status-badge status-${info.status || 'unknown'}">${info.status || 'Unknown'}</span>
                        </div>
                    </div>
                </div>
                ${info.tables && info.tables.length > 0 ? `
                <div class="info-section">
                    <h4><i class="fas fa-table"></i> Tables (${info.tables.length})</h4>
                    <div class="tables-list">
                        ${info.tables.map(table => `
                            <div class="table-info-item">
                                <div class="table-name">
                                    <i class="fas fa-table"></i>
                                    ${typeof table === 'string' ? table : table.name || 'Unknown'}
                                </div>
                                <div class="table-details">
                                    ${typeof table === 'string' ? 'Table information available' : `${table.row_count || 0} rows • ${table.column_count || 0} columns`}
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
                ` : ''}
            </div>
        `;
        this.openModal('databaseInfoModal');
    }
    
    async closeDatabase(databaseId) {
        if (confirm('Are you sure you want to close this database?')) {
            try {
                const response = await fetch(`/api/databases/${databaseId}/close`, {
                    method: 'POST'
                });
                
                const result = await response.json();
                
                if (result.success) {
                    this.showToast('Database closed successfully', 'success');
                    await this.loadDatabases();
                    
                    // Clear current selection if it was the closed database
                    if (this.currentDatabase === databaseId) {
                        this.currentDatabase = null;
                        this.currentTable = null;
                        this.renderTableList({});
                    }
                } else {
                    this.showToast(result.error || 'Failed to close database', 'error');
                }
            } catch (error) {
                console.error('Error closing database:', error);
                this.showToast('Failed to close database', 'error');
            }
        }
    }
    
    async viewTableDetails(tableName) {
        if (!this.currentDatabase) {
            this.showToast('Please select a database first', 'error');
            console.log('No database selected. Current database:', this.currentDatabase);
            return;
        }
        
        console.log('Executing natural language query with database:', this.currentDatabase);
        
        try {
            const response = await fetch(`/api/tables/${this.currentDatabase}/${tableName}/schema`);
            const result = await response.json();
            
            if (result.success) {
                this.showTableDetailsModal(result.data);
            } else {
                this.showToast(result.error || 'Failed to load table details', 'error');
            }
        } catch (error) {
            console.error('Error loading table details:', error);
            this.showToast('Failed to load table details', 'error');
        }
    }
    
    showTableDetailsModal(tableData) {
        const modal = document.getElementById('tableDetailsModal');
        const title = document.getElementById('tableDetailsTitle');
        const content = document.getElementById('tableDetailsContent');
        
        title.textContent = `Table: ${tableData.table_name}`;
        
        const html = `
            <div class="table-schema">
                <h4>Schema Information</h4>
                <p><strong>Rows:</strong> ${tableData.row_count}</p>
                <p><strong>Columns:</strong> ${tableData.columns.length}</p>
                
                <h4>Columns</h4>
                <table class="results-table">
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Type</th>
                            <th>Not Null</th>
                            <th>Default</th>
                            <th>Primary Key</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${tableData.columns.map(col => `
                            <tr>
                                <td><strong>${col.name}</strong></td>
                                <td>${col.type}</td>
                                <td>${col.not_null ? 'Yes' : 'No'}</td>
                                <td>${col.default_value || 'None'}</td>
                                <td>${col.primary_key ? 'Yes' : 'No'}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
        
        content.innerHTML = html;
        this.openModal('tableDetailsModal');
    }
    
    queryTable(tableName) {
        this.selectTable(tableName);
        
        // Switch to natural language tab and pre-fill with table query
        this.switchTab('natural');
        document.getElementById('naturalLanguageInput').value = `Show me all data from the ${tableName} table`;
        
        // Focus on the input
        document.getElementById('naturalLanguageInput').focus();
    }
    
    async handleOpenDatabase() {
        const filePathInput = document.getElementById('databaseFilePath');
        const fileInput = document.getElementById('databaseFileInput');
        let filePath = filePathInput.value.trim();
        
        if (!filePath) {
            this.showError('Please enter a file path or browse for a file');
            return;
        }
        
        try {
            this.showLoading('Opening database...');
            let dbInfo;
            
            // Check if a file was selected via browse
            if (fileInput.files.length > 0) {
                // Use the selected file for upload (same as load database)
                const file = fileInput.files[0];
                dbInfo = await this.databaseManager.loadDatabase(file);
            } else {
                // Check if path is relative (no drive letter or leading slash)
                if (!filePath.includes(':') && !filePath.startsWith('/') && !filePath.startsWith('\\')) {
                    // Assume it's a filename in the uploads directory
                    filePath = `uploads/${filePath}`;
                }
                
                // Use the manually entered path
                dbInfo = await this.databaseManager.openDatabase(filePath);
            }
            
            // Update UI
            await this.loadDatabases();
            this.selectDatabase(dbInfo.database_id);
            
            // Close modal and clear form
            this.closeModal('openDatabaseModal');
            filePathInput.value = '';
            fileInput.value = '';
            
            this.showSuccess('Database opened successfully!');
        } catch (error) {
            this.showError(`Failed to open database: ${error.message}`);
        } finally {
            this.hideLoading();
        }
    }
}

// Initialize the application when DOM is loaded
let app;
document.addEventListener('DOMContentLoaded', () => {
    app = new SQLiteAIManager();
});