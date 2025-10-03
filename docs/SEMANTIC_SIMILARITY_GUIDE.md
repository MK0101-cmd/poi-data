# 🔍 Semantic Similarity Detection Guide

## Overview

The Semantic Similarity Detection system is the **9th type of relationship detection** in the LibraryRAG pipeline. Unlike the 8 pattern-based detection methods, semantic similarity uses **vector embeddings** to find documents that are conceptually similar, even if they don't share explicit links, naming patterns, or references.

## Key Concepts

### What is Semantic Similarity?

Semantic similarity measures how similar two pieces of text are in **meaning**, not just in words. It uses:

- **Vector Embeddings**: Numerical representations of text that capture semantic meaning
- **Cosine Similarity**: Mathematical measure of similarity between embedding vectors
- **Threshold-Based Detection**: Documents above a similarity threshold are considered related

### Why Add Semantic Similarity?

The 8 pattern-based detections are excellent at finding **explicit relationships**:
- Markdown links
- Card references
- Building block connections
- Folder structure

But they miss **implicit relationships** where documents:
- Discuss similar topics using different terminology
- Share conceptual themes without explicit references
- Are semantically related but structurally isolated

**Semantic similarity bridges this gap**, creating a more complete relationship graph.

---

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────┐
│         Semantic Similarity System                  │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌──────────────────┐         ┌─────────────────┐ │
│  │   Embedding      │         │   Similarity    │ │
│  │   Cache          │◄────────┤   Detector      │ │
│  │   (Disk)         │         │                 │ │
│  └──────────────────┘         └────────┬────────┘ │
│                                        │          │
│  ┌──────────────────┐         ┌────────▼────────┐ │
│  │   Document       │◄────────┤   Integration   │ │
│  │   Embeddings     │         │   Layer         │ │
│  │   (Memory)       │         └────────┬────────┘ │
│  └──────────────────┘                  │          │
│                                        │          │
│  ┌──────────────────┐         ┌────────▼────────┐ │
│  │   Similarity     │         │  Relationship   │ │
│  │   Cache          │         │  Detector       │ │
│  │   (Memory)       │         │  (Enhanced)     │ │
│  └──────────────────┘         └─────────────────┘ │
└─────────────────────────────────────────────────────┘
```

### Key Classes

#### 1. `SemanticSimilarityDetector`

**Purpose**: Core engine for computing and caching semantic similarities.

**Key Features**:
- Embedding management and caching
- Cosine similarity calculation
- Similar document finding
- Cluster detection
- Statistics generation

**Configuration**:
```python
detector = SemanticSimilarityDetector(
    similarity_threshold=0.75,  # Min similarity (0.0-1.0)
    top_k=10,                   # Max similar docs to return
    use_cache=True,             # Enable embedding cache
    cache_path="embedding_cache.json"
)
```

#### 2. `SemanticSimilarityIntegration`

**Purpose**: Integrates semantic similarity with the existing `EnhancedRelationshipDetector`.

**How It Works**:
1. Patches the `detect_all_relationships` method
2. Runs all 8 pattern-based detections first
3. Adds semantic similarity detection
4. Excludes already-detected relationships
5. Deduplicates and returns combined results

---

## Usage

### Basic Usage

```python
from scripts.semantic_similarity import SemanticSimilarityDetector

# Initialize detector
detector = SemanticSimilarityDetector(
    similarity_threshold=0.75,
    top_k=10
)

# Add document embeddings
detector.add_document_embedding(
    file_path='doc1.md',
    content='Leadership and team management...',
    embedding=embedding_vector
)

# Find similar documents
similar = detector.find_similar_documents('doc1.md')

for doc in similar:
    print(f"{doc.target_path}: {doc.similarity_score:.3f}")
```

### Batch Processing

```python
# Prepare documents
documents = [
    {'file_path': 'doc1.md', 'content': '...'},
    {'file_path': 'doc2.md', 'content': '...'},
    # ... more documents
]

# Batch add with embedding generator
detector.batch_add_embeddings(
    documents,
    embedding_generator=generate_embedding  # Your embedding function
)

# This automatically uses cache and batches API calls
```

### Integration with Pipeline

```python
from scripts.pipeline_instrumented import InstrumentedLibraryRAGPipeline

# Create pipeline with semantic similarity enabled
pipeline = InstrumentedLibraryRAGPipeline(
    root_path="LibraryRAG",
    enable_semantic_similarity=True,
    similarity_threshold=0.75,
    top_k_similar=10
)

