# LibraryRAG - System Architecture

**Visual Reference**: System architecture for RAG implementation with Supabase

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │  Search  │  │ Browse   │  │ Filters  │  │ Related  │      │
│  │  Query   │  │ Content  │  │ & Tags   │  │ Content  │      │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘      │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                          API LAYER                              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Query Processing → Embedding → Search → Re-ranking     │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
┌──────────────┐  ┌─────────────┐  ┌─────────────┐
│   OpenAI     │  │  Supabase   │  │   Redis     │
│  Embeddings  │  │  Database   │  │   Cache     │
│              │  │             │  │             │
│ text-embed   │  │ PostgreSQL  │  │ Query       │
│ -3-small     │  │ + pgvector  │  │ Results     │
└──────────────┘  └─────────────┘  └─────────────┘
```

---

## Data Flow Architecture

### 1. Data Ingestion Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                    LIBRARYRAG CONTENT                           │
│  Activities (877 files) + Trainings (133 files) = 1,010 files  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│               STAGE 1: FILE DISCOVERY                           │
│  • Scan directory structure                                     │
│  • Extract file metadata                                        │
│  • Build hierarchy map                                          │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│               STAGE 2: CONTENT EXTRACTION                       │
│  • Parse markdown                                               │
│  • Extract sections                                             │
│  • Identify cross-references                                    │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│               STAGE 3: RELATIONSHIP MAPPING                     │
│  • Build relationship graph                                     │
│  • Identify cross-references                                    │
│  • Calculate relationship strength                              │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│               STAGE 4: CONTENT CHUNKING                         │
│  • Split by sections (## headers)                               │
│  • Target 500 tokens per chunk                                  │
│  • Preserve context                                             │
│  • ~5,000-15,000 chunks total                                   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│               STAGE 5: TAG GENERATION                           │
│  • Extract explicit tags                                        │
│  • Generate thematic tags                                       │
│  • 8 tag categories, 200+ unique tags                           │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│               STAGE 6: EMBEDDING GENERATION                     │
│  • Batch processing (100 chunks)                                │
│  • OpenAI text-embedding-3-small                                │
│  • 1536 dimensions per embedding                                │
│  • Cache embeddings                                             │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│               STAGE 7: DATABASE POPULATION                      │
│  • Insert documents                                             │
│  • Insert chunks with embeddings                                │
│  • Insert relationships                                         │
│  • Insert tags                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Query Processing Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER QUERY                                   │
│  "How to facilitate a team dialogue about conflict?"            │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                 QUERY PREPROCESSING                             │
│  • Parse query                                                  │
│  • Extract filters                                              │
│  • Identify intent                                              │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│               EMBEDDING GENERATION                              │
│  • Generate query embedding (OpenAI)                            │
│  • Check embedding cache                                        │
│  • Vector: [0.123, -0.456, ..., 0.789] (1536 dims)            │
└────────────────────────┬────────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
┌──────────────┐  ┌─────────────┐  ┌─────────────┐
│   Vector     │  │  Keyword    │  │   Filter    │
│   Search     │  │  Search     │  │   Search    │
│              │  │             │  │             │
│ Cosine       │  │ Full-text   │  │ Category,   │
│ Similarity   │  │ Search      │  │ Tags, etc.  │
└──────┬───────┘  └──────┬──────┘  └──────┬──────┘
       │                 │                 │
       └────────┬────────┴────────┬────────┘
                │                 │
                ▼                 ▼
┌─────────────────────────────────────────────────────────────────┐
│               HYBRID SEARCH RESULTS                             │
│  • Combine vector + keyword scores                              │
│  • Weight: 70% vector, 30% keyword                              │
│  • Apply filters                                                │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│               RE-RANKING                                        │
│  • Boost recent content                                         │
│  • Boost complete matches                                       │
│  • Consider user preferences                                    │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│               CONTEXT ASSEMBLY                                  │
│  • Retrieve top-k chunks (k=10)                                 │
│  • Get related documents                                        │
│  • Assemble context window                                      │
│  • Add metadata                                                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│               CACHE RESULTS                                     │
│  • Store in Redis                                               │
│  • TTL: 1 hour                                                  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│               RETURN TO USER                                    │
│  • Formatted results                                            │
│  • Citations with links                                         │
│  • Related content suggestions                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Database Schema Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                         documents                                │
├──────────────────────────────────────────────────────────────────┤
│ • id (PK)                     UUID                               │
│ • file_path                   TEXT (UNIQUE)                      │
│ • file_name                   TEXT                               │
│ • content                     TEXT                               │
│ • content_type                TEXT                               │
│ • category                    TEXT                               │
│ • subcategory                 TEXT                               │
│ • content_subtype             TEXT                               │
│ • parent_id (FK)              UUID → documents.id               │
│ • hierarchy_path              TEXT[]                             │
│ • depth                       INTEGER                            │
│ • created_at, updated_at      TIMESTAMP                          │
└───────────────┬──────────────────────────────────────────────────┘
                │
                │ 1:N
                │
                ▼
┌──────────────────────────────────────────────────────────────────┐
│                      document_chunks                             │
├──────────────────────────────────────────────────────────────────┤
│ • id (PK)                     UUID                               │
│ • document_id (FK)            UUID → documents.id               │
│ • chunk_text                  TEXT                               │
│ • chunk_index                 INTEGER                            │
│ • chunk_tokens                INTEGER                            │
│ • section_title               TEXT                               │
│ • section_type                TEXT                               │
│ • embedding                   VECTOR(1536) ⭐                    │
│ • created_at                  TIMESTAMP                          │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                     cross_references                             │
├──────────────────────────────────────────────────────────────────┤
│ • id (PK)                     UUID                               │
│ • source_document_id (FK)     UUID → documents.id               │
│ • target_document_id (FK)     UUID → documents.id               │
│ • reference_type              TEXT                               │
│ • relationship_strength       FLOAT                              │
│ • context                     TEXT                               │
│ • created_at                  TIMESTAMP                          │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                           tags                                   │
├──────────────────────────────────────────────────────────────────┤
│ • id (PK)                     UUID                               │
│ • tag_name                    TEXT (UNIQUE)                      │
│ • tag_category                TEXT                               │
│ • description                 TEXT                               │
│ • created_at                  TIMESTAMP                          │
└───────────────┬──────────────────────────────────────────────────┘
                │
                │ N:M via document_tags
                │
                ▼
┌──────────────────────────────────────────────────────────────────┐
│                      document_tags                               │
├──────────────────────────────────────────────────────────────────┤
│ • document_id (FK, PK)        UUID → documents.id               │
│ • tag_id (FK, PK)             UUID → tags.id                    │
│ • relevance_score             FLOAT                              │
│ • created_at                  TIMESTAMP                          │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                      card_metadata                               │
├──────────────────────────────────────────────────────────────────┤
│ • id (PK)                     UUID                               │
│ • card_type                   TEXT                               │
│ • deck_name                   TEXT                               │
│ • card_number                 INTEGER                            │
│ • card_name                   TEXT                               │
│ • series_name                 TEXT                               │
│ • series_index                INTEGER                            │
│ • document_id (FK)            UUID → documents.id               │
│ • image_url                   TEXT                               │
│ • themes                      TEXT[]                             │
│ • emotions                    TEXT[]                             │
│ • use_cases                   TEXT[]                             │
│ • created_at                  TIMESTAMP                          │
└──────────────────────────────────────────────────────────────────┘

Legend:
  PK = Primary Key
  FK = Foreign Key
  ⭐ = Vector embedding (special type)
  1:N = One-to-Many relationship
  N:M = Many-to-Many relationship
```

