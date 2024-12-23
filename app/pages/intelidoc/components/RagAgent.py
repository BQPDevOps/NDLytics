import os
import uuid
import asyncio

from typing import List, Dict, TypedDict, Optional, Any
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from pydantic import BaseModel, Field
from chromadb import HttpClient
from config import config
import nomic
import logging.handlers
import boto3
from langchain_core.messages import HumanMessage, BaseMessage
from langgraph.graph import Graph, StateGraph
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_groq import ChatGroq
from langchain_nomic.embeddings import NomicEmbeddings
import fitz


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
        self.ollama_embeddings = OllamaEmbeddings(
            model="nomic-embed-text-v1.5", base_url="http://127.0.0.1:11434"
        )
        self.model_ollama = ChatOllama(
            model="llama3.1:8b", base_url="http://127.0.0.1:11434", temperature=0
        )


class RagAgentState(TypedDict):
    messages: list[BaseMessage]
    context: list[str]
    response: str
    error: Optional[str]


class RagAgent:
    _instances = {}

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

        # Initialize basic attributes
        self.bucket_name = bucket_name
        self.directory_key = directory_key

        collection_name = directory_key.rstrip("/").split("/")[
            -1
        ]  # Get last part of path
        collection_name = "".join(
            c if c.isalnum() or c in "_-" else "" for c in collection_name
        )

        # Ensure minimum length
        if len(collection_name) < 3:
            collection_name = f"{collection_name}_{'_' * (3 - len(collection_name))}"

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
            self.chroma_client = HttpClient(host="44.217.220.109", port=8000)
        except Exception as e:
            print(f"Failed to initialize ChromaDB client: {str(e)}")
            raise
