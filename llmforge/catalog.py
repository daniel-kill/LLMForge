"""
Interactive Free Models Catalog and Inspector for LLMForge.
"""

from typing import List, Optional

from .banner import (
    RESET, BOLD, DIM, CYAN, AMBER, CRIMSON, GOLD, GREEN, PURPLE, GRAY, WHITE, DARK_GRAY,
    print_header, print_divider
)
from .client import OpenRouterClient
from .models import ModelInfo

class CatalogViewer:
    def __init__(self, client: OpenRouterClient):
        self.client = client

    def run(self) -> None:
        """Browse and filter free models."""
        models = self.client.get_free_models()
        if not models:
            print(f"{CRIMSON}Could not retrieve models.{RESET}")
            return

        while True:
            print_header("OPENROUTER FREE MODELS CATALOG", f"{len(models)} Total Free Models Discovered")
            print(f"{DARK_GRAY}Filter options:{RESET}")
            print(f"  {CYAN}[1]{RESET} All Free Models ({len(models)})")
            print(f"  {CYAN}[2]{RESET} 💬 Text & Reasoning Models")
            print(f"  {CYAN}[3]{RESET} 👁️  Vision & Multimodal Models")
            print(f"  {CYAN}[4]{RESET} 🎙️  Audio & Speech Models")
            print(f"  {CYAN}[5]{RESET} 🔍 Search by keyword / provider")
            print(f"  {CYAN}[6]{RESET} ⚡ Test / Ping a Model")
            print(f"  {CYAN}[0]{RESET} Back to Main Menu")

            choice = input(f"\n{AMBER}Select view [0-6]: {RESET}").strip()
            if choice == "0":
                break
            elif choice == "1":
                self._display_table(models, "ALL OPENROUTER FREE MODELS")
            elif choice == "2":
                filtered = [m for m in models if m.category in ("text", "router")]
                self._display_table(filtered, "TEXT & REASONING MODELS")
            elif choice == "3":
                filtered = [m for m in models if "image" in m.input_modalities or "video" in m.input_modalities]
                self._display_table(filtered, "VISION & MULTIMODAL MODELS")
            elif choice == "4":
                filtered = [m for m in models if m.category == "speech" or "audio" in m.output_modalities or "audio" in m.input_modalities]
                self._display_table(filtered, "AUDIO & SPEECH MODELS")
            elif choice == "5":
                kw = input(f"{AMBER}Search keyword (e.g. nvidia, gemma, lyria, flint, 1m): {RESET}").strip().lower()
                filtered = [
                    m for m in models 
                    if kw in m.id.lower() or kw in m.name.lower() or kw in m.description.lower()
                ]
                self._display_table(filtered, f"SEARCH RESULTS: '{kw}'")
            elif choice == "6":
                self._test_model(models)
            else:
                print(f"{CRIMSON}Invalid choice.{RESET}")

    def _display_table(self, models: List[ModelInfo], title: str) -> None:
        """Render clean terminal table."""
        print_header(title, f"{len(models)} Models")
        print(f" {BOLD}{'#':<3} {'Model Name':<34} {'Model ID':<44} {'Context':<12} {'Modalities':<16}{RESET}")
        print(f" {DARK_GRAY}{'─'*3} {'─'*34} {'─'*44} {'─'*12} {'─'*16}{RESET}")

        for idx, m in enumerate(models, 1):
            name_col = m.name[:32]
            id_col = m.id[:42]
            ctx_col = m.formatted_ctx
            mod_col = m.modality_badge

            # Highlight recommended or flagship models
            color = WHITE
            if "flint" in m.id:
                color = GOLD
            elif "nemotron" in m.id:
                color = GREEN
            elif "gemma" in m.id:
                color = CYAN
            elif "lyria" in m.id:
                color = PURPLE

            print(f" {DARK_GRAY}{idx:2d}{RESET}  {color}{name_col:<34}{RESET} {DARK_GRAY}{id_col:<44}{RESET} {PURPLE}{ctx_col:<12}{RESET} {GRAY}{mod_col:<16}{RESET}")

        print(f"\n{DARK_GRAY}Tip: Select Option 6 or use '/m <id>' in chat to use any of these models.{RESET}")
        input(f"\n{AMBER}Press Enter to return...{RESET}")

    def _test_model(self, models: List[ModelInfo]) -> None:
        """Ping a model with a quick test prompt."""
        print(f"\n{GOLD}{BOLD}Test / Ping a Model:{RESET}")
        print(f"Enter model number from list or model ID (e.g. recursive/flint-v1.0:free):")
        target = input(f"{AMBER}Model: {RESET}").strip()
        if not target:
            return

        if target.isdigit() and 1 <= int(target) <= len(models):
            target_id = models[int(target) - 1].id
        else:
            target_id = target

        print(f"\n{CYAN}Pinging {target_id}...{RESET}")
        test_messages = [{"role": "user", "content": "Respond with 'PONG' and your model identity."}]
        
        content, elapsed, err = self.client.chat_complete(test_messages, model=target_id)
        if err:
            print(f"{CRIMSON}✗ Error from {target_id}: {err}{RESET}\n")
        else:
            print(f"{GREEN}✓ Ping Success ({elapsed:.2f}s):{RESET}")
            print(f"{WHITE}{content}{RESET}\n")
        
        input(f"{AMBER}Press Enter to continue...{RESET}")