---

## Technology Stack Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     FRONTEND LAYER                              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Web UI (Optional)                                       │  │
│  │  • React / Vue / Svelte                                  │  │
│  │  • Search interface                                      │  │
│  │  • Result display                                        │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTPS
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                     APPLICATION LAYER                           │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  API Server (Optional)                                   │  │
│  │  • FastAPI / Flask / Express                             │  │
│  │  • Query processing                                      │  │
│  │  • Authentication                                        │  │
│  │  • Rate limiting                                         │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
┌──────────────┐  ┌─────────────┐  ┌─────────────┐
│   OpenAI     │  │  Supabase   │  │   Redis     │
│              │  │             │  │  (Optional) │
│ Embeddings   │  │ PostgreSQL  │  │             │
│ API          │  │ + pgvector  │  │ Caching     │
│              │  │ + Edge Fns  │  │ Layer       │
│ text-embed-  │  │             │  │             │
│ 3-small      │  │ Built-in    │  │ Query       │
│              │  │ Vector      │  │ Results     │
│ 1536 dims    │  │ Search      │  │             │
└──────────────┘  └─────────────┘  └─────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                     DATA LAYER                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  LibraryRAG Content                                      │  │
│  │  • 707 Markdown files                                    │  │
│  │  • 303 PNG images                                        │  │
│  │  • Organized hierarchy                                   │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                     PROCESSING LAYER                            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Data Pipeline (Python)                                  │  │
│  │  • File discovery                                        │  │
│  │  • Content extraction                                    │  │
│  │  • Chunking                                              │  │
│  │  • Embedding generation                                  │  │
│  │  • Database population                                   │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                     MONITORING LAYER                            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  • Supabase Dashboard                                    │  │
│  │  • Custom metrics                                        │  │
│  │  • Performance monitoring                                │  │
│  │  • Error tracking                                        │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Deployment Architecture

