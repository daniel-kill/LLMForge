"""
Main Interactive Terminal Menu Loop for LLMForge.
"""

import os
import sys
from typing import Dict, Any, Optional

from .banner import (
    RESET, BOLD, DIM, CYAN, AMBER, CRIMSON, GOLD, GREEN, PURPLE, GRAY, WHITE, DARK_GRAY,
    print_banner, print_header, print_box, print_divider, clear_screen
)
from .client import OpenRouterClient
from .config import get_api_key, save_api_key_to_env, load_settings, save_settings
from .chat import ChatSession
from .arena import ModelArena
from .catalog import CatalogViewer
from .quick import run_quick_prompt
from .personas import PERSONAS

def prompt_api_key_setup() -> Optional[str]:
    """Interactively guide user if API key is not yet set."""
    print_header("OPENROUTER API KEY CONFIGURATION", "Key required to access free-tier models")
    print(f"{DARK_GRAY}LLMForge detects you do not have OPENROUTER_API_KEY set in your environment.{RESET}")
    print(f"You can get a free key instantly at: {CYAN}https://openrouter.ai/keys{RESET}\n")

    key = input(f"{AMBER}Paste your OpenRouter API key: {RESET}").strip()
    if not key:
        print(f"{CRIMSON}Key cannot be empty.{RESET}")
        return None

    save = input(f"{AMBER}Save this key to ~/.llmforge/.env for future sessions? [Y/n]: {RESET}").strip().lower()
    if save != "n":
        save_api_key_to_env(key)
        print(f"{GREEN}✓ Key saved to ~/.llmforge/.env{RESET}")
    else:
        os.environ["OPENROUTER_API_KEY"] = key
    return key

def inspect_account_and_quota(client: OpenRouterClient, wait_enter: bool = True) -> None:
    """Display detailed API key info and free request quota."""
    print_header("OPENROUTER ACCOUNT & QUOTA STATUS", "Live data from /api/v1/auth/key")
    print(f"{CYAN}Checking account limits...{RESET}")

    info = client.check_auth()
    if not info.get("valid"):
        print(f"{CRIMSON}✗ Failed to query account:{RESET} {info.get('error')}\n")
        if wait_enter:
            input(f"{AMBER}Press Enter to return...{RESET}")
        return

    used = info.get("used", 0)
    limit = info.get("limit", 50)
    remaining = info.get("remaining", max(0, limit - used))
    pct = (remaining / limit) * 100 if limit > 0 else 0

    ratio_color = GREEN if remaining > 15 else (AMBER if remaining > 5 else CRIMSON)

    print()
    print(f"  {BOLD}Key Label:{RESET}            {WHITE}{info.get('label', 'Default')}{RESET}")
    print(f"  {BOLD}Account Tier:{RESET}         {PURPLE}{'Free Tier Account' if info.get('is_free_tier') else 'Paid Account'}{RESET}")
    print(f"  {BOLD}Daily Free Limit:{RESET}     {CYAN}{limit} requests / 24h{RESET}")
    print(f"  {BOLD}Used Today:{RESET}           {AMBER}{used} requests{RESET}")
    print(f"  {BOLD}Remaining Quota:{RESET}      {ratio_color}{BOLD}{remaining} requests ({pct:.1f}%){RESET}")
    print()

    # ASCII Quota Bar
    bar_width = 30
    filled = int((remaining / limit) * bar_width) if limit > 0 else 0
    quota_bar = f"{GREEN}{'█' * filled}{DARK_GRAY}{'░' * (bar_width - filled)}{RESET}"
    print(f"  Quota Pool: [{quota_bar}] {remaining}/{limit}\n")

    print(f"{GRAY}Note: Free models reset their 50 request daily allowance every 24 hours.{RESET}")
    print(f"{GRAY}Endpoint tested: https://openrouter.ai/api/v1/chat/completions{RESET}\n")
    if wait_enter:
        input(f"{AMBER}Press Enter to return to menu...{RESET}")