# Run pipeline
pipeline.run(generate_reports=True)

# Semantic similarities are automatically:
# 1. Computed during processing
# 2. Integrated into relationship detection
# 3. Saved in semantic_similarity_report.json
```

---

## Configuration Options

### Similarity Threshold

**Range**: 0.0 to 1.0  
**Default**: 0.75  
**Meaning**: Minimum cosine similarity for documents to be considered related

**Guidance**:
- **0.9-1.0**: Very similar (almost identical topics)
- **0.8-0.9**: Highly similar (same topic, different perspectives)
- **0.7-0.8**: Moderately similar (related topics)
- **0.6-0.7**: Somewhat similar (overlapping themes)
- **< 0.6**: Weakly similar (may produce noise)

**Example**:
```python
# Strict: Only very similar documents
detector = SemanticSimilarityDetector(similarity_threshold=0.85)

# Relaxed: Capture more relationships
detector = SemanticSimilarityDetector(similarity_threshold=0.70)
```

### Top-K Similar Documents

**Range**: 1 to ∞  
**Default**: 10  
**Meaning**: Maximum number of similar documents to return per document

**Guidance**:
- **5-10**: Good for focused relationships
- **10-20**: Comprehensive but manageable
- **> 20**: May produce too many relationships

**Example**:
```python
# Return only top 5 most similar
detector = SemanticSimilarityDetector(top_k=5)

# Return top 20 for comprehensive mapping
detector = SemanticSimilarityDetector(top_k=20)
```

### Caching

**Options**: `use_cache=True/False`  
**Default**: `True`  
**Cache File**: `embedding_cache.json`

**Benefits**:
- Avoids redundant API calls
- Speeds up repeated processing
- Reduces costs

**Cache Structure**:
```json
{
  "md5_hash_of_content": [0.123, 0.456, ...],
  "another_content_hash": [0.789, 0.012, ...]
}
```

---

## Advanced Features

### 1. Find Clusters

Automatically groups documents into semantic clusters:

```python
clusters = detector.find_clusters(
    min_cluster_size=3,        # At least 3 docs per cluster
    min_intra_similarity=0.8   # Avg similarity within cluster
)

for i, cluster in enumerate(clusters, 1):
    print(f"Cluster {i}: {len(cluster)} documents")
    for path in cluster:
        print(f"  - {path}")
```

**Use Cases**:
- Identify topic groups
- Discover content silos
- Guide content organization

### 2. Similarity Matrix

Generate a full similarity matrix for analysis:

```python
matrix, file_paths = detector.get_similarity_matrix()

# matrix[i][j] = similarity between file_paths[i] and file_paths[j]

# Find most similar pair
import numpy as np
i, j = np.unravel_index(np.argmax(matrix), matrix.shape)
print(f"Most similar: {file_paths[i]} <-> {file_paths[j]}")
print(f"Similarity: {matrix[i][j]:.3f}")
```

### 3. Query by Content

Find similar documents without adding to index:

```python
query = "How to improve team collaboration and leadership?"

similar = detector.find_similar_by_content(
    content=query,
    embedding_generator=generate_embedding,
    min_similarity=0.7
)

for doc in similar:
    print(f"{doc.target_path}: {doc.similarity_score:.3f}")
```

**Use Cases**:
- Ad-hoc searches
- User queries
- Content recommendations

### 4. Statistics and Analysis

Get comprehensive statistics:

```python
stats = detector.get_statistics()

print(f"Total documents: {stats['total_documents']}")
print(f"Cached embeddings: {stats['cached_embeddings']}")
print(f"Mean similarity: {stats['similarity_stats']['mean']:.3f}")
print(f"Median similarity: {stats['similarity_stats']['median']:.3f}")
```

---

## Performance Optimization

### 1. Embedding Cache

**Always enabled by default**. The cache:
- Stores embeddings by content hash
- Persists to disk
- Automatically loads on startup

**Benefits**:
- Re-processing is nearly instant
- Saves API costs
- Enables iterative development

### 2. Similarity Cache

In-memory cache of computed similarities:

```python
# Automatically caches similarity calculations
# Cache key: tuple(sorted([path1, path2]))

# First call: computes similarity
sim1 = detector.cosine_similarity(vec1, vec2)

# Second call: uses cache
sim2 = detector.cosine_similarity(vec1, vec2)  # Instant
```

### 3. Batch Processing

Process multiple documents efficiently:

```python
# Instead of:
for doc in documents:
    embedding = generate_embedding(doc['content'])
    detector.add_document_embedding(doc['file_path'], doc['content'], embedding)

