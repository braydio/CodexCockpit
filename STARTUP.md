# Start the python API
---

cd backend
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
./run.sh

# Start the desktop UI (Vite)
---
cd codex-cockpit-desktop
npm install
npm run dev
