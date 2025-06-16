from flask_socketio import emit, join_room, leave_room, disconnect
from flask import request, current_app
import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime
from app.models.database import DatabaseModel
from app.models.ai_service import AIService
from app.models.schemas import (
    WebSocketMessage, QueryType, DatabaseStatus,
    NaturalLanguageQueryRequest, QueryRequest
)
from pydantic import ValidationError

# Initialize services
db_model = DatabaseModel()
ai_service = AIService(db_model)
logger = logging.getLogger(__name__)

# Store active connections
active_connections: Dict[str, Dict[str, Any]] = {}

def serialize_websocket_message(message: WebSocketMessage) -> dict:
    """Helper function to serialize WebSocketMessage with datetime handling"""
    message_dict = message.dict()
    if isinstance(message_dict.get('timestamp'), datetime):
        message_dict['timestamp'] = message_dict['timestamp'].isoformat()
    return message_dict

def init_socketio_handlers(socketio):
    """Initialize all WebSocket event handlers"""
    
    @socketio.on('connect')
    def handle_connect(auth=None):
        """Handle client connection"""
        try:
            client_id = request.sid
            client_info = {
                'connected_at': datetime.utcnow().isoformat(),
                'ip_address': request.environ.get('REMOTE_ADDR'),
                'user_agent': request.headers.get('User-Agent'),
                'rooms': set()
            }
            
            active_connections[client_id] = client_info
            
            logger.info(f"Client connected: {client_id}")
            
            # Send welcome message
            welcome_message = WebSocketMessage(
                type="connection",
                data={
                    "status": "connected",
                    "client_id": client_id,
                    "server_time": datetime.utcnow().isoformat()
                },
                timestamp=datetime.utcnow()
            )
            
            emit('message', serialize_websocket_message(welcome_message))
            
        except Exception as e:
            logger.error(f"Error handling connection: {str(e)}")
            disconnect()
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        try:
            client_id = request.sid
            
            if client_id in active_connections:
                # Leave all rooms
                client_rooms = active_connections[client_id].get('rooms', set())
                for room in client_rooms:
                    leave_room(room)
                
                # Remove from active connections
                del active_connections[client_id]
                
                logger.info(f"Client disconnected: {client_id}")
            
        except Exception as e:
            logger.error(f"Error handling disconnection: {str(e)}")
    
    @socketio.on('join_database')
    def handle_join_database(data):
        """Join a database-specific room for updates"""
        try:
            client_id = request.sid
            database_id = data.get('database_id')
            
            if not database_id:
                error_message = WebSocketMessage(
                    type="error",
                    data={"error": "Database ID is required"}
                )
                emit('message', serialize_websocket_message(error_message))
                return
            
            # Validate database exists
            db_info = db_model.get_database_info(database_id)
            if not db_info:
                error_message = WebSocketMessage(
                    type="error",
                    data={"error": f"Database not found: {database_id}"}
                )
                emit('message', serialize_websocket_message(error_message))
                return
            
            room_name = f"database_{database_id}"
            join_room(room_name)
            
            # Update client info
            if client_id in active_connections:
                active_connections[client_id]['rooms'].add(room_name)
            
            # Send confirmation
            # Convert DatabaseInfo to dict with proper datetime serialization
            db_info_dict = {
                'id': db_info.id,
                'path': db_info.path,
                'tables': db_info.tables,
                'size': db_info.size,
                'status': db_info.status.value,
                'created_at': db_info.created_at.isoformat() if db_info.created_at else None,
                'last_accessed': db_info.last_accessed.isoformat() if db_info.last_accessed else None
            }
            
            join_message = WebSocketMessage(
                type="room_joined",
                data={
                    "room": room_name,
                    "database_id": database_id,
                    "database_info": db_info_dict
                }
            )
            
            emit('message', serialize_websocket_message(join_message))
            logger.info(f"Client {client_id} joined room {room_name}")
            
        except Exception as e:
            logger.error(f"Error joining database room: {str(e)}")
            error_message = WebSocketMessage(
                type="error",
                data={"error": str(e)}
            )
            emit('message', serialize_websocket_message(error_message))
    
    @socketio.on('leave_database')
    def handle_leave_database(data):
        """Leave a database-specific room"""
        try:
            client_id = request.sid
            database_id = data.get('database_id')
            
            if not database_id:
                error_message = WebSocketMessage(
                    type="error",
                    data={"error": "Database ID is required"}
                )
                emit('message', serialize_websocket_message(error_message))
                return
            
            room_name = f"database_{database_id}"
            leave_room(room_name)
            
            # Update client info
            if client_id in active_connections:
                active_connections[client_id]['rooms'].discard(room_name)
            
            # Send confirmation
            leave_message = WebSocketMessage(
                type="room_left",
                data={
                    "room": room_name,
                    "database_id": database_id
                }
            )
            
            emit('message', serialize_websocket_message(leave_message))
            logger.info(f"Client {client_id} left room {room_name}")
            
        except Exception as e:
            logger.error(f"Error leaving database room: {str(e)}")
            error_message = WebSocketMessage(
                type="error",
                data={"error": str(e)}
            )
            emit('message', serialize_websocket_message(error_message))
    
    @socketio.on('execute_query')
    def handle_execute_query(data):
        """Execute a SQL query and broadcast results"""
        try:
            client_id = request.sid
            
            # Validate required fields
            database_id = data.get('database_id')
            query = data.get('query')
            
            if not database_id or not query:
                error_message = WebSocketMessage(
                    type="error",
                    data={"error": "Database ID and query are required"}
                )
                emit('message', serialize_websocket_message(error_message))
                return
            
            # Send query started message
            start_message = WebSocketMessage(
                type="query_started",
                data={
                    "database_id": database_id,
                    "query": query
                }
            )
            emit('message', serialize_websocket_message(start_message))
            
            # Execute query
            result = db_model.execute_query(database_id, query)
            
            # Send results
            result_message = WebSocketMessage(
                type="query_result",
                data={
                    "database_id": database_id,
                    "query": query,
                    "result": result
                }
            )
            
            # Broadcast to database room
            room_name = f"database_{database_id}"
            socketio.emit('message', serialize_websocket_message(result_message), room=room_name)
            
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            error_message = WebSocketMessage(
                type="error",
                data={"error": str(e)}
            )
            emit('message', serialize_websocket_message(error_message))
    
    @socketio.on('natural_language_query')
    def handle_natural_language_query(data):
        """Process natural language query and return SQL"""
        try:
            client_id = request.sid
            
            # Validate request data
            try:
                nl_request = NaturalLanguageQueryRequest(**data)
            except ValidationError as e:
                error_message = WebSocketMessage(
                    type="error",
                    data={"error": "Invalid request data", "details": e.errors()},
    
                )
                emit('message', error_message.dict())
                return
            
            # Send processing started message
            start_message = WebSocketMessage(
                type="nl_processing_started",
                data={
                    "database_id": nl_request.database_id,
                    "query": nl_request.query
                },

            )
            emit('message', start_message.dict())
            
            # Process natural language query
            result = ai_service.process_natural_language_query(
                prompt=nl_request.query,
                database_id=nl_request.database_id,
                include_explanation=True
            )
            
            # Send results
            if result['success']:
                success_message = WebSocketMessage(
                    type="nl_query_result",
                    data={
                        "database_id": nl_request.database_id,
                        "original_query": nl_request.query,
                        "result": result
                    },
    
                )
                emit('message', success_message.dict())
                
            else:
                error_message = WebSocketMessage(
                    type="nl_query_error",
                    data={
                        "database_id": nl_request.database_id,
                        "query": nl_request.query,
                        "error": result.get('error')
                    },
    
                )
                emit('message', error_message.dict())
            
        except Exception as e:
            logger.error(f"Error processing natural language query: {str(e)}")
            error_message = WebSocketMessage(
                type="error",
                data={"error": str(e)},

            )
            emit('message', error_message.dict())
    
    @socketio.on('get_database_status')
    def handle_get_database_status(data):
        """Get current status of a database"""
        try:
            database_id = data.get('database_id')
            
            if not database_id:
                error_message = WebSocketMessage(
                    type="error",
                    data={"error": "Database ID is required"},
    
                )
                emit('message', error_message.dict())
                return
            
            # Get database info
            db_info = db_model.get_database_info(database_id)
            
            if db_info:
                status_message = WebSocketMessage(
                    type="database_status",
                    data={
                        "database_id": database_id,
                        "status": DatabaseStatus.CONNECTED.value,
                        "info": db_info
                    },
    
                )
            else:
                status_message = WebSocketMessage(
                    type="database_status",
                    data={
                        "database_id": database_id,
                        "status": DatabaseStatus.NOT_FOUND.value
                    },
    
                )
            
            emit('message', status_message.dict())
            
        except Exception as e:
            logger.error(f"Error getting database status: {str(e)}")
            error_message = WebSocketMessage(
                type="error",
                data={"error": str(e)},

            )
            emit('message', error_message.dict())
    
    @socketio.on('ping')
    def handle_ping(data):
        """Handle ping requests for connection health check"""
        try:
            pong_message = WebSocketMessage(
                type="pong",
                data={
                    "timestamp": datetime.utcnow().isoformat(),
                    "client_id": request.sid
                },

            )
            emit('message', pong_message.dict())
            
        except Exception as e:
            logger.error(f"Error handling ping: {str(e)}")
    
    @socketio.on('get_active_connections')
    def handle_get_active_connections(data):
        """Get information about active connections (admin only)"""
        try:
            # In a real application, you would check admin permissions here
            
            connections_info = {
                'total_connections': len(active_connections),
                'connections': [
                    {
                        'client_id': client_id,
                        'connected_at': info['connected_at'],
                        'rooms': list(info['rooms'])
                    }
                    for client_id, info in active_connections.items()
                ]
            }
            
            status_message = WebSocketMessage(
                type="active_connections",
                data=connections_info,

            )
            
            emit('message', status_message.dict())
            
        except Exception as e:
            logger.error(f"Error getting active connections: {str(e)}")
            error_message = WebSocketMessage(
                type="error",
                data={"error": str(e)},

            )
            emit('message', error_message.dict())

