import os

root_env = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
print(f"Checking file: {root_env}")

if not os.path.exists(root_env):
    print("FATAL: .env file does not exist!")
else:
    with open(root_env, 'r') as f:
        lines = f.readlines()
        
    print(f"Total lines: {len(lines)}")
    for line in lines:
        if line.strip().startswith("VITE_SUPABASE_URL") or line.strip().startswith("SUPABASE_URL"):
            print(f"URL Config: {line.strip()[:30]}...")
        if "KEY" in line:
            parts = line.strip().split('=', 1)
            if len(parts) == 2:
                key = parts[0]
                val = parts[1]
                if "dummy" in val or "here" in val or "placeholder" in val:
                    print(f"VIOLATION: {key} STILL HAS PLACEHOLDER: {val}")
                else:
                    print(f"OK: {key} appears to be set (Len: {len(val)})")
