<div align="center">

# 🚀 Ollama Benchmark Tool (OBT)

<img src="docs/assets/obt-logo.png" alt="OBT Logo" width="200"/>

### Unleash the Full Potential of Your Ollama Models

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg)](https://fastapi.tiangolo.com)
[![SvelteKit](https://img.shields.io/badge/SvelteKit-2.0%2B-FF3E00.svg)](https://kit.svelte.dev)
[![MongoDB](https://img.shields.io/badge/MongoDB-6.0%2B-47A248.svg)](https://www.mongodb.com/)
[![Made with Love](https://img.shields.io/badge/Made%20with-❤️-red.svg)](https://github.com/mikl0s/OBT)

*The ultimate benchmarking suite for Ollama models - measure, compare, and optimize your AI performance across different hardware configurations.*

[Getting Started](#getting-started) •
[Features](#features) •
[Documentation](#documentation) •
[Contributing](#contributing)

</div>

---

## 🌟 Features

- 🔍 **Comprehensive Model Discovery**
  - Automatic detection of local Ollama models
  - Support for both Windows and Linux environments

- 📊 **Advanced Benchmarking**
  - Three distinct test types for thorough evaluation
  - Real-time performance metrics
  - Resource usage tracking (CPU, GPU, RAM, VRAM)

- 💾 **Hardware Profiling**
  - Detailed system information collection
  - Cross-platform compatibility
  - Complete hardware configuration logging

- 📈 **Intuitive Dashboard**
  - Dark-themed, modern UI
  - Real-time test monitoring
  - Advanced search and filtering capabilities
  - Beautiful performance visualizations

## 🚀 Getting Started

### Quick Install

**Linux/macOS (Bash):**
```bash
curl -fsSL https://raw.githubusercontent.com/mikl0s/OBT/main/ollama-client/install.sh | sudo bash
```

**Windows (PowerShell):**
```powershell
[System.Net.WebRequest]::DefaultWebProxy.Credentials = [System.Net.CredentialCache]::DefaultCredentials; [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; iex ((New-Object System.Net.WebClient).DownloadString('https://raw.githubusercontent.com/mikl0s/OBT/main/ollama-client/install.ps1'))
```

### Prerequisites

- Linux-based operating system
- Root/sudo access
- Git

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/mikl0s/OBT.git
cd OBT
```

2. **Run the automated installer**
```bash
sudo ./install.sh
```

The installer will automatically set up:
- Python 3.10+ with required packages
- Node.js and pnpm
- Docker/Podman for MongoDB
- Ollama if not already installed

### Starting OBT

Simply run the start script:
```bash
./start.sh
```

This will:
1. Start MongoDB in a container
2. Launch the backend server
3. Start the frontend development server
4. Ensure Ollama is running

The dashboard will be available at `http://localhost:5173`

To stop all services gracefully, press `Ctrl+C` in the terminal where `start.sh` is running.

## 📖 Documentation

- [Architecture Overview](docs/architecture.md)
- [API Specification](docs/api-spec.md)
- [Setup Guide](docs/setup-guide.md)
- [Database Schema](docs/database-schema.md)

## 🔧 Development

```bash
# Install development dependencies
pnpm install

# Run tests
pnpm test

# Build for production
pnpm build
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'feat: Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.

## 🙏 Acknowledgments

- [Ollama](https://ollama.ai) for making local LLMs accessible
- All our amazing contributors

## 📬 Contact

Mikkel Georgsen - [@mikl0s](https://github.com/mikl0s)

Project Link: [https://github.com/mikl0s/OBT](https://github.com/mikl0s/OBT)

---

<div align="center">

### Made with ❤️ by [Dataløs](https://github.com/mikl0s)

<img src="docs/assets/datalos-logo.png" alt="Dataløs Logo" width="100"/>

</div>
