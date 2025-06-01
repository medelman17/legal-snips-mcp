#!/usr/bin/env python3
"""
Setup script for PostgreSQL database with pgvector extension
"""
import asyncio
import asyncpg
import os
import sys
from pathlib import Path

DEFAULT_DATABASE_URL = "postgresql://postgres:password@localhost:5432/legal_snippets"

async def check_pgvector_availability():
    """Check if pgvector extension is available"""
    database_url = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
    
    try:
        conn = await asyncpg.connect(database_url)
        
        # Check if pgvector is available
        result = await conn.fetchval("""
            SELECT 1 FROM pg_available_extensions WHERE name = 'vector'
        """)
        
        await conn.close()
        return result is not None
    except Exception as e:
        print(f"❌ Could not connect to database: {e}")
        return False

async def setup_database():
    """Initialize the database with tables and indexes"""
    database_url = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
    
    try:
        print("🔗 Connecting to PostgreSQL...")
        conn = await asyncpg.connect(database_url)
        
        print("📦 Installing pgvector extension...")
        await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        
        print("🗄️  Creating legal_snippets table...")
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
        
        print("📊 Creating indexes...")
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_legal_snippets_tags 
            ON legal_snippets USING GIN(tags);
        """)
        
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_legal_snippets_case_type 
            ON legal_snippets(case_type);
        """)
        
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_legal_snippets_combined_embedding 
            ON legal_snippets USING ivfflat (combined_embedding vector_cosine_ops)
            WITH (lists = 100);
        """)
        
        print("✅ Database setup completed successfully!")
        
        # Show table info
        result = await conn.fetchval("""
            SELECT COUNT(*) FROM legal_snippets
        """)
        print(f"📈 Current snippets in database: {result}")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False

async def test_embeddings():
    """Test that sentence transformers work correctly"""
    try:
        print("🧠 Testing embedding generation...")
        from sentence_transformers import SentenceTransformer
        
        model = SentenceTransformer('all-MiniLM-L6-v2')
        test_text = "This is a test legal citation"
        embedding = model.encode(test_text)
        
        print(f"✅ Generated embedding with {len(embedding)} dimensions")
        return True
        
    except Exception as e:
        print(f"❌ Embedding test failed: {e}")
        print("💡 Try running: poetry install")
        return False

def create_env_file():
    """Create a .env file template"""
    env_content = f"""# PostgreSQL Database Configuration
DATABASE_URL={DEFAULT_DATABASE_URL}

# Optional: Customize embedding model
EMBEDDING_MODEL=all-MiniLM-L6-v2

# Optional: Set similarity threshold for searches
DEFAULT_SIMILARITY_THRESHOLD=0.7
"""
    
    env_path = Path(".env")
    if not env_path.exists():
        with open(env_path, "w") as f:
            f.write(env_content)
        print(f"📝 Created .env file at {env_path.absolute()}")
    else:
        print("📝 .env file already exists")

async def main():
    print("🚀 Legal Snippets PostgreSQL Setup")
    print("=" * 40)
    
    # Create .env file
    create_env_file()
    
    # Test embeddings
    if not await test_embeddings():
        print("\n❌ Setup failed - embedding test unsuccessful")
        return
    
    # Check pgvector
    if not await check_pgvector_availability():
        print("\n❌ pgvector extension not available!")
        print("💡 Install pgvector on your PostgreSQL server:")
        print("   - Ubuntu/Debian: apt install postgresql-15-pgvector")
        print("   - macOS: brew install pgvector")
        print("   - Docker: use postgres image with pgvector")
        return
    
    print("✅ pgvector extension is available")
    
    # Setup database
    if await setup_database():
        print("\n🎉 Setup completed successfully!")
        print("\nNext steps:")
        print("1. Update DATABASE_URL in .env if needed")
        print("2. Run: poetry run python legal_snippets_postgres_server.py")
        print("3. Configure Claude Desktop with the new server")
    else:
        print("\n❌ Setup failed - check database connection")

if __name__ == "__main__":
    asyncio.run(main())