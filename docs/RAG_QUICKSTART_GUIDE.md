# LibraryRAG - Quick Start Guide

**Purpose**: Get started with RAG implementation in 1 hour

---

## Prerequisites

```bash
# Required software
- Python 3.10+
- Supabase account
- OpenAI API key
- Git
```

---

## Step 1: Environment Setup (10 minutes)

### 1.1 Create Supabase Project

```bash
# Option A: Using Supabase Dashboard
1. Go to https://supabase.com
2. Click "New Project"
3. Name: "poi-rag"
4. Database Password: [generate strong password]
5. Region: [choose closest to users]

# Option B: Using Supabase CLI
npm install -g supabase
supabase init
supabase start
```

### 1.2 Note Your Credentials

```bash
# Save these for later:
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key
OPENAI_API_KEY=sk-...
```

### 1.3 Create `.env` File

```bash
# Create .env in project root
cat > .env << EOF
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key
OPENAI_API_KEY=sk-...
EOF
```

### 1.4 Install Python Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install packages
pip install supabase openai python-dotenv pandas numpy markdown beautifulsoup4
```

---

## Step 2: Database Setup (10 minutes)

### 2.1 Enable Extensions

```sql
-- Run in Supabase SQL Editor
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pg_trgm;
```

### 2.2 Create Core Tables

```sql
-- documents table
CREATE TABLE documents (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  file_path TEXT NOT NULL UNIQUE,
  file_name TEXT NOT NULL,
  content TEXT NOT NULL,
  content_type TEXT NOT NULL,
  category TEXT NOT NULL,
  subcategory TEXT NOT NULL,
  content_subtype TEXT,
  parent_id UUID REFERENCES documents(id),
  hierarchy_path TEXT[],
  depth INTEGER NOT NULL DEFAULT 0,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- document_chunks table with embeddings
CREATE TABLE document_chunks (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  chunk_text TEXT NOT NULL,
  chunk_index INTEGER NOT NULL,
  chunk_tokens INTEGER,
  section_title TEXT,
  section_type TEXT,
  embedding VECTOR(1536),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  CONSTRAINT unique_document_chunk UNIQUE(document_id, chunk_index)
);

-- Create indexes
CREATE INDEX idx_documents_category ON documents(category);
CREATE INDEX idx_documents_subcategory ON documents(subcategory);
CREATE INDEX idx_chunks_document_id ON document_chunks(document_id);
CREATE INDEX idx_chunks_embedding ON document_chunks 
  USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

### 2.3 Enable Row Level Security (Optional)

```sql
-- Enable RLS
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_chunks ENABLE ROW LEVEL SECURITY;

-- Allow public read access
CREATE POLICY "Allow public read access to documents" 
  ON documents FOR SELECT USING (true);
CREATE POLICY "Allow public read access to chunks" 
  ON document_chunks FOR SELECT USING (true);
```

---

## Step 3: Create Data Pipeline (15 minutes)

### 3.1 Create `pipeline.py`

```python
import os
import json
from pathlib import Path
from typing import List, Dict
from dotenv import load_dotenv
from supabase import create_client
import openai

# Load environment
load_dotenv()

# Initialize clients
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)
openai.api_key = os.getenv("OPENAI_API_KEY")

class LibraryRAGPipeline:
    def __init__(self, root_path: str = "LibraryRAG"):
        self.root_path = Path(root_path)
        
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
            
            # Extract section title
            lines = section.split('\n')
            section_title = lines[0].replace('#', '').strip()
            section_text = '\n'.join(lines[1:])
            
            if len(section_text.strip()) < 50:  # Skip very short sections
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
        """Classify section type based on title"""
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
        doc_result = supabase.table('documents').insert({
            'file_path': file_metadata['file_path'],
            'file_name': file_metadata['file_name'],
            'content': content,
            'content_type': 'markdown',
            'category': file_metadata['category'],
            'subcategory': file_metadata['subcategory'],
            'hierarchy_path': file_metadata['hierarchy_path'],
            'depth': file_metadata['depth']
        }).execute()
        
        document_id = doc_result.data[0]['id']
        
        # Chunk content
        chunks = self.chunk_content(content, file_metadata)
        
        # Process chunks (with embeddings)
        for chunk in chunks:
            # Generate embedding
            embedding = self.generate_embedding(chunk['chunk_text'])
            
            # Insert chunk
            supabase.table('document_chunks').insert({
                'document_id': document_id,
                'chunk_text': chunk['chunk_text'],
                'chunk_index': chunk['chunk_index'],
                'section_title': chunk['section_title'],
                'section_type': chunk['section_type'],
                'embedding': embedding
            }).execute()
        
        print(f"  ✓ Inserted {len(chunks)} chunks")
        
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

# Run the pipeline
if __name__ == "__main__":
    pipeline = LibraryRAGPipeline()
    
    # Start with first 5 files for testing
    pipeline.run(limit=5)
    
    # Remove limit to process all files
    # pipeline.run()
```

---

## Step 4: Test with Sample Data (10 minutes)

### 4.1 Run Pipeline

```bash
# Process first 5 files
python pipeline.py

# Expected output:
# 🚀 Starting LibraryRAG pipeline...
# 📁 Found 707 markdown files
# Processing: LibraryRAG/Activities/FACES/MASTER-INDEX.md
#   ✓ Inserted 12 chunks
# ...
# ✅ Pipeline complete!
```

### 4.2 Verify Data

```sql
-- Check documents
SELECT COUNT(*) FROM documents;

-- Check chunks
SELECT COUNT(*) FROM document_chunks;

-- Check embeddings
SELECT COUNT(*) FROM document_chunks WHERE embedding IS NOT NULL;
```

---

## Step 5: Create Search Function (10 minutes)

### 5.1 Create Search Function in Supabase

```sql
CREATE OR REPLACE FUNCTION search_content(
  query_embedding VECTOR(1536),
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
  similarity_score FLOAT
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
    1 - (dc.embedding <=> query_embedding) AS similarity_score
  FROM document_chunks dc
  JOIN documents d ON dc.document_id = d.id
  WHERE 1 - (dc.embedding <=> query_embedding) > match_threshold
  ORDER BY dc.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;
```

### 5.2 Create `search.py`

```python
import os
from dotenv import load_dotenv
from supabase import create_client
import openai

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)
openai.api_key = os.getenv("OPENAI_API_KEY")

def search(query: str, match_count: int = 5):
    """Search the LibraryRAG"""
    
    # Generate query embedding
    print(f"🔍 Searching for: {query}")
    response = openai.embeddings.create(
        input=query,
        model="text-embedding-3-small"
    )
    query_embedding = response.data[0].embedding
    
    # Search in Supabase
    result = supabase.rpc(
        'search_content',
        {
            'query_embedding': query_embedding,
            'match_count': match_count
        }
    ).execute()
    
    # Display results
    print(f"\n📊 Found {len(result.data)} results:\n")
    
    for i, match in enumerate(result.data, 1):
        print(f"{i}. [{match['category']}/{match['subcategory']}] {match['section_title']}")
        print(f"   Similarity: {match['similarity_score']:.3f}")
        print(f"   Preview: {match['chunk_text'][:150]}...")
        print()
    
    return result.data

if __name__ == "__main__":
    # Test searches
    search("How to facilitate a team dialogue about conflict?")
    search("Stories about personal transformation")
    search("Reflection questions for leadership")
```

---

## Step 6: Test Search (5 minutes)

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
#    Preview: The moments when we are uncomfortable that take us to the next level...
# 
# 2. [Activities/SPEAK] Dialogue Starters
#    Similarity: 0.876
#    Preview: Use these questions to start meaningful conversations about...
# ...
```

---

## Next Steps

### Expand Your Implementation

1. **Process All Files**
   ```python
   # In pipeline.py, remove the limit
   pipeline.run()  # Will process all 707 files
   ```

2. **Add More Tables**
   - cross_references
   - tags
   - document_tags
   - card_metadata

3. **Enhance Search**
   - Add filters (category, tags)
   - Implement hybrid search (vector + keyword)
   - Add related content suggestions

4. **Build API**
   - FastAPI or Flask
   - RESTful endpoints
   - Authentication

5. **Create UI**
   - Search interface
   - Result display
   - Content browser

---

## Troubleshooting

### Issue: "Extension vector does not exist"
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### Issue: "No embedding generated"
Check your OpenAI API key and quota:
```python
import openai
openai.api_key = "your-key"
print(openai.models.list())
```

### Issue: "Slow search performance"
Rebuild the index:
```sql
REINDEX INDEX idx_chunks_embedding;
```

### Issue: "Connection refused"
Check Supabase URL and key:
```python
print(os.getenv("SUPABASE_URL"))
print(os.getenv("SUPABASE_KEY")[:20] + "...")
```

---

## Cost Estimation

### For Initial 5 Files
- Embeddings: ~$0.01
- Supabase: Free tier
- Total: ~$0.01

### For All 707 Files (~5,000 chunks)
- Embeddings: ~$5-10 (one-time)
- Supabase: Free tier sufficient
- Monthly: ~$0-1 (queries only)

---

## Resources

### Documentation
- **Full Plan**: `RAG_PREPARATION_PLAN.md`
- **Executive Summary**: `RAG_EXECUTIVE_SUMMARY.md`
- **Supabase Docs**: https://supabase.com/docs
- **OpenAI Embeddings**: https://platform.openai.com/docs/guides/embeddings
- **pgvector**: https://github.com/pgvector/pgvector

### Support
- Supabase Discord: https://discord.supabase.com
- Points of You®: [internal support]

---

## Success Checklist

- [ ] Supabase project created
- [ ] Extensions enabled (vector, uuid-ossp, pg_trgm)
- [ ] Tables created (documents, document_chunks)
- [ ] Python environment set up
- [ ] Dependencies installed
- [ ] .env file configured
- [ ] Pipeline runs successfully
- [ ] Data inserted into database
- [ ] Search function created
- [ ] Search returns relevant results

---

**Congratulations! 🎉** 

You now have a working RAG system for the LibraryRAG content!

Continue with the full implementation plan to add:
- Advanced search features
- All database tables
- Comprehensive metadata
- Performance optimization
- Production deployment

---

*Time to complete: ~1 hour*  
*Difficulty: Intermediate*  
*Prerequisites: Python, SQL basics, API keys*

