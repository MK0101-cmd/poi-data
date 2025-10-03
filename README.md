# 🎯 POI Data Processing Project

A comprehensive RAG (Retrieval-Augmented Generation) system for processing Points of You® training materials and documents.

## 🚀 Quick Start

1. **Setup Environment**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Pipeline**
   ```bash
   python scripts/pipeline_instrumented.py
   ```

3. **View Results**
   - Check `scripts/reports/pipeline_dashboard.html` for visualizations
   - Review `scripts/reports/pipeline_report.json` for detailed metrics

## 📚 Documentation

All documentation is organized in the [`docs/`](docs/) directory:

- **[📋 Documentation Index](docs/README.md)** - Complete documentation overview
- **[🚀 Quick Start Guide](docs/RAG_QUICKSTART_GUIDE.md)** - Get started quickly
- **[🔧 Implementation Guide](docs/INSTRUMENTATION_COMPLETE.md)** - Detailed implementation
- **[📊 Analysis Tools](docs/SEMANTIC_SIMILARITY_GUIDE.md)** - Semantic analysis

## 🏗️ Project Structure

```
poi-data/
├── docs/                    # 📚 All documentation
├── scripts/                 # 🐍 Python scripts
├── LibraryRAG/             # 📖 Processed data
├── datasources/            # 📄 Source documents
├── meadiasporces/          # 🖼️ Media assets
└── requirements.txt        # 📦 Dependencies
```

## 🛠️ Scripts

All Python scripts are in the [`scripts/`](scripts/) directory:

- **`pipeline_instrumented.py`** - Main processing pipeline
- **`semantic_similarity.py`** - Semantic analysis
- **`relationship_detector.py`** - Document relationships
- **`visualize_*.py`** - Visualization tools

See [scripts/README.md](scripts/README.md) for detailed script documentation.

## 📊 Features

- ✅ **Document Processing** - Convert and structure training materials
- ✅ **Semantic Analysis** - Find similar documents using embeddings
- ✅ **Relationship Detection** - Identify connections between documents
- ✅ **Pipeline Instrumentation** - Comprehensive monitoring and metrics
- ✅ **Visualization** - Charts, dashboards, and reports
- ✅ **RAG Integration** - Ready for retrieval-augmented generation

## 🎯 Use Cases

- **Training Material Analysis** - Process and analyze Points of You® content
- **Content Discovery** - Find related documents and activities
- **RAG Implementation** - Build retrieval systems for AI applications
- **Documentation Management** - Organize and structure training materials

## 📈 Recent Updates

- ✅ Moved all scripts to `scripts/` library
- ✅ Organized documentation in `docs/` directory
- ✅ Implemented semantic similarity detection
- ✅ Added comprehensive pipeline instrumentation
- ✅ Created visualization and reporting tools

## 🔗 Quick Links

- [📚 Full Documentation](docs/README.md)
- [🐍 Scripts Documentation](scripts/README.md)
- [🚀 Quick Start Guide](docs/RAG_QUICKSTART_GUIDE.md)
- [🔧 Implementation Guide](docs/INSTRUMENTATION_COMPLETE.md)

---


*For detailed documentation, see the [docs/](docs/) directory.*
