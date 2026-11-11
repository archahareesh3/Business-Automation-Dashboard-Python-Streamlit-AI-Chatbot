-- Enterprise Automation Platform - Supabase PostgreSQL schema
-- Run in Supabase SQL Editor.
-- Includes tenant isolation keys, primary/foreign keys, timestamps and indexes.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- 1. Organizations (tenant boundary)
CREATE TABLE IF NOT EXISTS public.organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 2. Organization members (Supabase Auth users)
CREATE TABLE IF NOT EXISTS public.organization_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    role TEXT NOT NULL DEFAULT 'employee'
        CHECK (role IN ('owner', 'admin', 'manager', 'employee')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (organization_id, user_id),
    UNIQUE (id, organization_id)
);

-- 3. Products / inventory
CREATE TABLE IF NOT EXISTS public.products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    sku TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    category TEXT,
    unit_price NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (unit_price >= 0),
    cost_price NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (cost_price >= 0),
    stock_quantity INTEGER NOT NULL DEFAULT 0 CHECK (stock_quantity >= 0),
    reorder_level INTEGER NOT NULL DEFAULT 10 CHECK (reorder_level >= 0),
    status TEXT NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'inactive', 'discontinued')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (organization_id, sku),
    UNIQUE (id, organization_id)
);

-- 4. Customers
CREATE TABLE IF NOT EXISTS public.customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    first_name TEXT NOT NULL,
    last_name TEXT,
    email TEXT,
    phone TEXT,
    company_name TEXT,
    address_line1 TEXT,
    address_line2 TEXT,
    city TEXT,
    state TEXT,
    postal_code TEXT,
    country TEXT DEFAULT 'India',
    customer_type TEXT NOT NULL DEFAULT 'individual'
        CHECK (customer_type IN ('individual', 'business')),
    status TEXT NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'inactive', 'blocked')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (id, organization_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS customers_org_email_unique
ON public.customers (organization_id, lower(email))
WHERE email IS NOT NULL;

-- 5. Suppliers
CREATE TABLE IF NOT EXISTS public.suppliers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    supplier_name TEXT NOT NULL,
    contact_person TEXT,
    email TEXT,
    phone TEXT,
    address_line1 TEXT,
    address_line2 TEXT,
    city TEXT,
    state TEXT,
    postal_code TEXT,
    country TEXT DEFAULT 'India',
    payment_terms TEXT,
    status TEXT NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'inactive', 'blocked')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (id, organization_id)
);

-- 6. Supplier-products junction (many-to-many)
CREATE TABLE IF NOT EXISTS public.supplier_products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    supplier_id UUID NOT NULL,
    product_id UUID NOT NULL,
    supplier_sku TEXT,
    supply_price NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (supply_price >= 0),
    lead_time_days INTEGER NOT NULL DEFAULT 0 CHECK (lead_time_days >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    FOREIGN KEY (supplier_id, organization_id)
        REFERENCES public.suppliers(id, organization_id) ON DELETE CASCADE,
    FOREIGN KEY (product_id, organization_id)
        REFERENCES public.products(id, organization_id) ON DELETE CASCADE,
    UNIQUE (supplier_id, product_id, organization_id)
);

-- 7. Orders
CREATE TABLE IF NOT EXISTS public.orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    order_number TEXT NOT NULL,
    customer_id UUID NOT NULL,
    order_date TIMESTAMPTZ NOT NULL DEFAULT now(),
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'confirmed', 'processing', 'shipped',
                          'delivered', 'cancelled', 'refunded')),
    subtotal NUMERIC(14,2) NOT NULL DEFAULT 0 CHECK (subtotal >= 0),
    tax_amount NUMERIC(14,2) NOT NULL DEFAULT 0 CHECK (tax_amount >= 0),
    shipping_amount NUMERIC(14,2) NOT NULL DEFAULT 0 CHECK (shipping_amount >= 0),
    discount_amount NUMERIC(14,2) NOT NULL DEFAULT 0 CHECK (discount_amount >= 0),
    total_amount NUMERIC(14,2) NOT NULL DEFAULT 0 CHECK (total_amount >= 0),
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    FOREIGN KEY (customer_id, organization_id)
        REFERENCES public.customers(id, organization_id),
    UNIQUE (organization_id, order_number),
    UNIQUE (id, organization_id)
);

-- 8. Order items (one order has many product lines)
CREATE TABLE IF NOT EXISTS public.order_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    order_id UUID NOT NULL,
    product_id UUID NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(12,2) NOT NULL CHECK (unit_price >= 0),
    line_total NUMERIC(14,2)
        GENERATED ALWAYS AS (quantity * unit_price) STORED,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    FOREIGN KEY (order_id, organization_id)
        REFERENCES public.orders(id, organization_id) ON DELETE CASCADE,
    FOREIGN KEY (product_id, organization_id)
        REFERENCES public.products(id, organization_id)
);

