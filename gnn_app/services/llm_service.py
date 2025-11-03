"""
Local LLM service using Ollama for AI assistance.
Provides fallback when Google ADK is not available or for local-only deployments.
"""

import httpx
from typing import Dict, List, Any, Optional
import structlog
import json
from datetime import datetime

from gnn_app.config import settings
from gnn_app.core.graph_schema import GraphNode, TemporalGraph

logger = structlog.get_logger()


class OllamaService:
    """
    Service for interacting with local Ollama LLM.
    Provides chat and analysis capabilities.
    """
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout: float = 60.0
    ):
        """
        Initialize Ollama service.
        
        Args:
            base_url: Ollama API base URL
            model_name: Model name (e.g., 'llama3.2', 'mistral')
            timeout: Request timeout in seconds
        """
        self.base_url = base_url or settings.llm.base_url
        self.model_name = model_name or settings.llm.model_name
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
        self.enabled = False
        
        logger.info(
            "Ollama service initialized",
            base_url=self.base_url,
            model=self.model_name
        )
    
    async def check_availability(self) -> bool:
        """Check if Ollama is available."""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get('models', [])
                available_models = [m['name'] for m in models]
                self.enabled = any(self.model_name in m for m in available_models)
                
                if self.enabled:
                    logger.info("Ollama available", models=available_models)
                else:
                    logger.warning(
                        "Model not found in Ollama",
                        requested=self.model_name,
                        available=available_models
                    )
                
                return self.enabled
        except Exception as e:
            logger.warning("Ollama not available", error=str(e))
            self.enabled = False
            return False
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> str:
        """
        Generate text using Ollama.
        
        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text
        """
        if not self.enabled:
            await self.check_availability()
            if not self.enabled:
                return "Ollama service is not available. Please ensure Ollama is running."
        
        try:
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            }
            
            if system_prompt:
                payload["system"] = system_prompt
            
            response = await self.client.post(
                f"{self.base_url}/api/generate",
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', '')
            else:
                logger.error("Ollama generation failed", status=response.status_code)
                return f"Error: {response.status_code}"
                
        except Exception as e:
            logger.error("Error generating with Ollama", error=str(e))
            return f"Error: {str(e)}"
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7
    ) -> str:
        """
        Chat with Ollama using conversation history.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            
        Returns:
            Assistant's response
        """
        if not self.enabled:
            await self.check_availability()
            if not self.enabled:
                return "Ollama service is not available."
        
        try:
            payload = {
                "model": self.model_name,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature
                }
            }
            
            response = await self.client.post(
                f"{self.base_url}/api/chat",
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('message', {}).get('content', '')
            else:
                logger.error("Ollama chat failed", status=response.status_code)
                return f"Error: {response.status_code}"
                
        except Exception as e:
            logger.error("Error chatting with Ollama", error=str(e))
            return f"Error: {str(e)}"
    
    async def analyze_node(
        self,
        node: GraphNode,
        neighbors: Optional[List[GraphNode]] = None
    ) -> str:
        """
        Analyze a node using Ollama.
        
        Args:
            node: Node to analyze
            neighbors: Connected nodes
            
        Returns:
            Analysis text
        """
        context = {
            "id": node.id,
            "type": node.type.value,
            "label": node.label,
            "risk_score": node.risk_score,
            "risk_level": node.risk_level.value,
            "relevance_score": node.relevance_score,
            "metadata": node.metadata
        }
        
        if neighbors:
            context["neighbors"] = [
                {
                    "id": n.id,
                    "type": n.type.value,
                    "label": n.label,
                    "risk_score": n.risk_score
                }
                for n in neighbors[:10]
            ]
        
        system_prompt = """You are Agent X, an AI assistant specialized in eDiscovery and risk analysis.
Analyze entities from temporal knowledge graphs and provide actionable insights."""
        
        prompt = f"""Analyze the following entity and provide insights:

{json.dumps(context, indent=2)}

Provide:
1. Risk Assessment
2. Key Connections
3. Anomalies or Concerns
4. Recommendations"""
        
        return await self.generate(prompt, system_prompt=system_prompt)
    
    async def answer_query(
        self,
        query: str,
        node: Optional[GraphNode] = None,
        graph_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Answer a query about a node or graph.
        
        Args:
            query: User's question
            node: Context node (optional)
            graph_context: Additional context (optional)
            
        Returns:
            Answer text
        """
        context_parts = []
        
        if node:
            context_parts.append(f"Selected Entity: {json.dumps({
                'id': node.id,
                'type': node.type.value,
                'label': node.label,
                'risk_score': node.risk_score,
                'relevance_score': node.relevance_score,
                'metadata': node.metadata
            }, indent=2, default=str)}")
        
        if graph_context:
            context_parts.append(f"Graph Context: {json.dumps(graph_context, indent=2, default=str)}")
        
        context = "\n\n".join(context_parts) if context_parts else "No specific context."
        
        system_prompt = """You are Agent X, an AI assistant for eDiscovery and risk management.
Answer questions clearly and concisely based on the provided data."""
        
        prompt = f"""Context:
{context}

Question: {query}

Answer:"""
        
        return await self.generate(prompt, system_prompt=system_prompt)
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


# Global Ollama service instance
_ollama_service: Optional[OllamaService] = None


def get_ollama_service() -> OllamaService:
    """Get or create the global Ollama service instance."""
    global _ollama_service
    if _ollama_service is None:
        _ollama_service = OllamaService()
    return _ollama_service
