-- Run this in Supabase SQL Editor before activating the n8n workflow.
-- Stores each inventory analysis result. The workflow uses service-role access
-- from n8n's server environment; never expose the service-role key in a browser.

CREATE TABLE IF NOT EXISTS public.inventory_recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL
        REFERENCES public.organizations(id) ON DELETE CASCADE,
    request_id TEXT NOT NULL,
    request_payload JSONB NOT NULL DEFAULT '{}'::JSONB,
    result JSONB NOT NULL DEFAULT '{}'::JSONB,
    status TEXT NOT NULL DEFAULT 'ok'
        CHECK (status IN ('ok', 'shortage', 'needs_review')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (organization_id, request_id)
);

CREATE INDEX IF NOT EXISTS idx_inventory_recommendations_org_created
ON public.inventory_recommendations (organization_id, created_at DESC);

ALTER TABLE public.inventory_recommendations ENABLE ROW LEVEL SECURITY;

-- Optional: add a policy for authenticated organization members if this table
-- is queried directly from the client. n8n service-role requests bypass RLS.
CREATE POLICY "Members can read their organization's inventory recommendations"
ON public.inventory_recommendations
FOR SELECT
TO authenticated
USING (
    EXISTS (
        SELECT 1
        FROM public.organization_members m
        WHERE m.organization_id = inventory_recommendations.organization_id
          AND m.user_id = auth.uid()
    )
);
