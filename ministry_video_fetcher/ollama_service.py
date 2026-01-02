"""
Ollama Service - Local LLM API Client
Provides integration with Ollama for AI-powered health and planning reports.
"""

import httpx
import json
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime


class OllamaService:
    """Client for communicating with local Ollama LLM service."""

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3"):
        self.base_url = base_url
        self.model = model
        self.timeout = 60.0  # 60 second timeout for generation
        self._last_check: Optional[datetime] = None
        self._is_available: bool = False

    async def check_availability(self) -> Dict[str, Any]:
        """
        Check if Ollama service is running and responsive.
        Returns status info including available models.
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Check if Ollama is running
                response = await client.get(f"{self.base_url}/api/tags")

                if response.status_code == 200:
                    data = response.json()
                    models = [m.get("name", "") for m in data.get("models", [])]

                    self._is_available = True
                    self._last_check = datetime.now()

                    return {
                        "available": True,
                        "model": self.model,
                        "models": models,
                        "hasRequestedModel": any(self.model in m for m in models),
                        "message": "Ollama is running"
                    }
                else:
                    self._is_available = False
                    return {
                        "available": False,
                        "model": self.model,
                        "message": f"Ollama returned status {response.status_code}"
                    }

        except httpx.ConnectError:
            self._is_available = False
            return {
                "available": False,
                "model": self.model,
                "message": "Cannot connect to Ollama. Is it running? Start with: ollama serve"
            }
        except httpx.TimeoutException:
            self._is_available = False
            return {
                "available": False,
                "model": self.model,
                "message": "Ollama connection timed out"
            }
        except Exception as e:
            self._is_available = False
            return {
                "available": False,
                "model": self.model,
                "message": f"Error checking Ollama: {str(e)}"
            }

    def check_availability_sync(self) -> Dict[str, Any]:
        """Synchronous version of check_availability for non-async contexts."""
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{self.base_url}/api/tags")

                if response.status_code == 200:
                    data = response.json()
                    models = [m.get("name", "") for m in data.get("models", [])]

                    self._is_available = True
                    self._last_check = datetime.now()

                    return {
                        "available": True,
                        "model": self.model,
                        "models": models,
                        "hasRequestedModel": any(self.model in m for m in models),
                        "message": "Ollama is running"
                    }
                else:
                    self._is_available = False
                    return {
                        "available": False,
                        "model": self.model,
                        "message": f"Ollama returned status {response.status_code}"
                    }

        except Exception as e:
            self._is_available = False
            return {
                "available": False,
                "model": self.model,
                "message": f"Cannot connect to Ollama: {str(e)}"
            }

    @property
    def is_available(self) -> bool:
        """Quick check if Ollama was available on last check."""
        return self._is_available

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        """
        Generate a response from Ollama.

        Args:
            prompt: The user prompt/question
            system_prompt: Optional system prompt to set context
            temperature: Creativity level (0.0-1.0)
            max_tokens: Maximum tokens to generate

        Returns:
            Dict with 'success', 'response', and optional 'error'
        """
        if not self._is_available:
            # Quick re-check
            await self.check_availability()

        if not self._is_available:
            return {
                "success": False,
                "response": None,
                "error": "Ollama is not available"
            }

        try:
            request_data = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            }

            if system_prompt:
                request_data["system"] = system_prompt

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=request_data
                )

                if response.status_code == 200:
                    data = response.json()
                    return {
                        "success": True,
                        "response": data.get("response", ""),
                        "model": data.get("model", self.model),
                        "total_duration": data.get("total_duration", 0),
                        "eval_count": data.get("eval_count", 0)
                    }
                else:
                    return {
                        "success": False,
                        "response": None,
                        "error": f"Ollama returned status {response.status_code}"
                    }

        except httpx.TimeoutException:
            return {
                "success": False,
                "response": None,
                "error": "Generation timed out. Try a shorter prompt or increase timeout."
            }
        except Exception as e:
            return {
                "success": False,
                "response": None,
                "error": f"Error generating response: {str(e)}"
            }

    def generate_sync(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        """Synchronous version of generate for non-async contexts."""
        # Check availability first
        status = self.check_availability_sync()
        if not status.get("available"):
            return {
                "success": False,
                "response": None,
                "error": status.get("message", "Ollama is not available")
            }

        try:
            request_data = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            }

            if system_prompt:
                request_data["system"] = system_prompt

            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    f"{self.base_url}/api/generate",
                    json=request_data
                )

                if response.status_code == 200:
                    data = response.json()
                    return {
                        "success": True,
                        "response": data.get("response", ""),
                        "model": data.get("model", self.model),
                        "total_duration": data.get("total_duration", 0),
                        "eval_count": data.get("eval_count", 0)
                    }
                else:
                    return {
                        "success": False,
                        "response": None,
                        "error": f"Ollama returned status {response.status_code}"
                    }

        except httpx.TimeoutException:
            return {
                "success": False,
                "response": None,
                "error": "Generation timed out"
            }
        except Exception as e:
            return {
                "success": False,
                "response": None,
                "error": f"Error: {str(e)}"
            }

    def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3
    ) -> Dict[str, Any]:
        """
        Generate a JSON response from Ollama.
        Uses lower temperature for more consistent structured output.

        Returns:
            Dict with 'success', 'data' (parsed JSON), and optional 'error'
        """
        # Add JSON instruction to system prompt
        json_system = (system_prompt or "") + "\n\nIMPORTANT: Respond ONLY with valid JSON. No markdown, no explanation, just the JSON object."

        result = self.generate_sync(
            prompt=prompt,
            system_prompt=json_system,
            temperature=temperature,
            max_tokens=2000
        )

        if not result.get("success"):
            return {
                "success": False,
                "data": None,
                "error": result.get("error", "Generation failed")
            }

        # Try to parse JSON from response
        response_text = result.get("response", "")

        # Clean up response - remove markdown code blocks if present
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]

        response_text = response_text.strip()

        try:
            data = json.loads(response_text)
            return {
                "success": True,
                "data": data,
                "raw_response": result.get("response")
            }
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "data": None,
                "error": f"Failed to parse JSON: {str(e)}",
                "raw_response": result.get("response")
            }


# Global instance
ollama_service = OllamaService()
