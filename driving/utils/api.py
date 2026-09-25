import requests


class ApiError(RuntimeError):
    """Raised when an upstream HTTP API cannot provide a usable response."""


class Api:
    TIMEOUT = (3.05, 10)

    def get(self, url, params):
        return self._request("get", url, params)

    def post(self, url, params):
        return self._request("post", url, params)

    def _request(self, method, url, params):
        try:
            if method == "get":
                response = requests.get(url, params=params, timeout=self.TIMEOUT)
            else:
                response = requests.post(
                    url,
                    params=params,
                    json=params,
                    timeout=self.TIMEOUT,
                )
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError) as exc:
            raise ApiError(f"upstream API request failed: {exc}") from exc

        if not isinstance(payload, dict):
            raise ApiError("upstream API returned an unexpected payload")
        return payload
