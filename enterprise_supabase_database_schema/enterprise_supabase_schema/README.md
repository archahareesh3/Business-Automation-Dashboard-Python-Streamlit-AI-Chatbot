# Enterprise Supabase Database Schema

This package contains a PostgreSQL schema for a multi-tenant enterprise automation platform.

## Files
- `enterprise_automation_schema.sql` — complete schema and indexes
- `README.md` — setup and relationship notes

## Tables
1. organizations — company/tenant records
2. organization_members — Supabase Auth users and roles
3. products — inventory catalogue and stock levels
4. customers — customer records
5. suppliers — supplier records
6. supplier_products — many-to-many supplier/product mapping
7. orders — customer orders
8. order_items — product lines in each order
9. shipments — shipment and tracking information
10. ai_agents — registered AI agents
11. ai_agent_logs — agent execution and audit history

## Relationships
- One organization has many members, products, customers, suppliers, orders, shipments and AI agents.
- One customer can place many orders.
- One order has many order_items.
- One product can appear in many order_items.
- Suppliers and products have a many-to-many relationship through supplier_products.
- One order can have multiple shipments (supports partial fulfilment).
- One AI agent has many ai_agent_logs.

Composite foreign keys include `organization_id` to prevent accidentally linking records across tenants.

## Install
1. Create a Supabase project.
2. Open **SQL Editor → New query**.
3. Paste and run `enterprise_automation_schema.sql`.
4. Verify the tables in **Table Editor**.
5. Configure Row Level Security policies for your organization membership and role rules before exposing data to client applications.

## Security notes
- RLS is enabled on all tables.
- This starter deliberately does not create broad client access policies.
- Add least-privilege policies for SELECT/INSERT/UPDATE/DELETE based on `organization_members`.
- Keep the Supabase `service_role` key on trusted servers only.
- Do not put secrets in frontend code.

## Design notes
- UUID primary keys use `gen_random_uuid()`.
- Timestamps use `TIMESTAMPTZ` and default to `now()`.
- `updated_at` is maintained by reusable PostgreSQL triggers.
- Monetary values use `NUMERIC`, not floating-point types.
- JSONB is used for agent configuration, inputs, outputs and shipment tracking events.
- This schema models product stock as a current quantity. For a larger ERP, add an inventory_movements table to maintain a full stock ledger.
