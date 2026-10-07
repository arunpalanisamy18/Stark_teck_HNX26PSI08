import json
import logging
import re
from typing import Any, Dict, Optional
import httpx

from app.config import OLLAMA_BASE_URL, OLLAMA_MODEL, OLLAMA_TIMEOUT_SECONDS

logger = logging.getLogger("veritas.ollama")

class OllamaService:
    def __init__(
        self,
        base_url: str = OLLAMA_BASE_URL,
        model: str = OLLAMA_MODEL,
        timeout: float = OLLAMA_TIMEOUT_SECONDS
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    async def is_available(self) -> bool:
        """Check if local Ollama service is reachable and responsive."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(f"{self.base_url}/api/tags")
                return res.status_code == 200
        except Exception as e:
            logger.warning(f"Ollama health check failed: {e}")
            return False

    def is_available_sync(self) -> bool:
        """Synchronous check for Ollama availability."""
        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.get(f"{self.base_url}/api/tags")
                return res.status_code == 200
        except Exception as e:
            logger.warning(f"Ollama sync health check failed: {e}")
            return False

    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        format_json: bool = True,
        temperature: float = 0.0,
    ) -> str:
        """Send prompt to local Ollama LLM and return raw response text."""
        url = f"{self.base_url}/api/generate"
        payload: Dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": 350,
            }
        }
        if system:
            payload["system"] = system
        if format_json:
            payload["format"] = "json"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.post(url, json=payload)
                res.raise_for_status()
                data = res.json()
                response_text = data.get("response", "")
                logger.info(f"Ollama generated {data.get('eval_count', 0)} tokens in {data.get('eval_duration', 0)/1e9:.2f}s")
                return response_text
        except httpx.TimeoutException:
            logger.error(f"Ollama request timed out after {self.timeout}s")
            raise RuntimeError(f"Local Ollama model timed out after {self.timeout}s.")
        except httpx.ConnectError:
            logger.error("Could not connect to Ollama service at 127.0.0.1:11434")
            raise RuntimeError("Ollama service is not running locally. Please ensure Ollama is started.")
        except Exception as e:
            logger.error(f"Ollama generation error: {e}")
            raise RuntimeError(f"Ollama inference error: {str(e)}")

    def generate_sync(
        self,
        prompt: str,
        system: Optional[str] = None,
        format_json: bool = True,
        temperature: float = 0.0,
    ) -> str:
        """Synchronous version of generate."""
        url = f"{self.base_url}/api/generate"
        payload: Dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": 350,
            }
        }
        if system:
            payload["system"] = system
        if format_json:
            payload["format"] = "json"

        try:
            with httpx.Client(timeout=self.timeout) as client:
                res = client.post(url, json=payload)
                res.raise_for_status()
                data = res.json()
                return data.get("response", "")
        except Exception as e:
            logger.error(f"Sync Ollama error: {e}")
            raise RuntimeError(f"Ollama sync inference error: {str(e)}")

    @staticmethod
    def extract_json(raw_text: str) -> Dict[str, Any]:
        """Extract and parse JSON safely from model response."""
        text = raw_text.strip()
        # Direct parse attempt
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Check for markdown code fences ```json ... ```
        fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        if fence_match:
            try:
                return json.loads(fence_match.group(1).strip())
            except json.JSONDecodeError:
                pass

        # Find first '{' and last '}'
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                pass

        raise ValueError(f"Could not parse valid JSON from LLM response:\n{raw_text}")

# Global singleton
ollama_service = OllamaService()

