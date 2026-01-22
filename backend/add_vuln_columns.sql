-- Add columns for OS detection and Vulnerabilities
ALTER TABLE scan_results
ADD COLUMN IF NOT EXISTS os_details text,
ADD COLUMN IF NOT EXISTS vulnerabilities jsonb;
