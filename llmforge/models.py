"""
Model catalog, metadata structures, and categorization for OpenRouter & Groq models.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class ModelInfo:
    id: str
    name: str
    context_length: int
    category: str  # 'text', 'multimodal', 'speech', 'router', 'guardrail'
    provider: str = "openrouter"  # 'openrouter' or 'groq'
    input_modalities: List[str] = field(default_factory=list)
    output_modalities: List[str] = field(default_factory=list)
    description: str = ""
    pricing_prompt: float = 0.0
    pricing_completion: float = 0.0

    @property
    def formatted_ctx(self) -> str:
        """Return human-readable context window format (e.g. 128K, 1M)."""
        if self.context_length >= 1_000_000:
            return f"{self.context_length // 1_000_000}M tokens"
        elif self.context_length >= 1000:
            return f"{self.context_length // 1000}K tokens"
        return f"{self.context_length} tokens"

    @property
    def modality_badge(self) -> str:
        """Return quick visual tag for modalities."""
        badges = []
        if self.category == "guardrail":
            return "🛡️ Guardrail"
        if 'image' in self.input_modalities:
            badges.append("👁️ Vision")
        if 'audio' in self.input_modalities or 'speech' in self.input_modalities:
            badges.append("🎙️ Audio-In")
        if 'audio' in self.output_modalities or 'speech' in self.output_modalities:
            badges.append("🔊 Speech-Out")
        if not badges:
            badges.append("💬 Text")
        return " | ".join(badges)

    @property
    def provider_badge(self) -> str:
        """Return provider visual tag."""
        if self.provider == "groq":
            return "⚡ Groq LPU"
        return "🌐 OpenRouter"


# Curated verified offline fallback list of OpenRouter Free Models
FALLBACK_FREE_MODELS: List[Dict[str, Any]] = [
    {
        "id": "recursive/flint-v1.0:free",
        "name": "Recursive: Flint (free)",
        "context_length": 262144,
        "category": "text",
        "provider": "openrouter",
        "input_modalities": ["text"],
        "output_modalities": ["text"],
        "description": "High performance instruction-tuned reasoning model by Recursive with 256K context."
    },
    {
        "id": "google/gemma-4-31b-it:free",
        "name": "Google: Gemma 4 31B (free)",
        "context_length": 262144,
        "category": "multimodal",
        "provider": "openrouter",
        "input_modalities": ["text", "image", "video"],
        "output_modalities": ["text"],
        "description": "Google's 31B instruction-tuned multimodal model with text, image, and video understanding."
    },
    {
        "id": "google/gemma-4-26b-a4b-it:free",
        "name": "Google: Gemma 4 26B A4B (free)",
        "context_length": 262144,
        "category": "multimodal",
        "provider": "openrouter",
        "input_modalities": ["text", "image", "video"],
        "output_modalities": ["text"],
        "description": "Google's 26B efficient architecture multimodal model."
    },
    {
        "id": "nvidia/nemotron-3.5-lightning:free",
        "name": "NVIDIA: Nemotron 3.5 Lightning (free)",
        "context_length": 1000000,
        "category": "text",
        "provider": "openrouter",
        "input_modalities": ["text"],
        "output_modalities": ["text"],
        "description": "NVIDIA high-speed lightning model with 1,000,000 token context window."
    },
    {
        "id": "nvidia/nemotron-3-ultra-550b-a55b:free",
        "name": "NVIDIA: Nemotron 3 Ultra (free)",
        "context_length": 1000000,
        "category": "text",
        "provider": "openrouter",
        "input_modalities": ["text"],
        "output_modalities": ["text"],
        "description": "Massive 550B MoE flagship model with deep reasoning and 1M token context."
    },
    {
        "id": "nvidia/nemotron-3.5-super-vl:free",
        "name": "NVIDIA: Nemotron 3.5 Super VL (free)",
        "context_length": 1000000,
        "category": "multimodal",
        "provider": "openrouter",
        "input_modalities": ["text", "image", "video"],
        "output_modalities": ["text"],
        "description": "Vision-language model by NVIDIA supporting long-context documents and media."
    },
    {
        "id": "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
        "name": "NVIDIA: Nemotron 3 Nano Omni (free)",
        "context_length": 256000,
        "category": "speech",
        "provider": "openrouter",
        "input_modalities": ["text", "image", "audio", "video"],
        "output_modalities": ["text"],
        "description": "Omni-modal reasoning model with native audio, image, and video comprehension."
    },
    {
        "id": "liquid/lfm-2.5-2.6b:free",
        "name": "LiquidAI: LFM2.5-2.6B (free)",
        "context_length": 65536,
        "category": "text",
        "provider": "openrouter",
        "input_modalities": ["text"],
        "output_modalities": ["text"],
        "description": "Liquid Neural Network architecture with ultra-low latency inference."
    },
    {
        "id": "cohere/north-mini-code:free",
        "name": "Cohere: North Mini Code (free)",
        "context_length": 256000,
        "category": "text",
        "provider": "openrouter",
        "input_modalities": ["text"],
        "output_modalities": ["text"],
        "description": "Specialized code generation and refactoring model by Cohere with 256K context."
    },
    {
        "id": "thinkingmachines/inkling:free",
        "name": "Thinking Machines: Inkling (free)",
        "context_length": 1048576,
        "category": "speech",
        "provider": "openrouter",
        "input_modalities": ["text", "image", "audio"],
        "output_modalities": ["text"],
        "description": "Multimodal agent with 1M context supporting audio, image, and text."
    },
    {
        "id": "google/lyria-3-pro-preview",
        "name": "Google: Lyria 3 Pro Preview",
        "context_length": 1048576,
        "category": "speech",
        "provider": "openrouter",
        "input_modalities": ["text", "image"],
        "output_modalities": ["text", "audio"],
        "description": "Google audio and speech synthesis preview model with text and audio outputs."
    },
    {
        "id": "google/lyria-3-clip-preview",
        "name": "Google: Lyria 3 Clip Preview",
        "context_length": 1048576,
        "category": "speech",
        "provider": "openrouter",
        "input_modalities": ["text", "image"],
        "output_modalities": ["text", "audio"],
        "description": "Fast audio generation model for musical clips and speech."
    },
    {
        "id": "openrouter/free",
        "name": "OpenRouter Free Auto-Router",
        "context_length": 200000,
        "category": "router",
        "provider": "openrouter",
        "input_modalities": ["text", "image"],
        "output_modalities": ["text"],
        "description": "Automatic router that dynamically delegates to whichever free model is currently active."
    }
]

# Curated verified Groq Models Catalog
FALLBACK_GROQ_MODELS: List[Dict[str, Any]] = [
    {
        "id": "qwen/qwen3.8-27b",
        "name": "Qwen 3.8 27B (Vision & Text)",
        "context_length": 131072,
        "category": "multimodal",
        "provider": "groq",
        "input_modalities": ["text", "image"],
        "output_modalities": ["text"],
        "description": "Flagship 27B multimodal model on Groq LPUs (>220 tok/s) with 128K context."
    },
    {
        "id": "openai/gpt-oss-20b",
        "name": "OpenAI GPT-OSS 20B",
        "context_length": 131072,
        "category": "text",
        "provider": "groq",
        "input_modalities": ["text"],
        "output_modalities": ["text"],
        "description": "High-efficiency open-weights 20B model on Groq hardware ($0.075/1M prompt)."
    },
    {
        "id": "openai/gpt-oss-120b",
        "name": "OpenAI GPT-OSS 120B",
        "context_length": 131072,
        "category": "text",
        "provider": "groq",
        "input_modalities": ["text"],
        "output_modalities": ["text"],
        "description": "Massive 120B parameter model with deep reasoning and 128K context ($0.15/1M prompt)."
    },
    {
        "id": "allam-2-7b",
        "name": "Allam 2 7B",
        "context_length": 4096,
        "category": "text",
        "provider": "groq",
        "input_modalities": ["text"],
        "output_modalities": ["text"],
        "description": "Bilingual Arabic and English language model optimized for rapid response."
    },
    {
        "id": "meta-llama/llama-prompt-guard-2-22m",
        "name": "Llama Prompt Guard 2 22M",
        "context_length": 512,
        "category": "guardrail",
        "provider": "groq",
        "input_modalities": ["text"],
        "output_modalities": ["text"],
        "description": "Least expensive model ($0.03/1M): ultra-fast 22M classifier detecting prompt injections & jailbreaks."
    },
    {
        "id": "meta-llama/llama-prompt-guard-2-86m",
        "name": "Llama Prompt Guard 2 86M",
        "context_length": 512,
        "category": "guardrail",
        "provider": "groq",
        "input_modalities": ["text"],
        "output_modalities": ["text"],
        "description": "Enhanced 86M classifier detecting prompt injection attacks ($0.04/1M)."
    },
    {
        "id": "whisper-large-v3-turbo",
        "name": "Whisper Large v3 Turbo",
        "context_length": 448,
        "category": "speech",
        "provider": "groq",
        "input_modalities": ["audio"],
        "output_modalities": ["text"],
        "description": "Blazing fast multilingual speech-to-text audio transcription engine."
    },
    {
        "id": "whisper-large-v3",
        "name": "Whisper Large v3",
        "context_length": 448,
        "category": "speech",
        "provider": "groq",
        "input_modalities": ["audio"],
        "output_modalities": ["text"],
        "description": "High accuracy multilingual speech-to-text transcription engine."
    },
    {
        "id": "canopylabs/orpheus-v1-english",
        "name": "Orpheus v1 English (TTS)",
        "context_length": 4096,
        "category": "speech",
        "provider": "groq",
        "input_modalities": ["text"],
        "output_modalities": ["audio"],
        "description": "Expressive English text-to-speech audio synthesis engine."
    },
    {
        "id": "canopylabs/orpheus-arabic-saudi",
        "name": "Orpheus Arabic Saudi (TTS)",
        "context_length": 4096,
        "category": "speech",
        "provider": "groq",
        "input_modalities": ["text"],
        "output_modalities": ["audio"],
        "description": "Expressive Arabic text-to-speech audio synthesis engine."
    }
]

def parse_model_from_api(raw: Dict[str, Any]) -> ModelInfo:
    """Parse raw OpenRouter API model dictionary into ModelInfo object."""
    model_id = raw.get("id", "")
    name = raw.get("name", model_id)
    ctx = raw.get("context_length", 0) or 0
    desc = raw.get("description", "")
    
    pricing = raw.get("pricing", {})
    p_prompt = float(pricing.get("prompt", 0) or 0)
    p_comp = float(pricing.get("completion", 0) or 0)
    
    arch = raw.get("architecture", {})
    modality_str = arch.get("modality", "text->text")
    
    # Parse input and output modalities
    in_mods = []
    out_mods = []
    if "->" in modality_str:
        left, right = modality_str.split("->", 1)
        in_mods = [m.strip() for m in left.split("+") if m.strip()]
        out_mods = [m.strip() for m in right.split("+") if m.strip()]
    else:
        in_mods = ["text"]
        out_mods = ["text"]

    # Categorize
    category = "text"
    if model_id == "openrouter/free":
        category = "router"
    elif "audio" in out_mods or "speech" in out_mods or "audio" in in_mods:
        category = "speech"
    elif "image" in in_mods or "video" in in_mods:
        category = "multimodal"

    return ModelInfo(
        id=model_id,
        name=name,
        context_length=ctx,
        category=category,
        provider="openrouter",
        input_modalities=in_mods,
        output_modalities=out_mods,
        description=desc,
        pricing_prompt=p_prompt,
        pricing_completion=p_comp
    )

def parse_groq_model_from_api(raw: Dict[str, Any]) -> ModelInfo:
    """Parse raw Groq API model dictionary into ModelInfo object."""
    model_id = raw.get("id", "")
    ctx = raw.get("context_window", 4096) or 4096
    
    # Identify known models or map metadata
    known = next((m for m in FALLBACK_GROQ_MODELS if m["id"] == model_id), None)
    if known:
        return ModelInfo(
            id=model_id,
            name=known["name"],
            context_length=known["context_length"],
            category=known["category"],
            provider="groq",
            input_modalities=known.get("input_modalities", ["text"]),
            output_modalities=known.get("output_modalities", ["text"]),
            description=known.get("description", "")
        )

    # Generic categorization based on model ID
    category = "text"
    in_mods = ["text"]
    out_mods = ["text"]

    if "guard" in model_id:
        category = "guardrail"
    elif "whisper" in model_id:
        category = "speech"
        in_mods = ["audio"]
        out_mods = ["text"]
    elif "orpheus" in model_id or "tts" in model_id:
        category = "speech"
        in_mods = ["text"]
        out_mods = ["audio"]
    elif "vision" in model_id or "vl" in model_id or "qwen" in model_id:
        category = "multimodal"
        in_mods = ["text", "image"]

    return ModelInfo(
        id=model_id,
        name=model_id,
        context_length=ctx,
        category=category,
        provider="groq",
        input_modalities=in_mods,
        output_modalities=out_mods,
        description=f"Groq LPU accelerated model ({model_id})"
    )
