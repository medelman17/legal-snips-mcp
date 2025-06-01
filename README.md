# Legal Research Snippets MCP Server

A Model Context Protocol (MCP) server for managing legal research snippets and case law findings with **two deployment options**:

1. **Basic Version** - JSON file storage for quick setup
2. **Advanced Version** - PostgreSQL with pgvector for AI-powered semantic search

## Features

### Basic Version (JSON)
- **Create snippets**: Save case citations with key language, tags, and context
- **Search**: Find snippets by text content or tags
- **Update/Delete**: Modify or remove existing snippets
- **Export**: Export all snippets in JSON or text format
- **Tag management**: View all unique tags in your collection
- **Local storage**: All data stored locally in JSON format

### Advanced Version (PostgreSQL + pgvector)
- **All basic features** plus:
- **Semantic search**: AI-powered similarity search using vector embeddings
- **Find similar snippets**: Discover related legal concepts automatically
- **Advanced filtering**: Combine semantic search with tag filtering
- **Scalable storage**: PostgreSQL backend for large collections
- **Vector similarity**: Uses sentence transformers for legal text understanding

## Setup

### Prerequisites
- Python 3.10 or higher
- Poetry (for dependency management)
- PostgreSQL 15+ with pgvector (for advanced version only)

### Quick Start (Basic Version)

```bash
# Install dependencies
poetry install

# Test the basic server
poetry run python test_server.py

# Run the basic JSON server
poetry run python legal_snippets_server.py
```

### Advanced Setup (PostgreSQL + Semantic Search)

#### Option 1: Using Docker (Recommended)
```bash
# Start PostgreSQL with pgvector
docker-compose up -d

# Wait for database to be ready, then setup
poetry run python setup_postgres.py

# Run the advanced server
poetry run python legal_snippets_postgres_server.py
```

#### Option 2: Existing PostgreSQL
```bash
# Install pgvector extension on your PostgreSQL server
# Ubuntu/Debian: sudo apt install postgresql-15-pgvector
# macOS: brew install pgvector

# Set your database URL
export DATABASE_URL="postgresql://user:pass@localhost:5432/legal_snippets"

# Setup database
poetry run python setup_postgres.py

# Run the advanced server
poetry run python legal_snippets_postgres_server.py
```

## Usage

### Running the Servers

```bash
# Basic JSON version
poetry run python legal_snippets_server.py

# Advanced PostgreSQL version
poetry run python legal_snippets_postgres_server.py
```

### Available Tools

#### Common Tools (Both Versions)

1. **create_snippet**: Create a new legal research snippet
   - `citation`: Case citation (e.g., "Smith v. Jones, 123 F.3d 456 (2nd Cir. 2023)")
   - `key_language`: Important legal text from the case
   - `tags`: List of categorization tags
   - `context`: Additional notes (optional)
   - `case_type`: Type of case (default: "civil")

2. **search_snippets**: Search snippets by keyword or tags
   - `query`: Text to search for (optional)
   - `tags`: List of tags to filter by (optional)

3. **get_snippet**: Retrieve a specific snippet by ID
   - `snippet_id`: The ID of the snippet to retrieve

4. **update_snippet**: Update an existing snippet
   - `snippet_id`: The ID of the snippet to update
   - Other parameters: same as create_snippet (all optional)

5. **delete_snippet**: Delete a snippet by ID
   - `snippet_id`: The ID of the snippet to delete

6. **list_tags**: Get all unique tags from the collection

7. **export_snippets**: Export all snippets
   - `format`: "json" or "text" (default: "json")

#### Advanced Tools (PostgreSQL Version Only)

8. **semantic_search**: AI-powered similarity search
   - `query`: Natural language query
   - `limit`: Maximum results (default: 10)
   - `similarity_threshold`: Minimum similarity score (default: 0.7)
   - `tags`: Optional tag filtering

9. **find_similar_snippets**: Find snippets similar to a given one
   - `snippet_id`: Reference snippet ID
   - `limit`: Maximum results (default: 5)

## Claude Desktop Configuration

Add one of these configurations to your Claude Desktop config file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

### Basic Version

