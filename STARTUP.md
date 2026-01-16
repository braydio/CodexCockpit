# Start the python API
---

cd backend
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
./run.sh

# Run a local Ollama model (optional)
---

# Install Ollama from https://ollama.com (or your package manager)
# Ensure the Ollama API is running on http://localhost:11434
ollama serve

# Pull a Qwen model
ollama pull qwen2.5

# Start the desktop UI (Vite)
---
cd codex-cockpit-desktop
npm install
npm run dev
