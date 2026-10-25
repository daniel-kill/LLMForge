"""
Quick single prompt runner with streaming for LLMForge.
Supports both OpenRouter and Groq LPU models.
"""

import sys
import time
from typing import Optional, Any

from .banner import (
    RESET, BOLD, CYAN, AMBER, CRIMSON, GOLD, GREEN, GRAY, WHITE, DARK_GRAY, BLUE,
    print_header
)

def run_quick_prompt(
    client: Any,
    prompt: Optional[str] = None,
    model: str = "recursive/flint-v1.0:free",
    system_prompt: Optional[str] = None,
    temperature: float = 0.7
) -> None:
    """Execute a single prompt and stream response to stdout."""
    provider_name = getattr(client, "provider", "openrouter").lower()
    prov_badge = f"{GOLD}[⚡ Groq LPU]{RESET}" if provider_name == "groq" else f"{BLUE}[🌐 OpenRouter]{RESET}"

    if not prompt:
        print_header("QUICK SINGLE PROMPT", f"{prov_badge} Target: {model}")
        try:
            prompt = input(f"{AMBER}Enter your prompt: {RESET}").strip()
        except (KeyboardInterrupt, EOFError):
            print()
            return

    if not prompt:
        print(f"{CRIMSON}Prompt cannot be empty.{RESET}")
        return

    # Check if target is a Prompt Guard model
    if "guard" in model.lower() and hasattr(client, "check_prompt_guard"):
        print(f"\n{DARK_GRAY}───────────────────────────────────────────────────────────{RESET}")
        print(f"{CYAN}{BOLD}Llama Prompt Guard Analysis:{RESET} {WHITE}{model}{RESET}")
        print(f"{DARK_GRAY}───────────────────────────────────────────────────────────{RESET}\n")
        res = client.check_prompt_guard(prompt, model=model)
        verdict = res.get("verdict", "UNKNOWN")
        v_color = GREEN if verdict == "SAFE" else (AMBER if verdict == "SUSPICIOUS" else CRIMSON)
        print(f"  {BOLD}Raw Probability Score:{RESET}  {WHITE}{res.get('score')}{RESET}")
        print(f"  {BOLD}Security Verdict:{RESET}       {v_color}{BOLD}{verdict}{RESET}")
        print(f"  {BOLD}Classification Time:{RESET}    {DARK_GRAY}{res.get('elapsed', 0):.3f}s{RESET}\n")
        return

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    print(f"\n{DARK_GRAY}───────────────────────────────────────────────────────────{RESET}")
    print(f"{prov_badge} {CYAN}{BOLD}Model:{RESET} {WHITE}{model}{RESET} | {CYAN}Temp:{RESET} {temperature}")
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

    spd_color = GREEN if speed > 100 else (CYAN if speed > 40 else DARK_GRAY)
    print(f"\n\n{DARK_GRAY}[⏱️  {elapsed:.2f}s | ~{approx_tokens} tokens | {spd_color}{speed:.1f} tok/s{DARK_GRAY}]{RESET}\n")