# Do:
detector.batch_add_embeddings(
    documents,
    embedding_generator=generate_embedding  # Batched API calls
)
```

**Benefits**:
- Batched API calls (faster)
- Bulk cache operations
- Progress tracking

---

## Integration with Relationship Detector

### How It Works

The semantic similarity detector integrates seamlessly with the enhanced relationship detector:

```python
# 1. Initialize both detectors
relationship_detector = EnhancedRelationshipDetector()
semantic_detector = SemanticSimilarityDetector()

# 2. Integrate
SemanticSimilarityIntegration.add_to_relationship_detector(
    relationship_detector,
    semantic_detector
)

# 3. Use as normal
relationships = relationship_detector.detect_all_relationships(
    content, file_path, file_metadata, all_files
)

# Now includes semantic similarity relationships!
```

### Detection Order

1. **Markdown Links** (explicit)
2. **Implicit Folder Relationships** (structural)
3. **Card References** (pattern-based)
4. **Building Block Connections** (pattern-based)
5. **Image References** (explicit)
6. **Cross-Activity References** (pattern-based)
7. **Journey/Workshop Progression** (structural)
8. **Tag-Based Similarity** (metadata)
9. **Semantic Similarity** (embedding-based) ← **NEW**

### Exclusion Logic

Semantic similarity **excludes documents already related** through other methods:

```python
# Existing relationships from methods 1-8
existing = {r.target_path for r in relationships}

# Find semantically similar (excluding existing)
similar = semantic_detector.find_similar_documents(
    file_path,
    exclude_paths=existing  # Won't return already-related docs
)
```

**Why?**
- Reduces redundancy
- Focuses on new discoveries
- Keeps relationship graph manageable

---

## Output and Reports

### Semantic Similarity Report

Generated as `semantic_similarity_report.json`:

```json
{
  "statistics": {
    "total_documents": 150,
    "cached_embeddings": 120,
    "cached_similarities": 2340,
    "similarity_stats": {
      "mean": 0.623,
      "std": 0.184,
      "min": 0.102,
      "max": 0.987,
      "median": 0.645
    }
  },
  "clusters": [
    {
      "cluster_id": 1,
      "size": 5,
      "documents": ["doc1.md", "doc2.md", "doc5.md", "doc7.md", "doc9.md"]
    },
    {
      "cluster_id": 2,
      "size": 4,
      "documents": ["doc3.md", "doc4.md", "doc6.md", "doc8.md"]
    }
  ],
  "sample_similarities": {
    "doc1.md": [
      {"document": "doc2.md", "similarity": "0.892"},
      {"document": "doc5.md", "similarity": "0.856"},
      {"document": "doc7.md", "similarity": "0.823"}
    ]
  }
}
```

### Relationship Output

Semantic similarity relationships in the relationship detector:

```json
{
  "source_path": "LibraryRAG/Activities/FACES/mindful.md",
  "target_path": "LibraryRAG/Activities/FLOW/awareness.md",
  "relationship_type": "semantic_similarity",
  "confidence": 0.847,
  "context": {
    "similarity_score": 0.847,
    "detection_method": "embedding_based",
    "excludes_existing": true
  }
}
```

---

## Best Practices

### 1. Start with Conservative Thresholds

```python
# Start strict
detector = SemanticSimilarityDetector(similarity_threshold=0.80)

# Review results
stats = detector.get_statistics()
print(f"Mean similarity: {stats['similarity_stats']['mean']:.3f}")

# Adjust if needed
if stats['similarity_stats']['mean'] > 0.85:
    # Can be more relaxed
    detector.similarity_threshold = 0.75
```

### 2. Monitor Cache Growth

```python
# Check cache size periodically
import os
cache_size = os.path.getsize("embedding_cache.json")
print(f"Cache size: {cache_size / 1024 / 1024:.2f} MB")

# Clear if needed
detector.embedding_cache.clear()
detector._save_embedding_cache()
```

### 3. Use Batch Processing for Large Libraries

```python
# Process in batches
batch_size = 50
for i in range(0, len(documents), batch_size):
    batch = documents[i:i+batch_size]
    detector.batch_add_embeddings(batch, embedding_generator)
    print(f"Processed {i+batch_size}/{len(documents)}")
```

### 4. Validate Results

```python
# Review top similar pairs
for path in detector.document_embeddings.keys():
    similar = detector.find_similar_documents(path)
    if similar:
        top = similar[0]
        if top.similarity_score > 0.9:
            print(f"Very similar: {path} <-> {top.target_path}")
            print(f"Score: {top.similarity_score:.3f}")
            # Manually verify they're actually similar
