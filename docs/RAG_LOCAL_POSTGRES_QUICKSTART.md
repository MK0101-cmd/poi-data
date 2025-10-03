# LibraryRAG - Quick Start Guide (Local PostgreSQL)

**Purpose**: Get started with RAG implementation using local PostgreSQL in 1-2 hours

---

## Prerequisites

```bash
# Required software
- Docker & Docker Compose (easiest option)
  OR
- PostgreSQL 15+ (manual installation)
- Python 3.10+
- OpenAI API key
- Git
```

---

## Option A: Docker Setup (Recommended - 1 hour)

### Step 1: Create Project Structure (5 minutes)

```bash
# Create project directory
mkdir poi-rag
cd poi-rag

# Create subdirectories
mkdir -p api backups init-scripts

# Create .env file
cat > .env << 'EOF'
DB_HOST=postgres
DB_PORT=5432
DB_NAME=poi_rag
DB_USER=poi_user
DB_PASSWORD=your_secure_password_here
OPENAI_API_KEY=sk-your-openai-key-here
PGADMIN_PASSWORD=admin_password_here
EOF

# IMPORTANT: Replace with your actual passwords and API key!
```

### Step 2: Create Docker Compose File (5 minutes)

```bash
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  postgres:
    image: postgres:15
    container_name: poi-postgres
    environment:
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: ${DB_NAME}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d
      - ./backups:/backups
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  pgadmin:
    image: dpage/pgadmin4
    container_name: poi-pgadmin
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@example.com
      PGADMIN_DEFAULT_PASSWORD: ${PGADMIN_PASSWORD}
    ports:
      - "5050:80"
    depends_on:
      postgres:
        condition: service_healthy
    restart: unless-stopped

volumes:
  postgres_data:
EOF
```

### Step 3: Start PostgreSQL (2 minutes)

```bash
# Start PostgreSQL container
docker-compose up -d

# Check status
docker-compose ps

# Check logs
docker-compose logs postgres

# Wait for PostgreSQL to be ready (should see "ready to accept connections")
```

### Step 4: Install pgvector Extension (3 minutes)

```bash
# Connect to PostgreSQL container
docker exec -it poi-postgres bash

# Inside container, install pgvector
apt-get update
apt-get install -y git build-essential postgresql-server-dev-15
cd /tmp
git clone https://github.com/pgvector/pgvector.git
cd pgvector
make
make install
exit

# Restart container
docker-compose restart postgres
```

### Step 5: Create Database Schema (5 minutes)

Download the schema file from the full plan, or create it:

```bash
# Create schema.sql with the complete schema from RAG_LOCAL_POSTGRES_PLAN.md
# (Section 3.1 - save as schema.sql)

# Load schema
docker exec -i poi-postgres psql -U poi_user -d poi_rag < schema.sql

# Verify tables created
docker exec -it poi-postgres psql -U poi_user -d poi_rag -c "\dt"

# Expected output: 6 tables
# documents, document_chunks, cross_references, tags, document_tags, card_metadata
```

### Step 6: Set Up Python Environment (10 minutes)

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Create requirements.txt
cat > requirements.txt << 'EOF'
psycopg2-binary==2.9.9
pgvector==0.2.3
openai==1.3.0
python-dotenv==1.0.0
pandas==2.1.0
numpy==1.24.0
markdown==3.5.0
beautifulsoup4==4.12.0
EOF

# Install packages
pip install -r requirements.txt
```

### Step 7: Create Database Module (10 minutes)

```bash
cat > database.py << 'EOF'
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
        conn = psycopg2.connect(**self.conn_params)
        register_vector(conn)
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
        with self.get_connection() as conn:
            cursor_factory = RealDictCursor if dict_cursor else None
            cursor = conn.cursor(cursor_factory=cursor_factory)
            try:
                yield cursor
            finally:
                cursor.close()
    
    def insert_document(self, doc_data):
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

# Test connection
if __name__ == "__main__":
    db = Database()
    with db.get_cursor() as cur:
        cur.execute("SELECT version()")
        print(f"✓ Connected to PostgreSQL: {cur.fetchone()['version']}")
EOF

