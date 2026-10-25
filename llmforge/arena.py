"""
The Model Arena — Benchmark and compare multiple models (OpenRouter & Groq LPU) on the exact same prompt.
"""

import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from .banner import (
    RESET, BOLD, DIM, CYAN, AMBER, CRIMSON, GOLD, GREEN, PURPLE, GRAY, WHITE, DARK_GRAY, BLUE,
    print_header, print_divider
)
from .client import OpenRouterClient, GroqClient, get_client
from .config import get_api_key
from .models import ModelInfo

class ModelArena:
    def __init__(
        self,
        default_client: Any,
        openrouter_client: Optional[OpenRouterClient] = None,
        groq_client: Optional[GroqClient] = None
    ):
        self.default_client = default_client
        self.openrouter_client = openrouter_client
        self.groq_client = groq_client

        # Discover or initialize clients if available
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

        # If passed default_client was one of them, ensure set
        if isinstance(self.default_client, OpenRouterClient):
            self.openrouter_client = self.default_client
        elif isinstance(self.default_client, GroqClient):
            self.groq_client = self.default_client

    def _get_all_contenders(self) -> List[ModelInfo]:
        """Aggregate available models from both OpenRouter and Groq."""
        contenders: List[ModelInfo] = []
        if self.openrouter_client:
            for m in self.openrouter_client.get_models():
                contenders.append(m)
        if self.groq_client:
            for m in self.groq_client.get_models():
                # Filter out pure guardrail or whisper models from arena text comparisons
                if m.category not in ("guardrail", "speech"):
                    contenders.append(m)
        return contenders

    def run(self, preset_prompt: Optional[str] = None) -> None:
        """Run interactive Model Arena session."""
        print_header("THE FORGE ARENA", "Cross-Provider Benchmark: OpenRouter Free Tier ⚔️ Groq LPUs")
        print(f"{DARK_GRAY}Test the exact same prompt against multiple models to evaluate latency, throughput, and reasoning depth.{RESET}\n")

        # 1. Fetch available contender models
        contenders = self._get_all_contenders()
        if not contenders:
            if hasattr(self.default_client, "get_models"):
                contenders = self.default_client.get_models()

        if not contenders:
            print(f"{CRIMSON}No models available for arena comparison.{RESET}")
            return

        print(f"{GOLD}{BOLD}Available Contenders:{RESET}")
        for idx, m in enumerate(contenders, 1):
            prov_tag = f"{GOLD}[⚡ Groq]{RESET}" if m.provider == "groq" else f"{BLUE}[🌐 OR]{RESET}"
            print(f"  {CYAN}[{idx:2d}]{RESET} {prov_tag} {WHITE}{m.name:<32}{RESET} {DARK_GRAY}{m.id:<38}{RESET} {PURPLE}[{m.formatted_ctx}]{RESET}")

        # 2. Select contenders
        print(f"\n{AMBER}Select 2 to 4 contenders by number (comma-separated, e.g. 1, 2, 8):{RESET}")
        selection = input(f"{CYAN}Contenders: {RESET}").strip()
        selected_contenders: List[ModelInfo] = []
        if not selection:
            # Default: try first OpenRouter model and first Groq model if both available
            or_m = next((m for m in contenders if m.provider == "openrouter"), None)
            gr_m = next((m for m in contenders if m.provider == "groq"), None)
            if or_m and gr_m:
                selected_contenders = [or_m, gr_m]
            else:
                selected_contenders = contenders[:2]
            print(f"{GRAY}Defaulting to: {selected_contenders[0].id} vs {selected_contenders[1].id}{RESET}")
        else:
            indices = []
            for part in selection.split(","):
                part = part.strip()
                if part.isdigit() and 1 <= int(part) <= len(contenders):
                    indices.append(int(part) - 1)
            
            if len(indices) < 2:
                print(f"{AMBER}Please select at least 2 models. Using first two.{RESET}")
                selected_contenders = contenders[:2]
            else:
                selected_contenders = [contenders[i] for i in indices[:4]]

        print(f"\n{GREEN}Selected Contenders for Battle:{RESET}")
        for sc in selected_contenders:
            tag = f"{GOLD}[Groq LPU]{RESET}" if sc.provider == "groq" else f"{BLUE}[OpenRouter]{RESET}"
            print(f"  ⚔️  {tag} {BOLD}{WHITE}{sc.name}{RESET} ({sc.id})")

        # 3. Choose or enter prompt
        prompt = preset_prompt
        if not prompt:
            print(f"\n{GOLD}{BOLD}Prompt Selection:{RESET}")
            print(f"  {CYAN}[1]{RESET} Explain the fundamental differences between a process and a thread.")
            print(f"  {CYAN}[2]{RESET} Write a Python function querying a REST API with exponential backoff.")
            print(f"  {CYAN}[3]{RESET} Compose a dramatic, atmospheric monologue from a 19th-century vampire lord.")
            print(f"  {CYAN}[4]{RESET} Enter custom benchmark prompt")

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
        print(f"{AMBER}{BOLD}ARENA BENCHMARK PROMPT:{RESET} {WHITE}{prompt}{RESET}")
        print(f"{DARK_GRAY}───────────────────────────────────────────────────────────────────{RESET}\n")

        # 4. Execute Benchmark
        results = []
        messages = [{"role": "user", "content": prompt}]

        for idx, contender in enumerate(selected_contenders, 1):
            prov_label = "⚡ Groq LPU" if contender.provider == "groq" else "🌐 OpenRouter"
            print(f"\n{PURPLE}{BOLD}==================================================================={RESET}")
            print(f"{GOLD}Contender {idx}/{len(selected_contenders)}:{RESET} {BOLD}{WHITE}{contender.name}{RESET} ({contender.id}) [{prov_label}]")
            print(f"{PURPLE}==================================================================={RESET}\n")

            start_t = time.time()
            full_text = ""
            error = None

            # Route to appropriate client
            target_client = self.groq_client if (contender.provider == "groq" and self.groq_client) else self.openrouter_client
            if not target_client:
                target_client = self.default_client

            try:
                for chunk in target_client.stream_chat(messages, model=contender.id, temperature=0.7):
                    full_text += chunk
                    sys.stdout.write(chunk)
                    sys.stdout.flush()
            except Exception as e:
                error = str(e)
                print(f"\n{CRIMSON}[Error executing {contender.id}: {error}]{RESET}")

            elapsed = time.time() - start_t
            approx_tokens = int(len(full_text.split()) * 1.3)
            tok_per_sec = (approx_tokens / elapsed) if elapsed > 0 else 0

            print(f"\n\n{DARK_GRAY}Metrics: ⏱️  {elapsed:.2f}s | ~{approx_tokens} tokens | {tok_per_sec:.1f} tok/s{RESET}")

            results.append({
                "model": contender.id,
                "name": contender.name,
                "provider": contender.provider,
                "text": full_text,
                "elapsed": elapsed,
                "tokens": approx_tokens,
                "speed": tok_per_sec,
                "error": error
            })

        # 5. Display Summary Table
        print(f"\n\n{GOLD}{BOLD}╔═══════════════════════════════════════════════════════════════════════════════════════════╗{RESET}")
        print(f"{GOLD}{BOLD}║                               ARENA BENCHMARK SUMMARY                                     ║{RESET}")
        print(f"{GOLD}{BOLD}╚═══════════════════════════════════════════════════════════════════════════════════════════╝{RESET}")
        print(f" {BOLD}{'Contender Model':<36} {'Provider':<14} {'Latency':<10} {'Tokens':<10} {'Throughput':<14}{RESET}")
        print(f" {DARK_GRAY}{'─'*36} {'─'*14} {'─'*10} {'─'*10} {'─'*14}{RESET}")

        for r in results:
            m_short = r["name"][:34]
            prov_str = "⚡ Groq LPU" if r["provider"] == "groq" else "🌐 OpenRouter"
            lat_str = f"{r['elapsed']:.2f}s"
            tok_str = f"~{r['tokens']}"
            spd_str = f"{r['speed']:.1f} tok/s"
            
            spd_color = GREEN if r["speed"] > 100 else (CYAN if r["speed"] > 40 else AMBER)
            print(f" {WHITE}{m_short:<36}{RESET} {GOLD if r['provider']=='groq' else BLUE}{prov_str:<14}{RESET} {WHITE}{lat_str:<10}{RESET} {WHITE}{tok_str:<10}{RESET} {spd_color}{BOLD}{spd_str:<14}{RESET}")

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

        content = [
            f"# LLMForge Arena Benchmark Report",
            f"**Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
            f"## Benchmark Prompt",
            f"```text\n{prompt}\n```\n",
            f"## Performance Summary\n",
            f"| Contender Model | Provider | Latency | Approx Tokens | Throughput |",
            f"|---|---|---|---|---|"
        ]

        for r in results:
            prov = "Groq LPU" if r["provider"] == "groq" else "OpenRouter"
            content.append(
                f"| `{r['name']} ({r['model']})` | {prov} | {r['elapsed']:.2f}s | ~{r['tokens']} | **{r['speed']:.1f} tok/s** |"
            )

        content.append("\n## Contender Responses\n")
        for r in results:
            prov = "Groq LPU" if r["provider"] == "groq" else "OpenRouter"
            content.append(f"### {r['name']} ({r['model']}) — {prov}\n")
            if r["error"]:
                content.append(f"> ❌ Error: {r['error']}\n")
            else:
                content.append(f"{r['text']}\n")
            content.append("---\n")

        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(content))

        print(f"{GREEN}✓ Report saved to: {filepath}{RESET}")