### Development Environment

```
┌──────────────────────────────────────────┐
│       LOCAL MACHINE                      │
│                                          │
│  ┌────────────────────────────────────┐ │
│  │  Development Database              │ │
│  │  (Supabase Local / Docker)         │ │
│  └────────────────────────────────────┘ │
│                                          │
│  ┌────────────────────────────────────┐ │
│  │  Python Environment                │ │
│  │  • Virtual environment             │ │
│  │  • Development dependencies        │ │
│  └────────────────────────────────────┘ │
│                                          │
│  ┌────────────────────────────────────┐ │
│  │  Code Editor (Cursor/VS Code)      │ │
│  └────────────────────────────────────┘ │
└──────────────────────────────────────────┘
```

### Production Environment

```
┌─────────────────────────────────────────────────────────────────┐
│                         PRODUCTION                              │
│                                                                 │
│  ┌────────────────────────────────────────────────────────────┐│
│  │  Supabase Cloud (Production)                               ││
│  │  • PostgreSQL + pgvector                                   ││
│  │  • Edge Functions                                          ││
│  │  • Built-in authentication                                 ││
│  │  • Automatic backups                                       ││
│  │  • CDN for static assets                                   ││
│  └────────────────────────────────────────────────────────────┘│
│                                                                 │
│  ┌────────────────────────────────────────────────────────────┐│
│  │  Redis Cloud (Optional)                                    ││
│  │  • Query caching                                           ││
│  │  • Session management                                      ││
│  └────────────────────────────────────────────────────────────┘│
│                                                                 │
│  ┌────────────────────────────────────────────────────────────┐│
│  │  API Server (Optional - Vercel/Railway/Render)            ││
│  │  • Custom business logic                                   ││
│  │  • Rate limiting                                           ││
│  │  • Custom authentication                                   ││
│  └────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

---

## Security Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    SECURITY LAYERS                              │
│                                                                 │
│  Layer 1: Network Security                                     │
│  ├─ HTTPS/TLS encryption                                       │
│  ├─ Supabase built-in DDoS protection                          │
│  └─ IP allowlisting (optional)                                 │
│                                                                 │
│  Layer 2: Authentication & Authorization                       │
│  ├─ Supabase Auth (JWT tokens)                                 │
│  ├─ Row Level Security (RLS) policies                          │
│  ├─ API key authentication                                     │
│  └─ Rate limiting per user/IP                                  │
│                                                                 │
│  Layer 3: Data Security                                        │
│  ├─ Encrypted at rest (Supabase)                               │
│  ├─ Encrypted in transit (TLS)                                 │
│  ├─ Regular backups                                            │
│  └─ No PII in embeddings                                       │
│                                                                 │
│  Layer 4: Application Security                                 │
│  ├─ Input validation                                           │
│  ├─ SQL injection prevention (prepared statements)             │
│  ├─ XSS protection                                             │
│  └─ CORS configuration                                         │
│                                                                 │
│  Layer 5: Monitoring & Auditing                                │
│  ├─ Access logs                                                │
│  ├─ Query monitoring                                           │
│  ├─ Error tracking                                             │
│  └─ Anomaly detection                                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Performance Optimization Layers

```
┌─────────────────────────────────────────────────────────────────┐
│                    OPTIMIZATION STRATEGY                        │
│                                                                 │
│  ┌────────────────────────────────────────────────────────────┐│
│  │  Level 1: Request Level                                    ││
│  │  • Query result caching (Redis)                            ││
│  │  • Embedding caching                                       ││
│  │  • Response compression                                    ││
│  └────────────────────────────────────────────────────────────┘│
│                                                                 │
│  ┌────────────────────────────────────────────────────────────┐│
│  │  Level 2: Database Level                                   ││
│  │  • Optimized indexes (B-tree, GIN, IVFFlat)               ││
│  │  • Connection pooling                                      ││
│  │  • Query optimization                                      ││
│  │  • Regular VACUUM and ANALYZE                              ││
│  └────────────────────────────────────────────────────────────┘│
│                                                                 │
│  ┌────────────────────────────────────────────────────────────┐│
│  │  Level 3: Application Level                                ││
│  │  • Batch processing                                        ││
│  │  • Async operations                                        ││
│  │  • Lazy loading                                            ││
│  │  • Code optimization                                       ││
│  └────────────────────────────────────────────────────────────┘│
│                                                                 │
│  ┌────────────────────────────────────────────────────────────┐│
│  │  Level 4: Infrastructure Level                             ││
│  │  • CDN for static assets                                   ││
│  │  • Load balancing                                          ││
│  │  • Auto-scaling                                            ││
│  │  • Edge functions                                          ││
│  └────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘

