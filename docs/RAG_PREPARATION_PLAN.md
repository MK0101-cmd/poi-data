# LibraryRAG - RAG Preparation Plan for Supabase

**Created:** October 3, 2025  
**Purpose:** Comprehensive plan for preparing Points of You® library content for RAG (Retrieval-Augmented Generation) operations using Supabase

---

## Executive Summary

The LibraryRAG contains **1,010 files** (707 markdown files + 303 images) organized into **Activities** (877 files) and **Trainings** (133 files). This plan outlines a strategy for:

1. **Data ingestion** and preprocessing
2. **Embedding generation** and storage
3. **Vector search** configuration
4. **Metadata structure** for enhanced retrieval
5. **Implementation roadmap**

---

## Table of Contents

1. [Content Analysis](#content-analysis)
2. [Database Schema Design](#database-schema-design)
3. [Data Processing Pipeline](#data-processing-pipeline)
4. [Embedding Strategy](#embedding-strategy)
5. [Metadata Structure](#metadata-structure)
6. [Supabase Configuration](#supabase-configuration)
7. [Implementation Roadmap](#implementation-roadmap)
8. [Query Patterns](#query-patterns)
9. [Performance Optimization](#performance-optimization)
10. [Testing Strategy](#testing-strategy)

---

## 1. Content Analysis

### 1.1 Content Inventory

#### Activities (877 files)
- **CANVASES**: 27 files - Themed canvases for mindfulness, self-discovery, emotional wellbeing, relationships, life transitions, goal setting
- **FACES**: 219 files (59 MD + 160 PNG) - 7 series (open-minded, givers, takers, stormy, calculated, lost, knowing)
- **FLOW**: 164 files (98 MD + 66 PNG) - 5 series (dream, in-between, conflict, belonging, presence) with 65 topics
- **JOURNEYS**: 11 files - Building blocks for facilitated journey programs
- **MASTERCLASSES**: 38 files - Training modules for facilitators
- **SPEAK**: 281 files (219 MD + 62 PNG) - Dialogue starters and communication tools
- **TCG**: 116 files (101 MD + 15 PNG) - The Coaching Game cards (14 concepts)
- **WORKSHOPS**: 21 files - Complete workshop designs

#### Trainings (133 files)
- **AI**: 25 files - AI implementation guides and prompts
- **BTC24**: 65 files - Business Trainer Certification program
- **CASESTUDIES**: 13 files - Real-world application examples
- **INTERACTION**: 22 files - Communication and interaction techniques
- **PHOTOTHERAPY**: 8 files - Phototherapy integration with Points of You

### 1.2 Content Types

| Type | Count | Purpose | RAG Priority |
|------|-------|---------|--------------|
| Master Indexes | ~15 | Navigation and cross-references | HIGH |
| Building Blocks | ~400 | Core content units | HIGH |
| Photo Cards | 303 PNG | Visual stimuli | MEDIUM |
| Reflection Cards | ~100 | Thematic prompts | HIGH |
| Stories & Tales | ~50 | Narrative examples | HIGH |
| Reflection Questions | ~100 | Facilitation prompts | HIGH |
| Training Applications | ~80 | Practical use cases | HIGH |
| Implementation Guides | ~40 | How-to instructions | HIGH |
| Templates | ~30 | Ready-to-use formats | MEDIUM |

### 1.3 Content Characteristics

- **Highly interconnected**: Extensive cross-references between files
- **Hierarchical structure**: Categories → Series → Building Blocks → Components
- **Multi-modal**: Text content + images + metadata
- **Context-dependent**: Content meaning depends on relationships
- **Training-focused**: Designed for facilitators and coaches

---

## 2. Database Schema Design

### 2.1 Core Tables

#### Table: `documents`
Primary content storage with metadata

```sql
CREATE TABLE documents (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  
  -- Content
  file_path TEXT NOT NULL UNIQUE,
  file_name TEXT NOT NULL,
  content TEXT NOT NULL,
  content_type TEXT NOT NULL, -- 'markdown', 'image'
  
  -- Metadata
  category TEXT NOT NULL, -- 'Activities', 'Trainings'
  subcategory TEXT NOT NULL, -- 'FACES', 'FLOW', 'AI', 'BTC24', etc.
  content_subtype TEXT, -- 'master-index', 'building-block', 'story', 'reflection-question', etc.
  
  -- Hierarchy
  parent_id UUID REFERENCES documents(id),
  hierarchy_path TEXT[], -- e.g., ['Activities', 'FACES', 'open-minded', 'stories']
  depth INTEGER NOT NULL DEFAULT 0,
  
  -- Timestamps
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  
  -- Indexes
  CONSTRAINT valid_category CHECK (category IN ('Activities', 'Trainings'))
);

CREATE INDEX idx_documents_category ON documents(category);
CREATE INDEX idx_documents_subcategory ON documents(subcategory);
CREATE INDEX idx_documents_content_subtype ON documents(content_subtype);
CREATE INDEX idx_documents_hierarchy_path ON documents USING GIN(hierarchy_path);
CREATE INDEX idx_documents_parent_id ON documents(parent_id);
```

#### Table: `document_chunks`
Chunked content for embedding

```sql
CREATE TABLE document_chunks (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  
  -- Document reference
  document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  
  -- Chunk content
  chunk_text TEXT NOT NULL,
  chunk_index INTEGER NOT NULL,
  chunk_tokens INTEGER, -- Estimated token count
  
  -- Chunk metadata
  section_title TEXT,
  section_type TEXT, -- 'overview', 'story', 'quote', 'question', 'application', etc.
  
  -- Vector embedding (pgvector extension)
  embedding VECTOR(1536), -- OpenAI text-embedding-3-small dimension
  
  -- Timestamps
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  
  CONSTRAINT unique_document_chunk UNIQUE(document_id, chunk_index)
);

CREATE INDEX idx_chunks_document_id ON document_chunks(document_id);
CREATE INDEX idx_chunks_section_type ON document_chunks(section_type);
CREATE INDEX idx_chunks_embedding ON document_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

#### Table: `cross_references`
Document relationships and connections

```sql
CREATE TABLE cross_references (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  
  -- Relationship
  source_document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  target_document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  
  -- Relationship metadata
  reference_type TEXT NOT NULL, -- 'related', 'parent-child', 'cross-series', 'example', 'template'
  relationship_strength FLOAT DEFAULT 1.0, -- 0.0 to 1.0
  context TEXT, -- Description of relationship
  
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  
  CONSTRAINT unique_cross_reference UNIQUE(source_document_id, target_document_id, reference_type)
);

CREATE INDEX idx_cross_refs_source ON cross_references(source_document_id);
CREATE INDEX idx_cross_refs_target ON cross_references(target_document_id);
CREATE INDEX idx_cross_refs_type ON cross_references(reference_type);
```

#### Table: `tags`
Content tagging for enhanced search

```sql
CREATE TABLE tags (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  tag_name TEXT NOT NULL UNIQUE,
  tag_category TEXT NOT NULL, -- 'theme', 'technique', 'audience', 'use-case', 'emotion', etc.
  description TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_tags_category ON tags(tag_category);
```

#### Table: `document_tags`
Many-to-many relationship between documents and tags

```sql
CREATE TABLE document_tags (
  document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  tag_id UUID NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
  relevance_score FLOAT DEFAULT 1.0, -- 0.0 to 1.0
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  
  PRIMARY KEY (document_id, tag_id)
);

CREATE INDEX idx_document_tags_document ON document_tags(document_id);
CREATE INDEX idx_document_tags_tag ON document_tags(tag_id);
```

#### Table: `card_metadata`
Specific metadata for photo and reflection cards

```sql
CREATE TABLE card_metadata (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  
  -- Card identification
  card_type TEXT NOT NULL, -- 'photo', 'reflection', 'word', 'question'
  deck_name TEXT NOT NULL, -- 'FACES', 'FLOW', 'TCG', 'SPEAK', 'PUNCTUM'
  card_number INTEGER,
  card_name TEXT,
  
  -- Series/Category
  series_name TEXT, -- 'open-minded', 'dream', 'solutions', etc.
  series_index INTEGER,
  
  -- Associated content
  document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
  image_url TEXT,
  
  -- Card metadata
  themes TEXT[], -- Array of themes
  emotions TEXT[], -- Associated emotions
  use_cases TEXT[], -- When to use this card
  
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  
  CONSTRAINT unique_card UNIQUE(deck_name, card_type, card_number)
);

CREATE INDEX idx_card_metadata_deck ON card_metadata(deck_name);
CREATE INDEX idx_card_metadata_series ON card_metadata(series_name);
CREATE INDEX idx_card_metadata_document ON card_metadata(document_id);
```

---

## 3. Data Processing Pipeline

### 3.1 Pipeline Stages

#### Stage 1: File Discovery & Cataloging
```python
# Pseudo-code structure
class FileDiscovery:
    def scan_directory(self, root_path: str) -> List[FileMetadata]:
        """
        Recursively scan LibraryRAG directory
        Extract: path, name, type, hierarchy, category
        """
        pass
    
    def classify_content(self, file_metadata: FileMetadata) -> ContentClassification:
        """
        Classify based on:
        - File location in hierarchy
        - File name patterns
        - Content structure
        """
        pass
```

**Output:** Complete file inventory with classification

#### Stage 2: Content Extraction & Parsing
```python
class ContentExtractor:
    def extract_markdown(self, file_path: str) -> StructuredContent:
        """
        Parse markdown:
        - Extract sections (## headers)
        - Extract links and cross-references
        - Extract lists, tables, code blocks
        - Preserve structure
        """
        pass
    
    def extract_metadata(self, content: str) -> Dict:
        """
        Extract from content:
        - Title (# header)
        - Overview section
        - Key concepts
        - Cross-references
        """
        pass
```

**Output:** Structured content with metadata

#### Stage 3: Relationship Mapping
```python
class RelationshipMapper:
    def extract_links(self, content: str) -> List[Link]:
        """
        Extract markdown links: [text](path)
        Resolve relative paths
        Identify link types
        """
        pass
    
    def build_hierarchy(self, files: List[FileMetadata]) -> HierarchyTree:
        """
        Build parent-child relationships
        Calculate depth
        Create hierarchy paths
        """
        pass
    
    def identify_cross_references(self, files: List[FileMetadata]) -> List[CrossRef]:
        """
        Identify:
        - Same-series relationships
        - Cross-series relationships
        - Examples and applications
        """
        pass
```

**Output:** Relationship graph

#### Stage 4: Content Chunking
```python
class ContentChunker:
    def chunk_by_section(self, content: StructuredContent) -> List[Chunk]:
        """
        Strategy 1: Section-based chunking
        - Split by ## and ### headers
        - Preserve section context
        - Include parent section in chunk
        """
        pass
    
    def chunk_by_semantic_unit(self, content: StructuredContent) -> List[Chunk]:
        """
        Strategy 2: Semantic chunking
        - Stories = one chunk
        - Questions = grouped chunks
        - Lists = contextual grouping
        """
        pass
    
    def optimize_chunk_size(self, chunks: List[Chunk], target_tokens: int = 500) -> List[Chunk]:
        """
        Optimize for embedding:
        - Target 300-800 tokens per chunk
        - Avoid splitting mid-sentence
        - Maintain context
        """
        pass
```

**Parameters:**
- Target chunk size: 500 tokens (±200)
- Minimum chunk size: 100 tokens
- Maximum chunk size: 1000 tokens
- Overlap: 50 tokens between adjacent chunks

**Output:** Chunked content ready for embedding

#### Stage 5: Tag Generation
```python
class TagGenerator:
    def extract_explicit_tags(self, content: StructuredContent) -> List[Tag]:
        """
        Extract from:
        - File path components
        - Section headers
        - Listed keywords
        """
        pass
    
    def generate_thematic_tags(self, content: str) -> List[Tag]:
        """
        Use NLP/LLM to identify:
        - Themes (leadership, creativity, conflict, etc.)
        - Techniques (reflection, facilitation, coaching)
        - Emotions (joy, fear, curiosity, etc.)
        - Use cases (team building, personal growth, etc.)
        """
        pass
```

**Tag Categories:**
- **Themes**: leadership, creativity, relationships, transitions, purpose, etc.
- **Techniques**: reflection, facilitation, coaching, dialogue, storytelling
- **Audiences**: individuals, teams, leaders, trainers, therapists
- **Use Cases**: team building, conflict resolution, goal setting, healing
- **Emotions**: joy, fear, curiosity, anger, peace, love, etc.
- **Duration**: 15min, 30min, 60min, 90min, half-day, full-day, multi-day
- **Tools**: photo cards, reflection cards, word cards, question cards
- **Decks**: FACES, FLOW, TCG, SPEAK, PUNCTUM

**Output:** Tagged content

#### Stage 6: Embedding Generation
```python
class EmbeddingGenerator:
    def __init__(self, model: str = "text-embedding-3-small"):
        self.model = model
        self.dimension = 1536
    
    def generate_chunk_embeddings(self, chunks: List[Chunk]) -> List[Vector]:
        """
        Generate embeddings for each chunk
        Batch processing for efficiency
        Handle rate limits
        """
        pass
    
    def add_metadata_context(self, chunk: Chunk) -> str:
        """
        Enhance chunk text with metadata:
        "Category: [category] | Series: [series] | Type: [type] | Content: [text]"
        """
        pass
```

**Embedding Strategy:**
- Model: OpenAI `text-embedding-3-small` (1536 dimensions)
- Alternative: OpenAI `text-embedding-3-large` (3072 dimensions) for higher quality
- Batch size: 100 chunks per API call
- Rate limiting: Respect OpenAI API limits
- Metadata enrichment: Prepend category and series info to chunk text

**Output:** Vector embeddings

#### Stage 7: Database Population
```python
class DatabasePopulator:
    def insert_documents(self, documents: List[Document]):
        """Bulk insert into documents table"""
        pass
    
    def insert_chunks(self, chunks: List[ChunkWithEmbedding]):
        """Bulk insert into document_chunks table"""
        pass
    
    def insert_relationships(self, relationships: List[CrossReference]):
        """Insert cross-references"""
        pass
    
    def insert_tags(self, tags: List[Tag], document_tags: List[DocumentTag]):
        """Insert tags and document_tags"""
        pass
```

**Output:** Populated Supabase database

### 3.2 Data Quality Checks

```python
class QualityChecker:
    def validate_embeddings(self, chunks: List[ChunkWithEmbedding]) -> Report:
        """
        - Check for null embeddings
        - Validate embedding dimensions
        - Check for duplicate chunks
        """
        pass
    
    def validate_relationships(self, cross_refs: List[CrossReference]) -> Report:
        """
        - Check for broken links
        - Validate bidirectional relationships
        - Identify orphaned documents
        """
        pass
    
    def validate_tags(self, document_tags: List[DocumentTag]) -> Report:
        """
        - Check tag consistency
        - Validate tag categories
        - Ensure minimum tag coverage
        """
        pass
```

---

## 4. Embedding Strategy

### 4.1 Embedding Model Selection

#### Primary Model: OpenAI `text-embedding-3-small`
- **Dimensions**: 1536
- **Cost**: $0.02 per 1M tokens
- **Performance**: Excellent for most use cases
- **Pros**: Fast, cost-effective, high quality
- **Cons**: External API dependency

#### Alternative: OpenAI `text-embedding-3-large`
- **Dimensions**: 3072
- **Cost**: $0.13 per 1M tokens
- **Performance**: Best-in-class
- **Use case**: Premium tier or critical applications

#### Open Source Alternative: `all-MiniLM-L6-v2`
- **Dimensions**: 384
- **Cost**: Free (self-hosted)
- **Performance**: Good for basic use cases
- **Use case**: Development, testing, budget constraints

### 4.2 Embedding Enhancement Techniques

#### Technique 1: Metadata Prefix
```python
def enhance_chunk_with_metadata(chunk: Chunk) -> str:
    """
    Prepend metadata to improve retrieval accuracy
    """
    metadata_prefix = f"""
    Category: {chunk.category}
    Subcategory: {chunk.subcategory}
    Type: {chunk.section_type}
    Series: {chunk.series_name if chunk.series_name else 'N/A'}
    
    Content:
    """
    return metadata_prefix + chunk.text
```

**Example:**
```
Category: Activities
Subcategory: FACES
Type: story
Series: open-minded

Content:
A curious child once asked their parent, "Where does the moon go during the day?" 
and "How are babies made?" These questions demonstrate the essence of open-mindedness...
```

#### Technique 2: Hierarchical Context
```python
def add_hierarchical_context(chunk: Chunk) -> str:
    """
    Include parent document titles for context
    """
    context = " > ".join(chunk.hierarchy_path)
    return f"[{context}]\n\n{chunk.text}"
```

#### Technique 3: Cross-Reference Enrichment
```python
def enrich_with_cross_references(chunk: Chunk, related_docs: List[Document]) -> str:
    """
    Optionally include related content summaries
    """
    related_context = "\n".join([
        f"Related: {doc.title}" for doc in related_docs[:3]
    ])
    return f"{chunk.text}\n\n{related_context}"
```

### 4.3 Embedding Storage

#### pgvector Configuration
```sql
-- Install pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create index for cosine similarity search
CREATE INDEX idx_chunks_embedding 
ON document_chunks 
USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);

-- For euclidean distance (alternative)
-- CREATE INDEX idx_chunks_embedding 
-- ON document_chunks 
-- USING ivfflat (embedding vector_l2_ops) 
-- WITH (lists = 100);
```

**Index Parameters:**
- `lists = 100`: For ~10,000 chunks (adjust based on dataset size)
- Rule of thumb: `lists = rows / 1000` (minimum 10, maximum 1000)
- Expected chunk count: ~5,000-15,000 chunks

---

## 5. Metadata Structure

### 5.1 Document Metadata Schema

```json
{
  "file_path": "LibraryRAG/Activities/FACES/open-minded/stories-tales.md",
  "file_name": "stories-tales.md",
  "category": "Activities",
  "subcategory": "FACES",
  "content_subtype": "stories",
  "hierarchy_path": ["Activities", "FACES", "open-minded", "stories"],
  "depth": 4,
  "parent_document": {
    "id": "uuid",
    "name": "open-minded README",
    "path": "LibraryRAG/Activities/FACES/open-minded/README.md"
  },
  "title": "OPEN-MINDED SERIES - Stories & Tales",
  "description": "Narrative examples demonstrating open-mindedness",
  "series": {
    "name": "open-minded",
    "index": 1,
    "total": 7
  },
  "tags": [
    {"name": "curiosity", "category": "theme"},
    {"name": "storytelling", "category": "technique"},
    {"name": "personal-growth", "category": "use-case"}
  ],
  "cross_references": [
    {
      "target": "LibraryRAG/Activities/FACES/givers/stories-tales.md",
      "type": "related",
      "strength": 0.8
    }
  ],
  "statistics": {
    "word_count": 1250,
    "story_count": 6,
    "estimated_reading_time": "5 minutes"
  }
}
```

### 5.2 Chunk Metadata Schema

```json
{
  "chunk_id": "uuid",
  "document_id": "uuid",
  "chunk_index": 3,
  "chunk_text": "A curious child once asked...",
  "chunk_tokens": 420,
  "section_title": "Story: The Curious Child",
  "section_type": "story",
  "embedding": [0.123, -0.456, ...],
  "tags": ["curiosity", "childhood", "questions"],
  "parent_document_metadata": {
    "category": "Activities",
    "subcategory": "FACES",
    "series": "open-minded"
  }
}
```

### 5.3 Tag Taxonomy

#### Theme Tags
- `leadership`, `creativity`, `relationships`, `transitions`, `purpose`, `balance`, `conflict`, `belonging`, `presence`, `mindfulness`, `authenticity`, `resilience`, `empathy`, `compassion`, `transformation`, `healing`, `growth`, `innovation`

#### Technique Tags
- `reflection`, `facilitation`, `coaching`, `dialogue`, `storytelling`, `visualization`, `metaphor`, `questioning`, `active-listening`, `reframing`, `mirroring`, `grounding`, `embodiment`

#### Audience Tags
- `individuals`, `teams`, `leaders`, `trainers`, `coaches`, `therapists`, `educators`, `executives`, `managers`, `employees`, `students`

#### Use Case Tags
- `team-building`, `conflict-resolution`, `goal-setting`, `decision-making`, `change-management`, `stress-management`, `relationship-building`, `self-discovery`, `career-development`, `personal-growth`, `healing`, `trauma-recovery`

#### Emotion Tags
- `joy`, `fear`, `curiosity`, `anger`, `peace`, `love`, `sadness`, `excitement`, `vulnerability`, `courage`, `hope`, `gratitude`, `shame`, `guilt`

#### Duration Tags
- `15min`, `30min`, `45min`, `60min`, `90min`, `half-day`, `full-day`, `multi-day`, `self-paced`

#### Tool Tags
- `photo-cards`, `reflection-cards`, `word-cards`, `question-cards`, `canvas`, `layout`, `journal`

#### Deck Tags
- `FACES`, `FLOW`, `TCG`, `SPEAK`, `PUNCTUM`, `mixed-deck`

---

## 6. Supabase Configuration

### 6.1 Project Setup

#### Step 1: Create Supabase Project
```bash
# Using Supabase CLI
supabase init
supabase start

# Or via Supabase Dashboard
# 1. Create new project
# 2. Note: Project URL, API keys
```

#### Step 2: Enable Extensions
```sql
-- Enable pgvector for vector operations
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable uuid generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pg_trgm for text search
CREATE EXTENSION IF NOT EXISTS pg_trgm;
```

#### Step 3: Create Tables
Run the SQL scripts from Section 2.1 to create all tables.

#### Step 4: Configure RLS (Row Level Security)
```sql
-- Enable RLS
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE cross_references ENABLE ROW LEVEL SECURITY;
ALTER TABLE tags ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_tags ENABLE ROW LEVEL SECURITY;
ALTER TABLE card_metadata ENABLE ROW LEVEL SECURITY;

-- Create policies (example for read-only access)
CREATE POLICY "Allow public read access to documents" 
ON documents FOR SELECT 
USING (true);

CREATE POLICY "Allow public read access to chunks" 
ON document_chunks FOR SELECT 
USING (true);

-- For write access, create policies based on authentication
-- Example: Only authenticated users can write
CREATE POLICY "Allow authenticated users to insert documents" 
ON documents FOR INSERT 
WITH CHECK (auth.role() = 'authenticated');
```

### 6.2 Indexes for Performance

```sql
-- Full-text search indexes
CREATE INDEX idx_documents_content_fts ON documents USING GIN(to_tsvector('english', content));
CREATE INDEX idx_documents_title_trgm ON documents USING GIN(file_name gin_trgm_ops);

-- Chunk search indexes
CREATE INDEX idx_chunks_text_fts ON document_chunks USING GIN(to_tsvector('english', chunk_text));
CREATE INDEX idx_chunks_section_title_trgm ON document_chunks USING GIN(section_title gin_trgm_ops);

-- Metadata search indexes
CREATE INDEX idx_documents_category_subcategory ON documents(category, subcategory);
CREATE INDEX idx_documents_hierarchy_gin ON documents USING GIN(hierarchy_path);

-- Performance indexes
CREATE INDEX idx_chunks_document_section ON document_chunks(document_id, section_type);
CREATE INDEX idx_card_metadata_composite ON card_metadata(deck_name, series_name, card_type);
```

### 6.3 Database Functions

#### Function: Hybrid Search (Vector + Keyword)
```sql
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
```

#### Function: Search with Filters
```sql
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
```

#### Function: Get Related Documents
```sql
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
```

### 6.4 API Configuration

#### Supabase Client Setup (Python)
```python
from supabase import create_client, Client
import os

# Initialize Supabase client
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)
```

#### Query Examples
```python
# Vector search
def vector_search(query_embedding: list, match_count: int = 10):
    result = supabase.rpc(
        'hybrid_search',
        {
            'query_embedding': query_embedding,
            'query_text': '',
            'match_count': match_count
        }
    ).execute()
    return result.data

# Search with filters
def filtered_search(query_embedding: list, category: str = None, tags: list = None):
    result = supabase.rpc(
        'search_with_filters',
        {
            'query_embedding': query_embedding,
            'filter_category': category,
            'filter_tags': tags,
            'match_count': 10
        }
    ).execute()
    return result.data

# Get related documents
def get_related(document_id: str):
    result = supabase.rpc(
        'get_related_documents',
        {
            'doc_id': document_id,
            'max_results': 5
        }
    ).execute()
    return result.data
```

---

## 7. Implementation Roadmap

### Phase 1: Foundation (Week 1-2)

#### Week 1: Setup & Schema
- [ ] Create Supabase project
- [ ] Enable extensions (pgvector, uuid-ossp, pg_trgm)
- [ ] Create all database tables
- [ ] Create indexes
- [ ] Set up RLS policies
- [ ] Create database functions
- [ ] Write database tests

**Deliverables:**
- Configured Supabase project
- Complete database schema
- Database documentation

#### Week 2: Data Pipeline Development
- [ ] Build file discovery module
- [ ] Build content extraction module
- [ ] Build relationship mapping module
- [ ] Build chunking module
- [ ] Build tag generation module
- [ ] Build embedding generation module
- [ ] Build database population module
- [ ] Implement quality checks

**Deliverables:**
- Complete data processing pipeline
- Unit tests for each module
- Pipeline documentation

### Phase 2: Data Ingestion (Week 3-4)

#### Week 3: Initial Data Load
- [ ] Run file discovery on LibraryRAG
- [ ] Extract and parse all markdown files
- [ ] Build relationship graph
- [ ] Generate chunks
- [ ] Extract and generate tags
- [ ] Generate embeddings (batch processing)
- [ ] Populate documents table
- [ ] Populate document_chunks table
- [ ] Populate cross_references table
- [ ] Populate tags and document_tags tables

**Deliverables:**
- Populated database
- Data quality report
- Ingestion logs

#### Week 4: Image Processing & Card Metadata
- [ ] Process photo card images
- [ ] Extract card metadata from directory structure
- [ ] Link cards to content
- [ ] Generate image embeddings (optional)
- [ ] Populate card_metadata table
- [ ] Validate card-content linkages

**Deliverables:**
- Complete card metadata
- Image processing report

### Phase 3: RAG System Development (Week 5-6)

#### Week 5: Query Interface
- [ ] Implement vector search function
- [ ] Implement hybrid search function
- [ ] Implement filtered search function
- [ ] Implement related document retrieval
- [ ] Build query API
- [ ] Implement caching layer
- [ ] Add rate limiting

**Deliverables:**
- Query API
- API documentation
- Performance benchmarks

#### Week 6: Context Assembly
- [ ] Implement context retrieval logic
- [ ] Implement re-ranking algorithm
- [ ] Build context formatter for LLM
- [ ] Implement citation system
- [ ] Add metadata enrichment
- [ ] Implement related content suggestions

**Deliverables:**
- Context assembly system
- Integration tests
- Example queries and responses

### Phase 4: Testing & Optimization (Week 7-8)

#### Week 7: Testing
- [ ] Create test query dataset (50+ queries)
- [ ] Run retrieval accuracy tests
- [ ] Evaluate search relevance
- [ ] Test filter combinations
- [ ] Test edge cases
- [ ] Load testing
- [ ] User acceptance testing

**Deliverables:**
- Test results report
- Identified issues and fixes
- Performance metrics

#### Week 8: Optimization
- [ ] Optimize embedding generation
- [ ] Optimize index configuration
- [ ] Optimize query performance
- [ ] Implement query caching
- [ ] Optimize chunk sizes
- [ ] Fine-tune re-ranking
- [ ] Implement monitoring

**Deliverables:**
- Optimized system
- Performance comparison report
- Monitoring dashboard

### Phase 5: Deployment & Documentation (Week 9-10)

#### Week 9: Deployment
- [ ] Set up production environment
- [ ] Deploy database
- [ ] Deploy API
- [ ] Configure monitoring
- [ ] Set up backups
- [ ] Implement error handling
- [ ] Set up alerting

**Deliverables:**
- Production deployment
- Deployment documentation
- Operations playbook

#### Week 10: Documentation & Training
- [ ] Write user documentation
- [ ] Write API documentation
- [ ] Create usage examples
- [ ] Write maintenance guide
- [ ] Create training materials
- [ ] Conduct team training

**Deliverables:**
- Complete documentation
- Training materials
- Knowledge base

---

## 8. Query Patterns

### 8.1 Common Query Types

#### Type 1: Semantic Search
**User Intent**: Find content related to a concept

**Example Queries:**
- "How to facilitate a team building session about communication?"
- "Stories about overcoming resistance to change"
- "Reflection questions for leadership development"

**Implementation:**
```python
def semantic_search(query: str, filters: dict = None) -> List[Result]:
    # Generate query embedding
    query_embedding = generate_embedding(query)
    
    # Search with optional filters
    results = supabase.rpc('search_with_filters', {
        'query_embedding': query_embedding,
        'filter_category': filters.get('category'),
        'filter_subcategory': filters.get('subcategory'),
        'filter_tags': filters.get('tags'),
        'match_count': 10
    }).execute()
    
    return results.data
```

#### Type 2: Card-Based Retrieval
**User Intent**: Get content for specific cards

**Example Queries:**
- "What is the meaning of FACES card #15?"
- "Show me reflection questions for the 'open-minded' series"
- "TCG 'Leadership' card facilitation guide"

**Implementation:**
```python
def card_based_search(deck: str, card_number: int = None, series: str = None):
    query = supabase.table('card_metadata') \
        .select('*, documents!inner(*)')
    
    if deck:
        query = query.eq('deck_name', deck)
    if card_number:
        query = query.eq('card_number', card_number)
    if series:
        query = query.eq('series_name', series)
    
    result = query.execute()
    return result.data
```

#### Type 3: Contextual Exploration
**User Intent**: Explore related content

**Example Queries:**
- "What are related activities to 'The Curious Child' story?"
- "Show me similar workshops to 'Transforming Trauma'"
- "Cross-references for FLOW 'Conflict' series"

**Implementation:**
```python
def contextual_exploration(document_id: str, depth: int = 2):
    # Get direct relationships
    related = supabase.rpc('get_related_documents', {
        'doc_id': document_id,
        'max_results': 5
    }).execute()
    
    # Optionally expand to 2nd degree relationships
    if depth > 1:
        for doc in related.data:
            related_2nd = supabase.rpc('get_related_documents', {
                'doc_id': doc['related_doc_id'],
                'max_results': 3
            }).execute()
            # Merge results
    
    return related.data
```

#### Type 4: Filtered Discovery
**User Intent**: Find content matching specific criteria

**Example Queries:**
- "Show me 90-minute workshops for team building"
- "Activities suitable for individuals dealing with transitions"
- "Training materials for AI implementation"

**Implementation:**
```python
def filtered_discovery(filters: dict):
    query = supabase.table('documents') \
        .select('''
            *,
            document_tags!inner(
                tags!inner(*)
            )
        ''')
    
    # Apply category filter
    if 'category' in filters:
        query = query.eq('category', filters['category'])
    
    # Apply tag filters
    if 'tags' in filters:
        for tag in filters['tags']:
            query = query.contains('document_tags.tags.tag_name', [tag])
    
    result = query.execute()
    return result.data
```

#### Type 5: Hierarchical Navigation
**User Intent**: Browse content hierarchy

**Example Queries:**
- "Show me all content in the FACES deck"
- "List all workshops under Personal Development"
- "What are the components of the open-minded series?"

**Implementation:**
```python
def hierarchical_browse(path: List[str]):
    query = supabase.table('documents') \
        .select('*') \
        .contains('hierarchy_path', path) \
        .order('depth', desc=False)
    
    result = query.execute()
    return result.data
```

### 8.2 Advanced Query Patterns

#### Pattern: Multi-Modal Search
Combine text queries with image references

```python
def multimodal_search(text_query: str, image_path: str = None):
    text_embedding = generate_text_embedding(text_query)
    
    results = []
    
    # Text search
    text_results = vector_search(text_embedding, match_count=10)
    results.extend(text_results)
    
    # Image search (if image provided)
    if image_path:
        image_embedding = generate_image_embedding(image_path)
        image_results = image_vector_search(image_embedding, match_count=5)
        results.extend(image_results)
    
    # Deduplicate and re-rank
    deduplicated = deduplicate_results(results)
    ranked = re_rank(deduplicated)
    
    return ranked
```

#### Pattern: Session Context Building
Build context for a facilitation session

```python
def build_session_context(theme: str, duration: str, audience: str):
    # Find relevant activities
    activities = filtered_discovery({
        'category': 'Activities',
        'tags': [theme, duration, audience]
    })
    
    # Find supporting stories
    stories = semantic_search(f"stories about {theme}", {
        'section_type': 'story'
    })
    
    # Find reflection questions
    questions = semantic_search(f"reflection questions for {theme}", {
        'section_type': 'reflection-question'
    })
    
    # Find similar workshops
    workshops = semantic_search(f"workshop for {theme} with {audience}", {
        'subcategory': 'WORKSHOPS'
    })
    
    return {
        'activities': activities,
        'stories': stories,
        'questions': questions,
        'workshops': workshops
    }
```

#### Pattern: Adaptive Context Assembly
Progressively expand context based on relevance

```python
def adaptive_context_assembly(query: str, initial_limit: int = 5, max_tokens: int = 4000):
    context_chunks = []
    current_tokens = 0
    
    # Initial search
    results = semantic_search(query, match_count=initial_limit)
    
    for result in results:
        if current_tokens + result['chunk_tokens'] > max_tokens:
            break
        
        context_chunks.append(result)
        current_tokens += result['chunk_tokens']
        
        # If we have room, add related content
        if current_tokens < max_tokens * 0.7:
            related = get_related_documents(result['document_id'], max_results=2)
            for rel_doc in related:
                if current_tokens + rel_doc['tokens'] > max_tokens:
                    break
                context_chunks.append(rel_doc)
                current_tokens += rel_doc['tokens']
    
    return context_chunks, current_tokens
```

---

## 9. Performance Optimization

### 9.1 Query Optimization

#### Strategy 1: Index Optimization
```sql
-- Monitor index usage
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;

-- Identify missing indexes
SELECT 
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation
FROM pg_stats
WHERE schemaname = 'public'
  AND n_distinct > 100
ORDER BY abs(correlation) DESC;
```

#### Strategy 2: Query Result Caching
```python
from functools import lru_cache
import hashlib

class QueryCache:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.ttl = 3600  # 1 hour
    
    def cache_key(self, query: str, filters: dict) -> str:
        data = f"{query}:{json.dumps(filters, sort_keys=True)}"
        return hashlib.md5(data.encode()).hexdigest()
    
    def get(self, query: str, filters: dict):
        key = self.cache_key(query, filters)
        cached = self.redis.get(key)
        if cached:
            return json.loads(cached)
        return None
    
    def set(self, query: str, filters: dict, results):
        key = self.cache_key(query, filters)
        self.redis.setex(key, self.ttl, json.dumps(results))
```

#### Strategy 3: Embedding Cache
```python
class EmbeddingCache:
    """Cache generated embeddings to avoid redundant API calls"""
    
    def __init__(self, cache_file: str = 'embedding_cache.json'):
        self.cache_file = cache_file
        self.cache = self._load_cache()
    
    def _load_cache(self):
        if os.path.exists(self.cache_file):
            with open(self.cache_file, 'r') as f:
                return json.load(f)
        return {}
    
    def get(self, text: str) -> list:
        text_hash = hashlib.md5(text.encode()).hexdigest()
        return self.cache.get(text_hash)
    
    def set(self, text: str, embedding: list):
        text_hash = hashlib.md5(text.encode()).hexdigest()
        self.cache[text_hash] = embedding
        self._save_cache()
    
    def _save_cache(self):
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f)
```

### 9.2 Embedding Optimization

#### Batch Processing
```python
def batch_embed_chunks(chunks: List[Chunk], batch_size: int = 100):
    embeddings = []
    
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i+batch_size]
        texts = [chunk.text for chunk in batch]
        
        # Batch API call
        response = openai.Embedding.create(
            input=texts,
            model="text-embedding-3-small"
        )
        
        batch_embeddings = [item['embedding'] for item in response['data']]
        embeddings.extend(batch_embeddings)
        
        # Rate limiting
        time.sleep(0.1)
    
    return embeddings
```

#### Dimension Reduction (Optional)
```python
from sklearn.decomposition import PCA

def reduce_embedding_dimensions(embeddings: np.ndarray, target_dim: int = 768):
    """
    Reduce embedding dimensions while preserving semantic meaning
    Trade-off: Lower storage, slightly reduced accuracy
    """
    pca = PCA(n_components=target_dim)
    reduced = pca.fit_transform(embeddings)
    return reduced
```

### 9.3 Database Optimization

#### Connection Pooling
```python
from supabase import create_client
import os

class SupabasePool:
    def __init__(self, pool_size: int = 10):
        self.pool_size = pool_size
        self.url = os.environ.get("SUPABASE_URL")
        self.key = os.environ.get("SUPABASE_KEY")
        self.pool = [create_client(self.url, self.key) for _ in range(pool_size)]
        self.current = 0
    
    def get_client(self):
        client = self.pool[self.current]
        self.current = (self.current + 1) % self.pool_size
        return client
```

#### Batch Inserts
```python
def batch_insert_chunks(chunks: List[dict], batch_size: int = 500):
    """
    Insert chunks in batches for better performance
    """
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i+batch_size]
        supabase.table('document_chunks').insert(batch).execute()
        print(f"Inserted {min(i+batch_size, len(chunks))}/{len(chunks)} chunks")
```

#### Vacuum and Analyze
```sql
-- Regular maintenance
VACUUM ANALYZE documents;
VACUUM ANALYZE document_chunks;
VACUUM ANALYZE cross_references;

-- Reindex for optimal performance
REINDEX TABLE document_chunks;
```

### 9.4 Monitoring & Metrics

```python
import time
from dataclasses import dataclass
from typing import List

@dataclass
class QueryMetrics:
    query: str
    execution_time: float
    results_count: int
    cache_hit: bool
    timestamp: float

class PerformanceMonitor:
    def __init__(self):
        self.metrics: List[QueryMetrics] = []
    
    def record_query(self, query: str, execution_time: float, results_count: int, cache_hit: bool):
        self.metrics.append(QueryMetrics(
            query=query,
            execution_time=execution_time,
            results_count=results_count,
            cache_hit=cache_hit,
            timestamp=time.time()
        ))
    
    def get_stats(self):
        total_queries = len(self.metrics)
        avg_time = sum(m.execution_time for m in self.metrics) / total_queries
        cache_hit_rate = sum(1 for m in self.metrics if m.cache_hit) / total_queries
        
        return {
            'total_queries': total_queries,
            'avg_execution_time': avg_time,
            'cache_hit_rate': cache_hit_rate
        }
```

---

## 10. Testing Strategy

### 10.1 Test Dataset Creation

#### Test Query Categories
1. **Semantic Queries** (20 queries)
   - "How to facilitate a dialogue about conflict?"
   - "Stories about personal transformation"
   - "Reflection questions for team building"

2. **Card Queries** (15 queries)
   - "FACES open-minded card #5"
   - "TCG Leadership building block"
   - "FLOW conflict series overview"

3. **Filtered Queries** (15 queries)
   - "90-minute workshops for teams"
   - "AI training materials"
   - "Personal development activities"

4. **Contextual Queries** (10 queries)
   - "Related content to 'The Curious Child' story"
   - "Similar workshops to 'Transforming Trauma'"

#### Ground Truth Dataset
```json
[
  {
    "query": "How to facilitate a dialogue about conflict?",
    "expected_categories": ["Activities", "Trainings"],
    "expected_subcategories": ["FLOW", "SPEAK", "INTERACTION"],
    "expected_content_types": ["facilitation-guide", "reflection-questions", "stories"],
    "expected_tags": ["conflict", "facilitation", "dialogue"],
    "relevant_documents": [
      "LibraryRAG/Activities/FLOW/conflict-series/README.md",
      "LibraryRAG/Activities/SPEAK/...",
      "LibraryRAG/Trainings/INTERACTION/..."
    ]
  }
  // ... more test cases
]
```

### 10.2 Evaluation Metrics

#### Metric 1: Retrieval Accuracy
```python
def calculate_precision_recall(retrieved: List[str], relevant: List[str]) -> dict:
    """
    Precision = (relevant retrieved) / (total retrieved)
    Recall = (relevant retrieved) / (total relevant)
    """
    retrieved_set = set(retrieved)
    relevant_set = set(relevant)
    
    true_positives = len(retrieved_set.intersection(relevant_set))
    
    precision = true_positives / len(retrieved_set) if retrieved_set else 0
    recall = true_positives / len(relevant_set) if relevant_set else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    return {
        'precision': precision,
        'recall': recall,
        'f1_score': f1
    }
```

#### Metric 2: Mean Reciprocal Rank (MRR)
```python
def calculate_mrr(test_cases: List[dict]) -> float:
    """
    Measures how quickly relevant results appear
    MRR = average of (1 / rank of first relevant result)
    """
    reciprocal_ranks = []
    
    for test_case in test_cases:
        retrieved = test_case['retrieved']
        relevant = set(test_case['relevant'])
        
        for i, doc in enumerate(retrieved, 1):
            if doc in relevant:
                reciprocal_ranks.append(1.0 / i)
                break
        else:
            reciprocal_ranks.append(0)
    
    return sum(reciprocal_ranks) / len(reciprocal_ranks)
```

#### Metric 3: Normalized Discounted Cumulative Gain (NDCG)
```python
import numpy as np

def calculate_ndcg(retrieved: List[str], relevant: dict, k: int = 10) -> float:
    """
    Measures ranking quality with graded relevance
    relevant = {doc_id: relevance_score} where relevance_score is 0-3
    """
    dcg = sum(
        (2**relevant.get(doc, 0) - 1) / np.log2(i + 2)
        for i, doc in enumerate(retrieved[:k])
    )
    
    ideal_ranking = sorted(relevant.values(), reverse=True)
    idcg = sum(
        (2**rel - 1) / np.log2(i + 2)
        for i, rel in enumerate(ideal_ranking[:k])
    )
    
    return dcg / idcg if idcg > 0 else 0
```

### 10.3 Test Suite

```python
class RAGTestSuite:
    def __init__(self, test_dataset: List[dict]):
        self.test_dataset = test_dataset
        self.results = []
    
    def run_tests(self):
        for test_case in self.test_dataset:
            result = self._run_single_test(test_case)
            self.results.append(result)
        
        return self._aggregate_results()
    
    def _run_single_test(self, test_case: dict) -> dict:
        query = test_case['query']
        filters = test_case.get('filters', {})
        
        # Execute search
        start_time = time.time()
        retrieved = semantic_search(query, filters)
        execution_time = time.time() - start_time
        
        # Extract document IDs
        retrieved_ids = [r['document_id'] for r in retrieved]
        relevant_ids = test_case['relevant_documents']
        
        # Calculate metrics
        metrics = calculate_precision_recall(retrieved_ids, relevant_ids)
        metrics['execution_time'] = execution_time
        
        return {
            'query': query,
            'metrics': metrics,
            'retrieved_count': len(retrieved_ids)
        }
    
    def _aggregate_results(self) -> dict:
        avg_precision = np.mean([r['metrics']['precision'] for r in self.results])
        avg_recall = np.mean([r['metrics']['recall'] for r in self.results])
        avg_f1 = np.mean([r['metrics']['f1_score'] for r in self.results])
        avg_time = np.mean([r['metrics']['execution_time'] for r in self.results])
        
        return {
            'avg_precision': avg_precision,
            'avg_recall': avg_recall,
            'avg_f1_score': avg_f1,
            'avg_execution_time': avg_time,
            'total_tests': len(self.results)
        }
```

### 10.4 Performance Tests

```python
class PerformanceTests:
    def test_query_latency(self, num_queries: int = 100):
        """Test query response times"""
        latencies = []
        
        for _ in range(num_queries):
            query = random.choice(self.test_queries)
            start = time.time()
            semantic_search(query)
            latencies.append(time.time() - start)
        
        return {
            'mean': np.mean(latencies),
            'median': np.median(latencies),
            'p95': np.percentile(latencies, 95),
            'p99': np.percentile(latencies, 99)
        }
    
    def test_concurrent_queries(self, num_concurrent: int = 10):
        """Test system under concurrent load"""
        import concurrent.futures
        
        def run_query():
            query = random.choice(self.test_queries)
            start = time.time()
            semantic_search(query)
            return time.time() - start
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_concurrent) as executor:
            futures = [executor.submit(run_query) for _ in range(num_concurrent)]
            latencies = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        return {
            'mean': np.mean(latencies),
            'max': max(latencies),
            'min': min(latencies)
        }
```

---

## 11. Next Steps & Recommendations

### 11.1 Immediate Actions

1. **Review and Approve Plan**
   - Stakeholder review
   - Budget approval
   - Timeline confirmation

2. **Set Up Development Environment**
   - Create Supabase project
   - Set up development database
   - Configure API keys

3. **Build Proof of Concept**
   - Test with small subset (e.g., FACES deck only)
   - Validate approach
   - Gather feedback

### 11.2 Future Enhancements

1. **Multi-Language Support**
   - Add support for multiple languages
   - Language-specific embeddings
   - Cross-language search

2. **Advanced Features**
   - Image search using CLIP embeddings
   - Audio/video content integration
   - Real-time content updates

3. **User Personalization**
   - User preference learning
   - Personalized recommendations
   - Usage analytics

4. **Integration Capabilities**
   - API for external applications
   - Plugin system
   - Webhook notifications

### 11.3 Success Criteria

1. **Functional Requirements**
   - ✅ All content successfully ingested
   - ✅ Search returns relevant results
   - ✅ Cross-references preserved
   - ✅ Metadata accurately captured

2. **Performance Requirements**
   - ✅ Query latency < 500ms (p95)
   - ✅ Precision > 0.8 for semantic queries
   - ✅ Recall > 0.7 for semantic queries
   - ✅ System handles 100+ concurrent queries

3. **Quality Requirements**
   - ✅ Content integrity maintained
   - ✅ Relationships accurately mapped
   - ✅ Tags are meaningful and useful
   - ✅ User satisfaction > 4/5

---

## 12. Budget & Resources

### 12.1 Infrastructure Costs (Monthly)

| Item | Cost | Notes |
|------|------|-------|
| Supabase Pro | $25 | Database + 8GB bandwidth |
| OpenAI API (Embeddings) | $50-100 | ~5M tokens (initial), ~1M/month maintenance |
| OpenAI API (Query) | $100-200 | For query embedding generation |
| Redis Cache (optional) | $10-20 | For query caching |
| **Total** | **$185-345/month** | After initial setup |

### 12.2 Initial Setup Costs

| Item | Cost | Notes |
|------|------|-------|
| Embedding Generation | $150-300 | One-time for ~10,000 chunks |
| Development Time | $20,000-40,000 | 10 weeks × $2k-4k/week |
| Testing & QA | $5,000-10,000 | 2 weeks |
| **Total Initial** | **$25,150-50,300** | |

### 12.3 Team Resources

| Role | Time Commitment | Duration |
|------|-----------------|----------|
| Backend Developer | Full-time | 8 weeks |
| Data Engineer | Full-time | 4 weeks |
| QA Engineer | Part-time (50%) | 4 weeks |
| Product Manager | Part-time (25%) | 10 weeks |

---

## Appendix A: Technology Stack

### Core Technologies
- **Database**: Supabase (PostgreSQL + pgvector)
- **Embedding Model**: OpenAI text-embedding-3-small
- **Backend**: Python 3.10+
- **Caching**: Redis (optional)
- **Monitoring**: Supabase built-in + custom dashboards

### Python Libraries
```txt
supabase==2.0.0
openai==1.0.0
numpy==1.24.0
pandas==2.0.0
markdown==3.4.0
beautifulsoup4==4.12.0
scikit-learn==1.3.0
pytest==7.4.0
```

---

## Appendix B: Sample Code

See implementation examples throughout the document for:
- Database schema creation (Section 2)
- Data processing pipeline (Section 3)
- Supabase functions (Section 6)
- Query patterns (Section 8)
- Testing suite (Section 10)

---

## Appendix C: Glossary

- **RAG**: Retrieval-Augmented Generation - AI technique combining retrieval and generation
- **Embedding**: Numerical vector representation of text
- **pgvector**: PostgreSQL extension for vector operations
- **Chunking**: Splitting documents into smaller, manageable pieces
- **Vector Search**: Finding similar content using vector similarity
- **Hybrid Search**: Combining vector search with keyword search
- **Cross-Reference**: Link between related documents
- **Metadata**: Descriptive information about content

---

**End of Plan**

**Document Version**: 1.0  
**Last Updated**: October 3, 2025  
**Status**: DRAFT - Pending Review