#### macOS/Linux
```json
{
  "mcpServers": {
    "legal-snippets": {
      "command": "poetry",
      "args": ["run", "python", "legal_snippets_server.py"],
      "cwd": "/absolute/path/to/legal-snips"
    }
  }
}
```

#### Windows Configuration Options

⚠️ **Important**: On Windows, the `cwd` parameter doesn't always work correctly with Poetry. Use one of these three proven methods:

**Option 1: Direct Python Path (Recommended)**
```json
{
  "mcpServers": {
    "legal-snippets": {
      "command": "C:\\Users\\YOUR_USERNAME\\GitHub\\legal-snips-mcp\\.venv\\Scripts\\python.exe",
      "args": [
        "C:\\Users\\YOUR_USERNAME\\GitHub\\legal-snips-mcp\\legal_snippets_server.py"
      ]
    }
  }
}
```

**Option 2: Batch File Wrapper**
1. Create `run_server.bat` in your project directory:
```batch
@echo off
cd /d C:\Users\YOUR_USERNAME\GitHub\legal-snips-mcp
poetry run python legal_snippets_server.py
```

2. Configure Claude Desktop:
```json
{
  "mcpServers": {
    "legal-snippets": {
      "command": "C:\\Users\\YOUR_USERNAME\\GitHub\\legal-snips-mcp\\run_server.bat"
    }
  }
}
```

**Option 3: CMD with Directory Change**
```json
{
  "mcpServers": {
    "legal-snippets": {
      "command": "cmd",
      "args": [
        "/c",
        "cd /d C:\\Users\\YOUR_USERNAME\\GitHub\\legal-snips-mcp && poetry run python legal_snippets_server.py"
      ]
    }
  }
}
```

### Advanced Version (PostgreSQL)

#### macOS/Linux
```json
{
  "mcpServers": {
    "legal-snippets-ai": {
      "command": "poetry",
      "args": ["run", "python", "legal_snippets_postgres_server.py"],
      "cwd": "/absolute/path/to/legal-snips",
      "env": {
        "DATABASE_URL": "postgresql://postgres:password@localhost:5432/legal_snippets"
      }
    }
  }
}
```

#### Windows
Use the same approaches as the Basic Version, but with `legal_snippets_postgres_server.py` instead. For example:

```json
{
  "mcpServers": {
    "legal-snippets-ai": {
      "command": "C:\\Users\\YOUR_USERNAME\\GitHub\\legal-snips-mcp\\.venv\\Scripts\\python.exe",
      "args": [
        "C:\\Users\\YOUR_USERNAME\\GitHub\\legal-snips-mcp\\legal_snippets_postgres_server.py"
      ],
      "env": {
        "DATABASE_URL": "postgresql://postgres:password@localhost:5432/legal_snippets"
      }
    }
  }
}
```

### ⚡ Quick Setup Verification

After updating your configuration:
1. **Save** the claude_desktop_config.json file
2. **Restart Claude Desktop** completely (quit and reopen)
3. Check if the server appears in Claude's MCP servers list
4. Test with a simple command like "list all tags"

## Example Usage in Claude

### Basic Examples (Both Versions)
- "Create a snippet for Smith v. Jones about contract damages with tags 'contract' and 'damages'"
- "Search for all snippets tagged with 'negligence'"
- "Export all my research snippets as text"
- "Update snippet 1 to add the tag 'landmark-case'"

### Advanced Examples (PostgreSQL Version)
- "Find snippets similar to 'breach of fiduciary duty in corporate governance'"
- "Search semantically for cases about 'reasonable person standard' with similarity above 0.8"
- "Find snippets most similar to snippet 5"
- "Search for legal concepts related to 'proximate cause' but only in tort cases"

## Data Storage

### Basic Version
- Snippets stored in `legal_snippets.json`
- Simple, portable, version-controllable
- Perfect for personal collections

### Advanced Version
- PostgreSQL database with vector embeddings
- Each snippet includes vector representations for semantic search
- Scalable for large collections (1000s of snippets)
- Full ACID compliance and concurrent access
- Each snippet includes: ID, citation, key language, tags, context, case type, timestamps, and 3 vector embeddings (384 dimensions each)

## Testing

Run the test suite to verify everything works:

