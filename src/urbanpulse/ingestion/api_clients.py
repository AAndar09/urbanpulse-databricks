from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class ApiClient:
    def __init__(
        self,
        base_url: str,
        timeout: int = 30,
        retries: int = 3,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        retry_strategy = Retry(
            total=retries,
            connect=retries,
            read=retries,
            status=retries,
            backoff_factor=1,
            status_forcelist=[
                429,
                500,
                502,
                503,
                504,
            ],
            allowed_methods=["GET"],
        )

        adapter = HTTPAdapter(
            max_retries=retry_strategy
        )

        self.session = requests.Session()

        self.session.mount(
            "https://",
            adapter,
        )

    def get(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> tuple[Any, int]:

        url = (
            f"{self.base_url}/"
            f"{endpoint.lstrip('/')}"
        )

        response = self.session.get(
            url,
            params=params,
            timeout=self.timeout,
        )

        response.raise_for_status()

        return (
            response.json(),
            response.status_code,
        )