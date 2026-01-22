-- Enable RLS
alter table if exists alerts enable row level security;
alter table if exists traffic_stats enable row level security;
alter table if exists system_status enable row level security;

-- Create tables
create table if not exists alerts (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz default now(),
  source_ip text not null,
  destination_ip text not null,
  protocol text,
  alert_type text,
  severity text check (severity in ('Low','Medium','High')),
  description text
);

create table if not exists traffic_stats (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz default now(),
  total_packets integer,
  tcp_packets integer,
  udp_packets integer,
  icmp_packets integer,
  http_packets integer default 0,
  https_packets integer default 0,
  dns_packets integer default 0,
  dhcp_packets integer default 0
);

create table if not exists system_status (
  id uuid primary key default gen_random_uuid(),
  updated_at timestamptz default now(),
  status text,
  monitored_interface text
);

-- RLS Policies
-- Allow authenticated users (dashboard) to read
create policy "Authenticated users can read alerts"
on alerts for select
to authenticated
using (true);

create policy "Authenticated users can read traffic_stats"
on traffic_stats for select
to authenticated
using (true);

create policy "Authenticated users can read system_status"
on system_status for select
to authenticated
using (true);

-- Allow service role (backend) to insert/update
-- Note: Service role bypasses RLS by default, but explicit policies can be good for documentation or if service_role RLS check is enabled.
-- Generally, we rely on the service_role key bypassing RLS. 
-- However, if we want to be explicit or if we use a specific user for the backend:
-- For now, we assume the backend uses the service_role key which has admin privileges.
