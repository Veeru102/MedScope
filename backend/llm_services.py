from typing import List, Dict, Any, Optional
import os
from openai import AsyncOpenAI
from dotenv import load_dotenv
import logging
import asyncio
from functools import wraps
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

def rate_limit(calls_per_minute=30):
    """Rate limiting decorator"""
    def decorator(func):
        last_called = [0.0]
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            time_between_calls = 60.0 / calls_per_minute
            
            if elapsed < time_between_calls:
                sleep_time = time_between_calls - elapsed
                await asyncio.sleep(sleep_time)
            
            last_called[0] = time.time()
            return await func(*args, **kwargs)
        return wrapper
    return decorator

class LLMService:
    """Modular LLM service for various text processing tasks"""
    
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        
        self.client = AsyncOpenAI(api_key=api_key)
        
        # Audience-specific prompt templates
        self.audience_prompts = {
            "patient": {
                "system": "You are a medical communication specialist who explains complex medical research to patients in simple, clear terms. Avoid jargon and use everyday language.",
                "style": "Use simple language, analogies, and focus on practical implications for patient care and quality of life."
            },
            "clinician": {
                "system": "You are a medical research analyst communicating with healthcare professionals. Use appropriate medical terminology while remaining concise.",
                "style": "Focus on clinical relevance, treatment implications, and evidence quality. Include relevant statistics and clinical endpoints."
            },
            "researcher": {
                "system": "You are a scientific peer reviewer providing detailed analysis for research colleagues.",
                "style": "Provide in-depth methodological critique, statistical analysis, and implications for future research. Use technical terminology freely."
            }
        }
    
    @rate_limit(calls_per_minute=30)
    async def generate_summary(self, 
                             text: str, 
                             audience: str = "clinician",
                             sections: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Generate audience-specific summary"""
        
        audience_config = self.audience_prompts.get(audience, self.audience_prompts["clinician"])
        
        # Build section-aware prompt if sections provided
        if sections:
            section_summaries = []
            for section_name, section_text in sections.items():
                if section_text.strip():
                    section_summaries.append(f"**{section_name}**:\n{section_text[:1000]}...")
            
            structured_text = "\n\n".join(section_summaries)
        else:
            structured_text = text[:12000]  # Limit text length
        
        prompt = f"""Summarize this medical research paper for a {audience}. {audience_config['style']}

Structure your summary with these sections:
- **Summary of the Paper**: Brief overview
- **Key Objectives**: Main research goals
- **Methodology**: How the study was conducted
- **Major Findings**: Key results and outcomes
- **Limitations**: Study limitations and caveats

Paper content:
{structured_text}"""

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": audience_config["system"]},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            return {
                "summary": response.choices[0].message.content,
                "audience": audience,
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error generating summary for {audience}: {e}")
            return {
                "summary": "Error generating summary",
                "audience": audience,
                "status": "error",
                "error": str(e)
            }
    
    @rate_limit(calls_per_minute=30)
    async def explain_text(self, 
                          selected_text: str, 
                          context: str,
                          user_question: str,
                          audience: str = "patient") -> Dict[str, Any]:
        """Explain selected text based on user question"""
        
        audience_config = self.audience_prompts.get(audience, self.audience_prompts["patient"])
        
        prompt = f"""A {audience} has highlighted the following text from a medical paper and asks: "{user_question}"

Highlighted text: "{selected_text}"

Context around the highlight:
{context}

Please provide a clear explanation that addresses their question. {audience_config['style']}"""

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": audience_config["system"]},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5
            )
            
            return {
                "explanation": response.choices[0].message.content,
                "highlighted_text": selected_text,
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error explaining text: {e}")
            return {
                "explanation": "Error generating explanation",
                "status": "error",
                "error": str(e)
            }
    
    @rate_limit(calls_per_minute=20)
    async def synthesize_papers(self, 
                               papers_data: List[Dict[str, Any]], 
                               synthesis_type: str = "comparison") -> Dict[str, Any]:
        """Synthesize findings across multiple papers"""
        
        synthesis_prompts = {
            "comparison": "Compare and contrast the methodologies and findings across these papers.",
            "evolution": "Analyze how the research has evolved over time based on publication dates.",
            "consensus": "Identify areas of consensus and disagreement across these studies.",
            "methods": "Create a unified summary of the different methodological approaches used."
        }
        
        # Build paper summaries
        paper_summaries = []
        for paper in papers_data:
            summary = f"""
Paper: {paper.get('title', 'Untitled')}
Year: {paper.get('year', 'Unknown')}
Key Findings: {paper.get('findings', 'Not provided')}
Methods: {paper.get('methods', 'Not provided')}
"""
            paper_summaries.append(summary)
        
        prompt = f"""{synthesis_prompts.get(synthesis_type, synthesis_prompts['comparison'])}

Papers to analyze:
{''.join(paper_summaries)}

Provide a comprehensive synthesis that would be valuable for researchers and clinicians."""

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a medical research synthesis expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4
            )
            
            return {
                "synthesis": response.choices[0].message.content,
                "type": synthesis_type,
                "paper_count": len(papers_data),
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error synthesizing papers: {e}")
            return {
                "synthesis": "Error generating synthesis",
                "status": "error",
                "error": str(e)
            }
    
    @rate_limit(calls_per_minute=30)
    async def answer_with_citations(self, 
                                  question: str, 
                                  relevant_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Answer question with proper citations to source chunks"""
        
        # Format chunks with indices
        formatted_chunks = []
        for idx, chunk in enumerate(relevant_chunks):
            formatted_chunks.append(
                f"[{idx+1}] Section: {chunk.get('metadata', {}).get('section', 'Unknown')}\n"
                f"Page: {chunk.get('metadata', {}).get('page', 'Unknown')}\n"
                f"Content: {chunk['content']}\n"
            )
        
        prompt = f"""Answer the following question based on the provided excerpts from a medical paper. 
Include citations in your answer using [1], [2], etc. to reference specific excerpts.

Question: {question}

Excerpts:
{''.join(formatted_chunks)}

Provide a comprehensive answer with proper citations."""

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a medical research assistant. Always cite your sources using the provided excerpt numbers."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            return {
                "answer": response.choices[0].message.content,
                "citations": [{"index": idx+1, "chunk": chunk} for idx, chunk in enumerate(relevant_chunks)],
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error generating answer with citations: {e}")
            return {
                "answer": "Error generating answer",
                "status": "error",
                "error": str(e)
            }
    
    @rate_limit(calls_per_minute=20)
    async def extract_key_topics(self, text: str) -> List[str]:
        """Extract key medical topics from text for clustering"""
        
        prompt = f"""Extract 3-5 key medical topics or research areas from this text. 
Return only the topics as a comma-separated list.

Text: {text[:2000]}"""

        try:
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a medical topic extraction specialist."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            topics = response.choices[0].message.content.split(',')
            return [topic.strip() for topic in topics]
            
        except Exception as e:
            logger.error(f"Error extracting topics: {e}")
            return [] 