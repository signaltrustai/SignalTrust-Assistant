# SignalTrust Assistant — Local Setup

## 1. Create a Virtual Environment

```bash
python3 -m venv .venv
```

## 2. Activate the Virtual Environment

**Windows (PowerShell):**

```powershell
.\.venv\Scripts\Activate.ps1
```

**Mac / Linux:**

```bash
source .venv/bin/activate
```

## 3. Install Requirements

```bash
pip install -r requirements.txt
```

## 4. Run the Assistant

There are several ways to run the assistant:

```bash
python -m assistant
```

```bash
python -m assistant.cli
```

```bash
python run.py
```

**PowerShell:**

```powershell
./run.ps1
```

**Bash:**

```bash
./run.sh
```
