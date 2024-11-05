from typing import List, Dict, TypedDict, Optional, Any
import boto3
import os
from langchain_core.messages import HumanMessage, BaseMessage
from langgraph.graph import Graph, StateGraph
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_groq import ChatGroq
from langchain_nomic.embeddings import NomicEmbeddings
import fitz
from components.shared import StaticPage
import asyncio
from nicegui import ui
import logging
from concurrent.futures import ThreadPoolExecutor
import aiohttp
import functools
from pydantic import BaseModel, Field
from chromadb import HttpClient
import uuid
from config import config
import nomic
import logging.handlers
from pathlib import Path


class Document(BaseModel):
    text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    id: Optional[str] = None


class Models:
    def __init__(self):
        self.nomic = nomic.login(config.nomic_api_key)
        self.nomic_embeddings = NomicEmbeddings(
            model="nomic-embed-text-v1.5",
        )
        self.ollama_embeddings = OllamaEmbeddings(model="nomic-embed-text-v1.5")
        self.model_groq_ollama = ChatGroq(
            model="llama-3.2-3b-preview",
            temperature=0,
            api_key=config.groq_api_key,
        )
        self.model_ollama = ChatOllama(model="llama-3.2-3b-preview", temperature=0)


class AgenticState(TypedDict):
    messages: list[BaseMessage]
    context: list[str]
    response: str
    error: str | None


