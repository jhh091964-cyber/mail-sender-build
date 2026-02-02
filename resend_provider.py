import requests

RESEND_API_BASE = "https://api.resend.com"

class ResendProvider:
    def __init__(self, api_key, proxies=None, timeout=30):
        self.api_key = api_key
        self.proxies = proxies
        self.timeout = timeout

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def send_one(self, payload: dict):
        r = requests.post(
            f"{RESEND_API_BASE}/emails",
            headers=self._headers(),
            json=payload,
            proxies=self.proxies,
            timeout=self.timeout
        )
        return r.status_code, self._safe_json(r), r.text

    def send_batch(self, payload_list: list):
        r = requests.post(
            f"{RESEND_API_BASE}/emails/batch",
            headers=self._headers(),
            json=payload_list,
            proxies=self.proxies,
            timeout=self.timeout
        )
        return r.status_code, self._safe_json(r), r.text

    @staticmethod
    def _safe_json(resp):
        try:
            return resp.json()
        except Exception:
            return None