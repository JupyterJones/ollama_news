#!/usr/bin/env python3
import sys
import json
import requests
from icecream import ic

def main():
    if len(sys.argv) < 2:
        print("Usage: python run_prompt.py 'your prompt here' [output_file.py]")
        sys.exit(1)

    prompt = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "code/output.py"

    ic(prompt)
    ic(output_file)

    url = "http://31.97.146.63:11444/api/generate"
    payload = {
        "model": "codellama:latest",
        "prompt": prompt,
        "options": {
            "temperature": 0
        },
        "stream": False
    }

    headers = {"Content-Type": "application/json"}
    ic("Sending request...")

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        result = response.json()
        generated_code = result.get("response", "")

        if not generated_code.strip():
            print("⚠️ No code returned by the model.")
            return

        # Save code to file
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(generated_code)

        ic(f"✅ Code saved to {output_file}")
        print(f"Code saved to {output_file}")
    except Exception as e:
        ic(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
