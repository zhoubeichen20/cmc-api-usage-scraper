import json
import os
import pickle
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


COOKIE_FIELDS = {
    "name",
    "value",
    "domain",
    "path",
    "expiry",
    "secure",
    "httpOnly",
    "sameSite",
}


@dataclass
class CookieManager:
    cookie_path: str = "cmc_session.pkl"

    def load_cookies(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.cookie_path):
            raise FileNotFoundError(f"Cookie file not found: {self.cookie_path}")
        with open(self.cookie_path, "rb") as f:
            cookies = pickle.load(f)
        if not isinstance(cookies, list):
            raise ValueError("Cookie file does not contain a list of cookies")
        return cookies

    def save_cookies(self, cookies: List[Dict[str, Any]]) -> None:
        with open(self.cookie_path, "wb") as f:
            pickle.dump(cookies, f)

    def validate_cookies(self, cookies: Optional[List[Dict[str, Any]]] = None) -> bool:
        if cookies is None:
            cookies = self.load_cookies()
        now = int(time.time())
        for cookie in cookies:
            expiry = cookie.get("expiry")
            if isinstance(expiry, (int, float)) and expiry < now:
                return False
        return True

    def inject_cookies(self, driver, cookies: Optional[List[Dict[str, Any]]] = None) -> None:
        if cookies is None:
            cookies = self.load_cookies()
        for cookie in cookies:
            filtered = {k: v for k, v in cookie.items() if k in COOKIE_FIELDS}
            if "sameSite" in filtered and filtered["sameSite"] not in {"Lax", "Strict", "None"}:
                filtered.pop("sameSite", None)
            driver.add_cookie(filtered)

    @staticmethod
    def from_json_file(path: str) -> List[Dict[str, Any]]:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise ValueError("JSON cookie file must be a list of cookies")
        return data
