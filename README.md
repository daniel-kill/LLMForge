# LLMForge ⚒️

[![License: MIT](https://img.shields.io/badge/License-MIT-amber.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![OpenRouter](https://img.shields.io/badge/OpenRouter-Free%20Tier%20Ready-crimson.svg)](https://openrouter.ai/)
[![Zero Dependencies](https://img.shields.io/badge/Dependencies-Zero%20Mandatory-success.svg)](#installation)

> **Terminal Foundry for OpenRouter's Free-Tier LLMs.**  
> An interactive terminal console, multi-turn streaming chat REPL, side-by-side benchmark arena, and live quota inspector built for developer productivity.

Created and maintained by [Daniel Kill](https://github.com/daniel-kill) (<daniel@danielkill.online>).

---

```
  _     _      __  __ _____                      
 | |   | |    |  \/  |  ___|__  _ __ __ _  ___   
 | |   | |    | |\/| | |_ / _ \| '__/ _` |/ _ \  
 | |___| |___ | |  | |  _| (_) | | | (_| |  __/  
 |_____|_____||_|  |_|_|  \___/|_|  \__, |\___|  
                                    |___/        
  ⚒  OpenRouter Free-Tier Terminal Foundry  ⚒
```

---

## ⚡ Highlights

- **Zero Mandatory External Dependencies:** Runs immediately on any machine with standard Python 3.8+ (`urllib`, `json`, `os`, `sys`).
- **Live Daily Quota Tracking:** Real-time visibility into OpenRouter's free tier allowance (50 daily requests, used, remaining, and auto-reset).
- **Dynamic Free Models Discovery:** Automatically syncs with OpenRouter's live `/api/v1/models` catalog, filtering models with `:free` tags and `$0.00` pricing.
- **Real-Time Token Streaming:** Fluid SSE-based token-by-token streaming with live generation metrics (tokens, elapsed seconds, tokens/sec).
- **The Model Arena:** Benchmark the exact same prompt against 2 to 4 free models simultaneously or sequentially with markdown report generation.
- **Expert Personas:** One-click persona switcher (Code Architect, SecOps Analyst, Gothic Lorekeeper, Concise Oracle, Deep Reasoner).
- **Cross-Platform UTF-8 & ANSI:** Fully supported on Windows Terminal (PowerShell 7 / pwsh, CMD) and Linux / WSL.

---

## 🌟 Featured OpenRouter Free Models

LLMForge dynamically surfaces and organizes what is available on OpenRouter's free tier:

| Model ID | Provider | Context Window | Modalities | Description |
| :--- | :--- | :--- | :--- | :--- |
| `recursive/flint-v1.0:free` | Recursive | 256K tokens | 💬 Text | High-performance flagship reasoning and instruction model |
| `nvidia/nemotron-3-ultra-550b-a55b:free` | NVIDIA | 1,000,000 tokens | 💬 Text | Massive 550B MoE model with deep reasoning and 1M context |
| `nvidia/nemotron-3.5-lightning:free` | NVIDIA | 1,000,000 tokens | 💬 Text | Ultra-fast throughput model with 1M token context |
| `google/gemma-4-31b-it:free` | Google | 256K tokens | 👁️ Text + Image + Video | Multimodal vision & reasoning powerhouse |
| `google/gemma-4-26b-a4b-it:free` | Google | 256K tokens | 👁️ Text + Image + Video | Efficient architecture multimodal model |
| `cohere/north-mini-code:free` | Cohere | 256K tokens | 💬 Code + Text | Specialized code generation and refactoring engine |
| `liquid/lfm-2.5-2.6b:free` | LiquidAI | 65K tokens | 💬 Text | Liquid Neural Network architecture for lightning-fast inference |
| `nvidia/nemotron-3.5-super-vl:free` | NVIDIA | 1,000,000 tokens | 👁️ Vision + Video | Long-context multimodal document and video analysis |
| `google/lyria-3-pro-preview` | Google | 1,000,000 tokens | 🔊 Audio + Speech Output | Advanced speech and audio generation model |
| `google/lyria-3-clip-preview` | Google | 1,000,000 tokens | 🔊 Audio + Speech Output | Fast audio and musical clip synthesis |
| `openrouter/free` | OpenRouter | 200K tokens | 💬 Text + Image | Auto-router delegating to available free endpoints |

---

## 🚀 Quickstart & Installation

### 1. Prerequisites
Ensure you have Python 3.8+ installed. Store your OpenRouter API key in your environment:

**Windows PowerShell:**
```powershell
$env:OPENROUTER_API_KEY = "sk-or-v1-..."
# Or persist permanently in your user profile:
[System.Environment]::SetEnvironmentVariable('OPENROUTER_API_KEY', 'sk-or-v1-...', 'User')
```

**Linux / macOS / WSL:**
```bash
export OPENROUTER_API_KEY="sk-or-v1-..."
```

*(Note: If the key is not set, LLMForge will politely prompt you on first launch and offer to save it securely to `~/.llmforge/.env`.)*

### 2. Clone & Run
```bash
git clone https://github.com/daniel-kill/LLMForge.git
cd LLMForge

# Launch interactive menu
python llmforge.py
```

Optional dependencies for enhanced styling and HTTP session caching:
```bash
pip install -r requirements.txt
```

---

## 🕹️ CLI Usage & Flags

LLMForge functions both as an interactive TUI menu and a powerful command-line utility:

```bash
# 1. Quick single prompt (streams response to stdout)
python llmforge.py -p "Who wrote Dracula?"

# 2. Specify target free model
python llmforge.py -p "Write an async HTTP retry decorator in Python" -m "cohere/north-mini-code:free"

# 3. Check live account quota & daily free request balance
python llmforge.py --quota

# 4. Jump straight into multi-turn chat session
python llmforge.py --chat

# 5. Jump into chat with a specific persona
python llmforge.py --chat --persona engineer

# 6. Launch The Model Arena side-by-side benchmark
python llmforge.py --arena

# 7. Browse the live free models catalog
python llmforge.py --catalog
```

---

## 💬 Chat Session Slash Commands

While in an interactive chat session, use slash commands to manage your workflow on the fly:

| Command | Shortcut | Description |
| :--- | :--- | :--- |
| `/model [id]` | `/m` | Switch active free model on the fly |
| `/persona [key]` | `/p` | Switch persona (engineer, cyber, dracula, oracle, reasoner, wordsmith) |
| `/system [text]` | `/s` | View or customize the system instruction |
| `/params [temp]` | — | Adjust temperature (0.0 to 1.5) |
| `/clear` | `/c` | Clear conversation context memory |
| `/save [filename]` | — | Export chat transcript to formatted Markdown |
| `/stats` | — | Display token counts, duration, and throughput metrics |
| `/help` | `/h` | View command guide |
| `/exit` | `/q` | Return to main menu |

---

## ⚔️ The Model Arena

The Model Arena lets you run an identical prompt across 2 to 4 free models to evaluate:
1. **Response Latency:** Time to first token and total completion time.
2. **Generation Throughput:** Tokens per second (tok/s).
3. **Reasoning Quality & Tone:** Compare how different architectures handle complex code, creative writing, or technical analysis.
4. **Report Export:** Automatically generate Markdown comparison tables with full responses.

---

## 📂 Project Architecture

```
LLMForge/
├── llmforge/
│   ├── __init__.py      # Package initialization & Windows UTF-8 reconfig
│   ├── banner.py        # ANSI color palettes, ASCII art, box layout
│   ├── config.py        # $env:OPENROUTER_API_KEY discovery & settings
│   ├── client.py        # OpenRouter API client (SSE streaming & retry)
│   ├── models.py        # Model catalog & modality data structures
│   ├── chat.py          # Interactive streaming chat REPL
│   ├── arena.py         # Multi-model side-by-side benchmark arena
│   ├── catalog.py       # Free models interactive browser & ping test
│   ├── personas.py      # System prompt presets (Engineer, Cyber, Dracula)
│   ├── quick.py         # Single prompt streaming executor
│   ├── menu.py          # Interactive terminal menu loop & quota monitor
│   └── cli.py           # Argument parser for CLI execution
├── llmforge.py          # Convenient top-level launcher executable
├── pyproject.toml       # Python packaging specification
├── requirements.txt     # Optional enhancement packages
├── LICENSE              # MIT License
└── README.md            # Comprehensive documentation
```

---

## 📜 License

MIT License — Copyright (c) 2026 [Daniel Kill](https://github.com/daniel-kill) (<daniel@danielkill.online>).  
All commits cryptographically signed using GPG key `0x9B542AA270F867E5`.