Target Performance Metrics:
  ✓ Query latency: < 500ms (p95)
  ✓ Throughput: 100+ concurrent queries
  ✓ Cache hit rate: > 70%
  ✓ Embedding reuse: > 90%
```

---

## Monitoring Dashboard View

```
┌─────────────────────────────────────────────────────────────────┐
│                    MONITORING DASHBOARD                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  📊 SYSTEM HEALTH                                              │
│  ├─ Database Status:     ✅ Healthy                            │
│  ├─ API Status:          ✅ Online                             │
│  ├─ Cache Status:        ✅ Connected                          │
│  └─ Uptime:              99.8%                                 │
│                                                                 │
│  📈 PERFORMANCE METRICS                                        │
│  ├─ Avg Query Time:      287ms                                 │
│  ├─ P95 Query Time:      456ms                                 │
│  ├─ P99 Query Time:      678ms                                 │
│  ├─ Cache Hit Rate:      76.3%                                 │
│  └─ Error Rate:          0.02%                                 │
│                                                                 │
│  💾 STORAGE                                                    │
│  ├─ Documents:           707                                   │
│  ├─ Chunks:              8,432                                 │
│  ├─ Embeddings:          8,432                                 │
│  ├─ Database Size:       2.3 GB                                │
│  └─ Cache Size:          145 MB                                │
│                                                                 │
│  🔍 SEARCH ANALYTICS                                           │
│  ├─ Queries Today:       1,247                                 │
│  ├─ Avg Results:         8.2 per query                         │
│  ├─ Top Categories:      Activities (67%), Trainings (33%)     │
│  └─ Popular Tags:        leadership, team-building, conflict   │
│                                                                 │
│  💰 COST TRACKING                                              │
│  ├─ OpenAI API:          $12.34 this month                     │
│  ├─ Supabase:            $25.00/month                          │
│  ├─ Redis:               $15.00/month                          │
│  └─ Total:               $52.34 this month                     │
│                                                                 │
│  ⚠️  ALERTS                                                    │
│  ├─ No critical alerts                                         │
│  └─ 1 warning: Cache fill ratio at 85%                         │
└─────────────────────────────────────────────────────────────────┘
```

---

## Integration Points

```
┌─────────────────────────────────────────────────────────────────┐
│                    EXTERNAL INTEGRATIONS                        │
│                                                                 │
│  Input Sources:                                                │
│  ┌────────────────────────────────────────────────────────────┐│
│  │  • LibraryRAG files (markdown + images)                    ││
│  │  • Additional content sources (future)                     ││
│  │  • User-generated content (future)                         ││
│  └────────────────────────────────────────────────────────────┘│
│                                                                 │
│  Output Consumers:                                             │
│  ┌────────────────────────────────────────────────────────────┐│
│  │  • Web applications                                        ││
│  │  • Mobile apps                                             ││
│  │  • Chatbots / AI assistants                               ││
│  │  • Third-party integrations (via API)                     ││
│  └────────────────────────────────────────────────────────────┘│
│                                                                 │
│  APIs:                                                         │
│  ┌────────────────────────────────────────────────────────────┐│
│  │  POST   /api/search                                        ││
│  │  GET    /api/documents/{id}                                ││
│  │  GET    /api/related/{id}                                  ││
│  │  GET    /api/cards/{deck}/{number}                         ││
│  │  POST   /api/filter                                        ││
│  └────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

---

## Scalability Path

```
Current (MVP)                Future (Scale)
└─ 700 docs                  └─ 10,000+ docs
└─ 8,000 chunks              └─ 100,000+ chunks
└─ 10 queries/min            └─ 1,000+ queries/min
└─ 1 language                └─ Multiple languages
└─ Text only                 └─ Text + images + video
└─ Single tenant             └─ Multi-tenant
└─ Basic search              └─ Personalized AI
```

---

## Summary

This architecture provides:

✅ **Scalable** - Handles growing content and query volume  
✅ **Performant** - Sub-500ms query response times  
✅ **Reliable** - Built on proven technologies  
✅ **Secure** - Multiple security layers  
✅ **Maintainable** - Clear separation of concerns  
✅ **Cost-Effective** - Optimized resource usage  
✅ **Extensible** - Easy to add new features  

---

**Next Steps**: Refer to `RAG_PREPARATION_PLAN.md` for detailed implementation guidance.