# Test database connection
python database.py
```

### Step 8: Create Data Pipeline (5 minutes)

```bash
cat > pipeline.py << 'EOF'
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
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def chunk_content(self, content: str, file_metadata: Dict) -> List[Dict]:
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
        response = openai.embeddings.create(
            input=text,
            model="text-embedding-3-small"
        )
        return response.data[0].embedding
    
    def process_file(self, file_metadata: Dict):
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
                'chunk_tokens': len(chunk['chunk_text'].split()) * 1.3
            })
        
        # Batch insert chunks
        if chunks_with_embeddings:
            self.db.insert_chunks_batch(chunks_with_embeddings)
        
        print(f"  ✓ Inserted {len(chunks_with_embeddings)} chunks")
        
    def run(self, limit: int = None):
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
    pipeline = LibraryRAGPipeline()
    pipeline.run(limit=5)  # Start with 5 files
EOF
```

### Step 9: Run Pipeline (10 minutes)

```bash
# Make sure you're in the LibraryRAG parent directory
# Or adjust the path in pipeline.py

# Run pipeline (process first 5 files)
python pipeline.py

# Expected output:
# 🚀 Starting LibraryRAG pipeline...
# 📁 Found 707 markdown files
# Processing: LibraryRAG/Activities/FACES/MASTER-INDEX.md
#   ✓ Inserted 12 chunks
# ...
# ✅ Pipeline complete!
```

### Step 10: Create Search Script (5 minutes)

```bash
cat > search.py << 'EOF'
import os
from dotenv import load_dotenv
import openai
from scripts.database import Database

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
db = Database()

def search(query: str, match_count: int = 5):
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
EOF
```

### Step 11: Test Search (5 minutes)

```bash
# Run search
python search.py

# Expected output:
# 🔍 Searching for: How to facilitate a team dialogue about conflict?
# 
# 📊 Found 5 results:
# 
# 1. [Activities/FLOW] Conflict Series Overview
#    Similarity: 0.892
#    Preview: The moments when we are uncomfortable...
# ...
```

### Step 12: Verify with pgAdmin (Optional)

```bash
# Access pgAdmin in browser
open http://localhost:5050

# Login:
# Email: admin@example.com
# Password: [your PGADMIN_PASSWORD from .env]

# Add server:
# Host: postgres (or localhost if accessing from host)
# Port: 5432
# Database: poi_rag
# Username: poi_user
# Password: [your DB_PASSWORD from .env]
```

---

## Option B: Manual Installation (2 hours)

### Step 1: Install PostgreSQL (15 minutes)

#### Ubuntu/Debian
```bash
# Add PostgreSQL repository
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -

# Install PostgreSQL 15
sudo apt update
sudo apt install -y postgresql-15 postgresql-server-dev-15

# Start service
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

#### macOS
```bash
# Using Homebrew
brew install postgresql@15

# Start service
brew services start postgresql@15
```

### Step 2: Install pgvector (10 minutes)

```bash
# Clone and build
cd /tmp
git clone https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install
```

### Step 3: Create Database (5 minutes)

```bash
# Switch to postgres user
sudo -u postgres psql

# In PostgreSQL shell:
CREATE DATABASE poi_rag;
CREATE USER poi_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE poi_rag TO poi_user;
\q

# Enable extensions
psql -U postgres -d poi_rag << 'EOF'
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pg_trgm;
GRANT ALL ON SCHEMA public TO poi_user;
\q
EOF
```

### Step 4-11: Follow Docker Steps

Continue with Steps 5-11 from Option A, but update your `.env`:

```bash
cat > .env << 'EOF'
DB_HOST=localhost
DB_PORT=5432
DB_NAME=poi_rag
DB_USER=poi_user
DB_PASSWORD=your_secure_password_here
OPENAI_API_KEY=sk-your-openai-key-here
EOF
```

---

## Verification Checklist

