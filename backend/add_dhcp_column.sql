ALTER TABLE traffic_stats 
ADD COLUMN IF NOT EXISTS dhcp_packets integer DEFAULT 0;