def manage_settings(settings: Dict[str, Any], client: OpenRouterClient) -> None:
    """Adjust settings interactively."""
    while True:
        print_header("FORGE SETTINGS & SAMPLING PARAMETERS", "Adjust defaults for chat and quick prompts")
        print(f"  {CYAN}[1]{RESET} Default Model:       {WHITE}{settings.get('default_model')}{RESET}")
        print(f"  {CYAN}[2]{RESET} Temperature:         {WHITE}{settings.get('temperature')}{RESET} (0.0=precise, 1.0=creative)")
        print(f"  {CYAN}[3]{RESET} Top-P:               {WHITE}{settings.get('top_p')}{RESET}")
        print(f"  {CYAN}[4]{RESET} Max Tokens:          {WHITE}{settings.get('max_tokens')}{RESET}")
        print(f"  {CYAN}[5]{RESET} Default System Prompt: {GRAY}{settings.get('system_prompt')[:45]}...{RESET}")
        print(f"  {CYAN}[0]{RESET} Back to Main Menu")

        choice = input(f"\n{AMBER}Select option to edit [0-5]: {RESET}").strip()
        if choice == "0":
            break
        elif choice == "1":
            models = client.get_free_models()
            print(f"\n{GOLD}Choose Default Free Model:{RESET}")
            for i, m in enumerate(models, 1):
                print(f"  [{i:2d}] {m.name} ({m.id})")
            m_choice = input(f"\n{AMBER}Select number: {RESET}").strip()
            if m_choice.isdigit() and 1 <= int(m_choice) <= len(models):
                settings["default_model"] = models[int(m_choice) - 1].id
                save_settings(settings)
                print(f"{GREEN}✓ Default model saved: {settings['default_model']}{RESET}\n")
        elif choice == "2":
            val = input(f"{AMBER}New Temperature [0.0 - 1.5]: {RESET}").strip()
            try:
                settings["temperature"] = max(0.0, min(1.5, float(val)))
                save_settings(settings)
                print(f"{GREEN}✓ Temperature saved.{RESET}\n")
            except ValueError:
                print(f"{CRIMSON}Invalid float.{RESET}\n")
        elif choice == "3":
            val = input(f"{AMBER}New Top-P [0.1 - 1.0]: {RESET}").strip()
            try:
                settings["top_p"] = max(0.1, min(1.0, float(val)))
                save_settings(settings)
                print(f"{GREEN}✓ Top-P saved.{RESET}\n")
            except ValueError:
                print(f"{CRIMSON}Invalid float.{RESET}\n")
        elif choice == "4":
            val = input(f"{AMBER}Max Tokens [256 - 32768]: {RESET}").strip()
            if val.isdigit():
                settings["max_tokens"] = int(val)
                save_settings(settings)
                print(f"{GREEN}✓ Max tokens saved.{RESET}\n")
        elif choice == "5":
            val = input(f"{AMBER}New System Prompt: {RESET}").strip()
            if val:
                settings["system_prompt"] = val
                save_settings(settings)
                print(f"{GREEN}✓ System prompt saved.{RESET}\n")

def run_main_menu() -> None:
    """Launch the main terminal menu system."""
    api_key = get_api_key()
    if not api_key:
        api_key = prompt_api_key_setup()
        if not api_key:
            print(f"{CRIMSON}Exiting: OpenRouter API Key is required to run LLMForge.{RESET}")
            sys.exit(1)

    client = OpenRouterClient(api_key)
    settings = load_settings()

    # Query quota info once at startup
    quota_info = client.check_auth()

    while True:
        clear_screen()
        print_banner(quota_info, current_model=settings.get("default_model", "recursive/flint-v1.0:free"))

        print(f"{GOLD}{BOLD}FORGE OPERATIONS:{RESET}")
        print(f"  {CYAN}[1]{RESET} 💬  {WHITE}{BOLD}Interactive Chat Session{RESET}         {GRAY}(Multi-turn conversation with streaming & personas){RESET}")
        print(f"  {CYAN}[2]{RESET} ⚡  {WHITE}{BOLD}Quick Single Prompt{RESET}              {GRAY}(Ask one-off question directly with streaming){RESET}")
        print(f"  {CYAN}[3]{RESET} ⚔️   {WHITE}{BOLD}The Model Arena{RESET}                  {GRAY}(Benchmark & compare 2-4 free models side-by-side){RESET}")
        print(f"  {CYAN}[4]{RESET} 📜  {WHITE}{BOLD}Free Models Catalog & Inspector{RESET}  {GRAY}(Browse text, vision, speech, and router models){RESET}")
        print(f"  {CYAN}[5]{RESET} 🔑  {WHITE}{BOLD}API Key & Free Quota Status{RESET}      {GRAY}(Check daily free requests remaining: 48/50){RESET}")
        print(f"  {CYAN}[6]{RESET} ⚙️   {WHITE}{BOLD}Settings & Sampling Parameters{RESET}   {GRAY}(Configure default model, temperature, top-p){RESET}")
        print(f"  {CYAN}[0]{RESET} 🚪  {GRAY}Exit LLMForge{RESET}")
        print_divider()

        try:
            choice = input(f"{AMBER}{BOLD}Select Operation [0-6]: {RESET}").strip()
        except (KeyboardInterrupt, EOFError):
            print(f"\n{GRAY}Exiting LLMForge. Goodbye!{RESET}")
            break

        if choice == "0":
            print(f"\n{GOLD}Thank you for using LLMForge. Happy hacking! ⚒️{RESET}\n")
            break
        elif choice == "1":
            session = ChatSession(
                client=client,
                model=settings.get("default_model", "recursive/flint-v1.0:free"),
                temperature=settings.get("temperature", 0.7),
                top_p=settings.get("top_p", 0.95)
            )
            session.start(quota_info)
            # Refresh quota after chat
            quota_info = client.check_auth()
        elif choice == "2":
            run_quick_prompt(
                client=client,
                model=settings.get("default_model", "recursive/flint-v1.0:free"),
                system_prompt=settings.get("system_prompt"),
                temperature=settings.get("temperature", 0.7)
            )
            input(f"{AMBER}Press Enter to return to menu...{RESET}")
            quota_info = client.check_auth()
        elif choice == "3":
            arena = ModelArena(client)
            arena.run()
            input(f"{AMBER}Press Enter to return to menu...{RESET}")
            quota_info = client.check_auth()
        elif choice == "4":
            catalog = CatalogViewer(client)
            catalog.run()
        elif choice == "5":
            inspect_account_and_quota(client)
            quota_info = client.check_auth()
        elif choice == "6":
            manage_settings(settings, client)
        else:
            print(f"{CRIMSON}Invalid choice. Select 0 through 6.{RESET}")
            time.sleep(1)
