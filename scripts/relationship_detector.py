"""
Enhanced Relationship Detection for LibraryRAG Pipeline
Detects explicit and implicit relationships between documents
"""

import re
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict
from dataclasses import dataclass, asdict


@dataclass
class Relationship:
    """Represents a relationship between two documents"""
    source_path: str
    target_path: str
    relationship_type: str
    confidence: float  # 0.0 to 1.0
    context: Dict[str, any]
    
    def to_dict(self) -> Dict:
        return asdict(self)


class EnhancedRelationshipDetector:
    """
    Detects multiple types of relationships:
    1. Explicit markdown links
    2. Card references (FACES-001, FLOW-042, etc.)
    3. Building block connections
    4. Folder-based relationships
    5. Naming pattern relationships
    6. Hierarchical relationships
    """
    
    def __init__(self):
        # Card reference patterns for different decks
        self.card_patterns = {
            'FACES': [
                r'\bFACES[-\s](\d{1,3})\b',  # FACES-001, FACES 42
                r'\bFACES\s+(?:card|Card)?\s*#?(\d{1,3})\b',  # FACES card 42
                r'\b(?:open-minded|givers|takers|stormy|calculated|lost|knowing)[-\s](\d{1,2})\b'  # series-based
            ],
            'FLOW': [
                r'\bFLOW[-\s](\d{1,2})\b',
                r'\bFLOW\s+(?:card|Card)?\s*#?(\d{1,2})\b',
                r'\b(?:dream|in-between|conflict|belonging|presence)[-\s]series\b'
            ],
            'TCG': [
                r'\bTCG[-\s](\d{1,2})\b',
                r'\bThe\s+Coaching\s+Game\s+#?(\d{1,2})\b',
                r'\b(?:solutions|learning|everything-is-possible|should-be|choice|calling|just-be|pause|devotion|leadership|point-of-view|intimacy|balance|success)\b'
            ],
            'SPEAK': [
                r'\bSPEAK\s*UP[-\s](\d{1,3})\b',
                r'\bSPEAK\s+(?:card|Card)?\s*#?(\d{1,3})\b'
            ],
            'PUNCTUM': [
                r'\bPUNCTUM[-\s](\d{1,2})\b',
                r'\bPUNCTUM\s+(?:card|Card)?\s*#?(\d{1,2})\b'
            ]
        }
        
        # Building block keywords
        self.building_block_keywords = {
            'stories': ['story', 'tale', 'narrative', 'anecdote'],
            'quotes': ['quote', 'quotation', 'saying', 'wisdom'],
            'questions': ['question', 'reflection question', 'inquiry'],
            'applications': ['application', 'training', 'exercise', 'activity'],
            'techniques': ['technique', 'method', 'approach', 'process'],
            'templates': ['template', 'framework', 'structure', 'format']
        }
        
        # Series names for FACES, FLOW, TCG
        self.series_names = {
            'FACES': ['open-minded', 'givers', 'takers', 'stormy', 'calculated', 'lost', 'knowing'],
            'FLOW': ['dream', 'in-between', 'conflict', 'belonging', 'presence'],
            'TCG': ['solutions', 'learning', 'everything-is-possible', 'should-be', 'choice', 
                    'calling', 'just-be', 'pause', 'devotion', 'leadership', 'point-of-view', 
                    'intimacy', 'balance', 'success']
        }
        
        # Cache for file path lookups
        self.file_index: Dict[str, str] = {}
        self.card_index: Dict[Tuple[str, int], str] = {}  # (deck, number) -> file_path
    
    def build_file_index(self, all_files: List[Dict]):
        """
        Build index of all files for fast lookup
        
        Args:
            all_files: List of file metadata from Stage 1
        """
        self.file_index.clear()
        self.card_index.clear()
        
        for file_info in all_files:
            file_path = file_info['file_path']
            file_name = file_info['file_name']
            
            # Index by filename
            self.file_index[file_name] = file_path
            
            # Index by path segments
            path_parts = Path(file_path).parts
            for i in range(len(path_parts)):
                key = '/'.join(path_parts[i:])
                self.file_index[key] = file_path
            
            # Index cards
            self._index_card_file(file_path, file_info)
    
    def _index_card_file(self, file_path: str, file_info: Dict):
        """Index card files for quick lookup"""
        path = Path(file_path)
        category = file_info.get('category', '')
        subcategory = file_info.get('subcategory', '')
        
        # Check if this is a card-related file
        if subcategory in ['FACES', 'FLOW', 'TCG', 'SPEAK', 'PUNCTUM']:
            # Try to extract card number from filename or path
            filename = path.stem
            
            # Pattern: 01-name.md, 02-name.md
            match = re.match(r'^(\d{1,2})-', filename)
            if match:
                card_num = int(match.group(1))
                self.card_index[(subcategory, card_num)] = file_path
            
            # For series-based (FACES, TCG)
            for series_list in self.series_names.get(subcategory, []):
                if series_list in str(path):
                    # This is a series file
                    pass
    
    def detect_all_relationships(self, content: str, file_path: str, 
                                 file_metadata: Dict, all_files: List[Dict]) -> List[Relationship]:
        """
        Detect all types of relationships for a file
        
        Args:
            content: File content
            file_path: Path to current file
            file_metadata: Metadata for current file
            all_files: All files in the dataset (for context)
            
        Returns:
            List of detected relationships
        """
        relationships = []
        
        # 1. Explicit markdown links
        relationships.extend(self._detect_markdown_links(content, file_path))
        
        # 2. Card references
        relationships.extend(self._detect_card_references(content, file_path, file_metadata))
        
        # 3. Building block connections
        relationships.extend(self._detect_building_blocks(content, file_path, file_metadata))
        
        # 4. Folder-based relationships
        relationships.extend(self._detect_folder_relationships(file_path, file_metadata, all_files))
        
        # 5. Naming pattern relationships
        relationships.extend(self._detect_naming_patterns(file_path, file_metadata, all_files))
        
        # 6. Hierarchical relationships
        relationships.extend(self._detect_hierarchical_relationships(file_path, file_metadata))
        
        # 7. Series relationships
        relationships.extend(self._detect_series_relationships(file_path, file_metadata, all_files))
        
        # 8. Cross-reference keywords
        relationships.extend(self._detect_keyword_references(content, file_path, file_metadata))
        
        # Deduplicate relationships
        unique_relationships = self._deduplicate_relationships(relationships)
        
        return unique_relationships
    
    def _detect_markdown_links(self, content: str, file_path: str) -> List[Relationship]:
        """Detect explicit markdown links [text](path)"""
        relationships = []
        
        # Pattern: [text](path)
        link_pattern = r'\[([^\]]+)\]\(([^\)]+)\)'
        matches = re.findall(link_pattern, content)
        
        for link_text, link_path in matches:
            # Skip external URLs
            if link_path.startswith(('http://', 'https://', '#')):
                continue
            
            # Resolve relative path
            target_path = self._resolve_path(file_path, link_path)
            
            if target_path:
                relationships.append(Relationship(
                    source_path=file_path,
                    target_path=target_path,
                    relationship_type='markdown_link',
                    confidence=1.0,  # Explicit link
                    context={
                        'link_text': link_text,
                        'link_path': link_path
                    }
                ))
        
        return relationships
    
    def _detect_card_references(self, content: str, file_path: str, 
                                 file_metadata: Dict) -> List[Relationship]:
        """Detect card references like FACES-001, FLOW-042"""
        relationships = []
        
        for deck, patterns in self.card_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                
                for match in matches:
                    # Extract card number if present
                    if match.groups():
                        card_num = int(match.group(1))
                    else:
                        # Series or concept reference
                        card_num = None
                    
                    # Look up card file
                    if card_num and (deck, card_num) in self.card_index:
                        target_path = self.card_index[(deck, card_num)]
                        
                        relationships.append(Relationship(
                            source_path=file_path,
                            target_path=target_path,
                            relationship_type='card_reference',
                            confidence=0.9,
                            context={
                                'deck': deck,
                                'card_number': card_num,
                                'reference_text': match.group(0)
                            }
                        ))
                    elif not card_num:
                        # Series or concept reference - find related files
                        concept = match.group(0).lower()
                        related_files = self._find_files_by_concept(deck, concept)
                        
                        for related_file in related_files:
                            relationships.append(Relationship(
                                source_path=file_path,
                                target_path=related_file,
                                relationship_type='concept_reference',
                                confidence=0.7,
                                context={
                                    'deck': deck,
                                    'concept': concept,
                                    'reference_text': match.group(0)
                                }
                            ))
        
        return relationships
    
    def _detect_building_blocks(self, content: str, file_path: str, 
                                 file_metadata: Dict) -> List[Relationship]:
        """Detect building block connections (stories, quotes, questions, etc.)"""
        relationships = []
        
        path = Path(file_path)
        parent_dir = path.parent
        
        for block_type, keywords in self.building_block_keywords.items():
            # Check if content references this building block type
            for keyword in keywords:
                pattern = r'\b' + re.escape(keyword) + r's?\b'
                if re.search(pattern, content, re.IGNORECASE):
                    # Look for related building block files in same directory
                    block_file = parent_dir / f"{block_type}.md"
                    
                    if block_file.exists() and str(block_file) != file_path:
                        relationships.append(Relationship(
                            source_path=file_path,
                            target_path=str(block_file),
                            relationship_type='building_block_reference',
                            confidence=0.8,
                            context={
                                'block_type': block_type,
                                'keyword': keyword
                            }
                        ))
                    
                    # Also check for naming variations
                    for variation in [f"{block_type}-tales", f"key-{block_type}", 
                                     f"training-{block_type}", f"{block_type}-guide"]:
                        var_file = parent_dir / f"{variation}.md"
                        if var_file.exists() and str(var_file) != file_path:
                            relationships.append(Relationship(
                                source_path=file_path,
                                target_path=str(var_file),
                                relationship_type='building_block_variation',
                                confidence=0.7,
                                context={
                                    'block_type': block_type,
                                    'variation': variation
                                }
                            ))
        
        return relationships
    
    def _detect_folder_relationships(self, file_path: str, file_metadata: Dict, 
                                     all_files: List[Dict]) -> List[Relationship]:
        """Detect implicit relationships based on folder structure"""
        relationships = []
        
        path = Path(file_path)
        parent_dir = path.parent
        
        # Find sibling files (same folder)
        siblings = [
            f['file_path'] for f in all_files 
            if Path(f['file_path']).parent == parent_dir 
            and f['file_path'] != file_path
        ]
        
        for sibling in siblings:
            # Sibling relationship (implicit)
            relationships.append(Relationship(
                source_path=file_path,
                target_path=sibling,
                relationship_type='sibling',
                confidence=0.6,
                context={
                    'folder': str(parent_dir),
                    'relationship': 'same_folder'
                }
            ))
        
        # Find cousin files (same grandparent, different parent)
        if len(path.parts) >= 3:
            grandparent = path.parents[1]
            
            cousins = [
                f['file_path'] for f in all_files
                if len(Path(f['file_path']).parts) >= 3
                and Path(f['file_path']).parents[1] == grandparent
                and Path(f['file_path']).parent != parent_dir
                and f['file_path'] != file_path
            ]
            
            for cousin in cousins[:10]:  # Limit to prevent explosion
                relationships.append(Relationship(
                    source_path=file_path,
                    target_path=cousin,
                    relationship_type='cousin',
                    confidence=0.4,
                    context={
                        'grandparent': str(grandparent),
                        'relationship': 'related_folder'
                    }
                ))
        
        return relationships
    
    def _detect_naming_patterns(self, file_path: str, file_metadata: Dict, 
                                 all_files: List[Dict]) -> List[Relationship]:
        """Detect relationships based on file naming patterns"""
        relationships = []
        
        path = Path(file_path)
        filename = path.stem
        
        # Pattern 1: Numbered files (01-name, 02-name)
        match = re.match(r'^(\d{1,2})-(.+)$', filename)
        if match:
            num, base_name = match.groups()
            num = int(num)
            
            # Look for previous/next in sequence
            for offset in [-1, 1]:
                target_num = num + offset
                target_name = f"{target_num:02d}-{base_name}.md"
                target_path = path.parent / target_name
                
                if target_path.exists():
                    relationships.append(Relationship(
                        source_path=file_path,
                        target_path=str(target_path),
                        relationship_type='sequence',
                        confidence=0.9,
                        context={
                            'sequence_position': num,
                            'direction': 'next' if offset > 0 else 'previous'
                        }
                    ))
        
        # Pattern 2: Same base name, different suffixes
        # Example: activity.md, activity-guide.md, activity-template.md
        base_pattern = re.sub(r'[-_](guide|template|example|full|summary|index)$', '', filename)
        
        for file_info in all_files:
            other_path = Path(file_info['file_path'])
            other_filename = other_path.stem
            
            if other_path.parent == path.parent and other_filename != filename:
                other_base = re.sub(r'[-_](guide|template|example|full|summary|index)$', '', other_filename)
                
                if base_pattern == other_base:
                    relationships.append(Relationship(
                        source_path=file_path,
                        target_path=file_info['file_path'],
                        relationship_type='name_variant',
                        confidence=0.8,
                        context={
                            'base_name': base_pattern,
                            'variant': other_filename
                        }
                    ))
        
        return relationships
    
    def _detect_hierarchical_relationships(self, file_path: str, 
                                           file_metadata: Dict) -> List[Relationship]:
        """Detect parent-child hierarchical relationships"""
        relationships = []
        
        path = Path(file_path)
        
        # Look for README or index files in parent directories
        for parent in path.parents:
            for index_name in ['README.md', 'index.md', 'MASTER-INDEX.md', 
                              'INDEX.md', '_index.md']:
                index_path = parent / index_name
                
                if index_path.exists() and str(index_path) != file_path:
                    relationships.append(Relationship(
                        source_path=file_path,
                        target_path=str(index_path),
                        relationship_type='child_of_index',
                        confidence=0.85,
                        context={
                            'index_file': index_name,
                            'level': len(path.relative_to(parent).parts)
                        }
                    ))
                    break  # Only one index per level
        
        # If this IS an index file, note it
        if path.name in ['README.md', 'MASTER-INDEX.md', 'INDEX.md']:
            # Find direct children
            if path.parent.exists():
                for child in path.parent.iterdir():
                    if child.is_file() and child.suffix == '.md' and child.name != path.name:
                        relationships.append(Relationship(
                            source_path=file_path,
                            target_path=str(child),
                            relationship_type='parent_of',
                            confidence=0.85,
                            context={
                                'relationship': 'index_to_child'
                            }
                        ))
        
        return relationships
    
    def _detect_series_relationships(self, file_path: str, file_metadata: Dict, 
                                     all_files: List[Dict]) -> List[Relationship]:
        """Detect relationships within card series (FACES, FLOW, TCG)"""
        relationships = []
        
        path = Path(file_path)
        subcategory = file_metadata.get('subcategory', '')
        
        # Check if file is in a series
        if subcategory in self.series_names:
            for series in self.series_names[subcategory]:
                if series in str(path).lower():
                    # This file is part of a series
                    # Find other files in same series
                    for file_info in all_files:
                        other_path = file_info['file_path']
                        if series in other_path.lower() and other_path != file_path:
                            relationships.append(Relationship(
                                source_path=file_path,
                                target_path=other_path,
                                relationship_type='same_series',
                                confidence=0.75,
                                context={
                                    'deck': subcategory,
                                    'series': series
                                }
                            ))
        
        return relationships
    
    def _detect_keyword_references(self, content: str, file_path: str, 
                                    file_metadata: Dict) -> List[Relationship]:
        """Detect references based on keywords and concepts"""
        relationships = []
        
        # Extract key concepts from content
        concepts = self._extract_concepts(content)
        
        # Match against file index
        for concept in concepts:
            # Look for files with matching concept in path or name
            for indexed_file in self.file_index.values():
                if concept.lower() in indexed_file.lower() and indexed_file != file_path:
                    relationships.append(Relationship(
                        source_path=file_path,
                        target_path=indexed_file,
                        relationship_type='keyword_match',
                        confidence=0.5,
                        context={
                            'keyword': concept
                        }
                    ))
        
        return relationships
    
    def _extract_concepts(self, content: str) -> Set[str]:
        """Extract key concepts from content"""
        concepts = set()
        
        # Extract words from headers
        header_pattern = r'^#{1,6}\s+(.+)$'
        for match in re.finditer(header_pattern, content, re.MULTILINE):
            header_text = match.group(1)
            # Extract meaningful words (3+ chars)
            words = re.findall(r'\b[a-zA-Z]{3,}\b', header_text)
            concepts.update(word.lower() for word in words if len(word) > 3)
        
        # Limit to top concepts
        return concepts
    
    def _resolve_path(self, source_path: str, link_path: str) -> Optional[str]:
        """Resolve relative path to absolute path"""
        source = Path(source_path)
        
        # Try direct lookup in index
        if link_path in self.file_index:
            return self.file_index[link_path]
        
        # Try relative resolution
        try:
            if link_path.startswith('/'):
                # Absolute from root
                resolved = Path(link_path.lstrip('/'))
            else:
                # Relative to source file
                resolved = (source.parent / link_path).resolve()
            
            resolved_str = str(resolved)
            if resolved_str in self.file_index.values():
                return resolved_str
            
            # Try with .md extension
            if not resolved_str.endswith('.md'):
                with_md = resolved_str + '.md'
                if with_md in self.file_index.values():
                    return with_md
        
        except:
            pass
        
        return None
    
    def _find_files_by_concept(self, deck: str, concept: str) -> List[str]:
        """Find files related to a concept"""
        matches = []
        
        for file_path in self.file_index.values():
            if deck in file_path and concept.lower() in file_path.lower():
                matches.append(file_path)
        
        return matches[:5]  # Limit results
    
    def _deduplicate_relationships(self, relationships: List[Relationship]) -> List[Relationship]:
        """Remove duplicate relationships, keeping highest confidence"""
        seen = {}
        
        for rel in relationships:
            key = (rel.source_path, rel.target_path, rel.relationship_type)
            
            if key not in seen or rel.confidence > seen[key].confidence:
                seen[key] = rel
        
        return list(seen.values())
    
    def get_relationship_summary(self, relationships: List[Relationship]) -> Dict:
        """Generate summary statistics for relationships"""
        by_type = defaultdict(int)
        by_confidence = {'high': 0, 'medium': 0, 'low': 0}
        
        for rel in relationships:
            by_type[rel.relationship_type] += 1
            
            if rel.confidence >= 0.8:
                by_confidence['high'] += 1
            elif rel.confidence >= 0.6:
                by_confidence['medium'] += 1
            else:
                by_confidence['low'] += 1
        
        return {
            'total': len(relationships),
            'by_type': dict(by_type),
            'by_confidence': by_confidence,
            'unique_targets': len(set(r.target_path for r in relationships))
        }


