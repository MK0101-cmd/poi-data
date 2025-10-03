"""
Semantic Similarity Module for LibraryRAG
Uses embeddings to detect semantically similar documents
"""

import numpy as np
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass
import json
from pathlib import Path
from collections import defaultdict
import hashlib


@dataclass
class SimilarDocument:
    """Represents a semantically similar document"""
    target_path: str
    similarity_score: float
    target_embedding: Optional[np.ndarray] = None


class SemanticSimilarityDetector:
    """
    Detects semantic similarity between documents using embeddings.
    
    This is the 9th type of relationship detection that complements
    the 8 pattern-based types with embedding-based similarity.
    """
    
    def __init__(self, 
                 similarity_threshold: float = 0.75,
                 top_k: int = 10,
                 use_cache: bool = True,
                 cache_path: str = "embedding_cache.json"):
        """
        Initialize semantic similarity detector
        
        Args:
            similarity_threshold: Minimum cosine similarity (0.0-1.0)
            top_k: Maximum number of similar documents to return
            use_cache: Whether to use embedding cache
            cache_path: Path to embedding cache file
        """
        self.similarity_threshold = similarity_threshold
        self.top_k = top_k
        self.use_cache = use_cache
        self.cache_path = cache_path
        
        # Storage for document embeddings
        self.document_embeddings: Dict[str, np.ndarray] = {}
        
        # Cache for similarity calculations
        self.similarity_cache: Dict[Tuple[str, str], float] = {}
        
        # Embedding cache (text hash -> embedding)
        self.embedding_cache: Dict[str, List[float]] = {}
        if use_cache:
            self._load_embedding_cache()
    
    def _load_embedding_cache(self):
        """Load embedding cache from disk"""
        try:
            if Path(self.cache_path).exists():
                with open(self.cache_path, 'r') as f:
                    self.embedding_cache = json.load(f)
                print(f"📦 Loaded {len(self.embedding_cache)} cached embeddings")
        except Exception as e:
            print(f"⚠️  Could not load embedding cache: {e}")
            self.embedding_cache = {}
    
    def _save_embedding_cache(self):
        """Save embedding cache to disk"""
        if not self.use_cache:
            return
        
        try:
            with open(self.cache_path, 'w') as f:
                json.dump(self.embedding_cache, f)
        except Exception as e:
            print(f"⚠️  Could not save embedding cache: {e}")
    
    def _get_text_hash(self, text: str) -> str:
        """Get hash of text for caching"""
        return hashlib.md5(text.encode()).hexdigest()
    
    def add_document_embedding(self, file_path: str, content: str, 
                               embedding: Optional[np.ndarray] = None,
                               embedding_generator = None):
        """
        Add or update document embedding
        
        Args:
            file_path: Path to document
            content: Document content (for caching)
            embedding: Pre-computed embedding (if available)
            embedding_generator: Function to generate embedding if not provided
        """
        if embedding is not None:
            # Use provided embedding
            self.document_embeddings[file_path] = np.array(embedding)
        elif embedding_generator is not None:
            # Check cache first
            text_hash = self._get_text_hash(content)
            
            if text_hash in self.embedding_cache:
                # Use cached embedding
                self.document_embeddings[file_path] = np.array(
                    self.embedding_cache[text_hash]
                )
            else:
                # Generate new embedding
                embedding = embedding_generator(content)
                self.document_embeddings[file_path] = np.array(embedding)
                
                # Cache it
                if self.use_cache:
                    self.embedding_cache[text_hash] = embedding.tolist()
        else:
            raise ValueError("Either embedding or embedding_generator must be provided")
    
    def batch_add_embeddings(self, documents: List[Dict], embedding_generator):
        """
        Add multiple document embeddings efficiently
        
        Args:
            documents: List of {file_path, content} dicts
            embedding_generator: Function to generate embeddings
        """
        # Separate cached and uncached
        cached_docs = []
        uncached_docs = []
        
        for doc in documents:
            file_path = doc['file_path']
            content = doc['content']
            text_hash = self._get_text_hash(content)
            
            if text_hash in self.embedding_cache:
                # Use cached
                self.document_embeddings[file_path] = np.array(
                    self.embedding_cache[text_hash]
                )
                cached_docs.append(file_path)
            else:
                uncached_docs.append(doc)
        
        print(f"📦 Using {len(cached_docs)} cached embeddings")
        print(f"🔄 Generating {len(uncached_docs)} new embeddings")
        
        # Generate embeddings for uncached documents
        if uncached_docs:
            # Batch generate if possible
            contents = [doc['content'] for doc in uncached_docs]
            embeddings = embedding_generator(contents)  # Assume batch support
            
            for doc, embedding in zip(uncached_docs, embeddings):
                file_path = doc['file_path']
                content = doc['content']
                text_hash = self._get_text_hash(content)
                
                self.document_embeddings[file_path] = np.array(embedding)
                
                if self.use_cache:
                    self.embedding_cache[text_hash] = embedding.tolist()
        
        # Save cache
        if self.use_cache and uncached_docs:
            self._save_embedding_cache()
    
    def cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two vectors
        
        Returns: Similarity score between 0.0 and 1.0
        """
        # Normalize vectors
        vec1_norm = vec1 / (np.linalg.norm(vec1) + 1e-10)
        vec2_norm = vec2 / (np.linalg.norm(vec2) + 1e-10)
        
        # Calculate cosine similarity
        similarity = np.dot(vec1_norm, vec2_norm)
        
        # Ensure in range [0, 1]
        return float(np.clip(similarity, 0.0, 1.0))
    
    def find_similar_documents(self, 
                               source_path: str, 
                               exclude_paths: Set[str] = None,
                               min_similarity: float = None) -> List[SimilarDocument]:
        """
        Find documents semantically similar to source document
        
        Args:
            source_path: Path to source document
            exclude_paths: Paths to exclude from results
            min_similarity: Override similarity threshold
            
        Returns:
            List of similar documents sorted by similarity (highest first)
        """
        if source_path not in self.document_embeddings:
            return []
        
        source_embedding = self.document_embeddings[source_path]
        threshold = min_similarity or self.similarity_threshold
        exclude_paths = exclude_paths or set()
        
        similar_docs = []
        
        for target_path, target_embedding in self.document_embeddings.items():
            # Skip self and excluded paths
            if target_path == source_path or target_path in exclude_paths:
                continue
            
            # Check cache
            cache_key = tuple(sorted([source_path, target_path]))
            if cache_key in self.similarity_cache:
                similarity = self.similarity_cache[cache_key]
            else:
                # Calculate similarity
                similarity = self.cosine_similarity(source_embedding, target_embedding)
                self.similarity_cache[cache_key] = similarity
            
            # Add if above threshold
            if similarity >= threshold:
                similar_docs.append(SimilarDocument(
                    target_path=target_path,
                    similarity_score=similarity,
                    target_embedding=target_embedding
                ))
        
        # Sort by similarity (highest first) and limit to top_k
        similar_docs.sort(key=lambda x: x.similarity_score, reverse=True)
        return similar_docs[:self.top_k]
    
    def find_similar_by_content(self, 
                                content: str, 
                                embedding_generator,
                                exclude_paths: Set[str] = None,
                                min_similarity: float = None) -> List[SimilarDocument]:
        """
        Find documents similar to given content (without adding to index)
        
        Args:
            content: Text content to find similar documents for
            embedding_generator: Function to generate embedding
            exclude_paths: Paths to exclude from results
            min_similarity: Override similarity threshold
            
        Returns:
            List of similar documents
        """
        # Generate embedding for content
        query_embedding = np.array(embedding_generator(content))
        threshold = min_similarity or self.similarity_threshold
        exclude_paths = exclude_paths or set()
        
        similar_docs = []
        
        for target_path, target_embedding in self.document_embeddings.items():
            if target_path in exclude_paths:
                continue
            
            similarity = self.cosine_similarity(query_embedding, target_embedding)
            
            if similarity >= threshold:
                similar_docs.append(SimilarDocument(
                    target_path=target_path,
                    similarity_score=similarity,
                    target_embedding=target_embedding
                ))
        
        similar_docs.sort(key=lambda x: x.similarity_score, reverse=True)
        return similar_docs[:self.top_k]
    
    def batch_find_similar(self, 
                          source_paths: List[str],
                          exclude_already_related: bool = True,
                          existing_relationships: Dict[str, Set[str]] = None) -> Dict[str, List[SimilarDocument]]:
        """
        Find similar documents for multiple sources efficiently
        
        Args:
            source_paths: List of source document paths
            exclude_already_related: Whether to exclude documents with existing relationships
            existing_relationships: Dict of {source_path: set(related_paths)}
            
        Returns:
            Dict mapping source_path to list of similar documents
        """
        results = {}
        existing_relationships = existing_relationships or {}
        
        for source_path in source_paths:
            exclude = existing_relationships.get(source_path, set()) if exclude_already_related else set()
            similar = self.find_similar_documents(source_path, exclude_paths=exclude)
            results[source_path] = similar
        
        return results
    
    def get_similarity_matrix(self, 
                             file_paths: Optional[List[str]] = None) -> Tuple[np.ndarray, List[str]]:
        """
        Generate similarity matrix for all or specified documents
        
        Args:
            file_paths: Specific files to include (None = all)
            
        Returns:
            (similarity_matrix, file_paths) tuple
        """
        if file_paths is None:
            file_paths = list(self.document_embeddings.keys())
        
        n = len(file_paths)
        matrix = np.zeros((n, n))
        
        for i, path1 in enumerate(file_paths):
            if path1 not in self.document_embeddings:
                continue
            
            for j, path2 in enumerate(file_paths):
                if i == j:
                    matrix[i, j] = 1.0
                    continue
                
                if path2 not in self.document_embeddings:
                    continue
                
                # Check cache
                cache_key = tuple(sorted([path1, path2]))
                if cache_key in self.similarity_cache:
                    similarity = self.similarity_cache[cache_key]
                else:
                    similarity = self.cosine_similarity(
                        self.document_embeddings[path1],
                        self.document_embeddings[path2]
                    )
                    self.similarity_cache[cache_key] = similarity
                
                matrix[i, j] = similarity
        
        return matrix, file_paths
    
    def find_clusters(self, 
                     min_cluster_size: int = 3,
                     min_intra_similarity: float = 0.8) -> List[List[str]]:
        """
        Find clusters of semantically similar documents
        
        Args:
            min_cluster_size: Minimum documents per cluster
            min_intra_similarity: Minimum average similarity within cluster
            
        Returns:
            List of clusters (each cluster is list of file paths)
        """
        # Get similarity matrix
        matrix, file_paths = self.get_similarity_matrix()
        n = len(file_paths)
        
        if n < min_cluster_size:
            return []
        
        # Simple clustering: greedy approach
        clusters = []
        used = set()
        
        for i in range(n):
            if i in used:
                continue
            
            # Find all similar documents
            similar_indices = [
                j for j in range(n) 
                if j != i and j not in used and matrix[i, j] >= min_intra_similarity
            ]
            
            if len(similar_indices) + 1 >= min_cluster_size:
                # Form cluster
                cluster_indices = [i] + similar_indices
                
                # Verify intra-cluster similarity
                similarities = []
                for idx1 in cluster_indices:
                    for idx2 in cluster_indices:
                        if idx1 < idx2:
                            similarities.append(matrix[idx1, idx2])
                
                avg_similarity = np.mean(similarities) if similarities else 0
                
                if avg_similarity >= min_intra_similarity:
                    cluster = [file_paths[idx] for idx in cluster_indices]
                    clusters.append(cluster)
                    used.update(cluster_indices)
        
        return clusters
    
    def get_statistics(self) -> Dict:
        """Get statistics about semantic similarity detector"""
        if not self.document_embeddings:
            return {
                'total_documents': 0,
                'cached_embeddings': len(self.embedding_cache),
                'cached_similarities': len(self.similarity_cache)
            }
        
        # Calculate some statistics
        embeddings_list = list(self.document_embeddings.values())
        all_similarities = []
        
        for i, emb1 in enumerate(embeddings_list):
            for emb2 in embeddings_list[i+1:]:
                sim = self.cosine_similarity(emb1, emb2)
                all_similarities.append(sim)
        
        return {
            'total_documents': len(self.document_embeddings),
            'cached_embeddings': len(self.embedding_cache),
            'cached_similarities': len(self.similarity_cache),
            'similarity_stats': {
                'mean': float(np.mean(all_similarities)) if all_similarities else 0,
                'std': float(np.std(all_similarities)) if all_similarities else 0,
                'min': float(np.min(all_similarities)) if all_similarities else 0,
                'max': float(np.max(all_similarities)) if all_similarities else 0,
                'median': float(np.median(all_similarities)) if all_similarities else 0
            }
        }
    
    def get_document_summary(self, file_path: str) -> Dict:
        """Get summary for a specific document"""
        if file_path not in self.document_embeddings:
            return {'error': 'Document not found'}
        
        similar = self.find_similar_documents(file_path)
        
        return {
            'file_path': file_path,
            'has_embedding': True,
            'embedding_dimension': len(self.document_embeddings[file_path]),
            'similar_documents_count': len(similar),
            'top_similar': [
                {
                    'path': Path(doc.target_path).name,
                    'similarity': f"{doc.similarity_score:.3f}"
                }
                for doc in similar[:5]
            ]
        }


class SemanticSimilarityIntegration:
    """
    Helper class to integrate semantic similarity with EnhancedRelationshipDetector
    """
    
    @staticmethod
    def add_to_relationship_detector(relationship_detector, 
                                     semantic_detector: SemanticSimilarityDetector):
        """
        Add semantic similarity as 9th detection method
        
        This patches the relationship detector to include semantic similarity
        """
        # Store reference
        relationship_detector.semantic_detector = semantic_detector
        
        # Add new detection method
        original_detect = relationship_detector.detect_all_relationships
        
        def detect_with_semantic(content: str, file_path: str, 
                                file_metadata: Dict, all_files: List[Dict]):
            # Run original 8 detection methods
            relationships = original_detect(content, file_path, file_metadata, all_files)
            
            # Add semantic similarity detection
            semantic_relationships = SemanticSimilarityIntegration._detect_semantic_similarity(
                file_path, 
                relationship_detector, 
                semantic_detector,
                relationships
            )
            
            relationships.extend(semantic_relationships)
            
            return relationship_detector._deduplicate_relationships(relationships)
        
        # Patch the method
        relationship_detector.detect_all_relationships = detect_with_semantic
    
    @staticmethod
    def _detect_semantic_similarity(file_path: str,
                                   relationship_detector,
                                   semantic_detector: SemanticSimilarityDetector,
                                   existing_relationships: List) -> List:
        """Detect semantic similarity relationships"""
        from .relationship_detector import Relationship
        
        # Get existing relationship targets to exclude
        existing_targets = {r.target_path for r in existing_relationships}
        
        # Find semantically similar documents
        similar_docs = semantic_detector.find_similar_documents(
            file_path,
            exclude_paths=existing_targets
        )
        
        # Convert to Relationship objects
        relationships = []
        for sim_doc in similar_docs:
            relationships.append(Relationship(
                source_path=file_path,
                target_path=sim_doc.target_path,
                relationship_type='semantic_similarity',
                confidence=float(sim_doc.similarity_score),
                context={
                    'similarity_score': float(sim_doc.similarity_score),
                    'detection_method': 'embedding_based',
                    'excludes_existing': True
                }
            ))
        
        return relationships


if __name__ == "__main__":
    """
    Test semantic similarity detection
    """
    import openai
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    openai.api_key = os.getenv("OPENAI_API_KEY")
    
    # Sample embedding generator
    def generate_embedding(text):
        if isinstance(text, list):
            # Batch mode
            response = openai.embeddings.create(
                input=text,
                model="text-embedding-3-small"
            )
            return [item.embedding for item in response.data]
        else:
            # Single mode
            response = openai.embeddings.create(
                input=text,
                model="text-embedding-3-small"
            )
            return response.data[0].embedding
    
    # Initialize detector
    detector = SemanticSimilarityDetector(
        similarity_threshold=0.75,
        top_k=5
    )
    
    # Sample documents
    docs = [
        {
            'file_path': 'doc1.md',
            'content': 'This is about leadership and team management.'
        },
        {
            'file_path': 'doc2.md',
            'content': 'Leadership skills for effective teams.'
        },
        {
            'file_path': 'doc3.md',
            'content': 'Cooking recipes and kitchen tips.'
        },
        {
            'file_path': 'doc4.md',
            'content': 'Team building activities and exercises.'
        }
    ]
    
    # Add embeddings
    print("Generating embeddings...")
    for doc in docs:
        embedding = generate_embedding(doc['content'])
        detector.add_document_embedding(
            doc['file_path'],
            doc['content'],
            embedding=embedding
        )
    
    # Find similar documents
    print("\nFinding similar documents to doc1.md:")
    similar = detector.find_similar_documents('doc1.md')
    
    for sim_doc in similar:
        print(f"  - {sim_doc.target_path}: {sim_doc.similarity_score:.3f}")
    
    # Get statistics
    print("\nStatistics:")
    stats = detector.get_statistics()
    print(json.dumps(stats, indent=2))
    
    # Find clusters
    print("\nFinding clusters...")
    clusters = detector.find_clusters(min_cluster_size=2, min_intra_similarity=0.7)
    for i, cluster in enumerate(clusters, 1):
        print(f"Cluster {i}: {cluster}")

