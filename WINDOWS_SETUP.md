# SAHAYA - Windows Setup

## Requirements
- Windows 10/11
- Python 3.11+ (recommended)
- Node.js 18+ (recommended)
- npm
- Git (optional)

## Backend

Open PowerShell:

```powershell
cd backend
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks activation, use:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
```

Create `backend\.env` from the project's `.env.example` if present and add the required secrets.

Start the backend:

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

## Frontend

Open another PowerShell window:

```powershell
cd frontend
npm install
npm run dev
```

Then open the URL Vite prints, normally:

`http://localhost:5173`

## Important

Do NOT copy a macOS `.venv` or `node_modules` between computers. This archive intentionally excludes those directories. They must be recreated on Windows.
