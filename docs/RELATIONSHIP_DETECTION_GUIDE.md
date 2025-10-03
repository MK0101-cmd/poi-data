# Enhanced Relationship Detection Guide

**Comprehensive relationship mapping for LibraryRAG pipeline Stage 3**

---

## Overview

The enhanced relationship detector goes far beyond simple markdown link extraction to identify **8 types of relationships** between documents:

1. **Explicit Markdown Links** - `[text](path)`
2. **Card References** - `FACES-001`, `FLOW-042`, `TCG #5`
3. **Building Block Connections** - Stories, quotes, questions, applications
4. **Folder-Based Relationships** - Siblings, cousins
5. **Naming Pattern Relationships** - Sequences, variants
6. **Hierarchical Relationships** - Parent-child, index files
7. **Series Relationships** - Same card series
8. **Keyword References** - Concept matching

---

## Quick Start

```python
from scripts.relationship_detector import EnhancedRelationshipDetector

# Initialize detector
detector = EnhancedRelationshipDetector()

# Build index from all files (Stage 1 output)
detector.build_file_index(all_files)

# Detect relationships for a file
relationships = detector.detect_all_relationships(
    content=file_content,
    file_path=file_path,
    file_metadata=file_metadata,
    all_files=all_files
)

# Get summary
summary = detector.get_relationship_summary(relationships)
print(f"Found {summary['total']} relationships")
```

---

## Relationship Types

### 1. Explicit Markdown Links

**Detection**: Standard markdown link syntax

**Patterns:**
```markdown
[See stories](stories-tales.md)
[FACES Overview](../FACES/README.md)
[Training Guide](/Trainings/BTC24/README.md)
```

**Output:**
```python
{
    'source_path': 'current/file.md',
    'target_path': 'stories-tales.md',
    'relationship_type': 'markdown_link',
    'confidence': 1.0,  # Explicit
    'context': {
        'link_text': 'See stories',
        'link_path': 'stories-tales.md'
    }
}
```

### 2. Card References

**Detection**: Various card reference formats across all decks

#### FACES Cards (100 cards)

**Patterns:**
- `FACES-001` to `FACES-100`
- `FACES card 42`
- `FACES #15`
- `open-minded-5` (series-based)
- `givers-12`
- `stormy-8`

**Series:**
- open-minded (cards 1-20)
- givers (21-40)
- takers (41-60)
- stormy (61-80)
- calculated (81-100)
- lost (all cards)
- knowing (all cards)

**Example:**
```markdown
Use FACES-015 for exploring openness.
The givers-5 card shows connection.
```

#### FLOW Cards (66 cards)

**Patterns:**
- `FLOW-01` to `FLOW-66`
- `FLOW card 42`
- `dream-series` (concept reference)

**Series:**
- dream-series (13 cards)
- in-between-series (13 cards)
- conflict-series (13 cards)
- belonging-series (13 cards)
- presence-series (13 cards)
- guidance card (1 card)

**Example:**
```markdown
The FLOW-25 card represents transition.
Use the dream-series for visioning.
```

#### TCG Cards (14 concepts)

**Patterns:**
- `TCG-01` to `TCG-14`
- `The Coaching Game #5`
- `solutions` (concept name)
- `leadership` (concept name)

**Concepts:**
- solutions, learning, everything-is-possible
- should-be, choice, calling
- just-be, pause, devotion
- leadership, point-of-view, intimacy
- balance, success

**Example:**
```markdown
TCG-10 leadership card helps explore influence.
The concept of should-be vs just-be.
```

#### SPEAK Cards

**Patterns:**
- `SPEAK UP-01` to `SPEAK UP-31`
- `SPEAK card 15`

**Example:**
```markdown
Use SPEAK UP-12 for dialogue starters.
```

#### PUNCTUM Cards

**Patterns:**
- `PUNCTUM-01` to `PUNCTUM-34`
- `PUNCTUM card 8`

### 3. Building Block Connections

**Detection**: Keywords + file structure

**Building Blocks:**
- **stories** / **tales** → `stories-tales.md`
- **quotes** / **quotations** → `key-quotes.md`
- **questions** / **reflection questions** → `reflection-questions.md`
- **applications** / **training** → `training-applications.md`
- **techniques** / **methods** → `techniques.md`
- **templates** / **frameworks** → `templates.md`

**Example Content:**
```markdown
## Stories & Tales

See the story about the curious child...

For reflection questions, refer to...
```

**Detected:**
```python
{
    'relationship_type': 'building_block_reference',
    'target_path': 'stories-tales.md',
    'confidence': 0.8,
    'context': {
        'block_type': 'stories',
        'keyword': 'story'
    }
}
```

### 4. Folder-Based Relationships

**Detection**: Same folder = siblings, same grandparent = cousins

**Example Structure:**
```
FACES/
  open-minded/
    README.md         ← sibling to stories-tales.md
    stories-tales.md  ← sibling to README.md
    key-quotes.md     ← sibling to both
  givers/
    README.md         ← cousin to open-minded/README.md
    stories-tales.md  ← cousin to open-minded/stories-tales.md
```

**Relationships:**
```python
# Sibling (same folder)
{
    'relationship_type': 'sibling',
    'confidence': 0.6,
    'context': {
        'folder': 'FACES/open-minded',
        'relationship': 'same_folder'
    }
}

# Cousin (related folder)
{
    'relationship_type': 'cousin',
    'confidence': 0.4,
    'context': {
        'grandparent': 'FACES',
        'relationship': 'related_folder'
    }
}
```

### 5. Naming Pattern Relationships

**Detection**: Numbered sequences and name variants

#### Numbered Sequences

**Pattern**: `01-name.md`, `02-name.md`, `03-name.md`

**Example:**
```
01-open-minded.md   ← previous to 02
02-givers.md        ← next from 01, previous to 03
03-takers.md        ← next from 02
```

**Detected:**
```python
{
    'relationship_type': 'sequence',
    'confidence': 0.9,
    'context': {
        'sequence_position': 2,
        'direction': 'next'  # or 'previous'
    }
}
```

#### Name Variants

**Pattern**: Same base, different suffixes

**Example:**
```
workshop.md
workshop-guide.md
workshop-template.md
workshop-full.md
```

**Detected:**
```python
{
    'relationship_type': 'name_variant',
    'confidence': 0.8,
    'context': {
        'base_name': 'workshop',
        'variant': 'workshop-guide'
    }
}
```

### 6. Hierarchical Relationships

**Detection**: README/INDEX files create parent-child relationships

**Example Structure:**
```
Activities/
  MASTER-INDEX.md       ← parent of everything below
  FACES/
    README.md           ← parent of all FACES files
    open-minded/
      README.md         ← parent of series files
      stories-tales.md  ← child of open-minded/README.md
```

**Relationships:**
```python
# Child to parent
{
    'relationship_type': 'child_of_index',
    'target_path': 'FACES/open-minded/README.md',
    'confidence': 0.85,
    'context': {
        'index_file': 'README.md',
        'level': 1
    }
}

# Parent to children (if current file is index)
{
    'relationship_type': 'parent_of',
    'confidence': 0.85,
    'context': {
        'relationship': 'index_to_child'
    }
}
```

### 7. Series Relationships

**Detection**: Files in same card series

**Example:**
```
FACES/
  open-minded/
    01-build-understanding.md      ← same_series
    02-gentle-openness.md          ← same_series
    03-curious-exploration.md      ← same_series
```

**Detected:**
```python
{
    'relationship_type': 'same_series',
    'confidence': 0.75,
    'context': {
        'deck': 'FACES',
        'series': 'open-minded'
    }
}
```

### 8. Keyword References

**Detection**: Concept matching in file paths

**Example Content:**
```markdown
# Leadership Development

This explores leadership principles...
```

**Detected matches:**
```python
{
    'relationship_type': 'keyword_match',
    'target_path': 'TCG/leadership/README.md',
    'confidence': 0.5,
    'context': {
        'keyword': 'leadership'
    }
}
```

---

## Confidence Levels

| Confidence | Range | Relationship Types |
|------------|-------|-------------------|
| **High** | 0.8 - 1.0 | Markdown links, sequences, building blocks |
| **Medium** | 0.6 - 0.79 | Siblings, name variants, hierarchical |
| **Low** | 0.0 - 0.59 | Cousins, keyword matches |

---

## Output Format

Each relationship is represented as:

```python
@dataclass
class Relationship:
    source_path: str          # Current file
    target_path: str          # Related file
    relationship_type: str    # Type (see above)
    confidence: float         # 0.0 to 1.0
    context: Dict            # Additional info
```

**Example:**
```python
Relationship(
    source_path='Activities/FACES/open-minded/README.md',
    target_path='Activities/FACES/open-minded/stories-tales.md',
    relationship_type='building_block_reference',
    confidence=0.8,
    context={
        'block_type': 'stories',
        'keyword': 'story'
    }
)
```

---

## Summary Statistics

```python
summary = detector.get_relationship_summary(relationships)

# Returns:
{
    'total': 45,
    'by_type': {
        'markdown_link': 5,
        'card_reference': 12,
        'building_block_reference': 8,
        'sibling': 15,
        'sequence': 2,
        'hierarchical': 3
    },
    'by_confidence': {
        'high': 25,    # >= 0.8
        'medium': 15,  # 0.6 - 0.79
        'low': 5       # < 0.6
    },
    'unique_targets': 38
}
```

---

## Integration with Pipeline

### Automatic in Instrumented Pipeline

```python
from scripts.pipeline_instrumented import InstrumentedLibraryRAGPipeline

# Automatically uses enhanced detection
pipeline = InstrumentedLibraryRAGPipeline()
pipeline.run()
```

### Manual Integration

```python
from scripts.relationship_detector import EnhancedRelationshipDetector

class YourPipeline:
    def __init__(self):
        self.detector = EnhancedRelationshipDetector()
    
    def process_files(self, all_files):
        # Build index once
        self.detector.build_file_index(all_files)
        
        for file_info in all_files:
            content = read_file(file_info['file_path'])
            
            # Detect relationships
            relationships = self.detector.detect_all_relationships(
                content=content,
                file_path=file_info['file_path'],
                file_metadata=file_info,
                all_files=all_files
            )
            
            # Store in database
            self.store_relationships(relationships)
```

---

## Performance Considerations

### Memory Usage

- **File Index**: ~5-10 MB for 700 files
- **Per-file Detection**: ~1-5 MB temporary
- **Total Overhead**: ~50-100 MB

### Processing Time

| Files | Time |
|-------|------|
| 10 | ~2 seconds |
| 100 | ~15 seconds |
| 707 | ~90 seconds |

**Optimization Tips:**
1. Build index once at start
2. Limit cousin relationships (default: 10 max)
3. Limit keyword matches (default: 5 max)
4. Disable low-confidence types if needed

### Disabling Specific Detection

```python
class CustomDetector(EnhancedRelationshipDetector):
    def detect_all_relationships(self, *args, **kwargs):
        relationships = []
        
        # Enable only what you need
        relationships.extend(self._detect_markdown_links(...))
        relationships.extend(self._detect_card_references(...))
        # Skip others...
        
        return relationships
```

---

## Database Storage

### Store Relationships in PostgreSQL

```python
def store_relationships(relationships: List[Relationship]):
    """Store relationships in cross_references table"""
    
    for rel in relationships:
        # Get document IDs
        source_id = get_document_id(rel.source_path)
        target_id = get_document_id(rel.target_path)
        
        if source_id and target_id:
            cursor.execute("""
                INSERT INTO cross_references 
                (source_document_id, target_document_id, reference_type, 
                 relationship_strength, context)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """, (
                source_id,
                target_id,
                rel.relationship_type,
                rel.confidence,
                json.dumps(rel.context)
            ))
```

### Query Relationships

```sql
-- Get all relationships for a document
SELECT 
    d.file_name as target_file,
    cr.reference_type,
    cr.relationship_strength,
    cr.context
FROM cross_references cr
JOIN documents d ON cr.target_document_id = d.id
WHERE cr.source_document_id = $1
ORDER BY cr.relationship_strength DESC;

-- Get relationship summary
SELECT 
    reference_type,
    COUNT(*) as count,
    AVG(relationship_strength) as avg_confidence
FROM cross_references
GROUP BY reference_type
ORDER BY count DESC;
```

---

## Examples

### Example 1: FACES Open-Minded README

**Content:**
```markdown
# Open-Minded Series

Uses FACES cards 1-20.

See [stories](stories-tales.md) for examples.
Also review the [givers series](../givers/README.md).

Building on the concept of curiosity from TCG-02 learning.
```

**Detected Relationships:**
1. Markdown link → `stories-tales.md` (confidence: 1.0)
2. Markdown link → `../givers/README.md` (confidence: 1.0)
3. Card reference → FACES card files 1-20 (confidence: 0.9)
4. Concept reference → `TCG/learning/` (confidence: 0.7)
5. Building block → `stories-tales.md` (confidence: 0.8)
6. Siblings → other files in `open-minded/` (confidence: 0.6)
7. Hierarchical → `FACES/README.md` (confidence: 0.85)
8. Series → other open-minded files (confidence: 0.75)

**Total: ~30-40 relationships**

### Example 2: Workshop File

**Content:**
```markdown
# Leadership Workshop

Uses FLOW-15, FLOW-18, and TCG leadership cards.
```

**Detected Relationships:**
1. Card reference → `FLOW/15-card.md` (confidence: 0.9)
2. Card reference → `FLOW/18-card.md` (confidence: 0.9)
3. Concept reference → `TCG/leadership/` files (confidence: 0.7)
4. Keyword match → files with "leadership" (confidence: 0.5)
5. Siblings → other workshops (confidence: 0.6)
6. Hierarchical → `Workshops/README.md` (confidence: 0.85)

**Total: ~15-20 relationships**

---

## Troubleshooting

### Issue: Too many relationships detected

**Solution:** Filter by confidence
```python
high_confidence = [
    r for r in relationships 
    if r.confidence >= 0.8
]
```

### Issue: Card references not found

**Cause:** Card files not properly indexed

**Solution:**
```python
# Ensure files follow naming convention
# FACES: 01-name.md to 100-name.md
# FLOW: 01-name.md to 66-name.md

# Or update _index_card_file() to match your structure
```

### Issue: Slow performance

**Solutions:**
1. Limit cousin relationships: Modify `_detect_folder_relationships()`
2. Skip keyword detection: Comment out in `detect_all_relationships()`
3. Process in batches

### Issue: Missing implicit relationships

**Check:**
1. File index built? `detector.build_file_index(all_files)`
2. Correct file structure?
3. Naming conventions followed?

---

## Best Practices

1. **Build index once** at pipeline start
2. **Filter by confidence** for your use case
3. **Store in database** for persistence
4. **Monitor performance** with instrumentation
5. **Validate relationships** periodically
6. **Document custom patterns** if adding

---

## Future Enhancements

Potential additions:
- [ ] Semantic similarity (embedding-based)
- [ ] Temporal relationships (created before/after)
- [ ] User-defined patterns
- [ ] Machine learning for confidence scores
- [ ] Relationship strength learning from usage
- [ ] Bi-directional relationship inference

---

## Summary

The Enhanced Relationship Detector provides:

✅ **8 relationship types** - Comprehensive detection  
✅ **High confidence** - Explicit > 0.8, implicit > 0.6  
✅ **Card-aware** - All Points of You® decks  
✅ **Building blocks** - Stories, quotes, questions, etc.  
✅ **Smart patterns** - Sequences, variants, hierarchies  
✅ **Fast** - ~0.1-0.5s per file  
✅ **Extensible** - Easy to add custom patterns  
✅ **Integrated** - Works with instrumented pipeline  

---

**Last Updated**: October 3, 2025  
**Version**: 1.0

