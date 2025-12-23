# Start the python API
---

cd backend
python -m venv .venv
.venv/bin/activate
pip install -r requirements.txt
./run.sh

# Start the GUI
---
cd gui
python -m http.server 8080
