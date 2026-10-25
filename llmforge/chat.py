"""
Interactive Multi-Turn Chat REPL for LLMForge.
Features real-time token streaming, dual-provider support (OpenRouter & Groq LPU),
slash commands, persona switching, and transcript exports.
"""

import os
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
from .personas import PERSONAS

class ChatSession:
    def __init__(
        self,
        client: Any,
        model: str = "recursive/flint-v1.0:free",
        persona_key: str = "default",
        temperature: float = 0.7,
        top_p: float = 0.95,
        provider: str = "openrouter"
    ):
        self.client = client
        self.provider = getattr(client, "provider", provider)
        self.model = model
        self.persona_key = persona_key
        self.system_prompt = PERSONAS.get(persona_key, PERSONAS["default"])["prompt"]
        self.temperature = temperature
        self.top_p = top_p
        self.messages: List[Dict[str, str]] = []
        self.session_start = datetime.now()
        self.total_tokens_generated = 0
        self.total_turns = 0

    def start(self, quota_info: Optional[Dict[str, Any]] = None) -> None:
        """Start the interactive chat loop."""
        p_info = PERSONAS.get(self.persona_key, PERSONAS["default"])
        prov_tag = f"{GOLD}[⚡ Groq LPU]{RESET}" if self.provider == "groq" else f"{BLUE}[🌐 OpenRouter]{RESET}"
        
        print_header("FORGE CHAT SESSION", f"{prov_tag} Model: {self.model} | Persona: {p_info['icon']} {p_info['name']}")
        print(f"{DARK_GRAY}Type your message and press Enter. Available commands:{RESET}")
        print(f"  {CYAN}/m{RESET} or {CYAN}/model{RESET}      - Switch model             {CYAN}/prov{RESET} or {CYAN}/provider{RESET}  - Switch provider (Groq ⇄ OpenRouter)")
        print(f"  {CYAN}/p{RESET} or {CYAN}/persona{RESET}    - Change persona           {CYAN}/c{RESET} or {CYAN}/clear{RESET}       - Clear chat history")
        print(f"  {CYAN}/s{RESET} or {CYAN}/system{RESET}     - Edit system prompt       {CYAN}/save{RESET}              - Save transcript to disk")
        print(f"  {CYAN}/guard{RESET} [text]      - Llama Prompt Guard test  {CYAN}/stats{RESET}             - Session analytics")
        print(f"  {CYAN}/help{RESET}              - Detailed command manual  {CYAN}/q{RESET} or {CYAN}/exit{RESET}       - Return to main menu")
        print_divider()

        while True:
            try:
                m_short = self.model.split('/')[-1]
                p_badge = f"{GOLD}Groq{RESET}" if self.provider == "groq" else f"{BLUE}OR{RESET}"
                prompt_label = f"{AMBER}{BOLD}You [{p_badge}:{m_short}]{RESET}{CYAN} ❯ {RESET}"
                user_input = input(prompt_label).strip()
            except (KeyboardInterrupt, EOFError):
                print(f"\n{GRAY}Session ended by user.{RESET}")
                break

            if not user_input:
                continue

            # Command handling
            if user_input.startswith("/"):
                cmd_parts = user_input.split(maxsplit=1)
                cmd = cmd_parts[0].lower()
                arg = cmd_parts[1].strip() if len(cmd_parts) > 1 else ""

                if cmd in ("/exit", "/quit", "/q"):
                    print(f"{GRAY}Returning to Forge Menu...{RESET}")
                    break
                elif cmd in ("/help", "/h"):
                    self._show_help()
                    continue
                elif cmd in ("/clear", "/c"):
                    self.messages = []
                    self.total_turns = 0
                    print(f"{GREEN}✓ Chat history cleared.{RESET}\n")
                    continue
                elif cmd in ("/provider", "/prov"):
                    self._switch_provider(arg)
                    continue
                elif cmd in ("/model", "/m", "/models"):
                    self._switch_model(arg)
                    continue
                elif cmd in ("/persona", "/p"):
                    self._switch_persona(arg)
                    continue
                elif cmd in ("/system", "/s"):
                    self._edit_system_prompt(arg)
                    continue
                elif cmd == "/guard":
                    self._test_guard(arg)
                    continue
                elif cmd == "/save":
                    self._save_transcript(arg)
                    continue
                elif cmd == "/stats":
                    self._show_stats()
                    continue
                elif cmd == "/params":
                    self._adjust_parameters(arg)
                    continue
                else:
                    print(f"{CRIMSON}Unknown command: {cmd}. Type /help for options.{RESET}\n")
                    continue

            # Execute user prompt
            self._send_message(user_input)

    def _switch_provider(self, target_prov: str) -> None:
        """Switch active provider between openrouter and groq."""
        if not target_prov:
            target_prov = "groq" if self.provider == "openrouter" else "openrouter"
        target_prov = target_prov.lower().strip()

        if target_prov not in ("openrouter", "groq"):
            print(f"{CRIMSON}Invalid provider: '{target_prov}'. Choose 'openrouter' or 'groq'.{RESET}\n")
            return

        key = get_api_key(target_prov)
        if not key:
            print(f"{CRIMSON}Cannot switch to {target_prov}: No API key found ({target_prov.upper()}_API_KEY).{RESET}\n")
            return

        try:
            new_client = get_client(target_prov, key)
            self.client = new_client
            self.provider = target_prov
            if target_prov == "groq":
                self.model = "qwen/qwen3.8-27b"
                print(f"{GREEN}✓ Switched to Groq LPU inference. Active model: {self.model}{RESET}\n")
            else:
                self.model = "recursive/flint-v1.0:free"
                print(f"{GREEN}✓ Switched to OpenRouter Free Tier. Active model: {self.model}{RESET}\n")
        except Exception as e:
            print(f"{CRIMSON}Failed to switch provider: {e}{RESET}\n")

    def _test_guard(self, text: str) -> None:
        """Run Llama Prompt Guard on user input."""
        if not text:
            text = input(f"{AMBER}Enter text for Prompt Guard evaluation: {RESET}").strip()
            if not text:
                return

        groq_key = get_api_key("groq")
        if not groq_key:
            print(f"{CRIMSON}Prompt Guard requires a Groq API Key (GROQ_API_KEY).{RESET}\n")
            return

        groq_client = GroqClient(groq_key)
        res = groq_client.check_prompt_guard(text)
        verdict = res.get("verdict", "UNKNOWN")
        v_color = GREEN if verdict == "SAFE" else (AMBER if verdict == "SUSPICIOUS" else CRIMSON)
        print(f"\n{BOLD}Llama Prompt Guard 2 22M Security Evaluation:{RESET}")
        print(f"  Verdict:  {v_color}{BOLD}{verdict}{RESET}")
        print(f"  Score:    {WHITE}{res.get('score')}{RESET}")
        print(f"  Latency:  {DARK_GRAY}{res.get('elapsed', 0):.3f}s{RESET}\n")

    def _send_message(self, text: str) -> None:
        """Send message to model and stream response."""
        self.messages.append({"role": "user", "content": text})
        self.total_turns += 1

        # Build payload with system prompt
        full_payload = [{"role": "system", "content": self.system_prompt}] + self.messages

        prov_str = "⚡ Groq" if self.provider == "groq" else "🌐 OpenRouter"
        print(f"\n{GREEN}{BOLD}Assistant ({self.model}) [{prov_str}]{RESET}:")
        full_response = ""
        start_time = time.time()

        try:
            for chunk in self.client.stream_chat(
                messages=full_payload,
                model=self.model,
                temperature=self.temperature,
                top_p=self.top_p
            ):
                full_response += chunk
                sys.stdout.write(chunk)
                sys.stdout.flush()
        except KeyboardInterrupt:
            print(f"\n{AMBER}[Generation interrupted by user]{RESET}")

        elapsed = time.time() - start_time
        print("\n")

        # Estimate tokens
        approx_tokens = len(full_response.split()) * 1.3
        self.total_tokens_generated += approx_tokens
        speed = (approx_tokens / elapsed) if elapsed > 0 else 0

        spd_color = GREEN if speed > 100 else (CYAN if speed > 40 else DARK_GRAY)
        print(f"{DARK_GRAY}[⏱️ {elapsed:.2f}s | ~{int(approx_tokens)} tokens | {spd_color}{speed:.1f} tok/s{DARK_GRAY}]{RESET}\n")
        self.messages.append({"role": "assistant", "content": full_response})

    def _show_help(self) -> None:
        """Display slash commands manual."""
        print(f"\n{BOLD}{GOLD}Forge Chat Command Guide:{RESET}")
        print(f"  {CYAN}/prov [groq|openrouter]{RESET} - Switch active inference provider")
        print(f"  {CYAN}/model [id]{RESET}             - Switch model (e.g. /model qwen/qwen3.8-27b)")
        print(f"  {CYAN}/guard [prompt]{RESET}          - Evaluate prompt using Llama Prompt Guard")
        print(f"  {CYAN}/persona [name]{RESET}         - Switch persona (default, engineer, cyber, dracula, oracle, reasoner, wordsmith)")
        print(f"  {CYAN}/system [text]{RESET}          - Set a custom system instruction")
        print(f"  {CYAN}/params [temp]{RESET}          - Adjust temperature (0.0 to 1.5, e.g. /params 0.2)")
        print(f"  {CYAN}/clear{RESET}                  - Erase conversation memory")
        print(f"  {CYAN}/save [filename]{RESET}        - Export dialogue to a Markdown file")
        print(f"  {CYAN}/stats{RESET}                  - Display tokens and timing statistics")
        print(f"  {CYAN}/exit{RESET} or {CYAN}/q{RESET}             - Return to the main menu\n")

    def _switch_model(self, model_id: str) -> None:
        """Switch active model or list options."""
        if not model_id:
            models = self.client.get_models()
            print(f"\n{GOLD}{BOLD}Available {self.provider.upper()} Models:{RESET}")
            for idx, m in enumerate(models, 1):
                print(f"  [{idx:2d}] {m.name} ({m.id}) - {m.formatted_ctx}")
            sel = input(f"\n{AMBER}Select number or type model ID: {RESET}").strip()
            if sel.isdigit() and 1 <= int(sel) <= len(models):
                self.model = models[int(sel) - 1].id
                print(f"{GREEN}✓ Model set to: {self.model}{RESET}\n")
            elif sel:
                self.model = sel
                print(f"{GREEN}✓ Model set to: {self.model}{RESET}\n")
            return

        self.model = model_id
        print(f"{GREEN}✓ Switched model to: {self.model}{RESET}\n")

    def _switch_persona(self, persona_name: str) -> None:
        """Switch assistant persona."""
        if not persona_name:
            print(f"\n{GOLD}{BOLD}Available Personas:{RESET}")
            for key, p in PERSONAS.items():
                print(f"  {CYAN}{key:<10}{RESET} {p['icon']} {WHITE}{p['name']:<22}{RESET} {GRAY}{p['desc']}{RESET}")
            sel = input(f"\n{AMBER}Select persona key (default: default): {RESET}").strip().lower()
            persona_name = sel or "default"

        if persona_name in PERSONAS:
            self.persona_key = persona_name
            self.system_prompt = PERSONAS[persona_name]["prompt"]
            p = PERSONAS[persona_name]
            print(f"{GREEN}✓ Activated persona: {p['icon']} {p['name']}{RESET}\n")
        else:
            print(f"{CRIMSON}Persona '{persona_name}' not found.{RESET}\n")

    def _edit_system_prompt(self, new_prompt: str) -> None:
        """Update system instructions."""
        if not new_prompt:
            print(f"\n{GOLD}Current System Prompt:{RESET}\n{DARK_GRAY}{self.system_prompt}{RESET}\n")
            new_prompt = input(f"{AMBER}Enter new system prompt: {RESET}").strip()
            if not new_prompt:
                return

        self.system_prompt = new_prompt
        print(f"{GREEN}✓ Custom system prompt set.{RESET}\n")

    def _adjust_parameters(self, arg: str) -> None:
        """Adjust temperature or top_p."""
        if not arg:
            print(f"\nCurrent Temperature: {self.temperature} | Top-P: {self.top_p}")
            val = input(f"{AMBER}New Temperature [0.0 - 1.5]: {RESET}").strip()
            if val:
                try:
                    self.temperature = max(0.0, min(1.5, float(val)))
                    print(f"{GREEN}✓ Temperature set to {self.temperature}{RESET}\n")
                except ValueError:
                    print(f"{CRIMSON}Invalid float.{RESET}\n")
            return

        try:
            self.temperature = max(0.0, min(1.5, float(arg)))
            print(f"{GREEN}✓ Temperature set to {self.temperature}{RESET}\n")
        except ValueError:
            print(f"{CRIMSON}Invalid float.{RESET}\n")

    def _show_stats(self) -> None:
        """Show conversation statistics."""
        elapsed = (datetime.now() - self.session_start).total_seconds()
        print(f"\n{BOLD}{GOLD}Session Analytics:{RESET}")
        print(f"  Provider:          {WHITE}{self.provider.upper()}{RESET}")
        print(f"  Active Model:      {WHITE}{self.model}{RESET}")
        print(f"  Duration:          {WHITE}{int(elapsed // 60)}m {int(elapsed % 60)}s{RESET}")
        print(f"  Dialogue Turns:    {WHITE}{self.total_turns}{RESET}")
        print(f"  Generated Tokens:  {WHITE}~{int(self.total_tokens_generated)}{RESET}")
        print(f"  Context Messages:  {WHITE}{len(self.messages)}{RESET}\n")

    def _save_transcript(self, custom_filename: str) -> None:
        """Export session dialogue to Markdown."""
        save_dir = Path.home() / ".llmforge" / "transcripts"
        save_dir.mkdir(parents=True, exist_ok=True)

        if custom_filename:
            if not custom_filename.endswith(".md"):
                custom_filename += ".md"
            filepath = save_dir / custom_filename
        else:
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            m_slug = self.model.replace("/", "_").replace(":", "_")
            filepath = save_dir / f"chat_{m_slug}_{stamp}.md"

        content = [
            f"# LLMForge Chat Transcript",
            f"- **Provider:** {self.provider.upper()}",
            f"- **Model:** `{self.model}`",
            f"- **Persona:** {self.persona_key}",
            f"- **Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
            "---",
            "## System Prompt",
            f"```text\n{self.system_prompt}\n```\n",
            "## Dialogue\n"
        ]

        for msg in self.messages:
            role_header = "### 👤 User" if msg["role"] == "user" else f"### 🤖 Assistant ({self.model})"
            content.append(f"{role_header}\n\n{msg['content']}\n")

        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(content))

        print(f"{GREEN}✓ Transcript saved to: {filepath}{RESET}\n")
