"""
API Clients for LLMForge:
- OpenRouterClient: OpenRouter Free-Tier model discovery, quota checking & streaming.
- GroqClient: Groq LPU Ultra-Fast Inference, model discovery & Llama Prompt Guard.
"""

import json
import time
import urllib.request
import urllib.error
from typing import Generator, List, Dict, Any, Optional, Tuple

from .models import (
    ModelInfo,
    FALLBACK_FREE_MODELS,
    FALLBACK_GROQ_MODELS,
    parse_model_from_api,
    parse_groq_model_from_api
)
from .config import get_api_key

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
GROQ_BASE_URL = "https://api.groq.com/openai/v1"

class OpenRouterClient:
    """Client for OpenRouter API."""
    provider = "openrouter"

    def __init__(self, api_key: str):
        self.api_key = api_key.strip()
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/daniel-kill/LLMForge",
            "X-Title": "LLMForge",
            "User-Agent": "LLMForge/1.0"
        }

    def check_auth(self) -> Dict[str, Any]:
        """
        Verify API key and retrieve account quota info from /auth/key.
        Returns dict with label, is_free_tier, limit, used, remaining.
        """
        req = urllib.request.Request(
            f"{OPENROUTER_BASE_URL}/auth/key",
            headers=self.headers,
            method="GET"
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8")).get("data", {})
                free_reqs = data.get("free_model_daily_requests", {})
                return {
                    "valid": True,
                    "provider": "openrouter",
                    "label": data.get("label", "Key"),
                    "is_free_tier": data.get("is_free_tier", True),
                    "used": free_reqs.get("used", 0),
                    "limit": free_reqs.get("limit", 50),
                    "remaining": free_reqs.get("remaining", 50),
                    "error": None
                }
        except urllib.error.HTTPError as e:
            return {
                "valid": False,
                "provider": "openrouter",
                "error": f"HTTP {e.code}: {e.reason}"
            }
        except Exception as e:
            return {
                "valid": False,
                "provider": "openrouter",
                "error": str(e)
            }

    def get_models(self) -> List[ModelInfo]:
        """
        Dynamically query OpenRouter for all available models and filter
        for free tier models (pricing == 0 or id ending with :free).
        Falls back to local verified catalog if offline.
        """
        req = urllib.request.Request(
            f"{OPENROUTER_BASE_URL}/models",
            headers=self.headers,
            method="GET"
        )
        try:
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode("utf-8")).get("data", [])
                free_list: List[ModelInfo] = []
                for item in data:
                    mid = item.get("id", "")
                    pricing = item.get("pricing", {})
                    p_prompt = float(pricing.get("prompt", 0) or 0)
                    p_comp = float(pricing.get("completion", 0) or 0)
                    if mid.endswith(":free") or (p_prompt == 0 and p_comp == 0):
                        free_list.append(parse_model_from_api(item))
                
                if free_list:
                    return sorted(free_list, key=lambda m: (m.id != "recursive/flint-v1.0:free", m.name))
        except Exception:
            pass

        # Fallback to local catalog
        return [
            ModelInfo(
                id=m["id"],
                name=m["name"],
                context_length=m["context_length"],
                category=m["category"],
                provider="openrouter",
                input_modalities=m.get("input_modalities", ["text"]),
                output_modalities=m.get("output_modalities", ["text"]),
                description=m.get("description", "")
            )
            for m in FALLBACK_FREE_MODELS
        ]

    get_free_models = get_models

    def stream_chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "recursive/flint-v1.0:free",
        temperature: float = 0.7,
        top_p: float = 0.95,
        max_tokens: int = 4096
    ) -> Generator[str, None, Dict[str, Any]]:
        """
        Stream chat response token by token via Server-Sent Events (SSE).
        Yields chunk text deltas. Returns summary metadata upon completion.
        """
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens,
            "stream": True
        }

        req = urllib.request.Request(
            f"{OPENROUTER_BASE_URL}/chat/completions",
            headers=self.headers,
            data=json.dumps(payload).encode("utf-8"),
            method="POST"
        )

        start_time = time.time()
        total_content = ""
        total_chunks = 0

        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                for line in resp:
                    line_str = line.decode("utf-8").strip()
                    if not line_str or line_str == "data: [DONE]":
                        continue
                    if line_str.startswith("data: "):
                        try:
                            chunk = json.loads(line_str[6:])
                            choices = chunk.get("choices", [])
                            if choices:
                                delta = choices[0].get("delta", {}).get("content", "")
                                if delta:
                                    total_content += delta
                                    total_chunks += 1
                                    yield delta
                        except Exception:
                            continue
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="ignore")
            try:
                err_json = json.loads(err_body)
                msg = err_json.get("error", {}).get("message", err_body)
            except Exception:
                msg = err_body
            yield f"\n[API Error {e.code}: {msg}]"
        except Exception as e:
            yield f"\n[Connection Error: {str(e)}]"

        duration = time.time() - start_time
        return {
            "content": total_content,
            "duration": duration,
            "chunks": total_chunks
        }

    def chat_complete(
        self,
        messages: List[Dict[str, str]],
        model: str = "recursive/flint-v1.0:free",
        temperature: float = 0.7,
        top_p: float = 0.95,
        max_tokens: int = 4096
    ) -> Tuple[Optional[str], float, Optional[str]]:
        """
        Non-streaming chat completion.
        Returns: (response_text, elapsed_seconds, error_message)
        """
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens,
            "stream": False
        }

        req = urllib.request.Request(
            f"{OPENROUTER_BASE_URL}/chat/completions",
            headers=self.headers,
            data=json.dumps(payload).encode("utf-8"),
            method="POST"
        )

        start_time = time.time()
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                elapsed = time.time() - start_time
                choices = data.get("choices", [])
                if choices:
                    content = choices[0].get("message", {}).get("content", "")
                    return content, elapsed, None
                return "", elapsed, "Empty response choices returned."
        except urllib.error.HTTPError as e:
            elapsed = time.time() - start_time
            err_body = e.read().decode("utf-8", errors="ignore")
            try:
                err_json = json.loads(err_body)
                msg = err_json.get("error", {}).get("message", err_body)
            except Exception:
                msg = err_body
            return None, elapsed, f"HTTP {e.code}: {msg}"
        except Exception as e:
            elapsed = time.time() - start_time
            return None, elapsed, str(e)


