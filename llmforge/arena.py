"""
The Model Arena — Benchmark and compare multiple OpenRouter free models on the same prompt.
"""

import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from .banner import (
    RESET, BOLD, DIM, CYAN, AMBER, CRIMSON, GOLD, GREEN, PURPLE, GRAY, WHITE, DARK_GRAY,
    print_header, print_divider
)
from .client import OpenRouterClient
from .models import ModelInfo

class ModelArena:
    def __init__(self, client: OpenRouterClient):
        self.client = client

    def run(self, preset_prompt: Optional[str] = None) -> None:
        """Run interactive Model Arena session."""
        print_header("THE FORGE ARENA", "Side-by-side benchmark & comparison of OpenRouter Free Models")
        print(f"{DARK_GRAY}Test the exact same prompt against multiple free models to evaluate speed, reasoning, and tone.{RESET}\n")

        # 1. Fetch available free models
        models = self.client.get_free_models()
        if not models:
            print(f"{CRIMSON}No free models available.{RESET}")
            return

        print(f"{GOLD}{BOLD}Available Free Contenders:{RESET}")
        for idx, m in enumerate(models, 1):
            print(f"  {CYAN}[{idx:2d}]{RESET} {WHITE}{m.name:<32}{RESET} {DARK_GRAY}{m.id:<42}{RESET} {PURPLE}[{m.formatted_ctx}]{RESET}")

        # 2. Select contenders
        print(f"\n{AMBER}Select 2 to 4 contenders by number (comma-separated, e.g. 1, 2, 4):{RESET}")
        selection = input(f"{CYAN}Contenders: {RESET}").strip()
        if not selection:
            # Default to Flint and Gemma or first two
            selected_models = [models[0].id, models[min(1, len(models)-1)].id]
            print(f"{GRAY}Defaulting to: {selected_models[0]} vs {selected_models[1]}{RESET}")
        else:
            indices = []
            for part in selection.split(","):
                part = part.strip()
                if part.isdigit() and 1 <= int(part) <= len(models):
                    indices.append(int(part) - 1)
            
            if len(indices) < 2:
                print(f"{AMBER}Please select at least 2 models. Using first two.{RESET}")
                selected_models = [models[0].id, models[1].id]
            else:
                selected_models = [models[i].id for i in indices[:4]]

        print(f"\n{GREEN}Selected Contenders:{RESET}")
        for sm in selected_models:
            print(f"  ⚔️  {BOLD}{WHITE}{sm}{RESET}")

        # 3. Choose or enter prompt
        prompt = preset_prompt
        if not prompt:
            print(f"\n{GOLD}{BOLD}Prompt Selection:{RESET}")
            print(f"  {CYAN}[1]{RESET} Explain the difference between process and thread in operating systems.")
            print(f"  {CYAN}[2]{RESET} Write a Python script to fetch a JSON API with retry logic.")
            print(f"  {CYAN}[3]{RESET} Compose a short dark gothic monologue from a vampire lord.")
            print(f"  {CYAN}[4]{RESET} Enter custom prompt")

            p_choice = input(f"\n{AMBER}Choose [1-4] (default: 4): {RESET}").strip()
            if p_choice == "1":
                prompt = "Explain the fundamental differences between a process and a thread in modern operating systems. Include memory allocation and concurrency considerations."
            elif p_choice == "2":
                prompt = "Write a complete, robust Python function using urllib or requests that queries a REST API with exponential backoff and error handling."
            elif p_choice == "3":
                prompt = "Compose a dramatic, atmospheric monologue delivered by a 19th-century vampire overlooking the misty Carpathian mountains at dusk."
            else:
                prompt = input(f"\n{AMBER}Enter your benchmark prompt: {RESET}").strip()

        if not prompt:
            print(f"{CRIMSON}Prompt cannot be empty.{RESET}")
            return

        print(f"\n{DARK_GRAY}───────────────────────────────────────────────────────────────────{RESET}")
        print(f"{AMBER}{BOLD}BENCHMARK PROMPT:{RESET} {WHITE}{prompt}{RESET}")
        print(f"{DARK_GRAY}───────────────────────────────────────────────────────────────────{RESET}\n")

        # 4. Execute Benchmark
        results = []
        messages = [{"role": "user", "content": prompt}]

        for idx, model_id in enumerate(selected_models, 1):
            print(f"\n{PURPLE}{BOLD}==================================================================={RESET}")
            print(f"{GOLD}Contender {idx}/{len(selected_models)}:{RESET} {BOLD}{WHITE}{model_id}{RESET}")
            print(f"{PURPLE}==================================================================={RESET}\n")

            start_t = time.time()
            full_text = ""
            error = None

            try:
                for chunk in self.client.stream_chat(messages, model=model_id, temperature=0.7):
                    full_text += chunk
                    sys.stdout.write(chunk)
                    sys.stdout.flush()
            except Exception as e:
                error = str(e)
                print(f"\n{CRIMSON}[Error executing {model_id}: {error}]{RESET}")

            elapsed = time.time() - start_t
            approx_tokens = int(len(full_text.split()) * 1.3)
            tok_per_sec = (approx_tokens / elapsed) if elapsed > 0 else 0

            print(f"\n\n{DARK_GRAY}Metrics: ⏱️  {elapsed:.2f}s | ~{approx_tokens} tokens | {tok_per_sec:.1f} tok/s{RESET}")

            results.append({
                "model": model_id,
                "text": full_text,
                "elapsed": elapsed,
                "tokens": approx_tokens,
                "speed": tok_per_sec,
                "error": error
            })

        # 5. Display Summary Table
        print(f"\n\n{GOLD}{BOLD}╔════════════════════════════════════════════════════════════════════════════════════════╗{RESET}")
        print(f"{GOLD}{BOLD}║                              ARENA BENCHMARK SUMMARY                                   ║{RESET}")
        print(f"{GOLD}{BOLD}╚════════════════════════════════════════════════════════════════════════════════════════╝{RESET}")
        print(f" {BOLD}{'Contender Model':<42} {'Latency':<12} {'Tokens':<12} {'Throughput':<15}{RESET}")
        print(f" {DARK_GRAY}{'─'*42} {'─'*12} {'─'*12} {'─'*15}{RESET}")

        for r in results:
            m_short = r["model"][:40]
            lat_str = f"{r['elapsed']:.2f}s"
            tok_str = f"~{r['tokens']}"
            spd_str = f"{r['speed']:.1f} tok/s"
            print(f" {WHITE}{m_short:<42}{RESET} {CYAN}{lat_str:<12}{RESET} {GREEN}{tok_str:<12}{RESET} {AMBER}{spd_str:<15}{RESET}")

        # 6. Offer to save report
        print()
        save_opt = input(f"{AMBER}Save Arena report to Markdown? [y/N]: {RESET}").strip().lower()
        if save_opt in ('y', 'yes'):
            self._save_report(prompt, results)

    def _save_report(self, prompt: str, results: List[Dict[str, Any]]) -> None:
        """Save benchmark report to markdown."""
        save_dir = Path.home() / ".llmforge" / "arena_reports"
        save_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = save_dir / f"arena_benchmark_{timestamp}.md"

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# LLMForge Arena Benchmark Report\n\n")
            f.write(f"- **Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"- **Prompt:** \"{prompt}\"\n\n")
            f.write("## Performance Summary\n\n")
            f.write("| Model | Latency (s) | Est. Tokens | Throughput (tok/s) |\n")
            f.write("| :--- | :--- | :--- | :--- |\n")
            for r in results:
                f.write(f"| `{r['model']}` | {r['elapsed']:.2f}s | ~{r['tokens']} | {r['speed']:.1f} |\n")
            f.write("\n---\n\n## Generated Outputs\n\n")

            for r in results:
                f.write(f"### {r['model']}\n\n")
                f.write(f"```markdown\n{r['text']}\n```\n\n")

        print(f"{GREEN}✓ Benchmark report saved to: {WHITE}{filepath}{RESET}\n")
