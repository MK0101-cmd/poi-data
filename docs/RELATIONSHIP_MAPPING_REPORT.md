================================================================================
RELATIONSHIP MAPPING REPORT
================================================================================
Generated: 2025-10-03 19:07:42
Source: pipeline_metrics_detailed.json

EXECUTIVE SUMMARY
--------------------------------------------------------------------------------
Total Files Analyzed:          707
Files Successfully Processed:  702 (99.3%)
Files Failed:                  5 (0.7%)
Files with Relationships:      5
Total Relationships Found:     1,325
Total Chunks Created:          26
Total Tags Generated:          17
Total Embeddings Created:      0

PIPELINE EXECUTION
--------------------------------------------------------------------------------
Start Time:     2025-10-03T19:00:25.218467
End Time:       2025-10-03T19:00:38.542063
Duration:       13.32s
Success Rate:   0.0%
Cache Hit Rate: 0.0%

CATEGORY BREAKDOWN
--------------------------------------------------------------------------------
Category        Files    Chunks   Tags     Embed    Relations 
--------------------------------------------------------------------------------
Activities      574      26       17       0        1325      
Trainings       133      0        0        0        0         

SUBCATEGORY BREAKDOWN (Top 15)
--------------------------------------------------------------------------------
Subcategory     Files    Chunks   Tags     Embed    Relations 
--------------------------------------------------------------------------------
SPEAK           219      0        0        0        0         
TCG             101      0        0        0        0         
FLOW            98       0        0        0        0         
BTC24           65       0        0        0        0         
FACES           59       0        0        0        0         
MASTERCLASSES   38       0        0        0        0         
CANVASES        27       26       17       0        1325      
AI              25       0        0        0        0         
INTERACTION     22       0        0        0        0         
WORKSHOPS       21       0        0        0        0         
CASESTUDIES     13       0        0        0        0         
JOURNEYS        11       0        0        0        0         
PHOTOTHERAPY    8        0        0        0        0         

RELATIONSHIP ANALYSIS
--------------------------------------------------------------------------------
✓ Found 5 files with relationships
✓ Total relationships detected: 1325

TOP FILES WITH MOST RELATIONSHIPS:

  • LibraryRAG\Activities\CANVASES\Canvas_Card_Integration_Summary.md
    Relationships: 489 | Size: 8,218 bytes
  • LibraryRAG\Activities\CANVASES\01_Mindfulness_and_Presence\Connecting_to_Presence_Building_Blocks.md
    Relationships: 278 | Size: 1,955 bytes
  • LibraryRAG\Activities\CANVASES\01_Mindfulness_and_Presence\Happiness_Hides_in_the_Little_Things_Building_Blocks.md
    Relationships: 275 | Size: 1,869 bytes
  • LibraryRAG\Activities\CANVASES\Canvas_Card_Mapping.md
    Relationships: 189 | Size: 10,125 bytes
  • LibraryRAG\Activities\CANVASES\Canvas_Thematic_Index.md
    Relationships: 94 | Size: 5,170 bytes

ERROR ANALYSIS
--------------------------------------------------------------------------------
❌ Total Errors: 5

  OpenAI Error: 5 occurrences
    - LibraryRAG\Activities\CANVASES\Canvas_Card_Integration_Summary.md
    - LibraryRAG\Activities\CANVASES\Canvas_Card_Mapping.md

DATABASE SCHEMA MAPPING
--------------------------------------------------------------------------------
The relationship data maps to the following database structure:

Table: cross_references
  • source_document_id  : UUID of source document
  • target_document_id  : UUID of target document
  • reference_type      : 'markdown_link', 'related', 'parent-child', etc.
  • relationship_strength: 0.0 to 1.0 (confidence score)
  • context             : Description or link text

Relationship Types:
  • markdown_link : Direct markdown hyperlinks [text](path)
  • parent-child  : Hierarchical folder relationships
  • cross-series  : References across different card series
  • example       : Activity references to card examples
  • semantic      : Similarity based on embeddings

RECOMMENDATIONS
--------------------------------------------------------------------------------
🔴 CRITICAL: No embeddings generated
   • Set OPENAI_API_KEY environment variable
   • Re-run pipeline to generate embeddings

🟢 IMPLEMENT SEMANTIC SIMILARITY
   • Once embeddings exist, compute cosine similarity between documents
   • Automatically discover related content based on meaning
   • Create relationship_strength scores based on embedding distance

🟢 MANUAL RELATIONSHIP ENRICHMENT
   • Map activities to their associated card collections
   • Link training materials to practical activities
   • Connect journey narratives to specific card stories

================================================================================
END OF REPORT
================================================================================