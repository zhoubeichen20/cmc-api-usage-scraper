import json
import os
import pickle
import sys
from typing import List, Dict, Any


def parse_netscape(lines: List[str]) -> List[Dict[str, Any]]:
    cookies = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) != 7:
            continue
        domain, flag, path, secure, expiry, name, value = parts
        cookies.append(
            {
                "domain": domain,
                "path": path,
                "secure": secure.lower() == "true",
                "expiry": int(expiry) if expiry.isdigit() else None,
                "name": name,
                "value": value,
            }
        )
    return cookies


def parse_cookie_string(content: str) -> List[Dict[str, Any]]:
    cookies = []
    for part in content.split(";"):
        if "=" not in part:
            continue
        name, value = part.split("=", 1)
        cookies.append({"name": name.strip(), "value": value.strip()})
    return cookies


def load_cookies(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        content = f.read().strip()

    if content.startswith("["):
        data = json.loads(content)
        if not isinstance(data, list):
            raise ValueError("JSON cookie file must be a list")
        return data

    if "\t" in content:
        return parse_netscape(content.splitlines())

    return parse_cookie_string(content)


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python convert_cookies.py cookies.txt [cmc_session.pkl]")
        return 1
    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else "cmc_session.pkl"
    if not os.path.exists(input_path):
        print(f"Input file not found: {input_path}")
        return 1
    cookies = load_cookies(input_path)
    with open(output_path, "wb") as f:
        pickle.dump(cookies, f)
    print(f"Saved {len(cookies)} cookies to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
