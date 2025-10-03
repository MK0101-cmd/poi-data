# LibraryRAG - RAG Preparation Plan (Local PostgreSQL)

**Updated Plan**: Using Local PostgreSQL instead of Supabase

**Date:** October 3, 2025  
**Status:** Ready for Implementation

---

## Overview

This document provides the adjusted implementation plan for RAG operations using **local PostgreSQL** with pgvector extension instead of Supabase. The core architecture remains the same, with changes primarily in setup, deployment, and management approaches.

---

## Key Changes from Supabase Version

| Aspect | Supabase Version | Local PostgreSQL Version |
|--------|------------------|--------------------------|
| **Database** | Supabase Cloud | Local PostgreSQL 15+ |
| **Setup** | Click & configure | Manual installation |
| **API Layer** | Built-in REST API | Custom (FastAPI/Flask) |
| **Authentication** | Supabase Auth | Custom (JWT/OAuth) |
| **Hosting** | Managed cloud | Self-hosted |
| **Backups** | Automatic | Manual/scripted |
| **Monitoring** | Built-in dashboard | Custom (pgAdmin/Grafana) |
| **Cost** | $25/month+ | Hardware/hosting only |
| **Complexity** | Low | Medium-High |

---

## Table of Contents

1. [System Requirements](#system-requirements)
2. [PostgreSQL Setup](#postgresql-setup)
3. [Database Schema](#database-schema)
4. [Data Processing Pipeline](#data-processing-pipeline)
5. [API Development](#api-development)
6. [Query Implementation](#query-implementation)
7. [Implementation Roadmap](#implementation-roadmap)
8. [Cost Analysis](#cost-analysis)
9. [Deployment Options](#deployment-options)
10. [Monitoring & Maintenance](#monitoring--maintenance)

---

## 1. System Requirements

### Minimum Requirements
- **OS**: Ubuntu 20.04+, macOS 10.15+, Windows 10+ (with WSL2)
- **CPU**: 4 cores
- **RAM**: 8GB (16GB recommended)
- **Storage**: 50GB SSD (for database + indexes)
- **PostgreSQL**: Version 15 or higher
- **Python**: 3.10+

### Recommended Production Requirements
- **OS**: Ubuntu 22.04 LTS Server
- **CPU**: 8+ cores
- **RAM**: 32GB+
- **Storage**: 200GB+ SSD (NVMe preferred)
- **Network**: 1Gbps
- **Backup Storage**: 500GB+

---

## 2. PostgreSQL Setup

### 2.1 Installation

#### Ubuntu/Debian
```bash
# Update package list
sudo apt update

# Install PostgreSQL 15
sudo apt install -y postgresql-15 postgresql-contrib-15

# Install development headers (needed for extensions)
sudo apt install -y postgresql-server-dev-15

# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Check status
sudo systemctl status postgresql
```

#### macOS (using Homebrew)
```bash
# Install PostgreSQL
brew install postgresql@15

# Start PostgreSQL service
brew services start postgresql@15

# Check status
brew services list
```

#### Windows (using WSL2)
```bash
# Follow Ubuntu instructions in WSL2
# Or use Docker (see below)
```

#### Docker (Recommended for Development)
```bash
# Create docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  postgres:
    image: postgres:15
    container_name: poi-postgres
    environment:
      POSTGRES_USER: poi_user
      POSTGRES_PASSWORD: your_secure_password
      POSTGRES_DB: poi_rag
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d
    restart: unless-stopped

volumes:
  postgres_data:
EOF

# Start container
docker-compose up -d

# Check logs
docker-compose logs -f postgres
```

### 2.2 Initial Configuration

#### Create Database and User
```bash
# Switch to postgres user
sudo -u postgres psql

# Or if using Docker
docker exec -it poi-postgres psql -U poi_user -d postgres
```

```sql
-- Create database
CREATE DATABASE poi_rag;

-- Create user (if not using Docker)
CREATE USER poi_user WITH PASSWORD 'your_secure_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE poi_rag TO poi_user;

-- Connect to database
\c poi_rag

-- Grant schema privileges
GRANT ALL ON SCHEMA public TO poi_user;

-- Exit
\q
```

### 2.3 Install pgvector Extension

```bash
# Clone pgvector repository
cd /tmp
git clone https://github.com/pgvector/pgvector.git
cd pgvector

# Build and install
make
sudo make install

# Or using package manager (Ubuntu 22.04+)
sudo apt install postgresql-15-pgvector
```

#### Enable Extension in Database
```sql
-- Connect to database
psql -U poi_user -d poi_rag

-- Create extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS btree_gin;

-- Verify installation
SELECT * FROM pg_extension;
```

### 2.4 PostgreSQL Configuration

#### Edit postgresql.conf
```bash
# Find config file location
sudo -u postgres psql -c "SHOW config_file"

# Edit configuration
sudo nano /etc/postgresql/15/main/postgresql.conf
```

#### Recommended Settings
```conf
# Memory Settings
shared_buffers = 4GB                    # 25% of RAM
effective_cache_size = 12GB             # 75% of RAM
maintenance_work_mem = 1GB
work_mem = 64MB

# Connection Settings
max_connections = 100
shared_preload_libraries = 'pg_stat_statements'

# Performance Settings
random_page_cost = 1.1                  # For SSD
effective_io_concurrency = 200          # For SSD
max_worker_processes = 8
max_parallel_workers_per_gather = 4
max_parallel_workers = 8
max_parallel_maintenance_workers = 4

# WAL Settings (for better performance)
wal_buffers = 16MB
checkpoint_completion_target = 0.9
checkpoint_timeout = 15min

# Logging
log_min_duration_statement = 1000       # Log slow queries (>1s)
log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '
```

#### Edit pg_hba.conf (Access Control)
```bash
sudo nano /etc/postgresql/15/main/pg_hba.conf
```

```conf
# Allow local connections
local   all             all                                     peer
host    all             all             127.0.0.1/32            scram-sha-256
host    all             all             ::1/128                 scram-sha-256

# For Docker or remote access (use with caution)
# host    all             all             0.0.0.0/0               scram-sha-256
```

#### Restart PostgreSQL
```bash
sudo systemctl restart postgresql

# Or for Docker
docker-compose restart postgres
```

---

## 3. Database Schema

### 3.1 Create Tables

Save this as `schema.sql`:

```sql
-- ============================================================================
-- DOCUMENTS TABLE
-- ============================================================================
CREATE TABLE documents (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  
  -- Content
  file_path TEXT NOT NULL UNIQUE,
  file_name TEXT NOT NULL,
  content TEXT NOT NULL,
  content_type TEXT NOT NULL,
  
  -- Metadata
  category TEXT NOT NULL,
  subcategory TEXT NOT NULL,
  content_subtype TEXT,
  
  -- Hierarchy
  parent_id UUID REFERENCES documents(id),
  hierarchy_path TEXT[],
  depth INTEGER NOT NULL DEFAULT 0,
  
  -- Timestamps
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  
  -- Constraints
  CONSTRAINT valid_category CHECK (category IN ('Activities', 'Trainings'))
);

-- Indexes
CREATE INDEX idx_documents_category ON documents(category);
CREATE INDEX idx_documents_subcategory ON documents(subcategory);
CREATE INDEX idx_documents_content_subtype ON documents(content_subtype);
CREATE INDEX idx_documents_hierarchy_path ON documents USING GIN(hierarchy_path);
CREATE INDEX idx_documents_parent_id ON documents(parent_id);
CREATE INDEX idx_documents_file_path ON documents(file_path);

-- Full-text search index
CREATE INDEX idx_documents_content_fts ON documents USING GIN(to_tsvector('english', content));

-- ============================================================================
-- DOCUMENT_CHUNKS TABLE
-- ============================================================================
CREATE TABLE document_chunks (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  
  -- Document reference
  document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  
  -- Chunk content
  chunk_text TEXT NOT NULL,
  chunk_index INTEGER NOT NULL,
  chunk_tokens INTEGER,
  
  -- Chunk metadata
  section_title TEXT,
  section_type TEXT,
  
  -- Vector embedding
  embedding VECTOR(1536),
  
  -- Timestamps
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  
  CONSTRAINT unique_document_chunk UNIQUE(document_id, chunk_index)
);

-- Indexes
CREATE INDEX idx_chunks_document_id ON document_chunks(document_id);
CREATE INDEX idx_chunks_section_type ON document_chunks(section_type);
CREATE INDEX idx_chunks_section_title ON document_chunks(section_title);

-- Vector index (IVFFlat for approximate nearest neighbor search)
CREATE INDEX idx_chunks_embedding ON document_chunks 
  USING ivfflat (embedding vector_cosine_ops) 
  WITH (lists = 100);

-- Full-text search index on chunks
CREATE INDEX idx_chunks_text_fts ON document_chunks 
  USING GIN(to_tsvector('english', chunk_text));

-- ============================================================================
-- CROSS_REFERENCES TABLE
-- ============================================================================
CREATE TABLE cross_references (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  
  -- Relationship
  source_document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  target_document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  
  -- Relationship metadata
  reference_type TEXT NOT NULL,
  relationship_strength FLOAT DEFAULT 1.0,
  context TEXT,
  
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  
  CONSTRAINT unique_cross_reference UNIQUE(source_document_id, target_document_id, reference_type)
);

-- Indexes
CREATE INDEX idx_cross_refs_source ON cross_references(source_document_id);
CREATE INDEX idx_cross_refs_target ON cross_references(target_document_id);
CREATE INDEX idx_cross_refs_type ON cross_references(reference_type);

-- ============================================================================
-- TAGS TABLE
-- ============================================================================
CREATE TABLE tags (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  tag_name TEXT NOT NULL UNIQUE,
  tag_category TEXT NOT NULL,
  description TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_tags_category ON tags(tag_category);
CREATE INDEX idx_tags_name ON tags(tag_name);

-- ============================================================================
-- DOCUMENT_TAGS TABLE (Many-to-Many)
-- ============================================================================
CREATE TABLE document_tags (
  document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  tag_id UUID NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
  relevance_score FLOAT DEFAULT 1.0,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  
  PRIMARY KEY (document_id, tag_id)
);

-- Indexes
CREATE INDEX idx_document_tags_document ON document_tags(document_id);
CREATE INDEX idx_document_tags_tag ON document_tags(tag_id);

-- ============================================================================
-- CARD_METADATA TABLE
-- ============================================================================
CREATE TABLE card_metadata (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  
  -- Card identification
  card_type TEXT NOT NULL,
  deck_name TEXT NOT NULL,
  card_number INTEGER,
  card_name TEXT,
  
  -- Series/Category
  series_name TEXT,
  series_index INTEGER,
  
  -- Associated content
  document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
  image_url TEXT,
  
  -- Card metadata
  themes TEXT[],
  emotions TEXT[],
  use_cases TEXT[],
  
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  
  CONSTRAINT unique_card UNIQUE(deck_name, card_type, card_number)
);

-- Indexes
CREATE INDEX idx_card_metadata_deck ON card_metadata(deck_name);
CREATE INDEX idx_card_metadata_series ON card_metadata(series_name);
CREATE INDEX idx_card_metadata_document ON card_metadata(document_id);
CREATE INDEX idx_card_metadata_card_number ON card_metadata(card_number);

-- ============================================================================
-- FUNCTIONS
-- ============================================================================

-- Function: Hybrid Search (Vector + Keyword)
CREATE OR REPLACE FUNCTION hybrid_search(
  query_embedding VECTOR(1536),
  query_text TEXT,
  match_threshold FLOAT DEFAULT 0.7,
  match_count INT DEFAULT 10,
  vector_weight FLOAT DEFAULT 0.7,
  keyword_weight FLOAT DEFAULT 0.3
)
RETURNS TABLE (
  chunk_id UUID,
  document_id UUID,
  chunk_text TEXT,
  section_title TEXT,
  category TEXT,
  subcategory TEXT,
  similarity_score FLOAT,
  combined_score FLOAT
) 
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  WITH vector_search AS (
    SELECT 
      dc.id,
      dc.document_id,
      dc.chunk_text,
      dc.section_title,
      d.category,
      d.subcategory,
      1 - (dc.embedding <=> query_embedding) AS vector_score
    FROM document_chunks dc
    JOIN documents d ON dc.document_id = d.id
    WHERE 1 - (dc.embedding <=> query_embedding) > match_threshold
    ORDER BY dc.embedding <=> query_embedding
    LIMIT match_count * 2
  ),
  keyword_search AS (
    SELECT 
      dc.id,
      ts_rank(to_tsvector('english', dc.chunk_text), plainto_tsquery('english', query_text)) AS keyword_score
    FROM document_chunks dc
    WHERE to_tsvector('english', dc.chunk_text) @@ plainto_tsquery('english', query_text)
  )
  SELECT 
    vs.id AS chunk_id,
    vs.document_id,
    vs.chunk_text,
    vs.section_title,
    vs.category,
    vs.subcategory,
    vs.vector_score AS similarity_score,
    (vs.vector_score * vector_weight + COALESCE(ks.keyword_score, 0) * keyword_weight) AS combined_score
  FROM vector_search vs
  LEFT JOIN keyword_search ks ON vs.id = ks.id
  ORDER BY combined_score DESC
  LIMIT match_count;
END;
$$;

-- Function: Search with Filters
CREATE OR REPLACE FUNCTION search_with_filters(
  query_embedding VECTOR(1536),
  filter_category TEXT DEFAULT NULL,
  filter_subcategory TEXT DEFAULT NULL,
  filter_tags TEXT[] DEFAULT NULL,
  match_threshold FLOAT DEFAULT 0.7,
  match_count INT DEFAULT 10
)
RETURNS TABLE (
  chunk_id UUID,
  document_id UUID,
  chunk_text TEXT,
  section_title TEXT,
  category TEXT,
  subcategory TEXT,
  similarity_score FLOAT,
  tags TEXT[]
) 
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT 
    dc.id AS chunk_id,
    dc.document_id,
    dc.chunk_text,
    dc.section_title,
    d.category,
    d.subcategory,
    1 - (dc.embedding <=> query_embedding) AS similarity_score,
    ARRAY_AGG(DISTINCT t.tag_name) AS tags
  FROM document_chunks dc
  JOIN documents d ON dc.document_id = d.id
  LEFT JOIN document_tags dt ON d.id = dt.document_id
  LEFT JOIN tags t ON dt.tag_id = t.id
  WHERE 
    1 - (dc.embedding <=> query_embedding) > match_threshold
    AND (filter_category IS NULL OR d.category = filter_category)
    AND (filter_subcategory IS NULL OR d.subcategory = filter_subcategory)
    AND (
      filter_tags IS NULL 
      OR EXISTS (
        SELECT 1 FROM document_tags dt2
        JOIN tags t2 ON dt2.tag_id = t2.id
        WHERE dt2.document_id = d.id AND t2.tag_name = ANY(filter_tags)
      )
    )
  GROUP BY dc.id, dc.document_id, dc.chunk_text, dc.section_title, d.category, d.subcategory, dc.embedding
  ORDER BY dc.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

-- Function: Get Related Documents
CREATE OR REPLACE FUNCTION get_related_documents(
  doc_id UUID,
  max_results INT DEFAULT 5
)
RETURNS TABLE (
  related_doc_id UUID,
  related_doc_path TEXT,
  related_doc_title TEXT,
  reference_type TEXT,
  relationship_strength FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT 
    cr.target_document_id AS related_doc_id,
    d.file_path AS related_doc_path,
    d.file_name AS related_doc_title,
    cr.reference_type,
    cr.relationship_strength
  FROM cross_references cr
  JOIN documents d ON cr.target_document_id = d.id
  WHERE cr.source_document_id = doc_id
  ORDER BY cr.relationship_strength DESC, cr.reference_type
  LIMIT max_results;
END;
$$;

-- Function: Update timestamp trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for documents table
CREATE TRIGGER update_documents_updated_at 
  BEFORE UPDATE ON documents 
  FOR EACH ROW 
  EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- VIEWS (Optional - for easier querying)
-- ============================================================================

-- View: Document with Tags
CREATE VIEW documents_with_tags AS
SELECT 
  d.*,
  ARRAY_AGG(DISTINCT t.tag_name) FILTER (WHERE t.tag_name IS NOT NULL) AS tags
FROM documents d
LEFT JOIN document_tags dt ON d.id = dt.document_id
LEFT JOIN tags t ON dt.tag_id = t.id
GROUP BY d.id;

-- View: Chunks with Document Info
CREATE VIEW chunks_with_documents AS
SELECT 
  dc.*,
  d.file_path,
  d.file_name,
  d.category,
  d.subcategory,
  d.content_subtype,
  d.hierarchy_path
FROM document_chunks dc
JOIN documents d ON dc.document_id = d.id;

-- ============================================================================
-- MAINTENANCE FUNCTIONS
-- ============================================================================

-- Function: Reindex all indexes
CREATE OR REPLACE FUNCTION reindex_all()
RETURNS VOID AS $$
BEGIN
  REINDEX TABLE documents;
  REINDEX TABLE document_chunks;
  REINDEX TABLE cross_references;
  REINDEX TABLE tags;
  REINDEX TABLE document_tags;
  REINDEX TABLE card_metadata;
  RAISE NOTICE 'All indexes reindexed successfully';
END;
$$ LANGUAGE plpgsql;

-- Function: Vacuum and analyze all tables
CREATE OR REPLACE FUNCTION vacuum_analyze_all()
RETURNS VOID AS $$
BEGIN
  VACUUM ANALYZE documents;
  VACUUM ANALYZE document_chunks;
  VACUUM ANALYZE cross_references;
  VACUUM ANALYZE tags;
  VACUUM ANALYZE document_tags;
  VACUUM ANALYZE card_metadata;
  RAISE NOTICE 'All tables vacuumed and analyzed successfully';
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- PERMISSIONS
-- ============================================================================

-- Grant permissions to poi_user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO poi_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO poi_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO poi_user;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO poi_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO poi_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT EXECUTE ON FUNCTIONS TO poi_user;

-- ============================================================================
-- STATISTICS (for query optimization)
-- ============================================================================

-- Update statistics
ANALYZE documents;
ANALYZE document_chunks;
ANALYZE cross_references;
ANALYZE tags;
ANALYZE document_tags;
ANALYZE card_metadata;

-- ============================================================================
-- COMMENTS (Documentation)
-- ============================================================================

COMMENT ON TABLE documents IS 'Primary content storage with metadata';
COMMENT ON TABLE document_chunks IS 'Chunked content with vector embeddings';
COMMENT ON TABLE cross_references IS 'Document relationships and connections';
COMMENT ON TABLE tags IS 'Content categorization tags';
COMMENT ON TABLE document_tags IS 'Many-to-many relationship between documents and tags';
COMMENT ON TABLE card_metadata IS 'Metadata for photo and reflection cards';

COMMENT ON FUNCTION hybrid_search IS 'Search combining vector similarity and keyword matching';
COMMENT ON FUNCTION search_with_filters IS 'Vector search with category and tag filters';
COMMENT ON FUNCTION get_related_documents IS 'Retrieve related documents via cross-references';
```

### 3.2 Load Schema

```bash
# Load schema into database
psql -U poi_user -d poi_rag -f schema.sql

# Or for Docker
docker exec -i poi-postgres psql -U poi_user -d poi_rag < schema.sql

# Verify tables created
psql -U poi_user -d poi_rag -c "\dt"

# Verify functions created
psql -U poi_user -d poi_rag -c "\df"
```

---

## 4. Data Processing Pipeline

The data processing pipeline remains largely the same as the Supabase version, but with direct PostgreSQL connections.

### 4.1 Connection Setup

```python
# requirements.txt
psycopg2-binary==2.9.9  # PostgreSQL adapter
pgvector==0.2.3          # pgvector Python client
openai==1.3.0
python-dotenv==1.0.0
pandas==2.1.0
numpy==1.24.0
markdown==3.5.0
beautifulsoup4==4.12.0
```

### 4.2 Database Connection

```python
# database.py
import psycopg2
from psycopg2.extras import execute_values, RealDictCursor
from pgvector.psycopg2 import register_vector
from contextlib import contextmanager
import os
from dotenv import load_dotenv

load_dotenv()

class Database:
    def __init__(self):
        self.conn_params = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'poi_rag'),
            'user': os.getenv('DB_USER', 'poi_user'),
            'password': os.getenv('DB_PASSWORD'),
        }
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = psycopg2.connect(**self.conn_params)
        register_vector(conn)  # Register pgvector type
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    @contextmanager
    def get_cursor(self, dict_cursor=True):
        """Context manager for database cursors"""
        with self.get_connection() as conn:
            cursor_factory = RealDictCursor if dict_cursor else None
            cursor = conn.cursor(cursor_factory=cursor_factory)
            try:
                yield cursor
            finally:
                cursor.close()
    
    def insert_document(self, doc_data):
        """Insert a single document"""
        with self.get_cursor() as cur:
            cur.execute("""
                INSERT INTO documents 
                (file_path, file_name, content, content_type, category, subcategory, 
                 content_subtype, hierarchy_path, depth)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                doc_data['file_path'],
                doc_data['file_name'],
                doc_data['content'],
                doc_data['content_type'],
                doc_data['category'],
                doc_data['subcategory'],
                doc_data.get('content_subtype'),
                doc_data['hierarchy_path'],
                doc_data['depth']
            ))
            return cur.fetchone()['id']
    
    def insert_chunks_batch(self, chunks):
        """Insert multiple chunks with embeddings"""
        with self.get_cursor() as cur:
            execute_values(cur, """
                INSERT INTO document_chunks 
                (document_id, chunk_text, chunk_index, chunk_tokens, 
                 section_title, section_type, embedding)
                VALUES %s
            """, [
                (
                    chunk['document_id'],
                    chunk['chunk_text'],
                    chunk['chunk_index'],
                    chunk.get('chunk_tokens'),
                    chunk.get('section_title'),
                    chunk.get('section_type'),
                    chunk['embedding']
                )
                for chunk in chunks
            ])
    
    def search_vector(self, query_embedding, limit=10, threshold=0.7):
        """Vector similarity search"""
        with self.get_cursor() as cur:
            cur.execute("""
                SELECT 
                    dc.id as chunk_id,
                    dc.document_id,
                    dc.chunk_text,
                    dc.section_title,
                    d.category,
                    d.subcategory,
                    1 - (dc.embedding <=> %s) as similarity_score
                FROM document_chunks dc
                JOIN documents d ON dc.document_id = d.id
                WHERE 1 - (dc.embedding <=> %s) > %s
                ORDER BY dc.embedding <=> %s
                LIMIT %s
            """, (query_embedding, query_embedding, threshold, query_embedding, limit))
            return cur.fetchall()
```

### 4.3 Complete Pipeline Implementation

```python
# pipeline.py
import os
from pathlib import Path
from typing import List, Dict
from dotenv import load_dotenv
import openai
from scripts.database import Database

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

class LibraryRAGPipeline:
    def __init__(self, root_path: str = "LibraryRAG"):
        self.root_path = Path(root_path)
        self.db = Database()
        
    def scan_files(self) -> List[Dict]:
        """Scan all markdown files"""
        files = []
        for file_path in self.root_path.rglob("*.md"):
            rel_path = str(file_path.relative_to(self.root_path))
            parts = rel_path.split(os.sep)
            
            files.append({
                'file_path': str(file_path),
                'file_name': file_path.name,
                'category': parts[0] if len(parts) > 0 else 'Unknown',
                'subcategory': parts[1] if len(parts) > 1 else 'Unknown',
                'hierarchy_path': parts,
                'depth': len(parts)
            })
        
        return files
    
    def read_file(self, file_path: str) -> str:
        """Read file content"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def chunk_content(self, content: str, file_metadata: Dict) -> List[Dict]:
        """Simple section-based chunking"""
        chunks = []
        sections = content.split('\n## ')
        
        for i, section in enumerate(sections):
            if not section.strip():
                continue
            
            lines = section.split('\n')
            section_title = lines[0].replace('#', '').strip()
            section_text = '\n'.join(lines[1:])
            
            if len(section_text.strip()) < 50:
                continue
            
            chunks.append({
                'chunk_text': section_text,
                'chunk_index': i,
                'section_title': section_title,
                'section_type': self._classify_section(section_title),
                'metadata': file_metadata
            })
        
        return chunks
    
    def _classify_section(self, title: str) -> str:
        """Classify section type"""
        title_lower = title.lower()
        
        if 'story' in title_lower or 'tale' in title_lower:
            return 'story'
        elif 'question' in title_lower:
            return 'reflection-question'
        elif 'quote' in title_lower:
            return 'quote'
        elif 'application' in title_lower or 'training' in title_lower:
            return 'training-application'
        elif 'overview' in title_lower or 'introduction' in title_lower:
            return 'overview'
        else:
            return 'general'
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using OpenAI"""
        response = openai.embeddings.create(
            input=text,
            model="text-embedding-3-small"
        )
        return response.data[0].embedding
    
    def process_file(self, file_metadata: Dict):
        """Process a single file"""
        print(f"Processing: {file_metadata['file_path']}")
        
        # Read content
        content = self.read_file(file_metadata['file_path'])
        
        # Insert document
        document_id = self.db.insert_document({
            **file_metadata,
            'content': content,
            'content_type': 'markdown'
        })
        
        # Chunk content
        chunks = self.chunk_content(content, file_metadata)
        
        # Prepare chunks with embeddings
        chunks_with_embeddings = []
        for chunk in chunks:
            embedding = self.generate_embedding(chunk['chunk_text'])
            chunks_with_embeddings.append({
                'document_id': document_id,
                'chunk_text': chunk['chunk_text'],
                'chunk_index': chunk['chunk_index'],
                'section_title': chunk['section_title'],
                'section_type': chunk['section_type'],
                'embedding': embedding,
                'chunk_tokens': len(chunk['chunk_text'].split()) * 1.3  # Rough estimate
            })
        
        # Batch insert chunks
        if chunks_with_embeddings:
            self.db.insert_chunks_batch(chunks_with_embeddings)
        
        print(f"  ✓ Inserted {len(chunks_with_embeddings)} chunks")
        
    def run(self, limit: int = None):
        """Run the pipeline"""
        print("🚀 Starting LibraryRAG pipeline...")
        
        # Scan files
        files = self.scan_files()
        print(f"📁 Found {len(files)} markdown files")
        
        # Process files
        for i, file_metadata in enumerate(files[:limit] if limit else files):
            try:
                self.process_file(file_metadata)
            except Exception as e:
                print(f"  ✗ Error: {e}")
        
        print("✅ Pipeline complete!")

if __name__ == "__main__":
    # Create .env file first
    pipeline = LibraryRAGPipeline()
    
    # Start with first 5 files for testing
    pipeline.run(limit=5)
    
    # Remove limit to process all files
    # pipeline.run()
```

---

## 5. API Development

### 5.1 FastAPI Implementation

```python
# requirements_api.txt
fastapi==0.104.0
uvicorn[standard]==0.24.0
pydantic==2.4.0
python-jose[cryptography]==3.3.0  # For JWT
passlib[bcrypt]==1.7.4  # For password hashing
python-multipart==0.0.6
```

### 5.2 API Server

```python
# api/main.py
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import openai
import os
from dotenv import load_dotenv

from scripts.database import Database

load_dotenv()

app = FastAPI(
    title="LibraryRAG API",
    description="RAG API for Points of You® Library",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize
db = Database()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Models
class SearchRequest(BaseModel):
    query: str
    limit: int = 10
    threshold: float = 0.7
    category: Optional[str] = None
    subcategory: Optional[str] = None
    tags: Optional[List[str]] = None

class SearchResult(BaseModel):
    chunk_id: str
    document_id: str
    chunk_text: str
    section_title: Optional[str]
    category: str
    subcategory: str
    similarity_score: float

class HealthResponse(BaseModel):
    status: str
    database: str
    version: str

# Routes
@app.get("/", response_model=HealthResponse)
async def root():
    """Health check endpoint"""
    try:
        with db.get_cursor() as cur:
            cur.execute("SELECT 1")
            db_status = "connected"
    except:
        db_status = "disconnected"
    
    return {
        "status": "ok",
        "database": db_status,
        "version": "1.0.0"
    }

@app.post("/api/search", response_model=List[SearchResult])
async def search(request: SearchRequest):
    """Semantic search endpoint"""
    try:
        # Generate query embedding
        response = openai.embeddings.create(
            input=request.query,
            model="text-embedding-3-small"
        )
        query_embedding = response.data[0].embedding
        
        # Search database
        results = db.search_vector(
            query_embedding=query_embedding,
            limit=request.limit,
            threshold=request.threshold
        )
        
        return results
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search error: {str(e)}"
        )

@app.get("/api/documents/{document_id}")
async def get_document(document_id: str):
    """Get document by ID"""
    try:
        with db.get_cursor() as cur:
            cur.execute("""
                SELECT * FROM documents WHERE id = %s
            """, (document_id,))
            document = cur.fetchone()
            
            if not document:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Document not found"
                )
            
            return document
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

@app.get("/api/documents/{document_id}/chunks")
async def get_document_chunks(document_id: str):
    """Get all chunks for a document"""
    try:
        with db.get_cursor() as cur:
            cur.execute("""
                SELECT * FROM document_chunks 
                WHERE document_id = %s 
                ORDER BY chunk_index
            """, (document_id,))
            chunks = cur.fetchall()
            
            return chunks
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

@app.get("/api/related/{document_id}")
async def get_related(document_id: str, limit: int = 5):
    """Get related documents"""
    try:
        with db.get_cursor() as cur:
            cur.execute("""
                SELECT * FROM get_related_documents(%s, %s)
            """, (document_id, limit))
            related = cur.fetchall()
            
            return related
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

@app.get("/api/stats")
async def get_stats():
    """Get database statistics"""
    try:
        with db.get_cursor() as cur:
            # Document count
            cur.execute("SELECT COUNT(*) as count FROM documents")
            doc_count = cur.fetchone()['count']
            
            # Chunk count
            cur.execute("SELECT COUNT(*) as count FROM document_chunks")
            chunk_count = cur.fetchone()['count']
            
            # Tag count
            cur.execute("SELECT COUNT(*) as count FROM tags")
            tag_count = cur.fetchone()['count']
            
            # Database size
            cur.execute("""
                SELECT pg_size_pretty(pg_database_size(current_database())) as size
            """)
            db_size = cur.fetchone()['size']
            
            return {
                "documents": doc_count,
                "chunks": chunk_count,
                "tags": tag_count,
                "database_size": db_size
            }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 5.3 Run API Server

```bash
# Install dependencies
pip install -r requirements_api.txt

# Run development server
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Or production with gunicorn
gunicorn api.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### 5.4 Test API

```bash
# Health check
curl http://localhost:8000/

# Search
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How to facilitate conflict resolution?",
    "limit": 5
  }'

# Stats
curl http://localhost:8000/api/stats
```

---

## 6. Query Implementation

Same search functions as Supabase version, but using psycopg2:

```python
# search.py
import os
from dotenv import load_dotenv
import openai
from scripts.database import Database

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
db = Database()

def search(query: str, match_count: int = 5):
    """Search the LibraryRAG"""
    
    print(f"🔍 Searching for: {query}")
    
    # Generate query embedding
    response = openai.embeddings.create(
        input=query,
        model="text-embedding-3-small"
    )
    query_embedding = response.data[0].embedding
    
    # Search database
    results = db.search_vector(
        query_embedding=query_embedding,
        limit=match_count
    )
    
    # Display results
    print(f"\n📊 Found {len(results)} results:\n")
    
    for i, match in enumerate(results, 1):
        print(f"{i}. [{match['category']}/{match['subcategory']}] {match['section_title']}")
        print(f"   Similarity: {match['similarity_score']:.3f}")
        print(f"   Preview: {match['chunk_text'][:150]}...")
        print()
    
    return results

if __name__ == "__main__":
    search("How to facilitate a team dialogue about conflict?")
    search("Stories about personal transformation")
    search("Reflection questions for leadership")
```

---

## 7. Implementation Roadmap

### Adjusted Timeline (10 weeks → 11-12 weeks)

Additional time needed for:
- Manual database setup and configuration
- API development
- Authentication implementation
- Monitoring setup

### Phase 1: Foundation (Weeks 1-3)
**Week 1: PostgreSQL Setup**
- [ ] Install PostgreSQL 15
- [ ] Install pgvector extension
- [ ] Configure PostgreSQL
- [ ] Create database and user
- [ ] Load schema
- [ ] Test connections

**Week 2: Development Environment**
- [ ] Set up Python environment
- [ ] Install dependencies
- [ ] Create database connection module
- [ ] Write data pipeline
- [ ] Unit tests

**Week 3: API Foundation**
- [ ] Set up FastAPI
- [ ] Create basic endpoints
- [ ] Implement authentication (optional)
- [ ] API documentation
- [ ] API tests

### Phase 2: Data Ingestion (Weeks 4-5)
Same as Supabase version

### Phase 3: RAG System (Weeks 6-7)
Same as Supabase version

### Phase 4: Testing (Weeks 8-9)
Same as Supabase version

### Phase 5: Deployment (Weeks 10-12)
**Week 10: Production Setup**
- [ ] Production database setup
- [ ] Server configuration
- [ ] Security hardening
- [ ] SSL certificates

**Week 11: Deployment**
- [ ] Deploy database
- [ ] Deploy API
- [ ] Set up monitoring
- [ ] Configure backups

**Week 12: Documentation & Training**
- [ ] Complete documentation
- [ ] Training materials
- [ ] Handoff to team

---

## 8. Cost Analysis

### Hardware/Infrastructure Costs

#### Development Environment (Local)
- **Hardware**: Existing machines ($0)
- **PostgreSQL**: Free open-source ($0)
- **Python/FastAPI**: Free open-source ($0)
- **Total**: **$0**

#### Production Environment

**Option A: Self-Hosted (VPS)**
| Item | Provider | Specs | Monthly Cost |
|------|----------|-------|--------------|
| VPS Server | DigitalOcean/Linode | 8 vCPU, 32GB RAM, 200GB SSD | $120 |
| Backup Storage | Any S3-compatible | 500GB | $10 |
| SSL Certificate | Let's Encrypt | Free | $0 |
| **Total** | | | **$130/month** |

**Option B: Self-Hosted (Dedicated)**
| Item | Cost |
|------|------|
| Server Hardware | $2,000-5,000 (one-time) |
| Hosting/Colocation | $100-300/month |
| Backup Storage | $20-50/month |
| **Total Initial** | **$2,000-5,000** |
| **Total Monthly** | **$120-350/month** |

**Option C: Managed PostgreSQL**
| Provider | Specs | Monthly Cost |
|----------|-------|--------------|
| AWS RDS | db.t3.xlarge (4vCPU, 16GB) | $200 |
| DigitalOcean Managed | 4GB RAM, 2vCPU | $60 |
| Aiven | 8GB RAM, 2vCPU | $120 |

### Total Cost Comparison

| Approach | Initial | Monthly | Notes |
|----------|---------|---------|-------|
| **Supabase** | $25,000-50,000 | $185-345 | Easiest, managed |
| **Local PostgreSQL (VPS)** | $25,000-50,000 | $250-370 | More control, same dev cost |
| **Local PostgreSQL (Dedicated)** | $27,000-55,000 | $240-470 | Most control, higher initial |

**Net Savings vs Supabase**: Minimal (~$0-50/month)  
**Trade-off**: More complexity, management overhead, longer setup time

### OpenAI API Costs (Same for all options)
- Initial embedding generation: $150-300 (one-time)
- Query embeddings: $100-200/month
- Total API: ~$150-300 first month, ~$100-200 ongoing

---

## 9. Deployment Options

### Option A: Docker Deployment (Recommended)

```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:15
    container_name: poi-postgres
    environment:
      POSTGRES_USER: poi_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: poi_rag
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    restart: unless-stopped
    command: >
      postgres
      -c shared_buffers=4GB
      -c effective_cache_size=12GB
      -c maintenance_work_mem=1GB
      -c max_connections=100
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U poi_user"]
      interval: 10s
      timeout: 5s
      retries: 5

  api:
    build: .
    container_name: poi-api
    environment:
      DB_HOST: postgres
      DB_PORT: 5432
      DB_NAME: poi_rag
      DB_USER: poi_user
      DB_PASSWORD: ${DB_PASSWORD}
      OPENAI_API_KEY: ${OPENAI_API_KEY}
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
    restart: unless-stopped
    command: uvicorn api.main:app --host 0.0.0.0 --port 8000

  nginx:
    image: nginx:alpine
    container_name: poi-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - api
    restart: unless-stopped

  pgadmin:
    image: dpage/pgadmin4
    container_name: poi-pgadmin
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@example.com
      PGADMIN_DEFAULT_PASSWORD: ${PGADMIN_PASSWORD}
    ports:
      - "5050:80"
    depends_on:
      - postgres
    restart: unless-stopped

volumes:
  postgres_data:
```

### Option B: System Service Deployment

```ini
# /etc/systemd/system/poi-api.service
[Unit]
Description=LibraryRAG API Service
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=simple
User=poi_user
WorkingDirectory=/opt/poi-rag
Environment="PATH=/opt/poi-rag/venv/bin"
Environment="DB_HOST=localhost"
Environment="DB_PORT=5432"
Environment="DB_NAME=poi_rag"
Environment="DB_USER=poi_user"
EnvironmentFile=/opt/poi-rag/.env
ExecStart=/opt/poi-rag/venv/bin/gunicorn api.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --access-logfile /var/log/poi-api/access.log \
    --error-logfile /var/log/poi-api/error.log
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable poi-api
sudo systemctl start poi-api
sudo systemctl status poi-api
```

---

## 10. Monitoring & Maintenance

### 10.1 Monitoring Tools

#### pgAdmin (Recommended)
```bash
# Install pgAdmin
pip install pgadmin4

# Or use Docker (see docker-compose.yml above)
```

#### Grafana + Prometheus
```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"

  postgres-exporter:
    image: prometheuscommunity/postgres-exporter
    environment:
      DATA_SOURCE_NAME: "postgresql://poi_user:${DB_PASSWORD}@postgres:5432/poi_rag?sslmode=disable"
    ports:
      - "9187:9187"
    depends_on:
      - postgres

  grafana:
    image: grafana/grafana
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards
    ports:
      - "3000:3000"
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD}

volumes:
  prometheus_data:
  grafana_data:
```

### 10.2 Backup Strategy

```bash
# backup.sh
#!/bin/bash

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"
DB_NAME="poi_rag"
DB_USER="poi_user"

# Create backup
pg_dump -U $DB_USER -d $DB_NAME -F c -f $BACKUP_DIR/poi_rag_$DATE.backup

# Compress
gzip $BACKUP_DIR/poi_rag_$DATE.backup

# Upload to S3 (optional)
# aws s3 cp $BACKUP_DIR/poi_rag_$DATE.backup.gz s3://your-bucket/backups/

# Delete old backups (keep last 7 days)
find $BACKUP_DIR -name "poi_rag_*.backup.gz" -mtime +7 -delete

echo "Backup completed: poi_rag_$DATE.backup.gz"
```

```bash
# Set up cron job for daily backups
crontab -e

# Add line (daily at 2 AM)
0 2 * * * /opt/poi-rag/backup.sh >> /var/log/poi-backup.log 2>&1
```

### 10.3 Maintenance Tasks

```bash
# maintenance.sh
#!/bin/bash

# Vacuum and analyze
psql -U poi_user -d poi_rag -c "SELECT vacuum_analyze_all();"

# Reindex
psql -U poi_user -d poi_rag -c "SELECT reindex_all();"

# Update statistics
psql -U poi_user -d poi_rag -c "ANALYZE;"

echo "Maintenance completed: $(date)"
```

```bash
# Weekly maintenance (Sundays at 3 AM)
0 3 * * 0 /opt/poi-rag/maintenance.sh >> /var/log/poi-maintenance.log 2>&1
```

---

## 11. Migration from Supabase (If Needed)

If you already have data in Supabase and want to migrate:

```bash
# Export from Supabase
pg_dump "postgresql://user:pass@db.supabase.co:5432/postgres" \
  -F c -f supabase_export.backup

# Import to local PostgreSQL
pg_restore -U poi_user -d poi_rag supabase_export.backup
```

---

## Summary: Local PostgreSQL vs Supabase

### Advantages of Local PostgreSQL
✅ **Full Control**: Complete control over configuration and optimization  
✅ **No Vendor Lock-in**: Can move anywhere  
✅ **Data Privacy**: Data stays on your infrastructure  
✅ **Potentially Lower Cost**: No cloud fees (but see trade-offs)  
✅ **Customization**: Can install any extensions, customize settings  

### Disadvantages of Local PostgreSQL
❌ **More Complexity**: Manual setup and configuration  
❌ **Maintenance Burden**: You manage backups, updates, monitoring  
❌ **No Built-in API**: Must build custom API layer  
❌ **Longer Setup Time**: 1-2 extra weeks for infrastructure  
❌ **Scalability**: Manual scaling vs automatic  
❌ **No Auth Out-of-Box**: Must implement authentication separately  

### Recommendation

**Use Local PostgreSQL if:**
- You have DevOps expertise in-house
- Data privacy/compliance requires on-premise hosting
- You need full control over database configuration
- Long-term cost optimization is priority
- You already have server infrastructure

**Use Supabase if:**
- You want faster time-to-market
- Limited DevOps resources
- Prefer managed service
- Need built-in auth and API
- Want automatic backups and scaling

---

## Next Steps

1. **Review this plan** - Understand the additional complexity
2. **Set up PostgreSQL** - Follow Section 2
3. **Load schema** - Run schema.sql (Section 3)
4. **Test pipeline** - Process sample data (Section 4)
5. **Build API** - Implement FastAPI (Section 5)
6. **Deploy** - Choose deployment option (Section 9)

---

**Document Version**: 1.0  
**Last Updated**: October 3, 2025  
**Status**: Ready for Implementation

