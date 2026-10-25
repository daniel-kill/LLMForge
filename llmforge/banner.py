"""
Terminal styling, ANSI colors, ASCII banner, and layout formatting for LLMForge.
Supports dual-provider indicators: OpenRouter Free Tier & Groq LPU Inference.
"""

import os
import sys

# Color Palette (Forge Amber / Crimson / Gold / Cyan)
RESET = '\033[0m'
BOLD = '\033[1m'
DIM = '\033[2m'
ITALIC = '\033[3m'
UNDERLINE = '\033[4m'

# Foreground Colors
GOLD = '\033[38;5;220m'
AMBER = '\033[38;5;214m'
ORANGE = '\033[38;5;208m'
CRIMSON = '\033[38;5;196m'
ROSE = '\033[38;5;204m'
CYAN = '\033[38;5;51m'
BLUE = '\033[38;5;39m'
TEAL = '\033[38;5;44m'
GREEN = '\033[38;5;82m'
PURPLE = '\033[38;5;141m'
GRAY = '\033[38;5;244m'
DARK_GRAY = '\033[38;5;238m'
WHITE = '\033[38;5;255m'

ASCII_LOGO = f"""{CRIMSON}{BOLD}
  _     _      __  __ _____                      
 | |   | |    |  \\/  |  ___|__  _ __ __ _  ___   
 | |   | |    | |\\/| | |_ / _ \\| '__/ _` |/ _ \\  
 | |___| |___ | |  | |  _| (_) | | | (_| |  __/  
 |_____|_____||_|  |_|_|  \\___/|_|  \\__, |\\___|  
                                    |___/        {RESET}
{AMBER}{BOLD}  ⚒  OpenRouter Free-Tier & Groq LPU Foundry  ⚒{RESET}
{GRAY}  Maintained by Daniel Kill <daniel@danielkill.online>{RESET}
"""

def clear_screen() -> None:
    """Clear terminal screen in a cross-platform manner."""
    if os.name == 'nt':
        os.system('cls')
    else:
        os.system('clear')

def print_banner(
    quota_info: dict | None = None,
    current_model: str = "recursive/flint-v1.0:free",
    provider: str = "openrouter"
) -> None:
    """Print the main application banner with provider & status indicators."""
    print(ASCII_LOGO)
    
    # Status Bar
    status_parts = []
    
    # Provider badge
    if provider.lower() == "groq":
        status_parts.append(f"{GOLD}{BOLD}[⚡ Groq LPU]{RESET}")
    else:
        status_parts.append(f"{BLUE}{BOLD}[🌐 OpenRouter]{RESET}")

    # Model name
    status_parts.append(f"{CYAN}Model:{RESET} {WHITE}{current_model}{RESET}")
    
    if provider.lower() == "groq":
        status_parts.append(f"{GREEN}⚡ Ultra-Fast LPU Hardware (~220+ tok/s){RESET}")
        status_parts.append(f"{PURPLE}[LPU Tier]{RESET}")
    else:
        if quota_info and quota_info.get("provider") == "openrouter":
            used = quota_info.get("used", 0)
            limit = quota_info.get("limit", 50)
            remaining = quota_info.get("remaining", max(0, limit - used))
            ratio_color = GREEN if remaining > 15 else (AMBER if remaining > 5 else CRIMSON)
            status_parts.append(f"{ratio_color}Daily Quota: {remaining}/{limit} left ({used} used){RESET}")
            if quota_info.get("is_free_tier"):
                status_parts.append(f"{PURPLE}[Free Account]{RESET}")
        else:
            status_parts.append(f"{AMBER}Free-Tier Mode (50/day){RESET}")

    bar = f"{DARK_GRAY}───┤ {RESET}" + f" {DARK_GRAY}|{RESET} ".join(status_parts) + f" {DARK_GRAY}├───{RESET}"
    print(bar)
    print()

def print_header(title: str, subtitle: str = "") -> None:
    """Print a section header with accent box."""
    print()
    print(f"{CRIMSON}{BOLD}┌──[ {AMBER}{title}{CRIMSON} ]{RESET}")
    if subtitle:
        print(f"{CRIMSON}│  {GRAY}{subtitle}{RESET}")
    print(f"{CRIMSON}└───{RESET}")

def print_box(text: str, title: str = "", border_color: str = CYAN) -> None:
    """Print text inside an enclosed terminal box."""
    lines = text.split('\n')
    max_len = max(len(line) for line in lines) if lines else 40
    if title:
        max_len = max(max_len, len(title) + 6)
    
    width = max_len + 4
    
    top = f"{border_color}┌"
    if title:
        top += f"─[ {BOLD}{WHITE}{title}{RESET}{border_color} ]"
        top += "─" * (width - len(title) - 6) + "┐"
    else:
        top += "─" * (width - 1) + "┐"
    
    print(top + RESET)
    for line in lines:
        padding = " " * (width - len(line) - 3)
        print(f"{border_color}│{RESET}  {line}{padding}{border_color}│{RESET}")
    print(f"{border_color}└" + "─" * (width - 1) + f"┘{RESET}")

def print_divider(label: str = "") -> None:
    """Print horizontal divider line."""
    if label:
        print(f"\n{DARK_GRAY}──────[ {AMBER}{label}{DARK_GRAY} ]" + "─" * 40 + f"{RESET}\n")
    else:
        print(f"{DARK_GRAY}" + "─" * 60 + f"{RESET}")
