# SQLite AI Manager

A powerful web-based SQLite database management tool with AI-powered natural language query capabilities. This application allows you to upload, explore, and query SQLite databases using both traditional SQL and natural language queries powered by AI.

![SQLite AI Manager](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-2.3+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

![image](https://github.com/user-attachments/assets/52149313-c639-455b-947c-80be46be2780)

![image](https://github.com/user-attachments/assets/305d79af-0668-4c8e-a670-6970fcbcd94a)



## 🌟 Features

### 🗄️ Database Management
- **Upload & Load**: Support for `.db`, `.sqlite`, and `.sqlite3` files (up to 100MB)
- **Multiple Databases**: Manage multiple databases simultaneously
- **Real-time Connection**: WebSocket-based real-time updates
- **Database Info**: View database statistics, schema, and metadata

### 🤖 AI-Powered Queries
- **Natural Language Processing**: Convert plain English to SQL queries
- **Query Explanation**: Get detailed explanations of query results
- **Smart Suggestions**: AI-powered query optimization suggestions
- **Safety Validation**: Automatic query safety checks
- **Related Queries**: Get suggestions for related queries

### 📊 Data Exploration
- **Interactive Tables**: Browse table data with pagination and sorting
- **Schema Visualization**: View table structures and relationships
- **Data Export**: Export results in JSON or CSV format
- **Record Management**: Insert, update, and delete records
- **Advanced Filtering**: Filter data with multiple conditions

### 🔧 Developer Features
- **SQL Editor**: Syntax highlighting and auto-completion
- **Query History**: Track and replay previous queries
- **Performance Monitoring**: Query execution time tracking
- **Error Handling**: Comprehensive error reporting
- **API Access**: RESTful API for programmatic access

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)
- OpenRouter API key (for AI features)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/ClaudiuJitea/SQliteAgent.git
   cd SQliteAgent
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   # Copy the example environment file
   cp .env.example .env
   
   # Edit .env file and add your OpenRouter API key
   # OPENROUTER_API_KEY=your_actual_api_key_here
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

6. **Open your browser**
   Navigate to `http://localhost:5000`

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the root directory with the following variables:

| Variable | Description | Required |
|----------|-------------|---------|
| `OPENROUTER_API_KEY` | OpenRouter API key for AI features | Yes |
| `SECRET_KEY` | Flask secret key for sessions | No (auto-generated) |
| `FLASK_CONFIG` | Configuration mode (development/production) | No (default: development) |
| `FLASK_DEBUG` | Enable Flask debug mode | No (default: True in development) |

### Getting an OpenRouter API Key

1. Visit [OpenRouter](https://openrouter.ai/)
2. Sign up for an account
3. Navigate to the API Keys section
4. Create a new API key
5. Add the key to your `.env` file

## 📁 Project Structure

```
SQliteAgent/
├── app/
│   ├── models/          # Data models and database operations
│   ├── routes/          # API endpoints
│   ├── services/        # Business logic and AI integration
│   └── websocket/       # WebSocket handlers
├── static/
│   ├── css/            # Stylesheets
│   ├── js/             # JavaScript files
│   └── index.html      # Main application interface
├── uploads/            # Database file storage
│   └── Chinook_Sqlite.sqlite  # Sample database
├── app.py              # Application entry point
├── config.py           # Configuration settings
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## 🎯 Usage

### Getting Started

1. **Upload a Database**: Click "Upload Database" and select a `.db`, `.sqlite`, or `.sqlite3` file
2. **Explore Tables**: Browse your database schema and table contents
3. **Run SQL Queries**: Use the SQL editor to execute custom queries
4. **Try AI Queries**: Use natural language to query your data (e.g., "Show me all customers from Germany")

### Sample Database

The application comes with the Chinook sample database, which contains:
- Music store data with artists, albums, tracks, and customers
- Perfect for testing and learning SQL queries
- Demonstrates relationships between tables

### AI Query Examples

- "Show me the top 5 best-selling albums"
- "List all customers from Canada"
- "What are the most popular music genres?"
- "Find tracks longer than 5 minutes"
- "Show me sales by country"

## 🔌 API Endpoints

### Database Operations
- `GET /api/databases` - List all loaded databases
- `POST /api/databases/upload` - Upload a new database
- `GET /api/databases/{db_id}/info` - Get database information
- `DELETE /api/databases/{db_id}` - Remove a database

### Table Operations
- `GET /api/tables/{db_id}` - List tables in a database
- `GET /api/tables/{db_id}/{table_name}` - Get table data
- `POST /api/tables/{db_id}/{table_name}/query` - Execute SQL query

### AI Operations
- `POST /api/ai/query` - Process natural language query
- `POST /api/ai/explain` - Explain query results
- `GET /api/ai/suggestions` - Get query suggestions

## 🛠️ Development

### Running in Development Mode

```bash
# Set environment variables
export FLASK_CONFIG=development
export FLASK_DEBUG=True

# Run the application
python app.py
```

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run tests
pytest

# Run with coverage
pytest --cov=app
```

## 🚀 Deployment

### Production Setup

1. **Set production environment**
   ```bash
   export FLASK_CONFIG=production
   export FLASK_DEBUG=False
   ```

2. **Use a production WSGI server**
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

3. **Set up reverse proxy** (nginx recommended)

### Docker Deployment

```dockerfile
# Dockerfile example
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: Report bugs or request features via [GitHub Issues](https://github.com/ClaudiuJitea/SQliteAgent/issues)
- **Documentation**: Check the [Wiki](https://github.com/ClaudiuJitea/SQliteAgent/wiki) for detailed documentation
- **Discussions**: Join the conversation in [GitHub Discussions](https://github.com/ClaudiuJitea/SQliteAgent/discussions)

## 🙏 Acknowledgments

- [OpenRouter](https://openrouter.ai/) for AI model access
- [Flask](https://flask.palletsprojects.com/) for the web framework
- [Chinook Database](https://github.com/lerocha/chinook-database) for the sample data
- All contributors who help improve this project

---

**Made with ❤️ by [ClaudiuJitea](https://github.com/ClaudiuJitea)**