class GroqClient:
    """
    Client for Groq LPU Inference API.
    Provides ultra-fast inference (>200 tok/s) and Llama Prompt Guard safety scoring.
    """
    provider = "groq"

    def __init__(self, api_key: str):
        self.api_key = api_key.strip()
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "LLMForge/1.0"
        }

    def check_auth(self) -> Dict[str, Any]:
        """
        Verify API key by querying /openai/v1/models.
        """
        req = urllib.request.Request(
            f"{GROQ_BASE_URL}/models",
            headers=self.headers,
            method="GET"
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8")).get("data", [])
                return {
                    "valid": True,
                    "provider": "groq",
                    "label": "Groq LPU Acceleration Key",
                    "is_free_tier": False,
                    "model_count": len(data),
                    "status": "Operational (LPU Active)",
                    "error": None
                }
        except urllib.error.HTTPError as e:
            return {
                "valid": False,
                "provider": "groq",
                "error": f"HTTP {e.code}: {e.reason}"
            }
        except Exception as e:
            return {
                "valid": False,
                "provider": "groq",
                "error": str(e)
            }

    def get_models(self) -> List[ModelInfo]:
        """
        Query Groq for all active models on the LPU infrastructure.
        Falls back to curated list if network fails.
        """
        req = urllib.request.Request(
            f"{GROQ_BASE_URL}/models",
            headers=self.headers,
            method="GET"
        )
        try:
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode("utf-8")).get("data", [])
                models: List[ModelInfo] = []
                for item in data:
                    models.append(parse_groq_model_from_api(item))
                if models:
                    # Sort prioritizing flagship qwen and gpt-oss models
                    return sorted(
                        models,
                        key=lambda m: (
                            m.id != "qwen/qwen3.8-27b",
                            m.id != "openai/gpt-oss-20b",
                            m.id != "openai/gpt-oss-120b",
                            m.name
                        )
                    )
        except Exception:
            pass

        # Curated fallback
        return [
            ModelInfo(
                id=m["id"],
                name=m["name"],
                context_length=m["context_length"],
                category=m["category"],
                provider="groq",
                input_modalities=m.get("input_modalities", ["text"]),
                output_modalities=m.get("output_modalities", ["text"]),
                description=m.get("description", "")
            )
            for m in FALLBACK_GROQ_MODELS
        ]

    get_free_models = get_models

    def stream_chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "qwen/qwen3.8-27b",
        temperature: float = 0.7,
        top_p: float = 0.95,
        max_tokens: int = 4096
    ) -> Generator[str, None, Dict[str, Any]]:
        """
        Stream chat response token by token via SSE on Groq LPUs.
        """
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens,
            "stream": True
        }

        req = urllib.request.Request(
            f"{GROQ_BASE_URL}/chat/completions",
            headers=self.headers,
            data=json.dumps(payload).encode("utf-8"),
            method="POST"
        )

        start_time = time.time()
        total_content = ""
        total_chunks = 0

        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                for line in resp:
                    line_str = line.decode("utf-8").strip()
                    if not line_str or line_str == "data: [DONE]":
                        continue
                    if line_str.startswith("data: "):
                        try:
                            chunk = json.loads(line_str[6:])
                            choices = chunk.get("choices", [])
                            if choices:
                                delta = choices[0].get("delta", {}).get("content", "")
                                if delta:
                                    total_content += delta
                                    total_chunks += 1
                                    yield delta
                        except Exception:
                            continue
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="ignore")
            try:
                err_json = json.loads(err_body)
                msg = err_json.get("error", {}).get("message", err_body)
            except Exception:
                msg = err_body
            yield f"\n[Groq API Error {e.code}: {msg}]"
        except Exception as e:
            yield f"\n[Groq Connection Error: {str(e)}]"

        duration = time.time() - start_time
        return {
            "content": total_content,
            "duration": duration,
            "chunks": total_chunks
        }

    def chat_complete(
        self,
        messages: List[Dict[str, str]],
        model: str = "qwen/qwen3.8-27b",
        temperature: float = 0.7,
        top_p: float = 0.95,
        max_tokens: int = 4096
    ) -> Tuple[Optional[str], float, Optional[str]]:
        """
        Non-streaming chat completion on Groq LPUs.
        """
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens,
            "stream": False
        }

        req = urllib.request.Request(
            f"{GROQ_BASE_URL}/chat/completions",
            headers=self.headers,
            data=json.dumps(payload).encode("utf-8"),
            method="POST"
        )

        start_time = time.time()
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                elapsed = time.time() - start_time
                choices = data.get("choices", [])
                if choices:
                    content = choices[0].get("message", {}).get("content", "")
                    return content, elapsed, None
                return "", elapsed, "Empty response returned from Groq."
        except urllib.error.HTTPError as e:
            elapsed = time.time() - start_time
            err_body = e.read().decode("utf-8", errors="ignore")
            try:
                err_json = json.loads(err_body)
                msg = err_json.get("error", {}).get("message", err_body)
            except Exception:
                msg = err_body
            return None, elapsed, f"HTTP {e.code}: {msg}"
        except Exception as e:
            elapsed = time.time() - start_time
            return None, elapsed, str(e)

    def check_prompt_guard(
        self,
        prompt: str,
        model: str = "meta-llama/llama-prompt-guard-2-22m"
    ) -> Dict[str, Any]:
        """
        Evaluate a prompt against Meta's Llama Prompt Guard classifier.
        Detects prompt injection and jailbreaking attempts.
        Returns score (0.0 to 1.0) and security verdict.
        """
        messages = [{"role": "user", "content": prompt}]
        content, elapsed, err = self.chat_complete(messages=messages, model=model, max_tokens=10)

        if err or content is None:
            return {
                "safe": False,
                "score": 1.0,
                "verdict": "ERROR",
                "elapsed": elapsed,
                "error": err
            }

        score = 0.0
        try:
            score = float(content.strip())
        except ValueError:
            score = 0.5 if "suspicious" in content.lower() else 0.0

        if score < 0.2:
            verdict = "SAFE"
        elif score < 0.6:
            verdict = "SUSPICIOUS"
        else:
            verdict = "INJECTION / JAILBREAK DETECTED"

        return {
            "model": model,
            "raw_output": content.strip(),
            "score": score,
            "verdict": verdict,
            "elapsed": elapsed,
            "error": None
        }


def get_client(provider: str = "openrouter", api_key: Optional[str] = None):
    """
    Factory function returning an instantiated client for the specified provider.
    """
    prov = provider.lower()
    if prov == "groq":
        key = api_key or get_api_key("groq")
        if not key:
            raise ValueError("No GROQ_API_KEY discovered.")
        return GroqClient(key)
    else:
        key = api_key or get_api_key("openrouter")
        if not key:
            raise ValueError("No OPENROUTER_API_KEY discovered.")
        return OpenRouterClient(key)
