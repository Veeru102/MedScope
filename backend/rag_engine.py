from typing import List, Dict, Any
import os
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.memory import ConversationBufferMemory
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
import openai
from openai import AsyncOpenAI
from dotenv import load_dotenv
import logging
import asyncio
import time
from functools import wraps

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

def rate_limit(calls_per_minute=50):
    """Rate limiting decorator"""
    def decorator(func):
        last_called = [0.0]
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Calculate time to wait
            elapsed = time.time() - last_called[0]
            time_between_calls = 60.0 / calls_per_minute
            
            if elapsed < time_between_calls:
                sleep_time = time_between_calls - elapsed
                logger.info(f"Rate limiting: waiting {sleep_time:.2f} seconds")
                await asyncio.sleep(sleep_time)
            
            last_called[0] = time.time()
            return await func(*args, **kwargs)
        return wrapper
    return decorator

async def retry_with_exponential_backoff(
    func,
    max_retries=3,
    initial_delay=1,
    backoff_factor=2,
    *args,
    **kwargs
):
    """Retry function with exponential backoff"""
    for attempt in range(max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            if attempt == max_retries:
                raise e
            
            # Check if it's a rate limit error
            if "429" in str(e) or "rate" in str(e).lower():
                delay = initial_delay * (backoff_factor ** attempt)
                logger.warning(f"Rate limit hit, retrying in {delay} seconds (attempt {attempt + 1}/{max_retries + 1})")
                await asyncio.sleep(delay)
            else:
                raise e

class RAGEngine:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
            
        # Initialize OpenAI client with minimal configuration
        self.openai_client = AsyncOpenAI(api_key=api_key)
        
        try:
            self.embeddings = OpenAIEmbeddings()
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI embeddings: {e}")
            raise
            
        self.vector_store = None
        self.qa_chain = None
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="answer"
        )
        # Define the path for the FAISS index file
        self.faiss_index_path = "faiss_index"

    def create_vector_store(self, chunks: List[str], metadata: Dict[str, Any] = None):
        """
        Create a FAISS vector store from document chunks
        """
        try:
            self.vector_store = FAISS.from_texts(
                chunks,
                self.embeddings,
                metadatas=[metadata] * len(chunks) if metadata else None
            )
            self.save_vector_store()
        except Exception as e:
            logger.error(f"Failed to create vector store: {e}")
            raise

    async def create_vector_store_from_documents_with_retry(self, documents: List[Document]):
        """
        Create a FAISS vector store from documents with rate limiting
        """
        if not documents:
            raise ValueError("Cannot create vector store from empty documents list.")

        try:
            # Add delay before creating vector store to avoid rate limits
            logger.info("Creating vector store with rate limiting...")
            await asyncio.sleep(1)  # Initial delay
            
            # Use retry logic for vector store creation
            self.vector_store = await retry_with_exponential_backoff(
                self._create_vector_store_async,
                3,  # max_retries
                1,  # initial_delay
                2,  # backoff_factor
                documents  # *args
            )
            self.save_vector_store()
            logger.info("Vector store created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create vector store from documents: {e}")
            raise

    async def _create_vector_store_async(self, documents: List[Document]):
        """Helper method to create vector store asynchronously"""
        # Process documents in smaller batches to avoid rate limits
        batch_size = 5
        if len(documents) > batch_size:
            logger.info(f"Processing {len(documents)} documents in batches of {batch_size}")
            
            # Create initial vector store with first batch
            first_batch = documents[:batch_size]
            vector_store = FAISS.from_documents(first_batch, self.embeddings)
            
            # Add remaining documents in batches with delays
            for i in range(batch_size, len(documents), batch_size):
                batch = documents[i:i + batch_size]
                logger.info(f"Processing batch {i//batch_size + 1}/{len(documents)//batch_size + 1}")
                
                # Add delay between batches
                await asyncio.sleep(2)
                
                batch_store = FAISS.from_documents(batch, self.embeddings)
                vector_store.merge_from(batch_store)
            
            return vector_store
        else:
            return FAISS.from_documents(documents, self.embeddings)

    def create_vector_store_from_documents(self, documents: List[Document]):
        """
        Create a FAISS vector store from a list of Langchain Document objects
        """
        # Run the async version in the event loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're already in an event loop, use create_task
                task = loop.create_task(self.create_vector_store_from_documents_with_retry(documents))
                # This is a bit tricky - we need to handle this case
                # For now, let's use the synchronous version but with delays
                logger.warning("Already in event loop, using synchronous method with delays")
                self._create_vector_store_sync_with_delays(documents)
            else:
                loop.run_until_complete(self.create_vector_store_from_documents_with_retry(documents))
        except RuntimeError:
            # No event loop, use synchronous version
            self._create_vector_store_sync_with_delays(documents)

    def _create_vector_store_sync_with_delays(self, documents: List[Document]):
        """Synchronous version with delays between API calls"""
        import time
        
        if not documents:
            raise ValueError("Cannot create vector store from empty documents list.")

        try:
            batch_size = 3  # Smaller batch size for sync version
            if len(documents) > batch_size:
                logger.info(f"Processing {len(documents)} documents in batches of {batch_size} with delays")
                
                # Create initial vector store with first batch
                first_batch = documents[:batch_size]
                self.vector_store = FAISS.from_documents(first_batch, self.embeddings)
                
                # Add remaining documents in batches with delays
                for i in range(batch_size, len(documents), batch_size):
                    batch = documents[i:i + batch_size]
                    logger.info(f"Processing batch {i//batch_size + 1}, waiting 3 seconds...")
                    
                    # Add delay between batches
                    time.sleep(3)
                    
                    batch_store = FAISS.from_documents(batch, self.embeddings)
                    self.vector_store.merge_from(batch_store)
            else:
                self.vector_store = FAISS.from_documents(documents, self.embeddings)
                
            self.save_vector_store()
            
        except Exception as e:
            logger.error(f"Failed to create vector store from documents: {e}")
            raise

    def save_vector_store(self):
        """
        Save the current FAISS vector store to disk.
        """
        if self.vector_store:
            try:
                self.vector_store.save_local(self.faiss_index_path)
                logger.info(f"FAISS index saved to {self.faiss_index_path}")
            except Exception as e:
                logger.error(f"Failed to save FAISS index: {e}")
                raise

    def load_vector_store(self):
        """
        Load the FAISS vector store from disk.
        """
        if os.path.exists(self.faiss_index_path):
            try:
                self.vector_store = FAISS.load_local(
                    self.faiss_index_path,
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
                logger.info(f"FAISS index loaded from {self.faiss_index_path}")
            except Exception as e:
                logger.error(f"Error loading FAISS index: {e}")
                self.vector_store = None
        else:
            logger.info("No existing FAISS index found.")
            self.vector_store = None

    def setup_qa_chain(self):
        """
        Set up the QA chain with the vector store
        """
        if not self.vector_store:
            self.load_vector_store()
            if not self.vector_store:
                return

        try:
            # Create the language model
            llm = ChatOpenAI(
                temperature=0.3,
                model="gpt-3.5-turbo"
            )

            # Create the prompt template
            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are a helpful medical research assistant. Use the following context to answer the question. If you don't know the answer, say so."),
                ("human", "Context: {context}\n\nQuestion: {input}")
            ])

            # Create the document processing chain
            question_answer_chain = create_stuff_documents_chain(llm, prompt)
            
            # Create the retrieval chain
            self.qa_chain = create_retrieval_chain(
                self.vector_store.as_retriever(),
                question_answer_chain
            )
            
            logger.info("QA chain setup complete")
                    
        except Exception as e:
            logger.error(f"Error setting up QA chain: {e}")
            raise

    async def query(self, question: str) -> Dict[str, Any]:
        """
        Query the RAG system with a question
        """
        if not self.qa_chain or self.qa_chain.retriever.vectorstore != self.vector_store:
            try:
                self.setup_qa_chain()
            except Exception as e:
                logger.error(f"Failed to setup QA chain during query: {e}")
                return {
                    "answer": "An error occurred while setting up the RAG system. Please try again.",
                    "sources": []
                }

        if not self.qa_chain:
            return {
                "answer": "The RAG system is not initialized. Please upload and process a document first.",
                "sources": []
            }

        try:
            result = await self.qa_chain.ainvoke({"input": question})
            return {
                "answer": result.get("answer", ""),
                "sources": [
                    {
                        "content": doc.page_content,
                        "metadata": doc.metadata
                    }
                    for doc in result.get("context", [])
                ]
            }
        except Exception as e:
            logger.error(f"Error in RAG query: {e}")
            raise

    @rate_limit(calls_per_minute=30)  # Conservative rate limiting
    async def _make_chat_completion(self, model_name: str, messages: List[Dict], temperature: float = 0.3):
        """Make a rate-limited chat completion request"""
        return await retry_with_exponential_backoff(
            self.openai_client.chat.completions.create,
            3,  # max_retries
            1,  # initial_delay
            2,  # backoff_factor
            model=model_name,
            messages=messages,
            temperature=temperature
        )

    async def summarize_paper(self, chunks: List[str]) -> Dict[str, Any]:
        """
        Generate a summary of the paper using GPT with rate limiting
        """
        if not chunks:
            return {
                "summary": "No content to summarize.",
                "status": "success"
            }

        try:
            full_text = "\n".join(chunks)
            
            max_prompt_length = 12000  # Reduced to be more conservative
            if len(full_text) > max_prompt_length:
                full_text = full_text[:max_prompt_length] + "\n... [Content truncated] ..."

            prompt = f"""You are a medical research assistant. Your task is to summarize the uploaded paper with emphasis on its:
- Key objectives
- Methodology
- Major findings
- Limitations

Paper content:
{full_text}
"""

            # Try different models with rate limiting
            models_to_try = ["gpt-4o-mini", "gpt-3.5-turbo", "gpt-4-turbo", "gpt-4"]
            
            response = None
            last_error = None
            
            for model_name in models_to_try:
                try:
                    logger.info(f"Attempting summarization with model: {model_name}")
                    
                    response = await self._make_chat_completion(
                        model_name=model_name,
                        messages=[
                            {"role": "system", "content": "You are a medical research assistant specializing in paper analysis and summarization."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.3
                    )
                    
                    logger.info(f"Successfully used model: {model_name}")
                    break
                    
                except Exception as e:
                    logger.warning(f"Failed to use model {model_name}: {e}")
                    last_error = e
                    
                    # Add extra delay if it's a rate limit error
                    if "429" in str(e):
                        logger.info("Rate limit detected, waiting extra time before next model...")
                        await asyncio.sleep(5)
                    
                    continue
            
            if response is None:
                raise Exception(f"All models failed. Last error: {last_error}")

            return {
                "summary": response.choices[0].message.content,
                "status": "success"
            }

        except Exception as e:
            logger.error(f"Error in paper summarization: {e}")
            return {
                "summary": "Error generating summary",
                "status": "error",
                "error": str(e)
            } 