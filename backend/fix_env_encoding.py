import os

# Path to root .env
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
print(f"Fixing encoding for: {env_path}")

content = ""
decoded = False

# Method 1: Try reading as UTF-16 (PowerShell default)
try:
    with open(env_path, 'r', encoding='utf-16') as f:
        content = f.read()
    print("Detected UTF-16. Read successful.")
    decoded = True
except Exception as e:
    print(f"Not valid UTF-16: {e}")

# Method 2: Try reading as UTF-8 (just in case)
if not decoded:
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            content = f.read()
        print("Detected UTF-8 (or subset). Read successful.")
        decoded = True
    except Exception as e:
         print(f"Not valid UTF-8: {e}")

if decoded:
    # Write back as clean UTF-8
    try:
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write(content.strip()) # Strip whitespace too
        print("Success! File rewritten as UTF-8.")
    except Exception as e:
        print(f"Failed to write file: {e}")
else:
    print("FATAL: Could not read file in standard encodings.")
