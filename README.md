# Nexus Business Automation Dashboard

A responsive, multi-page Streamlit dashboard starter with reusable UI helpers.

## Included modules
- Admin overview: KPI cards, revenue trend, order mix, recent orders
- Inventory management: searchable catalogue, low-stock alerts, add-item form
- Customer management: segments, directory, add-customer form
- Logistics management: shipment tracker, delivery progress, create-shipment form
- Business analytics: selectable metric visualizations and performance snapshot
- AI assistant: OpenAI-powered chat grounded in the dashboard's illustrative demo data
- AI agent control center: agent status, configuration selection, activity log

## Run locally
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
```

## AI assistant setup
The AI assistant works without an API key in local demo mode, answering common questions from the illustrative dashboard data. To enable OpenAI-generated replies, set `OPENAI_API_KEY` in your environment, or add it to `.streamlit/secrets.toml`:

```toml
OPENAI_API_KEY = "your-api-key"
```

The repository ignores `.streamlit/secrets.toml` so this local key is not accidentally committed.

On Windows PowerShell, set the key for the current terminal before starting Streamlit:

```powershell
$env:OPENAI_API_KEY = "your-api-key"
streamlit run app.py
```

The assistant uses `gpt-4o-mini` by default. Set `OPENAI_MODEL` to use another model available to your OpenAI account. Never commit API keys or share them in chat. The assistant sends the dashboard's illustrative demo data and your conversation to OpenAI; it cannot change records or perform business actions.

The dashboard uses illustrative in-memory demo data. Forms demonstrate UI flows but do not persist records. For production, connect a database (e.g. PostgreSQL), add authentication/role-based access, validate inputs server-side, and connect carrier/AI services through secure APIs.
