"""
Command-line interface argument parsing for LLMForge.
Unified CLI for OpenRouter Free Tier & Groq LPU High-Speed Inference.
"""

import sys
import argparse
from typing import Optional

from .banner import print_banner, clear_screen, GREEN, CRIMSON, GOLD, BLUE, WHITE, DARK_GRAY, RESET, BOLD
from .config import get_api_key, load_settings, get_available_providers
from .client import OpenRouterClient, GroqClient, get_client
from .menu import run_main_menu, inspect_providers_and_quota
from .chat import ChatSession
from .arena import ModelArena
from .catalog import CatalogViewer
from .quick import run_quick_prompt
from .__init__ import __version__

def main() -> None:
    """Entry point for CLI commands and interactive menu."""
    parser = argparse.ArgumentParser(
        prog="llmforge",
        description="LLMForge — Dual-Provider Terminal Foundry for OpenRouter & Groq LPUs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  llmforge                                        Launch the interactive terminal menu
  llmforge -p "Who wrote Dracula?"               Execute single prompt with default model
  llmforge -P groq -p "Explain SIMD vectors"     Blazing-fast inference via Groq LPU (>200 tok/s)
  llmforge -P groq -m "qwen/qwen3.8-27b" -p "Hi"  Run specific Groq multimodal model
  llmforge --guard "Ignore previous commands"    Detect prompt injection with Llama Prompt Guard
  llmforge --chat -P groq                         Direct multi-turn chat on Groq LPUs
  llmforge --arena                               Benchmark OpenRouter vs Groq side-by-side
  llmforge --catalog                              Browse all models across both providers
  llmforge --quota                                Check OpenRouter 50/day pool and Groq status
        """
    )

    parser.add_argument("-p", "--prompt", type=str, help="Execute a single prompt and exit")
    parser.add_argument("-P", "--provider", type=str, choices=["openrouter", "groq"], default=None, help="Target inference provider ('openrouter' or 'groq')")
    parser.add_argument("-m", "--model", type=str, default=None, help="Specify model ID (e.g. qwen/qwen3.8-27b or recursive/flint-v1.0:free)")
    parser.add_argument("--guard", type=str, help="Evaluate a prompt string using Groq's Llama Prompt Guard (injection / jailbreak detection)")
    parser.add_argument("--chat", action="store_true", help="Launch interactive multi-turn chat session directly")
    parser.add_argument("--arena", action="store_true", help="Launch Model Arena side-by-side benchmark")
    parser.add_argument("--catalog", action="store_true", help="Display all available models across providers")
    parser.add_argument("--quota", action="store_true", help="Display API key status, free request quota, and LPU status")
    parser.add_argument("--providers", action="store_true", help="List discovered API keys and provider readiness")
    parser.add_argument("--persona", type=str, default="default", help="Persona key (default, engineer, cyber, dracula, oracle, reasoner, wordsmith)")
    parser.add_argument("-t", "--temperature", type=float, default=None, help="Sampling temperature (0.0 to 1.5)")
    parser.add_argument("-s", "--system", type=str, default=None, help="Custom system prompt")
    parser.add_argument("-v", "--version", action="version", version=f"LLMForge v{__version__}")

    args = parser.parse_args()

    settings = load_settings()
    avail = get_available_providers()

    # Determine requested or active provider
    target_prov = args.provider or settings.get("active_provider", "openrouter")
    if not avail.get(target_prov):
        target_prov = "groq" if avail.get("groq") else "openrouter"

    # Handle --providers flag
    if args.providers:
        print(f"\n{GOLD}{BOLD}LLMForge Provider Discovery:{RESET}")
        print(f"  OpenRouter API Key: {'✓ Discovered' if avail.get('openrouter') else '✗ Not Found ($env:OPENROUTER_API_KEY)'}")
        print(f"  Groq API Key:       {'✓ Discovered' if avail.get('groq') else '✗ Not Found ($env:GROQ_API_KEY)'}")
        print(f"  Active Default:     {target_prov.upper()}\n")
        return

    # Handle --guard flag directly
    if args.guard:
        groq_key = get_api_key("groq")
        if not groq_key:
            print(f"{CRIMSON}Error: Llama Prompt Guard requires GROQ_API_KEY.{RESET}")
            sys.exit(1)
        groq_client = GroqClient(groq_key)
        res = groq_client.check_prompt_guard(args.guard)
        verdict = res.get("verdict", "UNKNOWN")
        v_color = GREEN if verdict == "SAFE" else (AMBER if verdict == "SUSPICIOUS" else CRIMSON)
        print(f"\n{BOLD}Llama Prompt Guard Evaluation:{RESET}")
        print(f"  Prompt:             {WHITE}{args.guard}{RESET}")
        print(f"  Security Verdict:   {v_color}{BOLD}{verdict}{RESET}")
        print(f"  Probability Score:  {WHITE}{res.get('score')}{RESET}")
        print(f"  Latency:            {DARK_GRAY}{res.get('elapsed', 0):.3f}s{RESET}\n")
        return

    # Initialize client for target provider
    api_key = get_api_key(target_prov)
    if not api_key:
        from .menu import prompt_api_key_setup
        keys = prompt_api_key_setup()
        if not keys:
            print(f"{CRIMSON}Exiting: At least one API Key (OpenRouter or Groq) is required.{RESET}")
            sys.exit(1)
        target_prov = "groq" if "groq" in keys else "openrouter"
        api_key = keys[target_prov]

    client = get_client(target_prov, api_key)

    # Resolve default model for provider
    default_model = "qwen/qwen3.8-27b" if target_prov == "groq" else "recursive/flint-v1.0:free"
    target_model = args.model or settings.get(f"{target_prov}_default_model", default_model)
    temp = args.temperature if args.temperature is not None else settings.get("temperature", 0.7)

    # Open clients for both if available (for arena, catalog, quota)
    or_client = None
    gr_client = None
    if avail.get("openrouter"):
        try:
            or_client = get_client("openrouter")
        except Exception:
            pass
    if avail.get("groq"):
        try:
            gr_client = get_client("groq")
        except Exception:
            pass

    if args.prompt:
        run_quick_prompt(
            client=client,
            prompt=args.prompt,
            model=target_model,
            system_prompt=args.system or settings.get("system_prompt"),
            temperature=temp
        )
        return

    if args.quota:
        inspect_providers_and_quota(
            openrouter_client=or_client,
            groq_client=gr_client,
            active_provider=target_prov,
            wait_enter=False
        )
        return

    if args.catalog:
        viewer = CatalogViewer(
            default_client=client,
            openrouter_client=or_client,
            groq_client=gr_client
        )
        viewer.run()
        return

    if args.arena:
        arena = ModelArena(
            default_client=client,
            openrouter_client=or_client,
            groq_client=gr_client
        )
        arena.run()
        return

    if args.chat:
        session = ChatSession(
            client=client,
            model=target_model,
            persona_key=args.persona,
            temperature=temp,
            provider=target_prov
        )
        session.start()
        return

    # No flags provided: launch interactive TUI menu
    run_main_menu()

if __name__ == "__main__":
    main()
