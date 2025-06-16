from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional, Union
from enum import Enum
from datetime import datetime

class QueryType(str, Enum):
    SELECT = "select"
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"
    CREATE = "create"
    DROP = "drop"
    DESCRIBE = "describe"
    COUNT = "count"
    AGGREGATE = "aggregate"
    UNKNOWN = "unknown"

class DatabaseStatus(str, Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    LOADING = "loading"

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

# Request Models
class DatabaseLoadRequest(BaseModel):
    file_path: str = Field(..., description="Path to the SQLite database file")
    
    @validator('file_path')
    def validate_file_path(cls, v):
        if not v.strip():
            raise ValueError('File path cannot be empty')
        return v.strip()

class QueryRequest(BaseModel):
    query: str = Field(..., description="SQL query to execute")
    params: Optional[List[Any]] = Field(None, description="Query parameters")
    
    @validator('query')
    def validate_query(cls, v):
        if not v.strip():
            raise ValueError('Query cannot be empty')
        return v.strip()

class NaturalLanguageQueryRequest(BaseModel):
    prompt: str = Field(..., description="Natural language query")
    database_id: str = Field(..., description="Database identifier")
    include_explanation: bool = Field(True, description="Include AI explanation of results")
    model: Optional[str] = Field(None, description="AI model to use for processing")
    
    @validator('prompt')
    def validate_prompt(cls, v):
        if not v.strip():
            raise ValueError('Prompt cannot be empty')
        return v.strip()

class TableDataRequest(BaseModel):
    table_name: str = Field(..., description="Name of the table")
    database_id: str = Field(..., description="Database identifier")
    limit: int = Field(100, ge=1, le=1000, description="Number of rows to return")
    offset: int = Field(0, ge=0, description="Number of rows to skip")
    filters: Optional[Dict[str, Any]] = Field(None, description="Filter conditions")
    sort_by: Optional[str] = Field(None, description="Column to sort by")
    sort_order: Optional[str] = Field("ASC", pattern="^(ASC|DESC)$", description="Sort order")

class RecordInsertRequest(BaseModel):
    table_name: str = Field(..., description="Name of the table")
    database_id: str = Field(..., description="Database identifier")
    data: Dict[str, Any] = Field(..., description="Record data")

class RecordUpdateRequest(BaseModel):
    table_name: str = Field(..., description="Name of the table")
    database_id: str = Field(..., description="Database identifier")
    record_id: Union[int, str] = Field(..., description="Record identifier")
    data: Dict[str, Any] = Field(..., description="Updated record data")
    id_column: str = Field("id", description="Name of the ID column")

class RecordDeleteRequest(BaseModel):
    table_name: str = Field(..., description="Name of the table")
    database_id: str = Field(..., description="Database identifier")
    record_id: Union[int, str] = Field(..., description="Record identifier")
    id_column: str = Field("id", description="Name of the ID column")

class DatabaseCreateRequest(BaseModel):
    description: str = Field(..., description="Natural language description of the database to create")
    database_name: str = Field(..., description="Name for the new database")
    
    @validator('description')
    def validate_description(cls, v):
        if not v.strip():
            raise ValueError('Description cannot be empty')
        if len(v.strip()) < 10:
            raise ValueError('Description must be at least 10 characters long')
        return v.strip()
    
    @validator('database_name')
    def validate_database_name(cls, v):
        if not v.strip():
            raise ValueError('Database name cannot be empty')
        # Remove invalid characters and ensure it ends with .sqlite
        clean_name = ''.join(c for c in v.strip() if c.isalnum() or c in '_-')
        if not clean_name:
            raise ValueError('Database name must contain valid characters')
        if not clean_name.lower().endswith('.sqlite'):
            clean_name += '.sqlite'
        return clean_name

# Response Models
class ColumnInfo(BaseModel):
    name: str
    type: str
    not_null: bool
    default_value: Optional[Any]
    primary_key: bool

class TableInfo(BaseModel):
    name: str
    columns: List[ColumnInfo]
    row_count: int

class DatabaseInfo(BaseModel):
    id: str
    path: str
    tables: List[str]
    size: int
    status: DatabaseStatus
    created_at: Optional[datetime] = None
    last_accessed: Optional[datetime] = None

class DatabaseSchema(BaseModel):
    database_id: str
    tables: Dict[str, TableInfo]
    total_tables: int
    total_size: int

class QueryResult(BaseModel):
    success: bool
    data: Optional[List[Dict[str, Any]]] = None
    columns: Optional[List[str]] = None
    row_count: Optional[int] = None
    rows_affected: Optional[int] = None
    message: Optional[str] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None

class ParsedQuery(BaseModel):
    original_query: str
    query_type: QueryType
    tables: List[str]
    columns: List[str]
    filters: List[Dict[str, Any]]
    aggregations: List[Dict[str, Any]]
    sorting: Optional[Dict[str, Any]]
    limit: Optional[int]
    confidence: float = Field(ge=0.0, le=1.0)
    suggestions: List[str]

class AIQueryResponse(BaseModel):
    success: bool
    sql_query: Optional[str] = None
    original_prompt: str
    parsed_info: Optional[ParsedQuery] = None
    query_result: Optional[QueryResult] = None
    explanation: Optional[str] = None
    error: Optional[str] = None
    processing_time: Optional[float] = None

class QuerySafetyAnalysis(BaseModel):
    safe: bool
    risk_level: RiskLevel
    warnings: List[str]
    recommendations: List[str]

class QueryOptimization(BaseModel):
    success: bool
    original_query: str
    suggestions: Optional[str] = None
    optimized_query: Optional[str] = None
    performance_notes: Optional[List[str]] = None
    error: Optional[str] = None

class TableDataResponse(BaseModel):
    success: bool
    table_name: str
    data: Optional[List[Dict[str, Any]]] = None
    columns: Optional[List[ColumnInfo]] = None
    total_rows: Optional[int] = None
    page_info: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class APIResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    data: Optional[Any] = None
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)

# WebSocket Models
class WebSocketMessage(BaseModel):
    type: str
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.now)

class DatabaseEvent(BaseModel):
    event_type: str  # 'connected', 'disconnected', 'query_executed', 'error'
    database_id: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)

class QueryEvent(BaseModel):
    event_type: str  # 'started', 'completed', 'failed'
    query_id: str
    database_id: str
    query: Optional[str] = None
    result: Optional[QueryResult] = None
    timestamp: datetime = Field(default_factory=datetime.now)

# Configuration Models
class AIConfig(BaseModel):
    api_key: str
    model: str
    base_url: str
    temperature: float = Field(0.1, ge=0.0, le=2.0)
    max_tokens: int = Field(1000, ge=1, le=4000)
    timeout: int = Field(30, ge=5, le=120)

class DatabaseConfig(BaseModel):
    max_size: int = Field(100 * 1024 * 1024)  # 100MB
    allowed_extensions: List[str] = Field(default=['.db', '.sqlite', '.sqlite3'])
    connection_timeout: int = Field(30)
    query_timeout: int = Field(60)

class AppConfig(BaseModel):
    debug: bool = False
    secret_key: str
    ai_config: AIConfig
    database_config: DatabaseConfig
    upload_folder: str
    rate_limits: Dict[str, str] = Field(default={
        "default": "200 per day, 50 per hour",
        "ai_queries": "100 per hour",
        "database_operations": "500 per hour"
    })