# Scripts Library

This directory contains all Python scripts for the POI Data processing project.

## Scripts Overview

### Core Scripts
- **`database.py`** - Database connection and management utilities
- **`instrumentation.py`** - Pipeline instrumentation and metrics collection
- **`pipeline_instrumented.py`** - Main instrumented pipeline for LibraryRAG processing
- **`relationship_detector.py`** - Enhanced relationship detection between documents
- **`semantic_similarity.py`** - Semantic similarity detection using embeddings

### Analysis & Visualization Scripts
- **`visualize_metrics.py`** - Metrics visualization utilities
- **`visualize_pipeline_report.py`** - Pipeline report visualization and HTML dashboard generation
- **`generate_relation_report.py`** - Relationship analysis report generation

## Usage

### Importing Scripts
```python
# Import individual modules
from scripts.database import Database
from scripts.pipeline_instrumented import InstrumentedLibraryRAGPipeline
from scripts.semantic_similarity import SemanticSimilarityDetector

# Import the entire scripts package
import scripts
```

### Running Scripts Directly
```bash
# Run visualization scripts
python scripts/visualize_pipeline_report.py
python scripts/generate_relation_report.py

# Run with specific files
python scripts/visualize_pipeline_report.py reports/pipeline_report.json
```

## Migration Notes

All scripts have been moved from the root directory to this `scripts/` directory. The following changes were made:

1. **Import Updates**: All internal imports between scripts now use relative imports (e.g., `from .database import Database`)
2. **External References**: All documentation and external files have been updated to reference scripts with the `scripts.` prefix
3. **Package Structure**: Added `__init__.py` to make this a proper Python package

## Dependencies

All scripts maintain their original dependencies. See `requirements.txt` in the project root for the complete list.
