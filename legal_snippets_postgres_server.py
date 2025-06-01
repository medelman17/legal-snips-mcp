from fastmcp import FastMCP
import asyncpg
import os
from datetime import datetime
from typing import List, Dict, Optional, Any
import json
import numpy as np
from sentence_transformers import SentenceTransformer
import asyncio
from contextlib import asynccontextmanager

# Initialize the MCP server
mcp = FastMCP("Legal Research Snippets - PostgreSQL")

# Global variables for database connection and embedding model
_db_pool = None
_embedding_model = None

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/legal_snippets")

class EmbeddingService:
    def __init__(self):
        self.model = None
    
    async def initialize(self):
        """Initialize the sentence transformer model"""
        if self.model is None:
            # Use a legal-domain optimized model or general one
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
    
    def encode_text(self, text: str) -> List[float]:
        """Generate embedding for text"""
        if self.model is None:
            raise RuntimeError("Embedding model not initialized")
        embedding = self.model.encode(text)
        return embedding.tolist()

# Global embedding service
embedding_service = EmbeddingService()

@asynccontextmanager
async def get_db():
    """Get database connection from pool"""
    global _db_pool
    if _db_pool is None:
        await initialize_db()
    async with _db_pool.acquire() as conn:
        yield conn

async def initialize_db():
    """Initialize database connection pool and create tables"""
    global _db_pool
    
    # Create connection pool
    _db_pool = await asyncpg.create_pool(DATABASE_URL)
    
    # Initialize embedding service
    await embedding_service.initialize()
    
    # Create tables and enable pgvector
    async with _db_pool.acquire() as conn:
        # Enable pgvector extension
        await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        
        # Create legal_snippets table with vector column
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS legal_snippets (
                id SERIAL PRIMARY KEY,
                citation TEXT NOT NULL,
                key_language TEXT NOT NULL,
                tags TEXT[] NOT NULL DEFAULT '{}',
                context TEXT DEFAULT '',
                case_type TEXT DEFAULT 'civil',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                citation_embedding vector(384),
                key_language_embedding vector(384),
                combined_embedding vector(384)
            );
        """)
        
        # Create indexes for better performance
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_legal_snippets_tags 
            ON legal_snippets USING GIN(tags);
        """)
        
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_legal_snippets_case_type 
            ON legal_snippets(case_type);
        """)
        
        # Vector similarity indexes
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_legal_snippets_combined_embedding 
            ON legal_snippets USING ivfflat (combined_embedding vector_cosine_ops)
            WITH (lists = 100);
        """)

def generate_embeddings(citation: str, key_language: str, context: str = "") -> Dict[str, List[float]]:
    """Generate embeddings for citation, key language, and combined text"""
    citation_emb = embedding_service.encode_text(citation)
    key_language_emb = embedding_service.encode_text(key_language)
    
    # Combined text for comprehensive search
    combined_text = f"Citation: {citation}. Key Language: {key_language}"
    if context:
        combined_text += f" Context: {context}"
    combined_emb = embedding_service.encode_text(combined_text)
    
    return {
        "citation_embedding": citation_emb,
        "key_language_embedding": key_language_emb,
        "combined_embedding": combined_emb
    }

