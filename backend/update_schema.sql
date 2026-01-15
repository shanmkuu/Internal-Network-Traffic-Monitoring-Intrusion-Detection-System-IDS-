-- Add columns for detailed protocol tracking
ALTER TABLE traffic_stats 
ADD COLUMN IF NOT EXISTS http_packets integer DEFAULT 0,
ADD COLUMN IF NOT EXISTS https_packets integer DEFAULT 0,
ADD COLUMN IF NOT EXISTS dns_packets integer DEFAULT 0;
