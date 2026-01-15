import os

root_env = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
print(f"--- Key Inspection ({root_env}) ---")

if os.path.exists(root_env):
    with open(root_env, 'r') as f:
        for line in f:
            line = line.strip()
            if "SUPABASE" in line and "=" in line:
                key, val = line.split("=", 1)
                status = "Unknown"
                if "dummy" in val or "placeholder" in val or "here" in val:
                    status = f"FAIL (Placeholder detected: '{val[:15]}...')"
                elif val.startswith("ey"):
                    status = f"PASS (Valid JWT: {val[:10]}...)"
                else:
                    status = f"WARN (Unrecognized format: '{val[:10]}...')"
                
                print(f"{key}: {status}")
else:
    print("File not found.")