@mcp.tool()
async def create_snippet(
    citation: str, 
    key_language: str, 
    tags: List[str], 
    context: str = "",
    case_type: str = "civil"
) -> Dict:
    """Create a new legal research snippet with semantic embeddings"""
    try:
        # Generate embeddings
        embeddings = generate_embeddings(citation, key_language, context)
        
        async with get_db() as conn:
            snippet_id = await conn.fetchval("""
                INSERT INTO legal_snippets 
                (citation, key_language, tags, context, case_type, 
                 citation_embedding, key_language_embedding, combined_embedding)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING id
            """, citation, key_language, tags, context, case_type,
                embeddings["citation_embedding"],
                embeddings["key_language_embedding"], 
                embeddings["combined_embedding"])
            
        return {
            "status": "success", 
            "snippet_id": snippet_id, 
            "message": f"Created snippet {snippet_id} for {citation}"
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to create snippet: {str(e)}"}

@mcp.tool()
async def search_snippets(query: str = "", tags: Optional[List[str]] = None) -> List[Dict]:
    """Search snippets by text content or tags using traditional search"""
    try:
        async with get_db() as conn:
            if query and tags:
                # Search by both text and tags
                rows = await conn.fetch("""
                    SELECT id, citation, key_language, tags, context, case_type, 
                           created_at, updated_at
                    FROM legal_snippets 
                    WHERE (citation ILIKE $1 OR key_language ILIKE $1 OR context ILIKE $1)
                    AND tags && $2
                    ORDER BY updated_at DESC
                """, f"%{query}%", tags)
            elif query:
                # Text search only
                rows = await conn.fetch("""
                    SELECT id, citation, key_language, tags, context, case_type, 
                           created_at, updated_at
                    FROM legal_snippets 
                    WHERE citation ILIKE $1 OR key_language ILIKE $1 OR context ILIKE $1
                    ORDER BY updated_at DESC
                """, f"%{query}%")
            elif tags:
                # Tag search only
                rows = await conn.fetch("""
                    SELECT id, citation, key_language, tags, context, case_type, 
                           created_at, updated_at
                    FROM legal_snippets 
                    WHERE tags && $1
                    ORDER BY updated_at DESC
                """, tags)
            else:
                # Return all snippets
                rows = await conn.fetch("""
                    SELECT id, citation, key_language, tags, context, case_type, 
                           created_at, updated_at
                    FROM legal_snippets 
                    ORDER BY updated_at DESC
                """)
            
        return [dict(row) for row in rows]
    except Exception as e:
        return [{"error": f"Search failed: {str(e)}"}]

@mcp.tool()
async def semantic_search(
    query: str, 
    limit: int = 10, 
    similarity_threshold: float = 0.7,
    tags: Optional[List[str]] = None
) -> List[Dict]:
    """Search snippets using semantic similarity based on embeddings"""
    try:
        # Generate embedding for the query
        query_embedding = embedding_service.encode_text(query)
        
        async with get_db() as conn:
            if tags:
                # Semantic search with tag filtering
                rows = await conn.fetch("""
                    SELECT id, citation, key_language, tags, context, case_type, 
                           created_at, updated_at,
                           1 - (combined_embedding <=> $1) as similarity_score
                    FROM legal_snippets 
                    WHERE tags && $2
                    AND 1 - (combined_embedding <=> $1) >= $3
                    ORDER BY combined_embedding <=> $1
                    LIMIT $4
                """, query_embedding, tags, similarity_threshold, limit)
            else:
                # Pure semantic search
                rows = await conn.fetch("""
                    SELECT id, citation, key_language, tags, context, case_type, 
                           created_at, updated_at,
                           1 - (combined_embedding <=> $1) as similarity_score
                    FROM legal_snippets 
                    WHERE 1 - (combined_embedding <=> $1) >= $2
                    ORDER BY combined_embedding <=> $1
                    LIMIT $3
                """, query_embedding, similarity_threshold, limit)
            
        results = []
        for row in rows:
            result = dict(row)
            result['similarity_score'] = float(result['similarity_score'])
            results.append(result)
            
        return results
    except Exception as e:
        return [{"error": f"Semantic search failed: {str(e)}"}]

@mcp.tool()
async def get_snippet(snippet_id: int) -> Optional[Dict]:
    """Retrieve a specific snippet by ID"""
    try:
        async with get_db() as conn:
            row = await conn.fetchrow("""
                SELECT id, citation, key_language, tags, context, case_type, 
                       created_at, updated_at
                FROM legal_snippets 
                WHERE id = $1
            """, snippet_id)
            
        return dict(row) if row else None
    except Exception as e:
        return {"error": f"Failed to get snippet: {str(e)}"}

@mcp.tool()
async def update_snippet(
    snippet_id: int,
    citation: Optional[str] = None,
    key_language: Optional[str] = None,
    tags: Optional[List[str]] = None,
    context: Optional[str] = None,
    case_type: Optional[str] = None
) -> Dict:
    """Update an existing snippet and regenerate embeddings if needed"""
    try:
        async with get_db() as conn:
            # Get current snippet data
            current = await conn.fetchrow("""
                SELECT citation, key_language, context FROM legal_snippets WHERE id = $1
            """, snippet_id)
            
            if not current:
                return {"status": "error", "message": f"Snippet {snippet_id} not found"}
            
            # Use new values or keep current ones
            new_citation = citation or current['citation']
            new_key_language = key_language or current['key_language'] 
            new_context = context or current['context']
            
            # Regenerate embeddings if text changed
            if citation or key_language or context:
                embeddings = generate_embeddings(new_citation, new_key_language, new_context)
                
                await conn.execute("""
                    UPDATE legal_snippets 
                    SET citation = $1, key_language = $2, tags = COALESCE($3, tags), 
                        context = $4, case_type = COALESCE($5, case_type),
                        citation_embedding = $6, key_language_embedding = $7, 
                        combined_embedding = $8, updated_at = CURRENT_TIMESTAMP
                    WHERE id = $9
                """, new_citation, new_key_language, tags, new_context, case_type,
                    embeddings["citation_embedding"], 
                    embeddings["key_language_embedding"],
                    embeddings["combined_embedding"], snippet_id)
            else:
                # Update only metadata
                await conn.execute("""
                    UPDATE legal_snippets 
                    SET tags = COALESCE($1, tags), case_type = COALESCE($2, case_type),
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = $3
                """, tags, case_type, snippet_id)
            
        return {"status": "success", "message": f"Updated snippet {snippet_id}"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to update snippet: {str(e)}"}

@mcp.tool()
async def delete_snippet(snippet_id: int) -> Dict:
    """Delete a snippet by ID"""
    try:
        async with get_db() as conn:
            result = await conn.execute("DELETE FROM legal_snippets WHERE id = $1", snippet_id)
            
        if result == "DELETE 1":
            return {"status": "success", "message": f"Deleted snippet {snippet_id}"}
        else:
            return {"status": "error", "message": f"Snippet {snippet_id} not found"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to delete snippet: {str(e)}"}

@mcp.tool()
async def list_tags() -> List[str]:
    """Get all unique tags from the snippet collection"""
    try:
        async with get_db() as conn:
            rows = await conn.fetch("SELECT DISTINCT unnest(tags) as tag FROM legal_snippets ORDER BY tag")
        return [row['tag'] for row in rows]
    except Exception as e:
        return [f"Error: {str(e)}"]

@mcp.tool()
async def export_snippets(format: str = "json") -> str:
    """Export all snippets in specified format (json or text)"""
    try:
        async with get_db() as conn:
            rows = await conn.fetch("""
                SELECT id, citation, key_language, tags, context, case_type, 
                       created_at, updated_at
                FROM legal_snippets 
                ORDER BY created_at
            """)
        
        if format == "text":
            result = []
            for row in rows:
                result.append(f"ID: {row['id']}\n")
                result.append(f"Citation: {row['citation']}\n")
                result.append(f"Key Language: {row['key_language']}\n")
                result.append(f"Tags: {', '.join(row['tags'])}\n")
                if row['context']:
                    result.append(f"Context: {row['context']}\n")
                result.append(f"Case Type: {row['case_type']}\n")
                result.append(f"Created: {row['created_at']}\n")
                result.append("-" * 50 + "\n")
            return "".join(result)
        else:
            # Convert to serializable format
            snippets = []
            for row in rows:
                snippet = dict(row)
                snippet['created_at'] = snippet['created_at'].isoformat()
                snippet['updated_at'] = snippet['updated_at'].isoformat()
                snippets.append(snippet)
            return json.dumps(snippets, indent=2)
    except Exception as e:
        return f"Export failed: {str(e)}"

@mcp.tool()
async def find_similar_snippets(snippet_id: int, limit: int = 5) -> List[Dict]:
    """Find snippets similar to a given snippet using vector similarity"""
    try:
        async with get_db() as conn:
            # Get the embedding of the reference snippet
            ref_row = await conn.fetchrow("""
                SELECT combined_embedding FROM legal_snippets WHERE id = $1
            """, snippet_id)
            
            if not ref_row:
                return [{"error": f"Snippet {snippet_id} not found"}]
            
            # Find similar snippets
            rows = await conn.fetch("""
                SELECT id, citation, key_language, tags, context, case_type,
                       1 - (combined_embedding <=> $1) as similarity_score
                FROM legal_snippets 
                WHERE id != $2
                ORDER BY combined_embedding <=> $1
                LIMIT $3
            """, ref_row['combined_embedding'], snippet_id, limit)
            
        results = []
        for row in rows:
            result = dict(row)
            result['similarity_score'] = float(result['similarity_score'])
            results.append(result)
            
        return results
    except Exception as e:
        return [{"error": f"Failed to find similar snippets: {str(e)}"}]

@mcp.resource("schema://legal_snippets_postgres")
def get_schema() -> str:
    """Provide information about the snippet data structure and capabilities"""
    return """Legal Snippets PostgreSQL Schema:
    
    Database Table: legal_snippets
    - id: Serial primary key
    - citation: Case citation (e.g., "Smith v. Jones, 123 F.3d 456 (2nd Cir. 2023)")
    - key_language: Important legal text from the case
    - tags: Array of categorization tags (e.g., ["contract", "damages", "breach"])
    - context: Additional notes and surrounding context
    - case_type: Type of case (civil, criminal, administrative, constitutional)
    - created_at: Timestamp of creation
    - updated_at: Timestamp of last update
    - citation_embedding: Vector embedding of citation (384 dimensions)
    - key_language_embedding: Vector embedding of key language (384 dimensions)
    - combined_embedding: Vector embedding of combined text (384 dimensions)
    
    Semantic Search Capabilities:
    - Vector similarity search using pgvector
    - Cosine similarity for finding related legal concepts
    - Configurable similarity thresholds
    - Tag-filtered semantic search
    
    Search Tools Available:
    - search_snippets: Traditional keyword/tag search
    - semantic_search: AI-powered similarity search
    - find_similar_snippets: Find snippets similar to a given one
    """

async def startup():
    """Initialize database and embedding model on startup"""
    await initialize_db()

async def shutdown():
    """Clean up database connections"""
    global _db_pool
    if _db_pool:
        await _db_pool.close()

if __name__ == "__main__":
    # Run the initialization
    asyncio.run(startup())
    
    # Start the MCP server
    try:
        mcp.run()
    finally:
        asyncio.run(shutdown())