if __name__ == "__main__":
    """
    Test enhanced relationship detection
    """
    
    # Sample test data
    sample_files = [
        {
            'file_path': 'LibraryRAG/Activities/FACES/open-minded/README.md',
            'file_name': 'README.md',
            'category': 'Activities',
            'subcategory': 'FACES'
        },
        {
            'file_path': 'LibraryRAG/Activities/FACES/open-minded/stories-tales.md',
            'file_name': 'stories-tales.md',
            'category': 'Activities',
            'subcategory': 'FACES'
        },
        {
            'file_path': 'LibraryRAG/Activities/FACES/01-open-minded.md',
            'file_name': '01-open-minded.md',
            'category': 'Activities',
            'subcategory': 'FACES'
        }
    ]
    
    sample_content = """
    # Open-Minded Series
    
    This series uses FACES-001 through FACES-020 cards.
    
    See also [stories](stories-tales.md) and [reflection questions](reflection-questions.md).
    
    Related to the FLOW dream-series and TCG solutions concept.
    """
    
    detector = EnhancedRelationshipDetector()
    detector.build_file_index(sample_files)
    
    relationships = detector.detect_all_relationships(
        content=sample_content,
        file_path='LibraryRAG/Activities/FACES/open-minded/README.md',
        file_metadata=sample_files[0],
        all_files=sample_files
    )
    
    print(f"Found {len(relationships)} relationships:")
    for rel in relationships:
        print(f"  - {rel.relationship_type}: {Path(rel.target_path).name} (confidence: {rel.confidence:.2f})")
    
    summary = detector.get_relationship_summary(relationships)
    print(f"\nSummary: {summary}")