class AgenticRAG:
    _instances = {}  # Change from single instance to dictionary of instances

    def setup_logging(self):
        """Setup logging configuration"""
        # Create logs directory if it doesn't exist
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        # Configure logger
        self.logger = logging.getLogger("AgenticRAG")
        self.logger.setLevel(logging.INFO)

        # Remove existing handlers to avoid duplicates
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)

        # Create formatters
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        console_formatter = logging.Formatter("%(levelname)s - %(message)s")

        # File handler with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_dir / "agentic_rag.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(file_formatter)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(console_formatter)

        # Add handlers to logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

        self.logger.info("Logging setup completed")

    def __new__(cls, bucket_name: str, directory_key: str):
        # Create unique key for this instance
        instance_key = f"{bucket_name}:{directory_key}"

        # Create new instance if one doesn't exist for this path
        if instance_key not in cls._instances:
            cls._instances[instance_key] = super().__new__(cls)
            cls._instances[instance_key]._initialized = False
            # Initialize logging for new instance
            cls._instances[instance_key].setup_logging = cls.setup_logging.__get__(
                cls._instances[instance_key], cls
            )

        return cls._instances[instance_key]

    def __init__(self, bucket_name: str, directory_key: str):
        # Skip if this instance is already initialized
        if self._initialized:
            return

        # Setup logging first
        self.setup_logging()

        # Log initialization parameters
        self.logger.info(
            f"Initializing new AgenticRAG instance for bucket: {bucket_name}, directory: {directory_key}"
        )

        # Initialize basic attributes
        self.bucket_name = bucket_name
        self.directory_key = directory_key

        # Format collection name - use only the last part of the path
        self.logger.info(f"Formatting collection name from directory: {directory_key}")
        collection_name = directory_key.rstrip("/").split("/")[
            -1
        ]  # Get last part of path
        collection_name = "".join(
            c if c.isalnum() or c in "_-" else "" for c in collection_name
        )

        # Ensure minimum length
        if len(collection_name) < 3:
            self.logger.info("Collection name too short, padding...")
            collection_name = f"{collection_name}_{'_' * (3 - len(collection_name))}"

        self.logger.info(f"Final collection name: {collection_name}")
        self.collection_name = collection_name

        self.is_initialized = False
        self.initialization_task = None
        self.cached_documents = {}

        self.models = Models()

        # Initialize thread pool with limited workers
        self.thread_pool = ThreadPoolExecutor(max_workers=2)

        # Create S3 client with config
        self.s3 = boto3.client("s3")

        # Initialize language models and embeddings
        self.setup_language_models()

        # Create workflow
        self.workflow = self.create_workflow()

        # Initialize ChromaDB client - don't call async method directly
        self.chroma_client = None
        self._initialized = True

    async def setup_chroma_client(self):
        """Setup ChromaDB client connection"""
        try:
            self.logger.info("Attempting to connect to ChromaDB at 44.201.110.10:8000")
            self.chroma_client = HttpClient(host="44.201.110.10", port=8000)
            self.logger.info("ChromaDB client initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize ChromaDB client: {str(e)}")
            raise

    async def quick_collection_check(self) -> bool:
        """Check if collection exists and has content in ChromaDB"""
        try:
            self.logger.info(
                f"Checking for existing collection: {self.collection_name}"
            )
            collections = self.chroma_client.list_collections()
            collection_names = [col.name for col in collections]
            self.logger.info(f"Found collections: {collection_names}")

            exists = any(col.name == self.collection_name for col in collections)
            self.logger.info(f"Collection {self.collection_name} exists: {exists}")

            if exists:
                # Check if collection has any documents
                collection = self.chroma_client.get_collection(self.collection_name)
                count = collection.count()
                self.logger.info(
                    f"Collection {self.collection_name} contains {count} documents"
                )
                return count > 0  # Return True only if collection has documents

            return False
        except Exception as e:
            self.logger.error(f"Collection check failed: {str(e)}")
            return False

    async def async_init(self):
        """Optimized async initialization"""
        if self.is_initialized:
            return

        try:
            # Setup ChromaDB client first
            await self.setup_chroma_client()

            # Check if collection exists and has content
            collection_exists = await self.quick_collection_check()

            if not collection_exists:
                self.logger.info(
                    f"Collection {self.collection_name} is empty or doesn't exist"
                )
                # Create collection if it doesn't exist
                try:
                    collection = self.chroma_client.get_collection(self.collection_name)
                    self.logger.info("Using existing empty collection")
                except:
                    self.logger.info(f"Creating new collection: {self.collection_name}")
                    collection = self.chroma_client.create_collection(
                        name=self.collection_name,
                        metadata={
                            "source": f"s3://{self.bucket_name}/{self.directory_key}"
                        },
                    )

                # Load documents
                self.logger.info("Starting document loading process")
                await self.load_pdfs_to_vector_store()
            else:
                self.logger.info(
                    f"Using existing collection with documents: {self.collection_name}"
                )

            self.is_initialized = True

        except Exception as e:
            self.logger.error(f"Initialization error: {str(e)}")
            self.is_initialized = False
            raise

    async def load_pdfs_to_vector_store(self):
        """Load PDFs from S3 directory to ChromaDB"""
        try:
            self.logger.info(
                f"Starting PDF loading from S3 path: s3://{self.bucket_name}/{self.directory_key}"
            )

            # List objects with pagination
            paginator = self.s3.get_paginator("list_objects_v2")
            pdf_files = []

            # Use synchronous pagination
            for page in paginator.paginate(
                Bucket=self.bucket_name, Prefix=self.directory_key
            ):
                if "Contents" in page:
                    pdf_files.extend(page["Contents"])

            self.logger.info(f"Found {len(pdf_files)} total files in directory")
            pdf_files = [f for f in pdf_files if f["Key"].endswith(".pdf")]
            self.logger.info(f"Found {len(pdf_files)} PDF files to process")

            # Process PDFs in parallel
            tasks = []
            for pdf_obj in pdf_files:
                self.logger.info(f"Creating task for PDF: {pdf_obj['Key']}")
                task = asyncio.create_task(self.process_pdf(pdf_obj))
                tasks.append(task)

            documents = []
            processed_count = 0
            for completed_task in asyncio.as_completed(tasks):
                doc = await completed_task
                processed_count += 1
                self.logger.info(f"Processed {processed_count}/{len(pdf_files)} PDFs")

                if doc:
                    documents.append(doc)
                    self.logger.info(
                        f"Added document to batch. Current batch size: {len(documents)}"
                    )

                # Batch upload when we have enough documents
                if len(documents) >= 5:
                    self.logger.info("Batch size reached 5, uploading to ChromaDB...")
                    await self.add_documents_to_collection(documents)
                    documents = []

            # Upload any remaining documents
            if documents:
                self.logger.info(f"Uploading final batch of {len(documents)} documents")
                await self.add_documents_to_collection(documents)

            self.logger.info("Completed PDF loading process")

        except Exception as e:
            self.logger.error(f"Error loading PDFs: {str(e)}", exc_info=True)
            raise

    async def process_pdf(self, pdf_obj):
        """Process a single PDF file"""
        key = pdf_obj["Key"]
        self.logger.info(f"Processing PDF: {key}")

        if not key.endswith(".pdf"):
            self.logger.info(f"Skipping non-PDF file: {key}")
            return None

        cache_key = f"{key}_{pdf_obj['LastModified'].timestamp()}"
        if cache_key in self.cached_documents:
            self.logger.info(f"Using cached version of PDF: {key}")
            return self.cached_documents[cache_key]

        local_path = f"/tmp/{os.path.basename(key)}"
        try:
            self.logger.info(f"Downloading PDF to: {local_path}")
            self.s3.download_file(self.bucket_name, key, local_path)

            self.logger.info(f"Extracting text from PDF: {key}")
            loop = asyncio.get_event_loop()
            pdf_text = await loop.run_in_executor(
                self.thread_pool, self.extract_text_from_pdf, local_path
            )

            self.logger.info(f"Creating document object for: {key}")
            doc = Document(
                text=pdf_text,
                metadata={
                    "source": key,
                    "filename": os.path.basename(key),
                    "type": "pdf",
                },
                id=str(uuid.uuid4()),
            )
            self.cached_documents[cache_key] = doc
            self.logger.info(f"Successfully processed PDF: {key}")
            return doc

        except Exception as e:
            self.logger.error(f"Error processing PDF {key}: {str(e)}", exc_info=True)
            return None
        finally:
            if os.path.exists(local_path):
                self.logger.info(f"Cleaning up temporary file: {local_path}")
                os.remove(local_path)

    async def add_documents_to_collection(self, documents: List[Document]):
        """Add documents to ChromaDB collection"""
        try:
            self.logger.info(f"Generating embeddings for {len(documents)} documents")
            embeddings = await self.get_embeddings([doc.text for doc in documents])

            self.logger.info(f"Adding documents to collection: {self.collection_name}")
            collection = self.chroma_client.get_collection(self.collection_name)
            collection.add(
                documents=[doc.text for doc in documents],
                embeddings=embeddings,
                metadatas=[doc.metadata for doc in documents],
                ids=[doc.id or str(uuid.uuid4()) for doc in documents],
            )
            self.logger.info(
                f"Successfully added {len(documents)} documents to collection"
            )
        except Exception as e:
            self.logger.error(
                f"Error adding documents to collection: {str(e)}", exc_info=True
            )
            raise

    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for texts using the configured embedding model"""
        try:
            return await self.models.nomic_embeddings.aembed_documents(texts)
        except Exception as e:
            self.logger.error(f"Error generating embeddings: {str(e)}")
            raise

    def setup_language_models(self):
        """Setup language models and embeddings with caching"""
        self.local_llm = "llama-3.2-3b-preview"
        self.llm = ChatGroq(
            model=self.local_llm,
            temperature=0,
            request_timeout=10,
            api_key=config.groq_api_key,
        )
        self.nomic_embeddings = self.models.nomic_embeddings

    def setup_rag_adapter(self):
        """Setup RAG adapter with optimized connection settings"""
        self.chroma_client = HttpClient(host="44.201.110.10", port=8000)

    def create_workflow(self) -> Graph:
        """Create the RAG workflow"""
        workflow = StateGraph(AgenticState)

        async def retrieve(state: AgenticState) -> AgenticState:
            """Retrieve documents with optimized handling"""
            if not self.is_initialized:
                try:
                    await asyncio.wait_for(self.start_initialization(), timeout=5)
                except asyncio.TimeoutError:
                    return {
                        **state,
                        "context": [],
                        "error": "System is still initializing",
                    }

            try:
                async with asyncio.timeout(5):
                    query = state["messages"][-1].content
                    # Get embeddings for the query
                    query_embedding = await self.get_embeddings([query])

                    # Query ChromaDB directly
                    collection = self.chroma_client.get_collection(self.collection_name)

                    # Log collection info for debugging
                    self.logger.info(f"Querying collection: {self.collection_name}")
                    self.logger.info(f"Query: {query}")

                    results = collection.query(
                        query_embeddings=query_embedding,
                        n_results=3,
                        include=["documents", "metadatas"],
                    )

                    # Log results for debugging
                    self.logger.info(f"Query results: {results}")

                    # Extract text from results and limit context size
                    if (
                        results
                        and results["documents"]
                        and len(results["documents"]) > 0
                    ):
                        # Get all relevant documents
                        all_docs = results["documents"][0]

                        # Combine and truncate the context
                        combined_text = " ".join(all_docs)
                        # Limit to approximately 2000 words (rough estimate for token limit)
                        words = combined_text.split()
                        if len(words) > 2000:
                            truncated_text = " ".join(words[:2000])
                            self.logger.info("Context truncated to 2000 words")
                        else:
                            truncated_text = combined_text

                        context = [truncated_text]
                    else:
                        context = []
                        self.logger.warning("No documents found in query results")

                    return {**state, "context": context, "error": None}
            except Exception as e:
                self.logger.error(f"Retrieval error: {str(e)}", exc_info=True)
                return {**state, "context": [], "error": str(e)}

        async def generate(state: AgenticState) -> AgenticState:
            """Generate response with timeout"""
            if state["error"]:
                return state

            try:
                async with asyncio.timeout(5):
                    query = state["messages"][-1].content
                    context = state["context"]

                    # Log context for debugging
                    self.logger.info(
                        f"Context length: {len(context[0]) if context else 0} characters"
                    )

                    if not context:
                        return {
                            **state,
                            "response": "I don't have any relevant information in the documents to answer your question.",
                        }

                    prompt = f"""Use the following context to answer the question. If the information isn't in the context, say so:

Context: {context[0]}

Question: {query}

Provide a clear and concise answer using only the information from the context. If the specific information isn't in the context, say so."""

                    response = await self.llm.ainvoke([HumanMessage(content=prompt)])
                    return {**state, "response": response.content}
            except Exception as e:
                self.logger.error(f"Generation error: {str(e)}", exc_info=True)
                return {**state, "error": str(e)}

        workflow.add_node("retrieve", retrieve)
        workflow.add_node("generate", generate)
        workflow.add_edge("retrieve", "generate")
        workflow.set_entry_point("retrieve")

        return workflow.compile()

    async def process_query(self, query: str) -> Dict:
        """Process queries with optimized handling"""
        try:
            if not self.is_initialized:
                await self.start_initialization()
                await self.initialization_task  # Wait for initialization to complete

            async with asyncio.timeout(10):
                state = AgenticState(
                    messages=[HumanMessage(content=query)],
                    context=[],
                    response="",
                    error=None,
                )

                result = await self.workflow.ainvoke(state)

                if result["error"]:
                    return {"response": f"Error: {result['error']}"}

                return {"response": result["response"]}

        except asyncio.TimeoutError:
            return {"response": "Request timed out. Please try again."}
        except Exception as e:
            self.logger.error(f"Query processing error: {str(e)}")
            return {"response": f"An error occurred: {str(e)}"}

    async def start_initialization(self):
        """Start the initialization process if not already started"""
        if self.initialization_task is None:
            self.initialization_task = asyncio.create_task(self.async_init())
        return self.initialization_task

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF with caching"""
        try:
            self.logger.info(f"Opening PDF file: {pdf_path}")
            with fitz.open(pdf_path) as doc:
                text = ""
                for page_num in range(len(doc)):
                    self.logger.info(f"Processing page {page_num + 1}/{len(doc)}")
                    page = doc[page_num]
                    text += page.get_text()

                self.logger.info(
                    f"Successfully extracted {len(text)} characters from PDF"
                )
                return text
        except Exception as e:
            self.logger.error(f"PDF extraction error: {str(e)}", exc_info=True)
            raise