```bash
# Check PostgreSQL is running
docker-compose ps  # For Docker
# OR
sudo systemctl status postgresql  # For manual

# Check database exists
psql -U poi_user -d poi_rag -c "SELECT current_database();"

# Check tables exist
psql -U poi_user -d poi_rag -c "\dt"

# Check data inserted
psql -U poi_user -d poi_rag -c "SELECT COUNT(*) FROM documents;"
psql -U poi_user -d poi_rag -c "SELECT COUNT(*) FROM document_chunks;"

# Check embeddings exist
psql -U poi_user -d poi_rag -c "SELECT COUNT(*) FROM document_chunks WHERE embedding IS NOT NULL;"
```

---

## Next Steps

### Expand Implementation

1. **Process All Files**
   ```python
   # In pipeline.py, change the limit
   pipeline.run()  # Will process all 707 files
   ```

2. **Build FastAPI**
   See `RAG_LOCAL_POSTGRES_PLAN.md` Section 5

3. **Set Up Monitoring**
   - Use pgAdmin for database management
   - Add Grafana for metrics (optional)

4. **Configure Backups**
   ```bash
   # Create backup script
   pg_dump -U poi_user -d poi_rag -F c -f backup_$(date +%Y%m%d).backup
   ```

---

## Troubleshooting

### Issue: "Could not connect to database"
```bash
# Check PostgreSQL is running
docker-compose ps  # For Docker
sudo systemctl status postgresql  # For manual

# Check connection settings
psql -U poi_user -d poi_rag -c "SELECT 1"
```

### Issue: "Extension vector does not exist"
```bash
# Reinstall pgvector (see Step 4 for Docker or Step 2 for manual)

# Verify installation
psql -U poi_user -d poi_rag -c "SELECT * FROM pg_extension WHERE extname='vector';"
```

### Issue: "No embeddings generated"
```bash
# Check OpenAI API key
python -c "import openai, os; openai.api_key=os.getenv('OPENAI_API_KEY'); print(openai.models.list())"
```

### Issue: "Slow queries"
```bash
# Run maintenance
psql -U poi_user -d poi_rag << 'EOF'
VACUUM ANALYZE document_chunks;
REINDEX INDEX idx_chunks_embedding;
EOF
```

---

## Cost Estimation

### Docker (Local Development)
- **Hardware**: Existing machine ($0)
- **Software**: All free/open-source ($0)
- **OpenAI API**: ~$0.10 for 5 files, $5-10 for all files
- **Total**: ~$5-10 for initial setup

### Production (VPS)
- **VPS**: DigitalOcean 8GB RAM ($40/month)
- **Backups**: $5/month
- **OpenAI API**: $100-200/month for queries
- **Total**: ~$145-245/month

---

## Comparison with Supabase

| Feature | Local PostgreSQL | Supabase |
|---------|------------------|----------|
| **Setup Time** | 1-2 hours | 30 minutes |
| **Database** | Self-managed | Managed |
| **API** | Must build (FastAPI) | Built-in REST API |
| **Auth** | Must implement | Built-in |
| **Backups** | Manual | Automatic |
| **Cost (initial)** | $5-10 (API only) | $5-10 (API only) |
| **Cost (monthly)** | $40-50 (VPS) | $25-50 (Supabase) |
| **Control** | Full | Limited |
| **Complexity** | Medium-High | Low |

---

## Success Checklist

- [ ] PostgreSQL 15 installed and running
- [ ] pgvector extension installed
- [ ] Database `poi_rag` created
- [ ] Schema loaded (6 tables + functions)
- [ ] Python environment set up
- [ ] Dependencies installed
- [ ] `.env` file configured
- [ ] Database connection working
- [ ] Pipeline runs successfully
- [ ] Data inserted (documents + chunks)
- [ ] Embeddings generated
- [ ] Search returns relevant results

---

**Congratulations! 🎉**

You now have a working RAG system with local PostgreSQL!

**Next Steps:**
1. Process all 707 files: `pipeline.run()`
2. Build API: See `RAG_LOCAL_POSTGRES_PLAN.md` Section 5
3. Set up monitoring: pgAdmin or Grafana
4. Configure backups: Daily automated backups
5. Deploy to production: Docker or VPS

---

*Time to complete: 1-2 hours*  
*Difficulty: Intermediate*  
*Prerequisites: Docker/PostgreSQL, Python basics, OpenAI API key*

