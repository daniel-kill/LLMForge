"""
Quick single prompt runner with streaming for LLMForge.
"""

import sys
import time
from typing import Optional

from .banner import (
    RESET, BOLD, CYAN, AMBER, CRIMSON, GOLD, GREEN, GRAY, WHITE, DARK_GRAY,
    print_header
)
from .client import OpenRouterClient

def run_quick_prompt(
    client: OpenRouterClient,
    prompt: Optional[str] = None,
    model: str = "recursive/flint-v1.0:free",
    system_prompt: Optional[str] = None,
    temperature: float = 0.7
) -> None:
    """Execute a single prompt and stream response to stdout."""
    if not prompt:
        print_header("QUICK SINGLE PROMPT", f"Target: {model}")
        try:
            prompt = input(f"{AMBER}Enter your prompt: {RESET}").strip()
        except (KeyboardInterrupt, EOFError):
            print()
            return

    if not prompt:
        print(f"{CRIMSON}Prompt cannot be empty.{RESET}")
        return

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    print(f"\n{DARK_GRAY}───────────────────────────────────────────────────────────{RESET}")
    print(f"{CYAN}{BOLD}Model:{RESET} {WHITE}{model}{RESET} | {CYAN}Temp:{RESET} {temperature}")
    print(f"{DARK_GRAY}───────────────────────────────────────────────────────────{RESET}\n")

    start_time = time.time()
    total_text = ""

    try:
        for chunk in client.stream_chat(messages, model=model, temperature=temperature):
            total_text += chunk
            sys.stdout.write(chunk)
            sys.stdout.flush()
    except KeyboardInterrupt:
        print(f"\n{AMBER}[Stream interrupted by user]{RESET}")

    elapsed = time.time() - start_time
    approx_tokens = int(len(total_text.split()) * 1.3)
    speed = (approx_tokens / elapsed) if elapsed > 0 else 0

    print(f"\n\n{DARK_GRAY}[⏱️  {elapsed:.2f}s | ~{approx_tokens} tokens | {speed:.1f} tok/s]{RESET}\n")
