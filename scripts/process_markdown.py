"""
Markdown Processing Script

Process pre-crawled markdown files from FireCrawl and store in database.

Supports:
- Individual markdown files (.md)
- Markdown with front matter (metadata)
- JSON exports from FireCrawl
- Bulk JSON arrays

Usage:
    python scripts/process_markdown.py
    python scripts/process_markdown.py --recursive
    python scripts/process_markdown.py --format json --input data/crawled/export.json
"""

import os
import json
import re
import argparse
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import hashlib

# Will be implemented with actual database later
# For now, this shows the structure


class MarkdownProcessor:
    """Process markdown files and prepare for vectorization"""
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 100):
        """
        Initialize processor
        
        Args:
            chunk_size: Number of words per chunk
            chunk_overlap: Number of overlapping words between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.processed_files = []
        self.errors = []
    
    def extract_front_matter(self, content: str) -> tuple[Dict, str]:
        """
        Extract YAML front matter from markdown
        
        Args:
            content: Markdown content
            
        Returns:
            Tuple of (metadata dict, content without front matter)
        """
        # Check for front matter (--- at start)
        if not content.startswith('---'):
            return {}, content
        
        # Find end of front matter
        parts = content.split('---', 2)
        if len(parts) < 3:
            return {}, content
        
        # Parse front matter (simple key: value parsing)
        metadata = {}
        front_matter = parts[1].strip()
        
        for line in front_matter.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                metadata[key.strip()] = value.strip()
        
        # Return metadata and content without front matter
        return metadata, parts[2].strip()
    
    def extract_metadata_from_filename(self, filepath: str) -> Dict:
        """
        Extract metadata from filename
        
        Examples:
            courses_ug_computing-science.md -> category: courses_ug
            study_undergraduate_entry-requirements.md -> category: study
        
        Args:
            filepath: Path to file
            
        Returns:
            Metadata dictionary
        """
        filename = Path(filepath).stem  # Get filename without extension
        metadata = {}
        
        # Try to extract category from filename
        parts = filename.split('_')
        if len(parts) >= 2:
            metadata['category'] = '_'.join(parts[:-1])
            metadata['slug'] = parts[-1]
        
        # Try to detect program type
        if 'ug' in filename.lower() or 'undergraduate' in filename.lower():
            metadata['program_type'] = 'undergraduate'
        elif 'pg' in filename.lower() or 'postgraduate' in filename.lower():
            metadata['program_type'] = 'postgraduate'
        
        return metadata
    
    def extract_title_from_content(self, content: str) -> Optional[str]:
        """
        Extract title from markdown content (first # heading)
        
        Args:
            content: Markdown content
            
        Returns:
            Title string or None
        """
        lines = content.split('\n')
        for line in lines:
            if line.startswith('# '):
                return line[2:].strip()
        return None
    
    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into overlapping chunks
        
        Args:
            text: Text to chunk
            
        Returns:
            List of text chunks
        """
        # Split into words
        words = text.split()
        
        if len(words) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(words):
            # Get chunk
            end = start + self.chunk_size
            chunk_words = words[start:end]
            chunk = ' '.join(chunk_words)
            chunks.append(chunk)
            
            # Move start position (with overlap)
            start += self.chunk_size - self.chunk_overlap
        
        return chunks
    
    def process_markdown_file(self, filepath: str) -> Dict:
        """
        Process a single markdown file
        
        Args:
            filepath: Path to markdown file
            
        Returns:
            Dictionary with processed data
        """
        try:
            # Read file
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract front matter metadata
            front_matter, clean_content = self.extract_front_matter(content)
            
            # Extract metadata from filename
            filename_metadata = self.extract_metadata_from_filename(filepath)
            
            # Combine metadata (front matter takes precedence)
            metadata = {**filename_metadata, **front_matter}
            
            # Extract title if not in metadata
            if 'title' not in metadata:
                title = self.extract_title_from_content(clean_content)
                if title:
                    metadata['title'] = title
            
            # Generate URL if not in metadata
            if 'url' not in metadata:
                # Try to construct from filename
                slug = Path(filepath).stem.replace('_', '/')
                metadata['url'] = f"https://www.stir.ac.uk/{slug}/"
            
            # Chunk the content
            chunks = self.chunk_text(clean_content)
            
            # Create document ID (hash of URL)
            doc_id = hashlib.md5(metadata.get('url', filepath).encode()).hexdigest()
            
            result = {
                'doc_id': doc_id,
                'filepath': filepath,
                'url': metadata.get('url'),
                'title': metadata.get('title', Path(filepath).stem),
                'category': metadata.get('category', 'other'),
                'program_type': metadata.get('program_type'),
                'metadata': metadata,
                'content': clean_content,
                'chunks': chunks,
                'chunk_count': len(chunks),
                'word_count': len(clean_content.split()),
                'processed_at': datetime.now().isoformat()
            }
            
            self.processed_files.append(result)
            return result
            
        except Exception as e:
            error = {
                'filepath': filepath,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            self.errors.append(error)
            print(f"❌ Error processing {filepath}: {e}")
            return None
    
    def process_json_file(self, filepath: str) -> List[Dict]:
        """
        Process JSON file (single object or array)
        
        Args:
            filepath: Path to JSON file
            
        Returns:
            List of processed documents
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle single object vs array
            if isinstance(data, dict):
                data = [data]
            
            results = []
            for item in data:
                # Extract data
                url = item.get('url', '')
                title = item.get('title', '')
                markdown = item.get('markdown', item.get('content', ''))
                metadata = item.get('metadata', {})
                
                # Chunk content
                chunks = self.chunk_text(markdown)
                
                # Create document ID
                doc_id = hashlib.md5(url.encode()).hexdigest()
                
                result = {
                    'doc_id': doc_id,
                    'filepath': filepath,
                    'url': url,
                    'title': title,
                    'category': metadata.get('category', 'other'),
                    'program_type': metadata.get('program_type'),
                    'metadata': metadata,
                    'content': markdown,
                    'chunks': chunks,
                    'chunk_count': len(chunks),
                    'word_count': len(markdown.split()),
                    'processed_at': datetime.now().isoformat()
                }
                
                results.append(result)
                self.processed_files.append(result)
            
            return results
            
        except Exception as e:
            error = {
                'filepath': filepath,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            self.errors.append(error)
            print(f"❌ Error processing {filepath}: {e}")
            return []
    
    def process_directory(self, directory: str, recursive: bool = False) -> List[Dict]:
        """
        Process all markdown/JSON files in directory
        
        Args:
            directory: Directory path
            recursive: Process subdirectories
            
        Returns:
            List of processed documents
        """
        results = []
        path = Path(directory)
        
        # Find all markdown and JSON files
        if recursive:
            md_files = list(path.rglob('*.md'))
            json_files = list(path.rglob('*.json'))
        else:
            md_files = list(path.glob('*.md'))
            json_files = list(path.glob('*.json'))
        
        total_files = len(md_files) + len(json_files)
        print(f"\n📂 Found {len(md_files)} markdown files and {len(json_files)} JSON files")
        print(f"🔄 Processing {total_files} files...\n")
        
        # Process markdown files
        for i, filepath in enumerate(md_files, 1):
            print(f"[{i}/{len(md_files)}] Processing {filepath.name}...", end=' ')
            result = self.process_markdown_file(str(filepath))
            if result:
                results.append(result)
                print(f"✅ ({result['chunk_count']} chunks)")
            else:
                print("❌")
        
        # Process JSON files
        for filepath in json_files:
            print(f"Processing {filepath.name}...", end=' ')
            json_results = self.process_json_file(str(filepath))
            results.extend(json_results)
            print(f"✅ ({len(json_results)} documents)")
        
        return results
    
    def generate_summary(self) -> Dict:
        """Generate processing summary"""
        from collections import defaultdict
        
        # Count by category
        category_counts = defaultdict(int)
        category_chunks = defaultdict(int)
        
        for doc in self.processed_files:
            category = doc.get('category', 'other')
            category_counts[category] += 1
            category_chunks[category] += doc['chunk_count']
        
        total_chunks = sum(doc['chunk_count'] for doc in self.processed_files)
        total_words = sum(doc['word_count'] for doc in self.processed_files)
        
        summary = {
            'total_files': len(self.processed_files),
            'total_chunks': total_chunks,
            'total_words': total_words,
            'total_errors': len(self.errors),
            'categories': dict(category_counts),
            'category_chunks': dict(category_chunks),
            'avg_chunks_per_file': total_chunks / len(self.processed_files) if self.processed_files else 0,
            'avg_words_per_file': total_words / len(self.processed_files) if self.processed_files else 0
        }
        
        return summary
    
    def save_processed_data(self, output_file: str):
        """
        Save processed data to JSON file
        
        Args:
            output_file: Output file path
        """
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            'processed_at': datetime.now().isoformat(),
            'summary': self.generate_summary(),
            'documents': self.processed_files,
            'errors': self.errors
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Saved processed data to {output_file}")


def print_summary(summary: Dict):
    """Print processing summary"""
    print("\n" + "="*70)
    print("📊 MARKDOWN PROCESSING SUMMARY")
    print("="*70)
    
    print(f"\n✅ Files processed: {summary['total_files']}")
    print(f"✅ Total chunks: {summary['total_chunks']}")
    print(f"✅ Total words: {summary['total_words']:,}")
    print(f"✅ Avg chunks/file: {summary['avg_chunks_per_file']:.1f}")
    print(f"✅ Avg words/file: {summary['avg_words_per_file']:.0f}")
    
    if summary['total_errors'] > 0:
        print(f"⚠️  Errors: {summary['total_errors']}")
    
    print("\n📋 BREAKDOWN BY CATEGORY:")
    print("-" * 70)
    
    for category in sorted(summary['categories'].keys()):
        file_count = summary['categories'][category]
        chunk_count = summary['category_chunks'][category]
        print(f"  {category:20s} | {file_count:4d} files | {chunk_count:5d} chunks")
    
    print("\n💡 NEXT STEPS:")
    print("-" * 70)
    print("  1. Review processed data in data/processed/")
    print("  2. Generate embeddings: python scripts/generate_embeddings.py")
    print("  3. Store in database: python scripts/store_in_db.py")
    print("  4. Test RAG agent: python scripts/test_rag.py")
    
    print("\n" + "="*70)


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(description='Process markdown files from FireCrawl')
    parser.add_argument(
        '--input',
        default='data/crawled',
        help='Input directory or file (default: data/crawled)'
    )
    parser.add_argument(
        '--output',
        default='data/processed/processed_data.json',
        help='Output file for processed data (default: data/processed/processed_data.json)'
    )
    parser.add_argument(
        '--format',
        choices=['auto', 'markdown', 'json'],
        default='auto',
        help='Input format (default: auto-detect)'
    )
    parser.add_argument(
        '--recursive',
        action='store_true',
        help='Process subdirectories recursively'
    )
    parser.add_argument(
        '--chunk-size',
        type=int,
        default=500,
        help='Chunk size in words (default: 500)'
    )
    parser.add_argument(
        '--chunk-overlap',
        type=int,
        default=100,
        help='Chunk overlap in words (default: 100)'
    )
    
    args = parser.parse_args()
    
    print("📄 Markdown Processing Tool")
    print("="*70)
    
    # Initialize processor
    processor = MarkdownProcessor(
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap
    )
    
    # Check if input exists
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"\n❌ Error: Input path not found: {args.input}")
        print("\n💡 Make sure to place your markdown files in data/crawled/")
        return
    
    # Process based on input type
    if input_path.is_file():
        # Single file
        if args.format == 'json' or input_path.suffix == '.json':
            processor.process_json_file(str(input_path))
        else:
            processor.process_markdown_file(str(input_path))
    else:
        # Directory
        processor.process_directory(str(input_path), recursive=args.recursive)
    
    # Generate and print summary
    summary = processor.generate_summary()
    print_summary(summary)
    
    # Save processed data
    processor.save_processed_data(args.output)
    
    # Save errors if any
    if processor.errors:
        error_file = Path(args.output).parent / 'errors.json'
        with open(error_file, 'w', encoding='utf-8') as f:
            json.dump(processor.errors, f, indent=2)
        print(f"\n⚠️  Saved {len(processor.errors)} errors to {error_file}")
    
    print("\n✨ Processing complete!")


if __name__ == "__main__":
    main()
