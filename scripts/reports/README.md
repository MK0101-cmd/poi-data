# 📊 Reports Directory

This directory contains all generated reports, visualizations, and analysis outputs from the POI Data processing pipeline.

## 📁 File Types

### 📈 JSON Reports
- **`pipeline_report.json`** - Main pipeline execution report with stage metrics
- **`pipeline_metrics_detailed.json`** - Detailed file-level processing metrics
- **`semantic_similarity_report.json`** - Semantic similarity analysis results

### 🖼️ Visualization Charts
- **`pipeline_dashboard.html`** - Interactive HTML dashboard with all visualizations
- **`pipeline_overview.png`** - Overview chart showing pipeline performance
- **`stage_durations.png`** - Stage duration analysis chart
- **`stage_success_rates.png`** - Success rate analysis by stage
- **`memory_usage.png`** - Memory usage over time chart
- **`file_processing.png`** - File processing time distribution
- **`errors.png`** - Error analysis and distribution chart

## 🚀 Usage

### Viewing Reports
```bash
# View HTML dashboard
open scripts/reports/pipeline_dashboard.html

# View JSON reports
cat scripts/reports/pipeline_report.json | python -m json.tool
cat scripts/reports/semantic_similarity_report.json | python -m json.tool
```

### Regenerating Reports
```bash
# Run the pipeline to generate new reports
python scripts/pipeline_instrumented.py

# Generate visualizations from existing reports
python scripts/visualize_pipeline_report.py scripts/reports/pipeline_report.json

# Generate relationship analysis report
python scripts/generate_relation_report.py scripts/reports/pipeline_metrics_detailed.json
```

## 📊 Report Contents

### Pipeline Report (`pipeline_report.json`)
- Stage execution times and success rates
- Memory usage statistics
- File processing counts
- Error summaries
- Overall pipeline performance metrics

### Detailed Metrics (`pipeline_metrics_detailed.json`)
- Individual file processing times
- Stage-by-stage file metrics
- Error details per file
- Memory usage per file
- API call timing data

### Semantic Similarity Report (`semantic_similarity_report.json`)
- Document similarity scores
- Similar document pairs
- Embedding analysis results
- Relationship detection data

## 🔄 File Generation

Reports are automatically generated when running:
- `scripts/pipeline_instrumented.py` - Generates all JSON reports
- `scripts/visualize_pipeline_report.py` - Generates PNG charts and HTML dashboard
- `scripts/generate_relation_report.py` - Generates relationship analysis

## 📝 Notes

- Reports are overwritten on each pipeline run
- Large datasets may generate large JSON files (10MB+)
- PNG files are optimized for web viewing
- HTML dashboard includes all visualizations in one file

---

*Reports are generated automatically by the pipeline. For manual generation, see the individual script documentation.*
