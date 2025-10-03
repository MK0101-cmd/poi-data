"""
Instrumented Pipeline for LibraryRAG
Includes comprehensive tracking for stages 1-6
"""

import os
import time
from pathlib import Path
from typing import List, Dict
from dotenv import load_dotenv
import openai

from .database import Database
from .instrumentation import PipelineInstrumentation, timed_stage
from .relationship_detector import EnhancedRelationshipDetector
from .semantic_similarity import SemanticSimilarityDetector, SemanticSimilarityIntegration

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")


class InstrumentedLibraryRAGPipeline:
    """
    LibraryRAG Pipeline with comprehensive instrumentation
    Tracks all stages 1-6 with detailed metrics
    """
    
    def __init__(self, root_path: str = "LibraryRAG", 
                 enable_file_tracking: bool = True,
                 enable_semantic_similarity: bool = True,
                 similarity_threshold: float = 0.75,
                 top_k_similar: int = 10):
        self.root_path = Path(root_path)
        self.db = Database()
        
        # Initialize instrumentation
        self.instrumentation = PipelineInstrumentation(
            enable_file_tracking=enable_file_tracking
        )
        
        # Initialize enhanced relationship detector
        self.relationship_detector = EnhancedRelationshipDetector()
        
        # Initialize semantic similarity detector
        self.enable_semantic_similarity = enable_semantic_similarity
        self.semantic_detector = SemanticSimilarityDetector(
            similarity_threshold=similarity_threshold,
            top_k=top_k_similar,
            use_cache=True,
            cache_path="embedding_cache.json"
        ) if enable_semantic_similarity else None
        
        # Integrate semantic similarity with relationship detector
        if self.enable_semantic_similarity:
            SemanticSimilarityIntegration.add_to_relationship_detector(
                self.relationship_detector,
                self.semantic_detector
            )
        
        # Embedding cache for stage 6
        self.embedding_cache: Dict[str, List[float]] = {}
        
        # Store all files for relationship detection
        self.all_files: List[Dict] = []
        
        # Store file content for semantic similarity
        self.file_contents: Dict[str, str] = {}
    
    def scan_files(self) -> List[Dict]:
        """
        Stage 1: File Discovery
        Scan all markdown files and extract metadata
        """
        self.instrumentation.start_stage(1, "File Discovery")
        
        files = []
        try:
            for file_path in self.root_path.rglob("*.md"):
                try:
                    rel_path = str(file_path.relative_to(self.root_path))
                    parts = rel_path.split(os.sep)
                    file_size = file_path.stat().st_size
                    
                    file_metadata = {
                        'file_path': str(file_path),
                        'file_name': file_path.name,
                        'file_size': file_size,
                        'category': parts[0] if len(parts) > 0 else 'Unknown',
                        'subcategory': parts[1] if len(parts) > 1 else 'Unknown',
                        'hierarchy_path': parts,
                        'depth': len(parts)
                    }
                    
                    files.append(file_metadata)
                    
                    # Track in instrumentation
                    self.instrumentation.track_file_start(
                        str(file_path), 
                        file_size
                    )
                    self.instrumentation.add_bytes_processed(1, file_size)
                    self.instrumentation.increment_processed(1)
                    
                except Exception as e:
                    self.instrumentation.increment_failed(1)
                    self.instrumentation.record_error(
                        1, e, {'file_path': str(file_path)}
                    )
                    continue
            
            self.instrumentation.total_files = len(files)
            self.all_files = files  # Store for relationship detection
            
            # Build relationship detector index
            print(f"Found {len(files)} markdown files")
            print(f"Building relationship index...")
            self.relationship_detector.build_file_index(files)
            print(f"Index built with {len(self.relationship_detector.file_index)} entries")
            
        except Exception as e:
            self.instrumentation.record_error(1, e)
            raise
        finally:
            self.instrumentation.end_stage(1)
        
        return files
    
    def read_file(self, file_path: str) -> str:
        """
        Stage 2: Content Extraction
        Read and parse file content
        """
        stage_start = time.time()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Track metrics
            file_size = os.path.getsize(file_path)
            self.instrumentation.add_bytes_processed(2, file_size)
            self.instrumentation.increment_processed(2)
            
            # Record timing for this file
            duration = time.time() - stage_start
            self.instrumentation.record_stage_time(2, file_path, duration)
            
            return content
            
        except Exception as e:
            self.instrumentation.increment_failed(2)
            self.instrumentation.record_error(
                2, e, {'file_path': file_path}
            )
            raise
    
    def extract_relationships(self, content: str, file_path: str, file_metadata: Dict) -> List[Dict]:
        """
        Stage 3: Relationship Mapping (Enhanced)
        Extract links, card references, building blocks, and implicit relationships
        """
        stage_start = time.time()
        
        try:
            # Use enhanced relationship detector
            relationships = self.relationship_detector.detect_all_relationships(
                content=content,
                file_path=file_path,
                file_metadata=file_metadata,
                all_files=self.all_files
            )
            
            # Convert Relationship objects to dicts
            relationship_dicts = [rel.to_dict() for rel in relationships]
            
            # Get summary statistics
            summary = self.relationship_detector.get_relationship_summary(relationships)
            
            # Update file metrics
            self.instrumentation.update_file_metrics(
                file_path,
                relationships_found=summary['total']
            )
            
            # Track by relationship type
            for rel_type, count in summary['by_type'].items():
                self.instrumentation.increment_processed(3, count)
            
            # Record timing
            duration = time.time() - stage_start
            self.instrumentation.record_stage_time(3, file_path, duration)
            
            return relationship_dicts
            
        except Exception as e:
            self.instrumentation.increment_failed(3)
            self.instrumentation.record_error(
                3, e, {'file_path': file_path}
            )
            return []
    
    def chunk_content(self, content: str, file_metadata: Dict) -> List[Dict]:
        """
        Stage 4: Content Chunking
        Split content into manageable chunks
        """
        stage_start = time.time()
        file_path = file_metadata['file_path']
        chunks = []
        
        try:
            sections = content.split('\n## ')
            
            for i, section in enumerate(sections):
                if not section.strip():
                    continue
                
                lines = section.split('\n')
                section_title = lines[0].replace('#', '').strip()
                section_text = '\n'.join(lines[1:])
                
                if len(section_text.strip()) < 50:
                    continue
                
                chunks.append({
                    'chunk_text': section_text,
                    'chunk_index': i,
                    'section_title': section_title,
                    'section_type': self._classify_section(section_title),
                    'metadata': file_metadata,
                    'chunk_tokens': len(section_text.split()) * 1.3  # Rough estimate
                })
            
            # Update metrics
            self.instrumentation.update_file_metrics(
                file_path,
                chunks_created=len(chunks)
            )
            self.instrumentation.increment_processed(4, len(chunks))
            
            # Record timing
            duration = time.time() - stage_start
            self.instrumentation.record_stage_time(4, file_path, duration)
            
            return chunks
            
        except Exception as e:
            self.instrumentation.increment_failed(4)
            self.instrumentation.record_error(
                4, e, {'file_path': file_path}
            )
            return []
    
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
    
    def generate_tags(self, content: str, file_path: str) -> List[str]:
        """
        Stage 5: Tag Generation
        Extract and generate tags from content
        """
        stage_start = time.time()
        tags = []
        
        try:
            # Simple keyword extraction (can be enhanced with NLP)
            keywords = {
                'leadership', 'team', 'conflict', 'communication', 
                'reflection', 'coaching', 'training', 'facilitation',
                'personal-growth', 'transformation', 'mindfulness'
            }
            
            content_lower = content.lower()
            for keyword in keywords:
                if keyword in content_lower:
                    tags.append(keyword)
            
            # Update metrics
            self.instrumentation.update_file_metrics(
                file_path,
                tags_generated=len(tags)
            )
            self.instrumentation.increment_processed(5, len(tags))
            
            # Record timing
            duration = time.time() - stage_start
            self.instrumentation.record_stage_time(5, file_path, duration)
            
            return tags
            
        except Exception as e:
            self.instrumentation.increment_failed(5)
            self.instrumentation.record_error(
                5, e, {'file_path': file_path}
            )
            return []
    
    def generate_embedding(self, text: str, use_cache: bool = True) -> List[float]:
        """
        Stage 6: Embedding Generation
        Generate vector embeddings using OpenAI
        """
        import hashlib
        
        # Check cache
        if use_cache:
            text_hash = hashlib.md5(text.encode()).hexdigest()
            if text_hash in self.embedding_cache:
                self.instrumentation.record_cache_hit()
                return self.embedding_cache[text_hash]
            else:
                self.instrumentation.record_cache_miss()
        
        # Generate embedding
        api_start = time.time()
        
        try:
            response = openai.embeddings.create(
                input=text,
                model="text-embedding-3-small"
            )
            embedding = response.data[0].embedding
            
            # Track API call
            api_duration = time.time() - api_start
            self.instrumentation.record_api_call('openai_embeddings', api_duration)
            self.instrumentation.increment_processed(6)
            
            # Cache result
            if use_cache:
                self.embedding_cache[text_hash] = embedding
            
            return embedding
            
        except Exception as e:
            self.instrumentation.increment_failed(6)
            self.instrumentation.record_error(6, e, {'text_preview': text[:100]})
            raise
    
    def process_file(self, file_metadata: Dict):
        """
        Process a single file through all stages
        """
        file_path = file_metadata['file_path']
        
        print(f"\n📄 Processing: {Path(file_path).name}")
        
        try:
            # Stage 2: Content Extraction
            self.instrumentation.start_stage(2, "Content Extraction")
            content = self.read_file(file_path)
            self.instrumentation.end_stage(2)
            
            # Store content for semantic similarity
            if self.enable_semantic_similarity:
                self.file_contents[file_path] = content
            
            # Stage 3: Relationship Mapping (Enhanced)
            self.instrumentation.start_stage(3, "Relationship Mapping")
            relationships = self.extract_relationships(content, file_path, file_metadata)
            self.instrumentation.end_stage(3)
            
            if relationships:
                print(f"  🔗 Found {len(relationships)} relationships")
            
            # Stage 4: Content Chunking
            self.instrumentation.start_stage(4, "Content Chunking")
            chunks = self.chunk_content(content, file_metadata)
            self.instrumentation.end_stage(4)
            
            if not chunks:
                print(f"  ⚠️  No chunks created for {file_path}")
                self.instrumentation.track_file_end(file_path, success=False, 
                    error="No chunks created")
                return
            
            # Stage 5: Tag Generation
            self.instrumentation.start_stage(5, "Tag Generation")
            tags = self.generate_tags(content, file_path)
            self.instrumentation.end_stage(5)
            
            # Stage 6: Embedding Generation
            self.instrumentation.start_stage(6, "Embedding Generation")
            chunks_with_embeddings = []
            
            for i, chunk in enumerate(chunks):
                embedding = self.generate_embedding(chunk['chunk_text'])
                chunks_with_embeddings.append({
                    'document_id': None,  # Will be set after document insert
                    'chunk_text': chunk['chunk_text'],
                    'chunk_index': chunk['chunk_index'],
                    'section_title': chunk['section_title'],
                    'section_type': chunk['section_type'],
                    'embedding': embedding,
                    'chunk_tokens': chunk.get('chunk_tokens')
                })
                
                # Progress indicator
                self.instrumentation.print_progress(
                    i + 1, len(chunks), 
                    f"  Embeddings"
                )
            
            self.instrumentation.end_stage(6)
            
            # Add to semantic similarity detector
            if self.enable_semantic_similarity and chunks_with_embeddings:
                # Use the first chunk's embedding as document embedding
                # (or could use average of all chunks, but first is simpler)
                document_embedding = chunks_with_embeddings[0]['embedding']
                self.semantic_detector.add_document_embedding(
                    file_path,
                    content,
                    embedding=document_embedding
                )
            
            # Update file metrics
            self.instrumentation.update_file_metrics(
                file_path,
                embeddings_created=len(chunks_with_embeddings)
            )
            
            # Stage 7: Database insertion (not tracked in stages 1-6)
            print(f"  💾 Inserting into database...")
            document_id = self.db.insert_document({
                **file_metadata,
                'content': content,
                'content_type': 'markdown'
            })
            
            # Update document_id in chunks
            for chunk in chunks_with_embeddings:
                chunk['document_id'] = document_id
            
            # Batch insert chunks
            self.db.insert_chunks_batch(chunks_with_embeddings)
            
            print(f"  ✓ Inserted {len(chunks_with_embeddings)} chunks")
            
            # Mark file as successfully processed
            self.instrumentation.track_file_end(file_path, success=True)
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            self.instrumentation.track_file_end(
                file_path, 
                success=False, 
                error=str(e)
            )
    
    def _compute_semantic_similarities(self):
        """
        Compute semantic similarities between all documents
        and save results
        """
        try:
            # Get statistics
            stats = self.semantic_detector.get_statistics()
            print(f"  📊 Semantic similarity statistics:")
            print(f"     Total documents: {stats['total_documents']}")
            print(f"     Cached embeddings: {stats['cached_embeddings']}")
            
            if stats['total_documents'] > 0:
                sim_stats = stats.get('similarity_stats', {})
                print(f"     Mean similarity: {sim_stats.get('mean', 0):.3f}")
                print(f"     Median similarity: {sim_stats.get('median', 0):.3f}")
            
            # Find clusters
            print(f"\n  🔍 Finding semantic clusters...")
            clusters = self.semantic_detector.find_clusters(
                min_cluster_size=3,
                min_intra_similarity=0.8
            )
            
            if clusters:
                print(f"  📦 Found {len(clusters)} clusters:")
                for i, cluster in enumerate(clusters[:5], 1):
                    print(f"     Cluster {i}: {len(cluster)} documents")
            else:
                print(f"  📦 No clusters found (threshold may be too high)")
            
            # Save results
            import json
            results = {
                'statistics': stats,
                'clusters': [
                    {
                        'cluster_id': i,
                        'size': len(cluster),
                        'documents': [str(Path(p).name) for p in cluster]
                    }
                    for i, cluster in enumerate(clusters, 1)
                ],
                'sample_similarities': {}
            }
            
            # Add sample similarities for first few documents
            all_paths = list(self.semantic_detector.document_embeddings.keys())
            for path in all_paths[:5]:
                similar = self.semantic_detector.find_similar_documents(path)
                results['sample_similarities'][str(Path(path).name)] = [
                    {
                        'document': str(Path(s.target_path).name),
                        'similarity': f"{s.similarity_score:.3f}"
                    }
                    for s in similar[:3]
                ]
            
            with open("reports/semantic_similarity_report.json", 'w') as f:
                json.dump(results, f, indent=2)
            
            print(f"  ✅ Semantic similarity report saved!")
            
        except Exception as e:
            print(f"  ⚠️  Error computing semantic similarities: {e}")
    
    def run(self, limit: int = None, generate_reports: bool = True):
        """
        Run the complete pipeline with instrumentation
        
        Args:
            limit: Limit number of files to process (None = all)
            generate_reports: Whether to generate and save reports
        """
        self.instrumentation.start_pipeline()
        
        try:
            # Stage 1: File Discovery
            files = self.scan_files()
            
            if limit:
                files = files[:limit]
                print(f"Processing first {limit} files...")
            
            # Process each file through stages 2-6
            for i, file_metadata in enumerate(files):
                print(f"\n[{i+1}/{len(files)}]", end=" ")
                self.process_file(file_metadata)
            
            # Stage 7: Semantic Similarity Analysis (if enabled)
            if self.enable_semantic_similarity:
                print("\n\n🔍 Computing semantic similarities...")
                self._compute_semantic_similarities()
            
            print("\n\n✅ Pipeline complete!")
            
        except Exception as e:
            print(f"\n\n❌ Pipeline failed: {e}")
            raise
        
        finally:
            self.instrumentation.end_pipeline()
            
            if generate_reports:
                print("\n📊 Generating reports...")
                self.instrumentation.print_report()
                self.instrumentation.save_report("reports/pipeline_report.json")
                self.instrumentation.save_detailed_metrics("reports/pipeline_metrics_detailed.json")
                print("\n✅ Reports saved!")


if __name__ == "__main__":
    """
    Example usage of instrumented pipeline with semantic similarity
    """
    
    # Create instrumented pipeline with semantic similarity
    pipeline = InstrumentedLibraryRAGPipeline(
        root_path="LibraryRAG",
        enable_file_tracking=True,  # Enable detailed file-level tracking
        enable_semantic_similarity=True,  # Enable semantic similarity detection
        similarity_threshold=0.75,  # Minimum similarity score
        top_k_similar=10  # Return top 10 similar documents
    )
    
    # Run pipeline
    # Start with a small number to test
    pipeline.run(limit=5, generate_reports=True)
    
    # To process all files:
    # pipeline.run(generate_reports=True)
    
    # To disable semantic similarity (faster, less memory):
    # pipeline_no_semantic = InstrumentedLibraryRAGPipeline(
    #     enable_semantic_similarity=False
    # )
    # pipeline_no_semantic.run()
    
    # To disable file-level tracking (reduces memory usage):
    # pipeline_no_tracking = InstrumentedLibraryRAGPipeline(
    #     enable_file_tracking=False,
    #     enable_semantic_similarity=True
    # )
    # pipeline_no_tracking.run()