```

---

## Troubleshooting

### Issue: Too Many Relationships

**Symptom**: Every document is related to dozens of others

**Solution**:
```python
# Increase threshold
detector.similarity_threshold = 0.80

# Reduce top-k
detector.top_k = 5
```

### Issue: Too Few Relationships

**Symptom**: Most documents have 0-1 similar documents

**Solution**:
```python
# Lower threshold
detector.similarity_threshold = 0.70

# Increase top-k
detector.top_k = 15

# Check your embeddings
stats = detector.get_statistics()
print(stats)  # Verify documents are actually loaded
```

### Issue: Cache Not Working

**Symptom**: Regenerates embeddings every time

**Solution**:
```python
# Verify cache is enabled
detector.use_cache = True

# Check cache file permissions
import os
os.access("embedding_cache.json", os.W_OK)  # Should be True

# Manually save cache
detector._save_embedding_cache()
```

### Issue: Out of Memory

**Symptom**: Crashes with large libraries

**Solution**:
```python
# Process in smaller batches
pipeline = InstrumentedLibraryRAGPipeline(
    enable_file_tracking=False,  # Reduces memory
    enable_semantic_similarity=True
)

# Or disable semantic similarity for this run
pipeline = InstrumentedLibraryRAGPipeline(
    enable_semantic_similarity=False
)
```

---

## Cost Estimation

### Embedding Generation

**Model**: `text-embedding-3-small`  
**Cost**: $0.02 per 1M tokens

**Estimation**:
- Average document: ~1,000 tokens
- 1,000 documents = 1M tokens ≈ $0.02
- **With cache**: Nearly $0 for re-processing

### Similarity Computation

**CPU-Based**: No API costs  
**Memory**: ~4KB per document (embedding vector)

**Example**:
- 1,000 documents: ~4 MB memory
- 10,000 documents: ~40 MB memory

---

## Examples

### Example 1: Basic Integration

```python
from scripts.semantic_similarity import SemanticSimilarityDetector
from scripts.relationship_detector import EnhancedRelationshipDetector

# Setup
rel_detector = EnhancedRelationshipDetector()
sem_detector = SemanticSimilarityDetector()

# Integrate
from scripts.semantic_similarity import SemanticSimilarityIntegration
SemanticSimilarityIntegration.add_to_relationship_detector(
    rel_detector, sem_detector
)

# Add embeddings
sem_detector.add_document_embedding('doc1.md', content1, embedding1)
sem_detector.add_document_embedding('doc2.md', content2, embedding2)

# Detect relationships (now includes semantic similarity)
relationships = rel_detector.detect_all_relationships(
    content1, 'doc1.md', metadata1, all_files
)

# Filter for semantic relationships
semantic_rels = [
    r for r in relationships 
    if r.relationship_type == 'semantic_similarity'
]

print(f"Found {len(semantic_rels)} semantic relationships")
```

### Example 2: Find Content Gaps

```python
# Find documents with no similar neighbors
lonely_docs = []

for path in detector.document_embeddings.keys():
    similar = detector.find_similar_documents(path, min_similarity=0.75)
    if not similar:
        lonely_docs.append(path)

print(f"Found {len(lonely_docs)} isolated documents:")
for doc in lonely_docs:
    print(f"  - {doc}")

# These might need:
# - Better tagging
# - Cross-linking
# - Content expansion
```

### Example 3: Topic Discovery

```python
# Find clusters to identify topics
clusters = detector.find_clusters(
    min_cluster_size=5,
    min_intra_similarity=0.82
)

print(f"Discovered {len(clusters)} topics:")
for i, cluster in enumerate(clusters, 1):
    print(f"\nTopic {i}: {len(cluster)} documents")
    
    # Analyze cluster content
    contents = [file_contents[path] for path in cluster]
    
    # Find common words (simplified)
    words = ' '.join(contents).lower().split()
    from collections import Counter
    common = Counter(words).most_common(10)
    
    print(f"  Common terms: {', '.join([w for w, _ in common])}")
```

---

## Summary

The Semantic Similarity Detection system:

✅ **Complements** pattern-based detection  
✅ **Discovers** implicit relationships  
✅ **Scales** to large libraries  
✅ **Caches** for efficiency  
✅ **Integrates** seamlessly  

Use it to create a more **complete and intelligent relationship graph** for your RAG system!

