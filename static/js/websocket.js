// WebSocket Client Module
class WebSocketClient {
    constructor(url = null) {
        this.url = url || this.getWebSocketURL();
        this.socket = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.eventHandlers = new Map();
        this.messageQueue = [];
        this.currentRoom = null;
        this.connectionId = null;
        this.heartbeatInterval = null;
        this.lastPong = Date.now();
    }
    
    // Get WebSocket URL based on current location
    getWebSocketURL() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host;
        return `${protocol}//${host}/socket.io/`;
    }
    
    // Connect to WebSocket server
    async connect() {
        try {
            if (this.socket && this.isConnected) {
                console.log('WebSocket already connected');
                return;
            }
            
            console.log('Connecting to WebSocket:', this.url);
            
            // Initialize Socket.IO connection
            this.socket = io(this.url, {
                transports: ['websocket', 'polling'],
                timeout: 10000,
                reconnection: true,
                reconnectionAttempts: this.maxReconnectAttempts,
                reconnectionDelay: this.reconnectDelay
            });
            
            this.setupEventHandlers();
            
            return new Promise((resolve, reject) => {
                const timeout = setTimeout(() => {
                    reject(new Error('Connection timeout'));
                }, 10000);
                
                this.socket.on('connect', () => {
                    clearTimeout(timeout);
                    this.onConnect();
                    resolve();
                });
                
                this.socket.on('connect_error', (error) => {
                    clearTimeout(timeout);
                    reject(error);
                });
            });
        } catch (error) {
            console.error('WebSocket connection error:', error);
            throw error;
        }
    }
    
    // Setup event handlers
    setupEventHandlers() {
        if (!this.socket) return;
        
        this.socket.on('connect', () => this.onConnect());
        this.socket.on('disconnect', (reason) => this.onDisconnect(reason));
        this.socket.on('reconnect', (attemptNumber) => this.onReconnect(attemptNumber));
        this.socket.on('reconnect_error', (error) => this.onReconnectError(error));
        this.socket.on('reconnect_failed', () => this.onReconnectFailed());
        
        // Custom event handlers
        this.socket.on('query_result', (data) => this.handleQueryResult(data));
        this.socket.on('database_update', (data) => this.handleDatabaseUpdate(data));
        this.socket.on('system_message', (data) => this.handleSystemMessage(data));
        this.socket.on('error_message', (data) => this.handleErrorMessage(data));
        this.socket.on('status_update', (data) => this.handleStatusUpdate(data));
        this.socket.on('pong', (data) => this.handlePong(data));
        this.socket.on('connection_info', (data) => this.handleConnectionInfo(data));
    }
    
    // Connection event handlers
    onConnect() {
        console.log('WebSocket connected');
        this.isConnected = true;
        this.reconnectAttempts = 0;
        this.connectionId = this.socket.id;
        
        // Process queued messages
        this.processMessageQueue();
        
        // Start heartbeat
        this.startHeartbeat();
        
        // Emit custom connect event
        this.emit('connected', { connectionId: this.connectionId });
        
        // Update UI
        this.updateConnectionStatus(true);
    }
    
    onDisconnect(reason) {
        console.log('WebSocket disconnected:', reason);
        this.isConnected = false;
        this.connectionId = null;
        
        // Stop heartbeat
        this.stopHeartbeat();
        
        // Emit custom disconnect event
        this.emit('disconnected', { reason });
        
        // Update UI
        this.updateConnectionStatus(false);
    }
    
    onReconnect(attemptNumber) {
        console.log('WebSocket reconnected after', attemptNumber, 'attempts');
        this.reconnectAttempts = 0;
        this.emit('reconnected', { attemptNumber });
    }
    
    onReconnectError(error) {
        console.error('WebSocket reconnection error:', error);
        this.reconnectAttempts++;
        this.emit('reconnect_error', { error, attempts: this.reconnectAttempts });
    }
    
    onReconnectFailed() {
        console.error('WebSocket reconnection failed');
        this.emit('reconnect_failed', {});
    }
    
    // Message handlers
    handleQueryResult(data) {
        console.log('Query result received:', data);
        this.emit('query_result', data);
    }
    
    handleDatabaseUpdate(data) {
        console.log('Database update received:', data);
        this.emit('database_update', data);
    }
    
    handleSystemMessage(data) {
        console.log('System message received:', data);
        this.emit('system_message', data);
    }
    
    handleErrorMessage(data) {
        console.error('Error message received:', data);
        this.emit('error_message', data);
    }
    
    handleStatusUpdate(data) {
        console.log('Status update received:', data);
        this.emit('status_update', data);
    }
    
    handlePong(data) {
        this.lastPong = Date.now();
        this.emit('pong', data);
    }
    
    handleConnectionInfo(data) {
        console.log('Connection info received:', data);
        this.emit('connection_info', data);
    }
    
    // Send messages
    send(event, data = {}) {
        if (!this.isConnected || !this.socket) {
            console.warn('WebSocket not connected, queuing message:', event, data);
            this.messageQueue.push({ event, data, timestamp: Date.now() });
            return false;
        }
        
        try {
            this.socket.emit(event, data);
            return true;
        } catch (error) {
            console.error('Error sending WebSocket message:', error);
            return false;
        }
    }
    
    // Database operations
    joinDatabase(databaseId) {
        if (this.currentRoom === databaseId) {
            console.log('Already in database room:', databaseId);
            return;
        }
        
        // Leave current room if any
        if (this.currentRoom) {
            this.leaveDatabase(this.currentRoom);
        }
        
        this.send('join_database', { database_id: databaseId });
        this.currentRoom = databaseId;
        console.log('Joined database room:', databaseId);
    }
    
    leaveDatabase(databaseId = null) {
        const dbId = databaseId || this.currentRoom;
        if (!dbId) return;
        
        this.send('leave_database', { database_id: dbId });
        
        if (dbId === this.currentRoom) {
            this.currentRoom = null;
        }
        
        console.log('Left database room:', dbId);
    }
    
    // Query operations
    executeQuery(databaseId, query, queryType = 'sql') {
        const data = {
            database_id: databaseId,
            query: query,
            query_type: queryType,
            timestamp: Date.now()
        };
        
        if (queryType === 'natural_language') {
            return this.send('execute_nl_query', data);
        } else {
            return this.send('execute_sql_query', data);
        }
    }
    
    getDatabaseStatus(databaseId) {
        return this.send('get_database_status', { database_id: databaseId });
    }
    
    // Heartbeat mechanism
    startHeartbeat() {
        this.stopHeartbeat(); // Clear any existing interval
        
        this.heartbeatInterval = setInterval(() => {
            if (this.isConnected) {
                this.send('ping', { timestamp: Date.now() });
                
                // Check if we haven't received a pong in too long
                if (Date.now() - this.lastPong > 30000) { // 30 seconds
                    console.warn('Heartbeat timeout, connection may be stale');
                    this.emit('heartbeat_timeout', {});
                }
            }
        }, 10000); // Send ping every 10 seconds
    }
    
    stopHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
        }
    }
    
    // Message queue processing
    processMessageQueue() {
        if (this.messageQueue.length === 0) return;
        
        console.log('Processing', this.messageQueue.length, 'queued messages');
        
        const messages = [...this.messageQueue];
        this.messageQueue = [];
        
        messages.forEach(({ event, data }) => {
            this.send(event, data);
        });
    }
    
    // Event handling
    on(event, handler) {
        if (!this.eventHandlers.has(event)) {
            this.eventHandlers.set(event, []);
        }
        this.eventHandlers.get(event).push(handler);
    }
    
    off(event, handler = null) {
        if (!this.eventHandlers.has(event)) return;
        
        if (handler) {
            const handlers = this.eventHandlers.get(event);
            const index = handlers.indexOf(handler);
            if (index > -1) {
                handlers.splice(index, 1);
            }
        } else {
            this.eventHandlers.delete(event);
        }
    }
    
    emit(event, data) {
        if (!this.eventHandlers.has(event)) return;
        
        const handlers = this.eventHandlers.get(event);
        handlers.forEach(handler => {
            try {
                handler(data);
            } catch (error) {
                console.error('Error in event handler:', error);
            }
        });
    }
    
    // Connection management
    disconnect() {
        if (this.socket) {
            this.stopHeartbeat();
            this.socket.disconnect();
            this.socket = null;
        }
        
        this.isConnected = false;
        this.connectionId = null;
        this.currentRoom = null;
        this.messageQueue = [];
        
        console.log('WebSocket disconnected manually');
    }
    
    reconnect() {
        if (this.socket) {
            this.socket.connect();
        } else {
            this.connect();
        }
    }
    
    // Status and utility methods
    getConnectionStatus() {
        return {
            isConnected: this.isConnected,
            connectionId: this.connectionId,
            currentRoom: this.currentRoom,
            reconnectAttempts: this.reconnectAttempts,
            queuedMessages: this.messageQueue.length,
            lastPong: this.lastPong
        };
    }
    
    updateConnectionStatus(connected) {
        const statusElement = document.getElementById('connection-status');
        if (statusElement) {
            statusElement.textContent = connected ? 'Connected' : 'Disconnected';
            statusElement.className = connected ? 'status-connected' : 'status-disconnected';
        }
        
        // Update connection indicator
        const indicator = document.querySelector('.connection-indicator');
        if (indicator) {
            indicator.className = `connection-indicator ${connected ? 'connected' : 'disconnected'}`;
            indicator.title = connected ? 'Connected to server' : 'Disconnected from server';
        }
    }
    
    // Get active connections info
    getActiveConnections() {
        return this.send('get_active_connections');
    }
    
    // Utility methods for debugging
    getStats() {
        return {
            connected: this.isConnected,
            connectionId: this.connectionId,
            currentRoom: this.currentRoom,
            reconnectAttempts: this.reconnectAttempts,
            queuedMessages: this.messageQueue.length,
            eventHandlers: Array.from(this.eventHandlers.keys()),
            lastPong: new Date(this.lastPong).toISOString(),
            uptime: this.isConnected ? Date.now() - this.lastPong : 0
        };
    }
    
    // Clear all event handlers
    clearEventHandlers() {
        this.eventHandlers.clear();
    }
    
    // Test connection
    async testConnection() {
        if (!this.isConnected) {
            throw new Error('Not connected to WebSocket server');
        }
        
        return new Promise((resolve, reject) => {
            const timeout = setTimeout(() => {
                this.off('pong', pongHandler);
                reject(new Error('Ping timeout'));
            }, 5000);
            
            const pongHandler = () => {
                clearTimeout(timeout);
                this.off('pong', pongHandler);
                resolve(true);
            };
            
            this.on('pong', pongHandler);
            this.send('ping', { test: true, timestamp: Date.now() });
        });
    }
    
    // Error recovery
    handleConnectionError(error) {
        console.error('WebSocket connection error:', error);
        
        // Attempt to reconnect if not already trying
        if (!this.socket || !this.socket.connected) {
            setTimeout(() => {
                if (this.reconnectAttempts < this.maxReconnectAttempts) {
                    console.log('Attempting to reconnect...');
                    this.reconnect();
                }
            }, this.reconnectDelay * Math.pow(2, this.reconnectAttempts)); // Exponential backoff
        }
    }
    
    // Message validation
    validateMessage(event, data) {
        if (typeof event !== 'string' || event.length === 0) {
            throw new Error('Invalid event name');
        }
        
        if (data && typeof data !== 'object') {
            throw new Error('Invalid data format');
        }
        
        return true;
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = WebSocketClient;
} else {
    window.WebSocketClient = WebSocketClient;
}