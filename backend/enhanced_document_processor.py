import fitz  # PyMuPDF
from typing import List, Dict, Any, Optional, Tuple
from langchain_text_splitters import RecursiveCharacterTextSplitter, SentenceTransformersTokenTextSplitter
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_core.documents import Document
import os
import logging
import re
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize

# Fix for backend restart issue: Download NLTK data only once and conditionally
def ensure_nltk_data():
    """Ensure NLTK punkt data is available without repeated downloads"""
    try:
        # Check if punkt data is already available
        nltk.data.find('tokenizers/punkt')
        logging.getLogger(__name__).info("NLTK punkt data already available")
    except LookupError:
        logging.getLogger(__name__).info("Downloading NLTK punkt data (one-time setup)")
        try:
            nltk.download('punkt', quiet=True)
            logging.getLogger(__name__).info("NLTK punkt data downloaded successfully")
        except Exception as e:
            logging.getLogger(__name__).error(f"Failed to download NLTK punkt data: {e}")
            # Continue without punkt if download fails
            pass

# Initialize NLTK data once
ensure_nltk_data()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedDocumentProcessor:
    """Enhanced document processor with sentence-based chunking and section detection"""
    
    def __init__(self, 
                 chunk_size: int = 1000, 
                 chunk_overlap: int = 200,
                 sentence_chunk_size: int = 5,
                 use_sentence_chunking: bool = True):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.sentence_chunk_size = sentence_chunk_size
        self.use_sentence_chunking = use_sentence_chunking
        
        # Initialize text splitters
        self.char_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        # Section header patterns for medical papers
        self.section_patterns = [
            r'^(abstract|introduction|methods?|methodology|results?|discussion|conclusion|references?|acknowledgments?)\s*$',
            r'^(background|objectives?|materials?\s+and\s+methods?|findings?|limitations?|implications?)\s*$',
            r'^\d+\.?\s+\w+',  # Numbered sections
            r'^[A-Z][A-Z\s]+$'  # All caps headers
        ]
        
    def extract_sections(self, text: str) -> Dict[str, str]:
        """Extract sections from the document based on headers"""
        sections = {}
        current_section = "Introduction"
        current_content = []
        
        lines = text.split('\n')
        
        for line in lines:
            line_stripped = line.strip()
            
            # Check if line matches any section pattern
            is_header = False
            for pattern in self.section_patterns:
                if re.match(pattern, line_stripped, re.IGNORECASE):
                    # Save previous section
                    if current_content:
                        sections[current_section] = '\n'.join(current_content)
                    
                    # Start new section
                    current_section = line_stripped
                    current_content = []
                    is_header = True
                    break
            
            if not is_header and line_stripped:
                current_content.append(line)
        
        # Save last section
        if current_content:
            sections[current_section] = '\n'.join(current_content)
        
        return sections
    
    def sentence_based_chunking(self, text: str, metadata: Dict[str, Any]) -> List[Document]:
        """Create chunks based on sentence boundaries with overlap"""
        sentences = sent_tokenize(text)
        chunks = []
        
        for i in range(0, len(sentences), self.sentence_chunk_size):
            # Get sentences for this chunk with overlap
            chunk_sentences = sentences[i:i + self.sentence_chunk_size + 2]
            chunk_text = ' '.join(chunk_sentences)
            
            # Calculate chunk metadata
            chunk_metadata = metadata.copy()
            chunk_metadata.update({
                'chunk_index': i // self.sentence_chunk_size,
                'sentence_start': i,
                'sentence_end': min(i + self.sentence_chunk_size, len(sentences)),
                'chunking_method': 'sentence_based'
            })
            
            chunks.append(Document(
                page_content=chunk_text,
                metadata=chunk_metadata
            ))
        
        return chunks
    
    def process_pdf_enhanced(self, pdf_path: str) -> Tuple[List[Document], Dict[str, Any]]:
        """
        Process PDF with enhanced chunking and section detection
        Returns: (chunks, document_info)
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        try:
            # Load PDF
            loader = PyMuPDFLoader(pdf_path)
            pages = loader.load()
            
            if not pages:
                return [], {}
            
            # Extract full text
            full_text = '\n'.join([page.page_content for page in pages])
            
            # Extract sections
            sections = self.extract_sections(full_text)
            
            # Extract metadata
            metadata = self.extract_metadata(pdf_path)
            metadata['sections'] = list(sections.keys())
            
            # Process chunks
            all_chunks = []
            
            if self.use_sentence_chunking:
                # Process each section with sentence-based chunking
                for section_name, section_text in sections.items():
                    section_metadata = metadata.copy()
                    section_metadata['section'] = section_name
                    
                    section_chunks = self.sentence_based_chunking(
                        section_text, 
                        section_metadata
                    )
                    all_chunks.extend(section_chunks)
            else:
                # Use character-based chunking
                for idx, page in enumerate(pages):
                    page_metadata = metadata.copy()
                    page_metadata.update({
                        'page': idx,
                        'chunking_method': 'character_based'
                    })
                    
                    page_chunks = self.char_splitter.split_text(page.page_content)
                    for chunk_idx, chunk in enumerate(page_chunks):
                        chunk_metadata = page_metadata.copy()
                        chunk_metadata['chunk_index'] = chunk_idx
                        
                        all_chunks.append(Document(
                            page_content=chunk,
                            metadata=chunk_metadata
                        ))
            
            # Add filename to all chunks
            for chunk in all_chunks:
                chunk.metadata['filename'] = os.path.basename(pdf_path)
            
            document_info = {
                'total_chunks': len(all_chunks),
                'sections': sections,
                'metadata': metadata,
                'chunking_method': 'sentence_based' if self.use_sentence_chunking else 'character_based'
            }
            
            return all_chunks, document_info
            
        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path}: {e}")
            raise
    
    def extract_metadata(self, pdf_path: str) -> Dict[str, Any]:
        """Extract enhanced metadata from PDF"""
        try:
            doc = fitz.open(pdf_path)
            metadata = doc.metadata
            
            # Extract additional information
            result = {
                "title": metadata.get("title", ""),
                "author": metadata.get("author", ""),
                "subject": metadata.get("subject", ""),
                "keywords": metadata.get("keywords", ""),
                "page_count": len(doc),
                "creation_date": metadata.get("creationDate", ""),
            }
            
            # Try to extract DOI and publication info
            first_page_text = doc[0].get_text() if len(doc) > 0 else ""
            
            # DOI pattern
            doi_pattern = r'(10\.\d{4,}/[-._;()/:\w]+)'
            doi_match = re.search(doi_pattern, first_page_text)
            if doi_match:
                result['doi'] = doi_match.group(1)
            
            # Journal pattern (simplified)
            journal_patterns = [
                r'(?:Journal of |J\. )([A-Za-z\s]+)',
                r'(?:Proceedings of |Proc\. )([A-Za-z\s]+)',
                r'([A-Za-z\s]+ Medicine)',
                r'([A-Za-z\s]+ Research)'
            ]
            
            for pattern in journal_patterns:
                match = re.search(pattern, first_page_text, re.IGNORECASE)
                if match:
                    result['journal'] = match.group(1).strip()
                    break
            
            doc.close()
            return result
            
        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
            return {}
    
    def find_citations(self, chunk_text: str, source_text: str) -> List[Dict[str, Any]]:
        """Find exact citations for a chunk within the source text"""
        citations = []
        
        # Clean texts for comparison
        chunk_clean = chunk_text.strip().lower()
        source_clean = source_text.lower()
        
        # Find chunk position in source
        position = source_clean.find(chunk_clean[:50])  # Use first 50 chars to locate
        
        if position != -1:
            # Find section
            lines_before = source_text[:position].split('\n')
            section = "Unknown"
            
            # Look backwards for section header
            for line in reversed(lines_before[-10:]):  # Check last 10 lines
                for pattern in self.section_patterns:
                    if re.match(pattern, line.strip(), re.IGNORECASE):
                        section = line.strip()
                        break
            
            # Calculate approximate page (assuming ~3000 chars per page)
            page_num = position // 3000 + 1
            
            citations.append({
                'section': section,
                'page': page_num,
                'position': position,
                'preview': source_text[max(0, position-50):position+200]
            })
        
        return citations 