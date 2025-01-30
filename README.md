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

- 🔍 **Multi-Client Model Management**
  - Automatic discovery of Ollama clients across your network
  - Real-time client health monitoring and status tracking
  - Intelligent cleanup of inactive clients

- 📊 **Advanced Model Organization**
  - Comprehensive model listing with size and modification tracking
  - Smart search and filtering capabilities
  - Multi-model selection for batch operations
  - Sortable columns for easy model management

- 💾 **Client Health Monitoring**
  - Automatic client registration and discovery
  - Real-time heartbeat tracking
  - Graceful handling of client disconnections
  - Cross-platform client support (Windows/Linux)

- 🚄 **Performance Testing**
  - Comprehensive benchmarking suite for model evaluation
  - Hardware-aware testing with CPU/GPU support
  - Detailed metrics including latency and tokens/second
  - Batch testing capabilities for multiple models
  - Custom prompt support for targeted testing

- 📈 **Modern User Interface**
  - Dark-themed, responsive design
  - Real-time updates without page refreshes
  - Advanced search and filtering capabilities
  - Intuitive model selection and management

- 🛠️ **Code Quality & Maintenance**
  - Comprehensive linting with ESLint, Ruff, and Black
  - Automated code formatting with Prettier and isort
  - Pre-commit hooks for code quality assurance
  - Exception handling improvements for better debugging

## 🚀 Getting Started

### Quick Start - Client Installation

#### Windows PowerShell (One-Line Install)
```powershell
irm https://raw.githubusercontent.com/mikl0s/OBT/main/ollama-client/install.ps1 | iex
```

#### Linux/macOS (One-Line Install)
```bash
curl -sSL https://raw.githubusercontent.com/mikl0s/OBT/main/ollama-client/install.sh | bash
```

### Prerequisites

#### Server Requirements
- Python 3.10 or higher
- Node.js 18 or higher
- pnpm package manager
- MongoDB 6.0 or higher

#### Client Requirements
- Python 3.10 or higher
- Ollama installed and running
- Internet connection for client registration

### Manual Installation

#### Server Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/OBT.git
   cd OBT
   ```

2. Install and start backend:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # or `venv\Scripts\activate` on Windows
   pip install -r requirements.txt
   uvicorn app.main:app --reload --port 8881
   ```

3. Install and start frontend:
   ```bash
   cd ../frontend
   pnpm install
   pnpm dev
   ```

#### Client Setup (Manual)

1. Navigate to client directory:
   ```bash
   cd ollama-client
   ```

2. Create and activate virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # or `venv\Scripts\activate` on Windows
   ```

3. Install dependencies and start client:
   ```bash
   pip install -r requirements.txt
   python main.py
   ```

4. Open your browser and navigate to `http://localhost:5173`

### Environment Variables

Create a `.env` file in both the backend and ollama-client directories:

```env
# backend/.env
PORT=8881
HOST=0.0.0.0
CLIENT_TIMEOUT_SECONDS=60

# ollama-client/.env
OBT_SERVER_URL=http://localhost:8881
OLLAMA_URL=http://localhost:11434
CLIENT_ID=my-client
HEARTBEAT_INTERVAL=10
```

See `.env.example` in each directory for all available options.

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
