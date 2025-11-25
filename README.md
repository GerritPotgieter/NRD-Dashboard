# Install deps
## NPM stuff
```bash
npm i
```

## Python stuff
```bash
pythom -m .venv venv
./.venv/Scripts/Activate.psl
pip install -r requirements.txt
```

# Start backend server

```bash 
.venv\Scripts\python.exe -m uvicorn backend.server:app --reload --host 0.0.0.0 --port 8000
```


# Start frontend
```
cd frontend
npm start
```

