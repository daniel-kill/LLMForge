"""
Command-line interface argument parsing for LLMForge.
"""

import sys
import argparse
from typing import Optional

from .banner import print_banner, clear_screen, GREEN, CRIMSON, RESET
from .config import get_api_key, load_settings
from .client import OpenRouterClient
from .menu import run_main_menu, inspect_account_and_quota
from .chat import ChatSession
from .arena import ModelArena
from .catalog import CatalogViewer
from .quick import run_quick_prompt
from .__init__ import __version__

def main() -> None:
    """Entry point for CLI commands and interactive menu."""
    parser = argparse.ArgumentParser(
        prog="llmforge",
        description="LLMForge — OpenRouter Terminal Foundry for Free-Tier Models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  llmforge                          Launch the interactive terminal menu
  llmforge -p "Who wrote Dracula?"  Quick prompt with default model (Recursive Flint)
  llmforge -p "Write quicksort" -m "google/gemma-4-31b-it:free"
  llmforge --chat                   Jump straight into interactive chat REPL
  llmforge --arena                  Launch multi-model benchmark comparison
  llmforge --catalog                Browse all available OpenRouter free models
  llmforge --quota                  Check daily free request quota (48/50)
        """
    )

    parser.add_argument("-p", "--prompt", type=str, help="Execute a single prompt and exit")
    parser.add_argument("-m", "--model", type=str, default=None, help="Specify model ID (default: recursive/flint-v1.0:free)")
    parser.add_argument("--chat", action="store_true", help="Launch interactive multi-turn chat session directly")
    parser.add_argument("--arena", action="store_true", help="Launch Model Arena side-by-side benchmark")
    parser.add_argument("--catalog", action="store_true", help="Display all available free models")
    parser.add_argument("--quota", action="store_true", help="Display API key quota and remaining daily requests")
    parser.add_argument("--persona", type=str, default="default", help="Persona key (default, engineer, cyber, dracula, oracle, reasoner, wordsmith)")
    parser.add_argument("-t", "--temperature", type=float, default=None, help="Sampling temperature (0.0 to 1.5)")
    parser.add_argument("-s", "--system", type=str, default=None, help="Custom system prompt")
    parser.add_argument("-v", "--version", action="version", version=f"LLMForge v{__version__}")

    args = parser.parse_args()

    # If any specific non-interactive or direct flag is given
    api_key = get_api_key()
    if not api_key:
        from .menu import prompt_api_key_setup
        api_key = prompt_api_key_setup()
        if not api_key:
            print(f"{CRIMSON}Exiting: OpenRouter API Key required.{RESET}")
            sys.exit(1)

    client = OpenRouterClient(api_key)
    settings = load_settings()

    target_model = args.model or settings.get("default_model", "recursive/flint-v1.0:free")
    temp = args.temperature if args.temperature is not None else settings.get("temperature", 0.7)

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
        inspect_account_and_quota(client, wait_enter=False)
        return

    if args.catalog:
        viewer = CatalogViewer(client)
        viewer.run()
        return

    if args.arena:
        arena = ModelArena(client)
        arena.run()
        return

    if args.chat:
        session = ChatSession(
            client=client,
            model=target_model,
            persona_key=args.persona,
            temperature=temp
        )
        session.start()
        return

    # No flags provided: launch interactive TUI menu
    run_main_menu()

if __name__ == "__main__":
    main()
