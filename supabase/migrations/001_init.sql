-- Agentropy SaaS schema (Supabase Postgres).
-- Apply in the Supabase dashboard: SQL Editor -> paste -> Run.
-- The API connects with the SERVICE ROLE key (bypasses RLS); the policies
-- below are defense-in-depth for direct client access.

-- ---------------------------------------------------------------------------
-- profiles: one row per Supabase Auth user
-- ---------------------------------------------------------------------------
create table if not exists profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  email text,
  created_at timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- workspaces: a project/tenant; seats are unlimited by product decision
-- ---------------------------------------------------------------------------
create table if not exists workspaces (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null references profiles(id) on delete cascade,
  name text not null,
  created_at timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- api_keys: hashed ingest keys (plaintext shown once at creation, never stored)
-- ---------------------------------------------------------------------------
create table if not exists api_keys (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid not null references workspaces(id) on delete cascade,
  key_hash text not null,
  name text not null default 'default',
  revoked boolean not null default false,
  created_at timestamptz not null default now()
);
create index if not exists idx_api_keys_hash on api_keys(key_hash)
  where revoked = false;

-- ---------------------------------------------------------------------------
-- subscriptions: mirrored from Polar webhooks
-- ---------------------------------------------------------------------------
create table if not exists subscriptions (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid references workspaces(id) on delete set null,
  polar_customer_id text,
  polar_subscription_id text unique,
  tier text, -- 'starter' | 'pro'
  status text, -- 'active' | 'canceled' | 'past_due' | ...
  current_period_end timestamptz,
  created_at timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- usage_events: billable/plan-relevant counters per workspace
-- ---------------------------------------------------------------------------
create table if not exists usage_events (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid not null references workspaces(id) on delete cascade,
  kind text not null, -- e.g. 'insight_run', 'span_ingested'
  quantity integer not null default 1,
  at timestamptz not null default now()
);
create index if not exists idx_usage_events_ws on usage_events(workspace_id, at desc);

-- ---------------------------------------------------------------------------
-- Row Level Security (service role bypasses; clients get least privilege)
-- ---------------------------------------------------------------------------
alter table profiles enable row level security;
alter table workspaces enable row level security;
alter table api_keys enable row level security;
alter table subscriptions enable row level security;
alter table usage_events enable row level security;

create policy "users read own profile"
  on profiles for select using (auth.uid() = id);
create policy "users manage own workspaces"
  on workspaces for all using (auth.uid() = owner_id);
create policy "owners manage workspace keys"
  on api_keys for all using (
    exists (select 1 from workspaces w
            where w.id = api_keys.workspace_id and w.owner_id = auth.uid())
  );
create policy "owners read own subscriptions"
  on subscriptions for select using (
    exists (select 1 from workspaces w
            where w.id = subscriptions.workspace_id and w.owner_id = auth.uid())
  );
create policy "owners read own usage"
  on usage_events for select using (
    exists (select 1 from workspaces w
            where w.id = usage_events.workspace_id and w.owner_id = auth.uid())
  );
