"""
Interactive Multi-Turn Chat REPL for LLMForge.
Features real-time token streaming, slash commands, persona switching, and transcript exports.
"""

import os
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
from .personas import PERSONAS

class ChatSession:
    def __init__(
        self,
        client: OpenRouterClient,
        model: str = "recursive/flint-v1.0:free",
        persona_key: str = "default",
        temperature: float = 0.7,
        top_p: float = 0.95
    ):
        self.client = client
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
        
        print_header("FORGE CHAT SESSION", f"Model: {self.model} | Persona: {p_info['icon']} {p_info['name']}")
        print(f"{DARK_GRAY}Type your message and press Enter. Available commands:{RESET}")
        print(f"  {CYAN}/m{RESET} or {CYAN}/model{RESET}   - Switch free model        {CYAN}/p{RESET} or {CYAN}/persona{RESET} - Change persona")
        print(f"  {CYAN}/s{RESET} or {CYAN}/system{RESET}  - Edit system prompt       {CYAN}/c{RESET} or {CYAN}/clear{RESET}   - Clear chat history")
        print(f"  {CYAN}/save{RESET}          - Save transcript to disk   {CYAN}/stats{RESET}          - Session analytics")
        print(f"  {CYAN}/help{RESET}          - Detailed command manual   {CYAN}/q{RESET} or {CYAN}/exit{RESET}   - Return to main menu")
        print_divider()

        while True:
            try:
                prompt_label = f"{AMBER}{BOLD}You [{self.model.split('/')[-1]}]{RESET}{CYAN} ❯ {RESET}"
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
                elif cmd in ("/model", "/m"):
                    self._switch_model(arg)
                    continue
                elif cmd in ("/persona", "/p"):
                    self._switch_persona(arg)
                    continue
                elif cmd in ("/system", "/s"):
                    self._edit_system_prompt(arg)
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

    def _send_message(self, text: str) -> None:
        """Send message to model and stream response."""
        self.messages.append({"role": "user", "content": text})
        self.total_turns += 1

        # Build payload with system prompt
        full_payload = [{"role": "system", "content": self.system_prompt}] + self.messages

        print(f"\n{GREEN}{BOLD}Assistant ({self.model}){RESET}:")
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

        print(f"{DARK_GRAY}[⏱️ {elapsed:.2f}s | ~{int(approx_tokens)} tokens | {speed:.1f} tok/s]{RESET}\n")
        self.messages.append({"role": "assistant", "content": full_response})

    def _show_help(self) -> None:
        """Display slash commands manual."""
        print(f"\n{BOLD}{GOLD}Forge Chat Command Guide:{RESET}")
        print(f"  {CYAN}/model [id]{RESET}      - Switch to another model (e.g. /model google/gemma-4-31b-it:free)")
        print(f"  {CYAN}/persona [name]{RESET}  - Switch persona (default, engineer, cyber, dracula, oracle, reasoner, wordsmith)")
        print(f"  {CYAN}/system [text]{RESET}   - Set a custom system instruction")
        print(f"  {CYAN}/params [temp]{RESET}   - Adjust temperature (0.0 to 1.5, e.g. /params 0.2)")
        print(f"  {CYAN}/clear{RESET}           - Erase conversation memory")
        print(f"  {CYAN}/save [filename]{RESET} - Export dialogue to a Markdown file")
        print(f"  {CYAN}/stats{RESET}           - View session performance metrics")
        print(f"  {CYAN}/exit{RESET}            - Return to the Forge Main Menu\n")

    def _switch_model(self, model_arg: str) -> None:
        """Switch model interactively or via argument."""
        if model_arg:
            self.model = model_arg
            print(f"{GREEN}✓ Model set to: {self.model}{RESET}\n")
            return

        models = self.client.get_free_models()
        print(f"\n{GOLD}{BOLD}Select Free Model:{RESET}")
        for idx, m in enumerate(models, 1):
            is_active = f" {GREEN}*ACTIVE*{RESET}" if m.id == self.model else ""
            print(f"  {CYAN}[{idx:2d}]{RESET} {WHITE}{m.name}{RESET} {DARK_GRAY}({m.id}){RESET}{is_active}")

        choice = input(f"\n{AMBER}Enter model number (or Enter to cancel): {RESET}").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(models):
            self.model = models[int(choice) - 1].id
            print(f"{GREEN}✓ Switched model to: {self.model}{RESET}\n")
        else:
            print(f"{GRAY}Model unchanged.{RESET}\n")

    def _switch_persona(self, arg: str) -> None:
        """Switch assistant persona."""
        if arg and arg in PERSONAS:
            self.persona_key = arg
            self.system_prompt = PERSONAS[arg]["prompt"]
            print(f"{GREEN}✓ Persona switched to: {PERSONAS[arg]['icon']} {PERSONAS[arg]['name']}{RESET}\n")
            return

        print(f"\n{GOLD}{BOLD}Available Expert Personas:{RESET}")
        keys = list(PERSONAS.keys())
        for idx, k in enumerate(keys, 1):
            p = PERSONAS[k]
            is_active = f" {GREEN}*ACTIVE*{RESET}" if k == self.persona_key else ""
            print(f"  {CYAN}[{idx}]{RESET} {p['icon']} {WHITE}{p['name']}{RESET}{is_active}")
            print(f"      {GRAY}{p['desc']}{RESET}")

        choice = input(f"\n{AMBER}Select persona number (or Enter to cancel): {RESET}").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(keys):
            selected_key = keys[int(choice) - 1]
            self.persona_key = selected_key
            self.system_prompt = PERSONAS[selected_key]["prompt"]
            print(f"{GREEN}✓ Persona switched to: {PERSONAS[selected_key]['icon']} {PERSONAS[selected_key]['name']}{RESET}\n")

    def _edit_system_prompt(self, arg: str) -> None:
        """View or update system prompt."""
        if arg:
            self.system_prompt = arg
            print(f"{GREEN}✓ System prompt updated.{RESET}\n")
            return

        print(f"\n{GOLD}Current System Prompt:{RESET}")
        print(f"{GRAY}{self.system_prompt}{RESET}\n")
        new_prompt = input(f"{AMBER}Enter new prompt (or Enter to keep): {RESET}").strip()
        if new_prompt:
            self.system_prompt = new_prompt
            print(f"{GREEN}✓ System prompt updated.{RESET}\n")

    def _adjust_parameters(self, arg: str) -> None:
        """Adjust temperature and sampling params."""
        if arg:
            try:
                t = float(arg)
                if 0.0 <= t <= 2.0:
                    self.temperature = t
                    print(f"{GREEN}✓ Temperature set to {self.temperature}{RESET}\n")
                    return
            except ValueError:
                pass

        print(f"\n{GOLD}Sampling Parameters:{RESET}")
        print(f"  Temperature: {self.temperature} (0.0=deterministic, 1.0=creative)")
        print(f"  Top-P:       {self.top_p}")
        new_t = input(f"\n{AMBER}New Temperature [0.0 - 1.5] (Enter to keep): {RESET}").strip()
        if new_t:
            try:
                self.temperature = max(0.0, min(1.5, float(new_t)))
                print(f"{GREEN}✓ Temperature set to {self.temperature}{RESET}\n")
            except ValueError:
                print(f"{CRIMSON}Invalid float value.{RESET}\n")

    def _show_stats(self) -> None:
        """Display session stats."""
        duration = datetime.now() - self.session_start
        mins = int(duration.total_seconds() // 60)
        secs = int(duration.total_seconds() % 60)

        print(f"\n{GOLD}{BOLD}Session Performance Analytics:{RESET}")
        print(f"  Duration:         {mins}m {secs}s")
        print(f"  Turns Completed:  {self.total_turns}")
        print(f"  Model in Use:     {self.model}")
        print(f"  Est. Tokens:      ~{int(self.total_tokens_generated)}")
        print(f"  Active Persona:   {PERSONAS.get(self.persona_key, {}).get('name', 'Custom')}\n")

    def _save_transcript(self, custom_name: str) -> None:
        """Export conversation transcript to Markdown."""
        if not self.messages:
            print(f"{AMBER}No conversation to save.{RESET}\n")
            return

        save_dir = Path.home() / ".llmforge" / "transcripts"
        save_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if custom_name:
            filename = f"{custom_name.replace('.md', '')}_{timestamp}.md"
        else:
            filename = f"chat_{self.model.split('/')[-1]}_{timestamp}.md"

        filepath = save_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# LLMForge Chat Transcript\n\n")
            f.write(f"- **Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"- **Model:** `{self.model}`\n")
            f.write(f"- **Persona:** {PERSONAS.get(self.persona_key, {}).get('name', 'Custom')}\n")
            f.write(f"- **System Prompt:** {self.system_prompt}\n\n")
            f.write("---\n\n")

            for m in self.messages:
                role = "**User**" if m["role"] == "user" else f"**Assistant (`{self.model}`)**"
                f.write(f"### {role}\n\n{m['content']}\n\n")

        print(f"{GREEN}✓ Transcript saved to:{RESET} {WHITE}{filepath}{RESET}\n")