def broadcast_database_update(database_id: str, update_type: str, data: Dict[str, Any]):
    """Broadcast database updates to all clients in the database room"""
    try:
        from app import socketio  # Import here to avoid circular imports
        
        room_name = f"database_{database_id}"
        
        update_message = WebSocketMessage(
            type="database_update",
            data={
                "database_id": database_id,
                "update_type": update_type,
                "data": data
            }
        )
        
        socketio.emit('message', update_message.dict(), room=room_name)
        logger.info(f"Broadcasted {update_type} update to room {room_name}")
        
    except Exception as e:
        logger.error(f"Error broadcasting database update: {str(e)}")

def broadcast_system_message(message_type: str, data: Dict[str, Any]):
    """Broadcast system-wide messages to all connected clients"""
    try:
        from app import socketio  # Import here to avoid circular imports
        
        system_message = WebSocketMessage(
            type=message_type,
            data=data
        )
        
        socketio.emit('message', system_message.dict())
        logger.info(f"Broadcasted system message: {message_type}")
        
    except Exception as e:
        logger.error(f"Error broadcasting system message: {str(e)}")

def get_connection_stats() -> Dict[str, Any]:
    """Get statistics about active connections"""
    try:
        total_connections = len(active_connections)
        rooms_count = {}
        
        for client_info in active_connections.values():
            for room in client_info.get('rooms', set()):
                rooms_count[room] = rooms_count.get(room, 0) + 1
        
        return {
            'total_connections': total_connections,
            'rooms': rooms_count,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting connection stats: {str(e)}")
        return {
            'total_connections': 0,
            'rooms': {},
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }