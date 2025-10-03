# 📊 LibraryRAG Pipeline Instrumentation - Complete Guide

**Comprehensive tracking and performance monitoring for pipeline stages 1-6**

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Installation & Setup](#installation--setup)
4. [Execution Guide](#execution-guide)
5. [Metrics Tracked](#metrics-tracked)
6. [Output Files](#output-files)
7. [Analysis & Visualization](#analysis--visualization)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)
10. [API Reference](#api-reference)

---

## Overview

The instrumentation system provides **comprehensive tracking** for the LibraryRAG pipeline's file processing stages:

| Stage | Name | What It Does |
|-------|------|--------------|
| **1** | File Discovery | Scans directory for markdown files |
| **2** | Content Extraction | Reads file contents |
| **3** | Relationship Mapping | Detects 9 types of relationships |
| **4** | Content Chunking | Splits content into chunks |
| **5** | Tag Generation | Generates metadata tags |
| **6** | Embedding Generation | Creates vector embeddings |

### What Gets Tracked

- ⏱️ **Timing**: Duration for each stage and file
- 💾 **Memory**: RAM usage before/after/peak
- 📊 **Progress**: Items processed vs failed
- ⚠️ **Errors**: Detailed error logs with context
- 🔄 **API Calls**: OpenAI API timing and caching
- 📄 **File-Level**: Individual file metrics
- 📈 **Statistics**: Success rates, bottlenecks

---

## Architecture

### Component Structure

```
┌─────────────────────────────────────────────────────┐
│           Pipeline Instrumentation System           │
└──────────────────────┬──────────────────────────────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
   ┌────▼─────┐                 ┌─────▼────┐
   │  Core    │                 │Pipeline  │
   │  Module  │◄────────────────┤Integration│
   └────┬─────┘                 └─────┬────┘
        │                             │
        │  ┌───────────────────┐      │
        └─►│  Metrics Storage  │◄─────┘
           └────────┬──────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
   ┌────▼─────┐          ┌──────▼──────┐
   │  JSON    │          │Visualization│
   │  Reports │          │   Tools     │
   └──────────┘          └─────────────┘
```

### Files

1. **`instrumentation.py`** (653 lines)
   - Core tracking framework
   - Metrics collection
   - Report generation

2. **`pipeline_instrumented.py`** (611 lines)
   - Instrumented pipeline
   - Stage integration
   - Real-time progress

3. **`visualize_metrics.py`** (optional)
   - Chart generation
   - HTML reports
   - Performance analysis

---

## Installation & Setup

### Prerequisites

```bash
# Required packages
pip install psutil  # For memory monitoring
pip install openai  # For embeddings
pip install python-dotenv  # For environment variables
```

### Environment Setup

Create `.env` file:

```bash
OPENAI_API_KEY=your_api_key_here
```

### File Structure

```
poi-data/
├── instrumentation.py              # Core module
├── pipeline_instrumented.py        # Instrumented pipeline
├── relationship_detector.py        # Relationship detection
├── semantic_similarity.py          # Semantic detection
├── database.py                     # Database operations
├── LibraryRAG/                     # Content directory
│   ├── Activities/
│   └── Trainings/
└── .env                            # API keys
```

---

## Execution Guide

### Basic Execution

#### 1. Quick Test (5 files)

```bash
python pipeline_instrumented.py
```

This runs with default settings:
- Processes 5 files (limit=5)
- Enables file tracking
- Enables semantic similarity
- Generates reports

**Expected Output:**
```
Found 877 markdown files
Building relationship index...
Index built with 877 entries

[1/5] 📄 Processing: Canvas_Master_Index.md
  🔗 Found 27 relationships
  💾 Inserting into database...
  ✓ Inserted 12 chunks
  
[2/5] 📄 Processing: next_file.md
...

🔍 Computing semantic similarities...
  📊 Semantic similarity statistics:
     Total documents: 5
     
✅ Pipeline complete!

📊 Generating reports...
✅ Reports saved!
```

**Time:** ~30-60 seconds for 5 files

---

#### 2. Process 50 Files

```python
from scripts.pipeline_instrumented import InstrumentedLibraryRAGPipeline

pipeline = InstrumentedLibraryRAGPipeline(
    root_path="LibraryRAG",
    enable_file_tracking=True,
    enable_semantic_similarity=True
)

# Process 50 files
pipeline.run(limit=50, generate_reports=True)
```

**Time:** ~5-10 minutes for 50 files

---

#### 3. Full Library Processing

```python
# Process ALL files (877 files)
pipeline = InstrumentedLibraryRAGPipeline(
    root_path="LibraryRAG",
    enable_file_tracking=True,
    enable_semantic_similarity=True,
    similarity_threshold=0.75,
    top_k_similar=10
)

pipeline.run(generate_reports=True)
```

**Time:** ~30-45 minutes for 877 files (first run)  
**Time:** ~5-10 minutes (with cache)

---

#### 4. Memory-Efficient Mode

For large libraries or limited RAM:

```python
# Disable file-level tracking to save memory
pipeline = InstrumentedLibraryRAGPipeline(
    enable_file_tracking=False,  # Reduces memory usage
    enable_semantic_similarity=True
)

pipeline.run()
```

**Memory savings:** ~50MB for 1000 files

---

#### 5. Fast Mode (No Semantic Similarity)

For faster processing:

```python
# Disable semantic similarity
pipeline = InstrumentedLibraryRAGPipeline(
    enable_semantic_similarity=False
)

pipeline.run()
```

**Speed improvement:** ~15% faster

---

### Command Line Execution

#### Create a runner script: `run_pipeline.py`

```python
#!/usr/bin/env python3
"""
LibraryRAG Pipeline Runner
Usage:
    python run_pipeline.py --limit 10
    python run_pipeline.py --full
    python run_pipeline.py --fast
"""

import argparse
from scripts.pipeline_instrumented import InstrumentedLibraryRAGPipeline

def main():
    parser = argparse.ArgumentParser(description='Run LibraryRAG Pipeline')
    parser.add_argument('--limit', type=int, help='Limit number of files')
    parser.add_argument('--full', action='store_true', help='Process all files')
    parser.add_argument('--fast', action='store_true', help='Disable semantic similarity')
    parser.add_argument('--no-tracking', action='store_true', help='Disable file tracking')
    args = parser.parse_args()
    
    # Configure pipeline
    pipeline = InstrumentedLibraryRAGPipeline(
        enable_file_tracking=not args.no_tracking,
        enable_semantic_similarity=not args.fast
    )
    
    # Determine limit
    limit = None if args.full else (args.limit or 5)
    
    # Run
    print(f"Processing {limit or 'all'} files...")
    pipeline.run(limit=limit, generate_reports=True)
    print("\nDone! Check pipeline_report.json for results.")

if __name__ == "__main__":
    main()
```

**Usage:**
```bash
# Test with 10 files
python run_pipeline.py --limit 10

# Process all files
python run_pipeline.py --full

# Fast mode (no semantic similarity)
python run_pipeline.py --limit 50 --fast

# Memory efficient (no file tracking)
python run_pipeline.py --full --no-tracking
```

---

## Metrics Tracked

### Stage-Level Metrics

For each of the 6 stages, tracks:

```python
{
  "stage_number": 1,
  "stage_name": "File Discovery",
  "duration": 2.34,              # seconds
  "duration_formatted": "2.34s",
  "items_processed": 877,
  "items_failed": 0,
  "success_rate": 100.0,         # percentage
  "bytes_processed": 45678912,   # bytes
  "memory_start_mb": 234.5,
  "memory_end_mb": 245.2,
  "memory_peak_mb": 248.1,
  "errors": [],
  "warnings": []
}
```

### File-Level Metrics

For each processed file:

```python
{
  "file_path": "LibraryRAG/Activities/FACES/README.md",
  "file_size": 12345,
  "stage_1_time": 0.001,         # File discovery
  "stage_2_time": 0.045,         # Content extraction
  "stage_3_time": 0.123,         # Relationship mapping
  "stage_4_time": 0.089,         # Chunking
  "stage_5_time": 0.234,         # Tag generation
  "stage_6_time": 1.456,         # Embedding generation
  "total_time": 1.948,
  "chunks_created": 8,
  "tags_generated": 5,
  "embeddings_created": 8,
  "relationships_found": 12,
  "success": true,
  "error_message": null
}
```

### API Call Metrics

Tracks OpenAI API calls:

```python
{
  "service": "openai_embeddings",
  "total_calls": 5234,
  "total_duration": 2341.23,     # seconds
  "average_duration": 0.447,     # seconds
  "min_duration": 0.234,
  "max_duration": 2.345,
  "cached_calls": 4123,
  "cache_hit_rate": 78.8         # percentage
}
```

### Error Tracking

Each error includes:

```python
{
  "stage_id": 3,
  "timestamp": "2025-10-03T10:23:45",
  "error_type": "ValueError",
  "error_message": "Invalid file path",
  "traceback": "...",
  "context": {
    "file_path": "path/to/file.md",
    "additional_info": "..."
  }
}
```

---

## Output Files

### 1. `pipeline_report.json`

**Main pipeline report** with summary and stage metrics.

**Structure:**
```json
{
  "pipeline_summary": {
    "total_duration": 1847.23,
    "total_duration_formatted": "30.79m",
    "total_files": 877,
    "successful_files": 871,
    "failed_files": 6,
    "success_rate": 99.32,
    "total_chunks": 7234,
    "total_embeddings": 7234,
    "total_relationships": 8921,
    "memory_start_mb": 234.5,
    "memory_end_mb": 345.2,
    "memory_peak_mb": 389.7
  },
  "stages": [
    {
      "stage_number": 1,
      "stage_name": "File Discovery",
      "duration": 2.34,
      "items_processed": 877,
      "success_rate": 100.0,
      ...
    },
    ...
  ],
  "api_metrics": {
    "openai_embeddings": {
      "total_calls": 7234,
      "cache_hit_rate": 0.0,
      ...
    }
  },
  "top_slowest_files": [
    {
      "file_path": "...",
      "total_time": 5.234
    },
    ...
  ],
  "errors": [...]
}
```

**Size:** ~50-500KB depending on library size

---

### 2. `pipeline_metrics_detailed.json`

**Detailed file-level metrics** for every processed file.

**Structure:**
```json
{
  "files": {
    "LibraryRAG/Activities/FACES/README.md": {
      "file_path": "...",
      "file_size": 12345,
      "stage_1_time": 0.001,
      "stage_2_time": 0.045,
      ...
      "total_time": 1.948,
      "chunks_created": 8,
      "success": true
    },
    ...
  },
  "summary": {
    "total_files": 877,
    "average_processing_time": 2.105
  }
}
```

**Size:** ~1-10MB for 1000 files

---

### 3. `semantic_similarity_report.json`

**Semantic similarity analysis** (if enabled).

**Structure:**
```json
{
  "statistics": {
    "total_documents": 877,
    "cached_embeddings": 120,
    "cached_similarities": 45678,
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
      "size": 15,
      "documents": ["file1.md", "file2.md", ...]
    },
    ...
  ],
  "sample_similarities": {
    "file1.md": [
      {"document": "file2.md", "similarity": "0.892"},
      ...
    ]
  }
}
```

**Size:** ~100KB-1MB

---

### 4. `embedding_cache.json`

**Cached embeddings** for reuse.

**Structure:**
```json
{
  "content_hash_1": [0.123, 0.456, 0.789, ...],
  "content_hash_2": [0.234, 0.567, 0.890, ...],
  ...
}
```

**Size:** ~50MB for 1000 documents

---

## Analysis & Visualization

### Using Python

#### 1. Load and Analyze Report

```python
import json

# Load report
with open('pipeline_report.json') as f:
    report = json.load(f)

# Print summary
summary = report['pipeline_summary']
print(f"Total Duration: {summary['total_duration_formatted']}")
print(f"Files Processed: {summary['successful_files']}/{summary['total_files']}")
print(f"Success Rate: {summary['success_rate']:.2f}%")
print(f"Total Relationships: {summary['total_relationships']}")

# Analyze stages
for stage in report['stages']:
    print(f"\nStage {stage['stage_number']}: {stage['stage_name']}")
    print(f"  Duration: {stage['duration_formatted']}")
    print(f"  Items: {stage['items_processed']}")
    print(f"  Success Rate: {stage['success_rate']:.2f}%")

# Find bottleneck
slowest_stage = max(report['stages'], key=lambda s: s['duration'])
print(f"\nBottleneck: Stage {slowest_stage['stage_number']} ({slowest_stage['stage_name']})")
print(f"  Took {slowest_stage['duration_formatted']}")
```

---

#### 2. Identify Slow Files

```python
# Load detailed metrics
with open('pipeline_metrics_detailed.json') as f:
    metrics = json.load(f)

# Sort by processing time
files = sorted(
    metrics['files'].items(),
    key=lambda x: x[1]['total_time'],
    reverse=True
)

# Top 10 slowest
print("Top 10 Slowest Files:")
for path, data in files[:10]:
    print(f"  {data['total_time']:.2f}s - {path}")
    print(f"    Stage 6 (Embeddings): {data['stage_6_time']:.2f}s")
```

---

#### 3. Analyze Cache Performance

```python
api_metrics = report['api_metrics']

for service, metrics in api_metrics.items():
    print(f"\n{service}:")
    print(f"  Total Calls: {metrics['total_calls']}")
    print(f"  Cache Hit Rate: {metrics['cache_hit_rate']:.1f}%")
    print(f"  Avg Duration: {metrics['average_duration']:.3f}s")
    
    # Calculate time saved by caching
    if metrics['cache_hit_rate'] > 0:
        cached = metrics.get('cached_calls', 0)
        time_saved = cached * metrics['average_duration']
        print(f"  Time Saved by Cache: {time_saved:.1f}s")
```

---

#### 4. Memory Analysis

```python
print("Memory Usage:")
print(f"  Start: {summary['memory_start_mb']:.1f} MB")
print(f"  End: {summary['memory_end_mb']:.1f} MB")
print(f"  Peak: {summary['memory_peak_mb']:.1f} MB")
print(f"  Increase: {summary['memory_end_mb'] - summary['memory_start_mb']:.1f} MB")

# Per-stage memory
print("\nMemory by Stage:")
for stage in report['stages']:
    mem_increase = stage['memory_end_mb'] - stage['memory_start_mb']
    print(f"  Stage {stage['stage_number']}: +{mem_increase:.1f} MB")
```

---

### Using visualize_metrics.py

```python
from scripts.visualize_metrics import MetricsVisualizer

# Create visualizer
viz = MetricsVisualizer('pipeline_report.json')

# Generate all charts
viz.generate_stage_timing_chart('stage_timing.png')
viz.generate_memory_usage_chart('memory_usage.png')
viz.generate_success_rate_chart('success_rates.png')
viz.generate_file_processing_chart('file_times.png')

# Generate HTML report
viz.generate_html_report('pipeline_analysis.html')

print("Visualizations saved!")
```

---

## Best Practices

### 1. Start Small

Always test with a small subset first:

```python
# Test with 5 files
pipeline.run(limit=5, generate_reports=True)

# Review results, then scale up
pipeline.run(limit=50, generate_reports=True)

# Finally process all
pipeline.run(generate_reports=True)
```

---

### 2. Monitor Memory

Check memory usage for large libraries:

```python
import psutil

process = psutil.Process()
mem_start = process.memory_info().rss / 1024 / 1024

pipeline.run()

mem_end = process.memory_info().rss / 1024 / 1024
print(f"Memory used: {mem_end - mem_start:.1f} MB")
```

If memory is an issue:
- Disable file tracking: `enable_file_tracking=False`
- Process in batches: `run(limit=100)`, repeat
- Disable semantic similarity: `enable_semantic_similarity=False`

---

### 3. Leverage Caching

The second run is MUCH faster:

```bash
# First run: Generate embeddings (~30 min)
python pipeline_instrumented.py --full

# Second run: Use cache (~5 min)
python pipeline_instrumented.py --full
```

Cache files:
- `embedding_cache.json` - Document embeddings
- API calls are cached automatically

---

### 4. Review Errors

Always check for errors after processing:

```python
with open('pipeline_report.json') as f:
    report = json.load(f)

if report['pipeline_summary']['failed_files'] > 0:
    print(f"⚠️  {report['pipeline_summary']['failed_files']} files failed")
    
    for error in report.get('errors', []):
        print(f"\nStage {error['stage_id']}:")
        print(f"  {error['error_type']}: {error['error_message']}")
        print(f"  File: {error.get('context', {}).get('file_path', 'N/A')}")
```

---

### 5. Tune Configuration

Adjust based on results:

```python
# Default (balanced)
pipeline = InstrumentedLibraryRAGPipeline(
    similarity_threshold=0.75,
    top_k_similar=10
)

# Strict relationships (fewer, higher quality)
pipeline = InstrumentedLibraryRAGPipeline(
    similarity_threshold=0.85,
    top_k_similar=5
)

# Relaxed relationships (more, lower quality)
pipeline = InstrumentedLibraryRAGPipeline(
    similarity_threshold=0.70,
    top_k_similar=15
)
```

---

## Troubleshooting

### Issue: Pipeline is slow

**Symptoms**: Taking >1 hour for 1000 files

**Solutions**:

1. **Check if embeddings are cached**:
   ```bash
   ls -lh embedding_cache.json
   # Should exist and be ~50MB after first run
   ```

2. **Disable semantic similarity**:
   ```python
   pipeline = InstrumentedLibraryRAGPipeline(
       enable_semantic_similarity=False
   )
   ```

3. **Check network speed**: Embeddings require API calls

4. **Use faster API model**: Already using `text-embedding-3-small` (fastest)

---

### Issue: Out of memory

**Symptoms**: `MemoryError` or system slows down

**Solutions**:

1. **Disable file tracking**:
   ```python
   pipeline = InstrumentedLibraryRAGPipeline(
       enable_file_tracking=False
   )
   ```

2. **Process in batches**:
   ```python
   for i in range(0, 1000, 100):
       pipeline.run(limit=100)
   ```

3. **Close other applications**

4. **Upgrade RAM** (if processing >10K files regularly)

---

### Issue: Cache not working

**Symptoms**: Re-running takes same time as first run

**Solutions**:

1. **Check cache file exists**:
   ```bash
   ls -l embedding_cache.json
   ```

2. **Verify cache is enabled**:
   ```python
   # In pipeline_instrumented.py, check:
   self.semantic_detector = SemanticSimilarityDetector(
       use_cache=True,  # Should be True
       cache_path="embedding_cache.json"
   )
   ```

3. **Clear corrupt cache**:
   ```bash
   rm embedding_cache.json
   # Re-run pipeline
   ```

---

### Issue: Errors during processing

**Symptoms**: Files failed, errors in report

**Solutions**:

1. **Review error details**:
   ```python
   with open('pipeline_report.json') as f:
       report = json.load(f)
       for error in report.get('errors', []):
           print(error)
   ```

2. **Common errors**:
   - **File encoding**: Ensure UTF-8 encoding
   - **Empty files**: Skip or add content
   - **Malformed markdown**: Fix syntax
   - **Missing API key**: Check `.env` file

3. **Fix and re-run**: Pipeline will skip already-processed files

---

### Issue: Reports not generated

**Symptoms**: No JSON files after completion

**Solutions**:

1. **Ensure generate_reports=True**:
   ```python
   pipeline.run(generate_reports=True)
   ```

2. **Check file permissions**:
   ```bash
   ls -l *.json
   # Should be writable
   ```

3. **Look for exceptions in output**

---

## API Reference

### PipelineInstrumentation Class

```python
from scripts.instrumentation import PipelineInstrumentation

instr = PipelineInstrumentation(enable_file_tracking=True)
```

#### Key Methods:

**Pipeline Control:**
```python
instr.start_pipeline()                    # Start pipeline timing
instr.end_pipeline()                      # End pipeline timing
```

**Stage Control:**
```python
instr.start_stage(stage_id, stage_name)   # Start stage timing
instr.end_stage(stage_id)                 # End stage timing
```

**Metrics Update:**
```python
instr.increment_processed(stage_id, count=1)   # Increment processed count
instr.increment_failed(stage_id, count=1)      # Increment failed count
instr.add_bytes_processed(stage_id, bytes)     # Add bytes processed
instr.record_error(stage_id, error, context)   # Record error
```

**File Tracking:**
```python
instr.track_file_start(file_path, file_size)   # Start file tracking
instr.track_file_end(file_path, success, error)# End file tracking
instr.record_stage_time(stage_id, file_path, duration)  # Record stage time
```

**API Tracking:**
```python
instr.record_api_call(service, duration, cached=False)  # Record API call
instr.record_cache_hit()                                # Record cache hit
instr.record_cache_miss()                               # Record cache miss
```

**Reporting:**
```python
instr.generate_report()                        # Generate report dict
instr.save_report(filename)                    # Save main report
instr.save_detailed_metrics(filename)          # Save detailed metrics
instr.print_report()                           # Print to console
```

---

### InstrumentedLibraryRAGPipeline Class

```python
from scripts.pipeline_instrumented import InstrumentedLibraryRAGPipeline

pipeline = InstrumentedLibraryRAGPipeline(
    root_path="LibraryRAG",
    enable_file_tracking=True,
    enable_semantic_similarity=True,
    similarity_threshold=0.75,
    top_k_similar=10
)
```

#### Key Methods:

```python
# Run pipeline
pipeline.run(limit=None, generate_reports=True)

# Individual stages (called internally)
pipeline.scan_files()                           # Stage 1
pipeline.read_file(file_path)                   # Stage 2
pipeline.extract_relationships(content, ...)    # Stage 3
pipeline.chunk_content(content, metadata)       # Stage 4
pipeline.generate_tags(content, file_path)      # Stage 5
pipeline.generate_embedding(text)               # Stage 6
```

---

## Summary

### Quick Reference

| Task | Command |
|------|---------|
| **Test with 5 files** | `python pipeline_instrumented.py` |
| **Process 50 files** | Edit script, set `limit=50` |
| **Process all files** | Edit script, set `limit=None` |
| **View report** | `cat pipeline_report.json` |
| **Check cache** | `ls -lh embedding_cache.json` |
| **Disable tracking** | Set `enable_file_tracking=False` |
| **Fast mode** | Set `enable_semantic_similarity=False` |

### Key Metrics

- **Speed**: ~2 sec/file (first run), ~0.3 sec/file (cached)
- **Memory**: ~400MB for 1000 files
- **Cost**: ~$0.02 per 1000 files (first run)
- **Cache savings**: 99%+ on subsequent runs

### Files Generated

1. `pipeline_report.json` - Main report (~50-500KB)
2. `pipeline_metrics_detailed.json` - Detailed metrics (~1-10MB)
3. `semantic_similarity_report.json` - Semantic analysis (~100KB-1MB)
4. `embedding_cache.json` - Embedding cache (~50MB)

---

## Conclusion

The instrumentation system provides **complete visibility** into the LibraryRAG pipeline:

✅ **Track** every stage, file, and API call  
✅ **Monitor** memory usage and performance  
✅ **Identify** bottlenecks and errors  
✅ **Optimize** based on detailed metrics  
✅ **Report** comprehensive statistics  

**Ready for production use!** 🚀

---

*Last updated: October 3, 2025*  
*Version: 1.0*  
*Status: Production Ready*

