# n8n AI Inventory Management Workflow

## Included
- `ai_inventory_management_workflow.json`: importable n8n workflow
- `supabase_inventory_recommendations.sql`: table migration for saved results
- `sample_webhook_payload.json`: example POST body

## Setup
1. Run `supabase_inventory_recommendations.sql` in Supabase SQL Editor.
2. In the n8n server environment, set:
   - `SUPABASE_URL=https://YOUR_PROJECT_REF.supabase.co`
   - `SUPABASE_SERVICE_ROLE_KEY=YOUR_SERVICE_ROLE_KEY`
3. Restart n8n after adding environment variables. If your n8n deployment blocks `$env` access, replace the expressions with an n8n Header Auth credential and configure the Supabase URL in the HTTP Request nodes.
4. Import the JSON from n8n: Workflows → Import from File.
5. Confirm your existing `products` table has `organization_id`, `sku`, `name`, `stock_quantity`, `reorder_level`, and `cost_price`.
6. Activate the workflow and copy its production webhook URL.

## Request
POST JSON to `/webhook/ai-inventory-check`:
```json
{
  "organization_id": "YOUR-ORGANIZATION-UUID",
  "request_id": "optional-unique-request-id",
  "items": [
    { "sku": "SKU-1001", "requested_quantity": 30 }
  ]
}
```

## Logic
- Retrieves matching product rows scoped to `organization_id`.
- Flags missing SKUs and quantities that exceed current stock.
- Projects stock after fulfilling the request.
- Recommends replenishment to restore the configured `reorder_level`.
- Saves the analysis in `inventory_recommendations`.
- Returns the analysis as JSON.

The workflow is an importable starter. Configure secrets, test with a non-production organization, and add an authenticated webhook/API gateway before production use. Do not expose the Supabase service-role key to clients.
