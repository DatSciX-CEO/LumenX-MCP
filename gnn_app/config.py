"""
Configuration for the GNN application.
All settings for models, embeddings, and deployment.
"""

from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
import os


class GNNModelConfig(BaseModel):
    """Configuration for GNN model architecture."""
    hidden_dim: int = Field(default=128, description="Hidden dimension size")
    num_layers: int = Field(default=3, description="Number of GNN layers")
    dropout: float = Field(default=0.1, description="Dropout rate")
    aggregation: str = Field(default="mean", description="Aggregation method")
    activation: str = Field(default="relu", description="Activation function")


class EmbeddingConfig(BaseModel):
    """Configuration for embedding generation."""
    model_name: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="Local embedding model"
    )
    embedding_dim: int = Field(default=384, description="Embedding dimension")
    batch_size: int = Field(default=32, description="Batch size for embedding")
    device: str = Field(default="cpu", description="Device (cpu/cuda)")


class LLMConfig(BaseModel):
    """Configuration for local LLM."""
    provider: str = Field(default="ollama", description="LLM provider (ollama/google-adk)")
    model_name: str = Field(default="llama3.2", description="Model name")
    base_url: str = Field(default="http://localhost:11434", description="Ollama base URL")
    temperature: float = Field(default=0.7, description="Temperature for generation")
    max_tokens: int = Field(default=2048, description="Max tokens to generate")


class GoogleADKConfig(BaseModel):
    """Configuration for Google ADK integration."""
    enabled: bool = Field(default=True, description="Enable Google ADK agents")
    api_key: Optional[str] = Field(default=None, description="Google API key")
    project_id: Optional[str] = Field(default=None, description="GCP project ID")
    region: str = Field(default="us-central1", description="GCP region")


class APIConfig(BaseModel):
    """Configuration for FastAPI server."""
    host: str = Field(default="0.0.0.0", description="API host")
    port: int = Field(default=8000, description="API port")
    reload: bool = Field(default=False, description="Auto-reload on changes")
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        description="CORS allowed origins"
    )


class DataConfig(BaseModel):
    """Configuration for data storage and processing."""
    data_dir: Path = Field(default=Path("data"), description="Data directory")
    cache_dir: Path = Field(default=Path(".cache"), description="Cache directory")
    model_dir: Path = Field(default=Path("models"), description="Model checkpoint directory")
    max_nodes: int = Field(default=10000, description="Maximum nodes in graph")
    max_edges: int = Field(default=50000, description="Maximum edges in graph")


class Settings(BaseSettings):
    """Main application settings."""
    
    # Project info
    project_name: str = "Predictive Data Mapping GNN"
    version: str = "1.0.0"
    debug: bool = Field(default=False, description="Debug mode")
    
    # Component configs
    gnn: GNNModelConfig = Field(default_factory=GNNModelConfig)
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    google_adk: GoogleADKConfig = Field(default_factory=GoogleADKConfig)
    api: APIConfig = Field(default_factory=APIConfig)
    data: DataConfig = Field(default_factory=DataConfig)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_nested_delimiter = "__"


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings


# Create necessary directories
def setup_directories():
    """Create necessary directories if they don't exist."""
    settings.data.data_dir.mkdir(parents=True, exist_ok=True)
    settings.data.cache_dir.mkdir(parents=True, exist_ok=True)
    settings.data.model_dir.mkdir(parents=True, exist_ok=True)


# Setup on import
setup_directories()
