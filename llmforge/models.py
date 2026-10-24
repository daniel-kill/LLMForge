"""
Model catalog, metadata structures, and categorization for OpenRouter free models.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class ModelInfo:
    id: str
    name: str
    context_length: int
    category: str  # 'text', 'multimodal', 'speech', 'router'
    input_modalities: List[str] = field(default_factory=list)
    output_modalities: List[str] = field(default_factory=list)
    description: str = ""
    pricing_prompt: float = 0.0
    pricing_completion: float = 0.0

    @property
    def formatted_ctx(self) -> str:
        """Return human-readable context window format (e.g. 256K, 1M)."""
        if self.context_length >= 1_000_000:
            return f"{self.context_length // 1_000_000}M tokens"
        elif self.context_length >= 1000:
            return f"{self.context_length // 1000}K tokens"
        return f"{self.context_length} tokens"

    @property
    def modality_badge(self) -> str:
        """Return quick visual tag for modalities."""
        badges = []
        if 'image' in self.input_modalities:
            badges.append("👁️ Vision")
        if 'audio' in self.input_modalities or 'speech' in self.input_modalities:
            badges.append("🎙️ Audio-In")
        if 'audio' in self.output_modalities or 'speech' in self.output_modalities:
            badges.append("🔊 Speech-Out")
        if not badges:
            badges.append("💬 Text")
        return " | ".join(badges)


# Curated verified offline fallback list of OpenRouter Free Models
FALLBACK_FREE_MODELS: List[Dict[str, Any]] = [
    {
        "id": "recursive/flint-v1.0:free",
        "name": "Recursive: Flint (free)",
        "context_length": 262144,
        "category": "text",
        "input_modalities": ["text"],
        "output_modalities": ["text"],
        "description": "High performance instruction-tuned reasoning model by Recursive with 256K context."
    },
    {
        "id": "google/gemma-4-31b-it:free",
        "name": "Google: Gemma 4 31B (free)",
        "context_length": 262144,
        "category": "multimodal",
        "input_modalities": ["text", "image", "video"],
        "output_modalities": ["text"],
        "description": "Google's 31B instruction-tuned multimodal model with text, image, and video understanding."
    },
    {
        "id": "google/gemma-4-26b-a4b-it:free",
        "name": "Google: Gemma 4 26B A4B (free)",
        "context_length": 262144,
        "category": "multimodal",
        "input_modalities": ["text", "image", "video"],
        "output_modalities": ["text"],
        "description": "Google's 26B efficient architecture multimodal model."
    },
    {
        "id": "nvidia/nemotron-3.5-lightning:free",
        "name": "NVIDIA: Nemotron 3.5 Lightning (free)",
        "context_length": 1000000,
        "category": "text",
        "input_modalities": ["text"],
        "output_modalities": ["text"],
        "description": "NVIDIA high-speed lightning model with 1,000,000 token context window."
    },
    {
        "id": "nvidia/nemotron-3-ultra-550b-a55b:free",
        "name": "NVIDIA: Nemotron 3 Ultra (free)",
        "context_length": 1000000,
        "category": "text",
        "input_modalities": ["text"],
        "output_modalities": ["text"],
        "description": "Massive 550B MoE flagship model with deep reasoning and 1M token context."
    },
    {
        "id": "nvidia/nemotron-3.5-super-vl:free",
        "name": "NVIDIA: Nemotron 3.5 Super VL (free)",
        "context_length": 1000000,
        "category": "multimodal",
        "input_modalities": ["text", "image", "video"],
        "output_modalities": ["text"],
        "description": "Vision-language model by NVIDIA supporting long-context documents and media."
    },
    {
        "id": "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
        "name": "NVIDIA: Nemotron 3 Nano Omni (free)",
        "context_length": 256000,
        "category": "speech",
        "input_modalities": ["text", "image", "audio", "video"],
        "output_modalities": ["text"],
        "description": "Omni-modal reasoning model with native audio, image, and video comprehension."
    },
    {
        "id": "liquid/lfm-2.5-2.6b:free",
        "name": "LiquidAI: LFM2.5-2.6B (free)",
        "context_length": 65536,
        "category": "text",
        "input_modalities": ["text"],
        "output_modalities": ["text"],
        "description": "Liquid Neural Network architecture with ultra-low latency inference."
    },
    {
        "id": "cohere/north-mini-code:free",
        "name": "Cohere: North Mini Code (free)",
        "context_length": 256000,
        "category": "text",
        "input_modalities": ["text"],
        "output_modalities": ["text"],
        "description": "Specialized code generation and refactoring model by Cohere with 256K context."
    },
    {
        "id": "thinkingmachines/inkling:free",
        "name": "Thinking Machines: Inkling (free)",
        "context_length": 1048576,
        "category": "speech",
        "input_modalities": ["text", "image", "audio"],
        "output_modalities": ["text"],
        "description": "Multimodal agent with 1M context supporting audio, image, and text."
    },
    {
        "id": "google/lyria-3-pro-preview",
        "name": "Google: Lyria 3 Pro Preview",
        "context_length": 1048576,
        "category": "speech",
        "input_modalities": ["text", "image"],
        "output_modalities": ["text", "audio"],
        "description": "Google audio and speech synthesis preview model with text and audio outputs."
    },
    {
        "id": "google/lyria-3-clip-preview",
        "name": "Google: Lyria 3 Clip Preview",
        "context_length": 1048576,
        "category": "speech",
        "input_modalities": ["text", "image"],
        "output_modalities": ["text", "audio"],
        "description": "Fast audio generation model for musical clips and speech."
    },
    {
        "id": "openrouter/free",
        "name": "OpenRouter Free Auto-Router",
        "context_length": 200000,
        "category": "router",
        "input_modalities": ["text", "image"],
        "output_modalities": ["text"],
        "description": "Automatic router that dynamically delegates to whichever free model is currently active."
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
        input_modalities=in_mods,
        output_modalities=out_mods,
        description=desc,
        pricing_prompt=p_prompt,
        pricing_completion=p_comp
    )
