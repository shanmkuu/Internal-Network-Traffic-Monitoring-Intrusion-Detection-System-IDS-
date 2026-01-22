-- Add missing columns for extended traffic stats
ALTER TABLE traffic_stats
ADD COLUMN IF NOT EXISTS http_packets integer DEFAULT 0,
ADD COLUMN IF NOT EXISTS https_packets integer DEFAULT 0,
ADD COLUMN IF NOT EXISTS dns_packets integer DEFAULT 0,
ADD COLUMN IF NOT EXISTS dhcp_packets integer DEFAULT 0;