-- 9. Shipments (an order may have multiple partial shipments)
CREATE TABLE IF NOT EXISTS public.shipments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    order_id UUID NOT NULL,
    tracking_number TEXT,
    carrier TEXT,
    shipping_method TEXT,
    origin_address TEXT,
    destination_address TEXT NOT NULL,
    shipped_at TIMESTAMPTZ,
    estimated_delivery_at TIMESTAMPTZ,
    delivered_at TIMESTAMPTZ,
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'picked_up', 'in_transit', 'out_for_delivery',
                          'delivered', 'delayed', 'returned', 'cancelled')),
    shipping_cost NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (shipping_cost >= 0),
    tracking_events JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    FOREIGN KEY (order_id, organization_id)
        REFERENCES public.orders(id, organization_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS shipments_org_tracking_unique
ON public.shipments (organization_id, tracking_number)
WHERE tracking_number IS NOT NULL;

-- 10. AI agents (registered automation agents)
CREATE TABLE IF NOT EXISTS public.ai_agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    agent_name TEXT NOT NULL,
    agent_type TEXT NOT NULL,
    description TEXT,
    model_name TEXT,
    status TEXT NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'paused', 'disabled', 'error')),
    configuration JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (id, organization_id)
);

-- 11. AI agent logs (execution/audit history)
CREATE TABLE IF NOT EXISTS public.ai_agent_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    agent_id UUID NOT NULL,
    event_type TEXT NOT NULL,
    task_name TEXT,
    input_data JSONB NOT NULL DEFAULT '{}'::jsonb,
    output_data JSONB NOT NULL DEFAULT '{}'::jsonb,
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'running', 'success', 'failed', 'cancelled')),
    error_message TEXT,
    tokens_used INTEGER NOT NULL DEFAULT 0 CHECK (tokens_used >= 0),
    execution_time_ms INTEGER CHECK (execution_time_ms >= 0),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    FOREIGN KEY (agent_id, organization_id)
        REFERENCES public.ai_agents(id, organization_id) ON DELETE CASCADE
);

-- updated_at trigger function
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$;

-- Attach updated_at triggers
DO $$
DECLARE
    tbl TEXT;
BEGIN
    FOREACH tbl IN ARRAY ARRAY[
        'organizations', 'organization_members', 'products', 'customers',
        'suppliers', 'orders', 'shipments', 'ai_agents'
    ]
    LOOP
        EXECUTE format(
            'DROP TRIGGER IF EXISTS set_%I_updated_at ON public.%I',
            tbl, tbl
        );
        EXECUTE format(
            'CREATE TRIGGER set_%I_updated_at
             BEFORE UPDATE ON public.%I
             FOR EACH ROW EXECUTE FUNCTION public.set_updated_at()',
            tbl, tbl
        );
    END LOOP;
END;
$$;

-- Query-performance indexes
CREATE INDEX IF NOT EXISTS idx_products_org_stock
ON public.products (organization_id, stock_quantity);

CREATE INDEX IF NOT EXISTS idx_customers_org
ON public.customers (organization_id);

CREATE INDEX IF NOT EXISTS idx_suppliers_org
ON public.suppliers (organization_id);

CREATE INDEX IF NOT EXISTS idx_supplier_products_product
ON public.supplier_products (product_id, organization_id);

CREATE INDEX IF NOT EXISTS idx_orders_org_status_date
ON public.orders (organization_id, status, order_date DESC);

CREATE INDEX IF NOT EXISTS idx_orders_customer
ON public.orders (customer_id, organization_id);

CREATE INDEX IF NOT EXISTS idx_order_items_order
ON public.order_items (order_id, organization_id);

CREATE INDEX IF NOT EXISTS idx_shipments_order
ON public.shipments (order_id, organization_id);

CREATE INDEX IF NOT EXISTS idx_shipments_org_status
ON public.shipments (organization_id, status);

CREATE INDEX IF NOT EXISTS idx_ai_agents_org_status
ON public.ai_agents (organization_id, status);

CREATE INDEX IF NOT EXISTS idx_ai_agent_logs_agent_created
ON public.ai_agent_logs (agent_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_ai_agent_logs_org_created
ON public.ai_agent_logs (organization_id, created_at DESC);

-- Enable RLS. Add organization-member policies before exposing tables to clients.
ALTER TABLE public.organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.organization_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.products ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.suppliers ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.supplier_products ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.order_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.shipments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ai_agents ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ai_agent_logs ENABLE ROW LEVEL SECURITY;

-- Note: No permissive client policies are created here intentionally.
-- Configure policies based on your membership/role model before client access.
-- Backend service-role operations bypass RLS; never expose service-role keys.