```bash
# Basic version
poetry run python test_server.py

# Advanced version (after database setup)
poetry run python setup_postgres.py
```

## Troubleshooting

### Common Issues and Solutions

#### Windows: "ModuleNotFoundError: No module named 'fastmcp'"
**Problem**: Poetry dependencies aren't installed or Poetry is running from wrong directory.

**Solutions**:
1. Ensure you've run `poetry install` in the project directory
2. Use Option 1 (Direct Python Path) from the Windows configuration above
3. Verify `.venv` folder exists in your project directory

#### Windows: "Poetry could not find a pyproject.toml file"
**Problem**: Claude Desktop isn't changing to the correct working directory.

**Solution**: This is a known issue with `cwd` on Windows. Use one of the three Windows configuration options shown above instead of relying on `cwd`.

#### "Server transport closed unexpectedly"
**Problem**: The server crashed or couldn't start properly.

**Solutions**:
1. Test the server manually first: `poetry run python legal_snippets_server.py`
2. Check Python version: must be 3.10 or higher
3. Ensure all paths in configuration are absolute paths with proper escaping

#### "Server disconnected" in Claude Desktop
**Problem**: Configuration path or command is incorrect.

**Solutions**:
1. Verify all paths exist and use double backslashes on Windows
2. Test the exact command from your configuration in a terminal
3. Check Claude Desktop logs for detailed error messages

### Quick Diagnostic Commands

```bash
# Check Poetry installation
poetry --version

# Verify Python version
poetry run python --version

# Test server startup
poetry run python legal_snippets_server.py

# List installed packages
poetry show

# Reinstall dependencies
poetry install --no-root
```

## File Structure

```
legal-snips/
├── legal_snippets_server.py         # Basic JSON MCP server
├── legal_snippets_postgres_server.py # Advanced PostgreSQL MCP server
├── setup_postgres.py                # Database setup script
├── test_server.py                   # Test script for basic version
├── docker-compose.yml               # PostgreSQL + pgvector setup
├── init.sql                         # Database initialization
├── pyproject.toml                   # Poetry configuration
├── README.md                        # This file
├── .env                            # Environment variables (created by setup)
└── legal_snippets.json             # Basic version data storage
```

## Performance Comparison

| Feature | Basic (JSON) | Advanced (PostgreSQL) |
|---------|-------------|----------------------|
| Setup Time | 2 minutes | 10 minutes |
| Search Speed | Fast for <100 snippets | Fast for 1000s+ snippets |
| Semantic Search | ❌ Keyword only | ✅ AI-powered similarity |
| Concurrent Users | ❌ Single user | ✅ Multiple users |
| Scalability | <1000 snippets | 10,000+ snippets |
| Dependencies | Minimal | PostgreSQL + ML models |
| Storage Size | Small | Larger (includes embeddings) |

## When to Use Which Version

**Choose Basic (JSON) if:**
- Quick setup needed
- Personal use only
- Small collection (<500 snippets)
- Simple keyword search is sufficient

**Choose Advanced (PostgreSQL) if:**
- Need semantic/conceptual search
- Multiple users accessing simultaneously
- Large collection (>500 snippets)
- Want to find conceptually similar cases
- Professional/team environment

## Advanced Features Deep Dive

### Semantic Search Capabilities

The PostgreSQL version uses sentence transformers to create 384-dimensional vector embeddings for:

1. **Citation text** - Helps find similar case names and courts
2. **Key language** - Enables conceptual matching of legal principles  
3. **Combined text** - Provides holistic similarity across all content

### Example Semantic Searches

```python
# Find cases about similar legal concepts
"Search for cases about 'duty of care in medical malpractice'"

# Discover related precedents
"Find snippets similar to 'proximate cause in negligence claims'"

# Conceptual tag-filtered search
"Semantic search for 'reasonable person standard' in tort cases only"
```

### Vector Similarity Scoring

- Cosine similarity scores range from 0.0 to 1.0
- Higher scores indicate greater conceptual similarity
- Configurable thresholds allow tuning precision vs recall
- Default threshold of 0.7 provides good balance for legal text

---

🎉 **Ready to revolutionize your legal research workflow!** Start with the basic version and upgrade to semantic search when you need AI-powered legal concept discovery.