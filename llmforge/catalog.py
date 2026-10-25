"""
Interactive Free & LPU Models Catalog and Inspector for LLMForge.
Supports both OpenRouter Free-Tier and Groq LPU model catalogs.
"""

import sys
import time
from typing import List, Optional, Any

from .banner import (
    RESET, BOLD, DIM, CYAN, AMBER, CRIMSON, GOLD, GREEN, PURPLE, GRAY, WHITE, DARK_GRAY, BLUE,
    print_header, print_divider
)
from .client import OpenRouterClient, GroqClient, get_client
from .config import get_api_key
from .models import ModelInfo

class CatalogViewer:
    def __init__(
        self,
        default_client: Any,
        openrouter_client: Optional[OpenRouterClient] = None,
        groq_client: Optional[GroqClient] = None
    ):
        self.default_client = default_client
        self.openrouter_client = openrouter_client
        self.groq_client = groq_client

        if not self.openrouter_client and get_api_key("openrouter"):
            try:
                self.openrouter_client = get_client("openrouter")
            except Exception:
                pass

        if not self.groq_client and get_api_key("groq"):
            try:
                self.groq_client = get_client("groq")
            except Exception:
                pass

        if isinstance(self.default_client, OpenRouterClient):
            self.openrouter_client = self.default_client
        elif isinstance(self.default_client, GroqClient):
            self.groq_client = self.default_client

    def _get_all_models(self) -> List[ModelInfo]:
        """Aggregate models from both providers."""
        all_m: List[ModelInfo] = []
        if self.openrouter_client:
            all_m.extend(self.openrouter_client.get_models())
        if self.groq_client:
            all_m.extend(self.groq_client.get_models())
        if not all_m and hasattr(self.default_client, "get_models"):
            all_m.extend(self.default_client.get_models())
        return all_m

    def run(self) -> None:
        """Browse and filter models interactively."""
        models = self._get_all_models()
        if not models:
            print(f"{CRIMSON}Could not retrieve models from active providers.{RESET}")
            return

        while True:
            prov_summary = []
            if self.openrouter_client:
                prov_summary.append("OpenRouter")
            if self.groq_client:
                prov_summary.append("Groq LPU")

            print_header("FORGE MODELS CATALOG & INSPECTOR", f"{len(models)} Total Models ({', '.join(prov_summary)})")
            print(f"{DARK_GRAY}Filter & View Options:{RESET}")
            print(f"  {CYAN}[1]{RESET} All Models ({len(models)} models)")
            print(f"  {CYAN}[2]{RESET} 🌐 OpenRouter Free-Tier Models")
            print(f"  {CYAN}[3]{RESET} ⚡ Groq LPU Ultra-Fast Models")
            print(f"  {CYAN}[4]{RESET} 💬 Text & Reasoning Models")
            print(f"  {CYAN}[5]{RESET} 👁️  Vision & Multimodal Models")
            print(f"  {CYAN}[6]{RESET} 🎙️  Audio & Speech Models")
            print(f"  {CYAN}[7]{RESET} 🛡️  Guardrail & Security Models (Prompt Guard 22M / 86M)")
            print(f"  {CYAN}[8]{RESET} 🔍 Search by keyword / architecture")
            print(f"  {CYAN}[9]{RESET} ⚡ Test / Ping a Model")
            print(f"  {CYAN}[0]{RESET} Back to Main Menu")

            choice = input(f"\n{AMBER}Select view [0-9]: {RESET}").strip()
            if choice == "0":
                break
            elif choice == "1":
                self._display_table(models, "ALL MODELS (OPENROUTER & GROQ)")
            elif choice == "2":
                filtered = [m for m in models if m.provider == "openrouter"]
                self._display_table(filtered, "OPENROUTER FREE-TIER MODELS")
            elif choice == "3":
                filtered = [m for m in models if m.provider == "groq"]
                self._display_table(filtered, "GROQ LPU ULTRA-FAST MODELS")
            elif choice == "4":
                filtered = [m for m in models if m.category in ("text", "router")]
                self._display_table(filtered, "TEXT & REASONING MODELS")
            elif choice == "5":
                filtered = [m for m in models if "image" in m.input_modalities or "video" in m.input_modalities]
                self._display_table(filtered, "VISION & MULTIMODAL MODELS")
            elif choice == "6":
                filtered = [m for m in models if m.category == "speech" or "audio" in m.output_modalities or "audio" in m.input_modalities]
                self._display_table(filtered, "AUDIO & SPEECH MODELS")
            elif choice == "7":
                filtered = [m for m in models if m.category == "guardrail"]
                self._display_table(filtered, "GUARDRAIL & SECURITY MODELS")
            elif choice == "8":
                kw = input(f"{AMBER}Search keyword (e.g. qwen, flint, guard, nemotron, 1m): {RESET}").strip().lower()
                filtered = [
                    m for m in models 
                    if kw in m.id.lower() or kw in m.name.lower() or kw in m.description.lower()
                ]
                self._display_table(filtered, f"SEARCH RESULTS: '{kw}'")
            elif choice == "9":
                self._test_model(models)
            else:
                print(f"{CRIMSON}Invalid choice.{RESET}")

    def _display_table(self, models: List[ModelInfo], title: str) -> None:
        """Render clean terminal table."""
        print_header(title, f"{len(models)} Models")
        print(f" {BOLD}{'#':<3} {'Provider':<10} {'Model Name':<32} {'Model ID':<38} {'Context':<11} {'Type/Modality':<14}{RESET}")
        print(f" {DARK_GRAY}{'─'*3} {'─'*10} {'─'*32} {'─'*38} {'─'*11} {'─'*14}{RESET}")

        for idx, m in enumerate(models, 1):
            prov_tag = f"{GOLD}⚡ Groq{RESET}" if m.provider == "groq" else f"{BLUE}🌐 OR{RESET}"
            name_col = m.name[:30]
            id_col = m.id[:36]
            ctx_col = m.formatted_ctx
            mod_col = m.modality_badge

            color = WHITE
            if "qwen" in m.id:
                color = GOLD
            elif "flint" in m.id:
                color = GREEN
            elif "guard" in m.id:
                color = CRIMSON
            elif "nemotron" in m.id:
                color = CYAN

            print(f" {DARK_GRAY}{idx:2d}{RESET}  {prov_tag:<19} {color}{name_col:<32}{RESET} {DARK_GRAY}{id_col:<38}{RESET} {PURPLE}{ctx_col:<11}{RESET} {GRAY}{mod_col:<14}{RESET}")

        print(f"\n{DARK_GRAY}Tip: Use Option 9 to ping any model, or use /model in chat.{RESET}")
        input(f"\n{AMBER}Press Enter to return...{RESET}")

    def _test_model(self, models: List[ModelInfo]) -> None:
        """Ping a model with a quick test prompt."""
        print(f"\n{GOLD}{BOLD}Test / Ping a Model:{RESET}")
        print(f"Enter model number from list or model ID (e.g. qwen/qwen3.8-27b or recursive/flint-v1.0:free):")
        target = input(f"{AMBER}Model: {RESET}").strip()
        if not target:
            return

        target_model = None
        if target.isdigit() and 1 <= int(target) <= len(models):
            target_model = models[int(target) - 1]
        else:
            target_model = next((m for m in models if m.id == target), None)
            if not target_model:
                target_model = ModelInfo(id=target, name=target, context_length=4096, category="text", provider="groq" if "/" not in target or "qwen" in target else "openrouter")

        client = self.groq_client if (target_model.provider == "groq" and self.groq_client) else self.openrouter_client
        if not client:
            client = self.default_client

        print(f"\n{CYAN}Pinging {target_model.name} ({target_model.id}) on {target_model.provider.upper()}...{RESET}\n")

        # Handle Prompt Guard specially
        if target_model.category == "guardrail":
            if isinstance(client, GroqClient):
                res = client.check_prompt_guard("Hello, Dracula!")
                print(f"Prompt Guard Output: {res}")
                return

        start_t = time.time()
        try:
            for chunk in client.stream_chat(
                [{"role": "user", "content": "Respond with exactly 1 sentence introducing yourself."}],
                model=target_model.id,
                temperature=0.5
            ):
                sys.stdout.write(chunk)
                sys.stdout.flush()
        except Exception as e:
            print(f"\n{CRIMSON}Ping failed: {e}{RESET}")
        
        elapsed = time.time() - start_t
        print(f"\n\n{DARK_GRAY}[⏱️  Latency: {elapsed:.2f}s]{RESET}\n")
