"""A python3 library to communicate locally with IntesisHome devices

Source: https://github.com/rklomp/pyintesishome-local
"""
from typing import Any

from aiohttp import ClientSession

from .exceptions import (
    IntesisHomeAuthenticationFailedException,
    IntesisHomeException,
    IntesisHomeUnauthenticatedException,
)

API_URL = "api.cgi"
DATA_URL = "js/data/data.json"


class IntesisHomeApi:
    """API wrapper to communicate locally with IntesisHome devices."""

    def __init__(
        self,
        websession: ClientSession,
        host: str,
    ):
        self.websession = websession
        self.host = host
        self.username = "guest"
        self.password = None
        self._session_id = None

    async def authenticate(self, username: str, password: str) -> bool:
        """Authenticate using username and password."""
        try:
            response = await self.request("login", username=username, password=password)
            self._session_id = response["id"].get("sessionID")
        except IntesisHomeAuthenticationFailedException:
            return False

        return True

    async def request(self, command: str, **kwargs) -> Any:
        """Make a request."""
        payload = {
            "command": command,
            "data": {"sessionID": self._session_id, **kwargs},
        }

        response = await self.websession.post(
            f"http://{self.host}/{API_URL}", json=payload
        )

        if response.status != 200:
            raise IntesisHomeException("HTTP response status is unexpected (not 200)")

        json_response = await response.json()

        if not json_response["success"]:
            if json_response["error"]["code"] == 1:
                raise IntesisHomeUnauthenticatedException(
                    json_response["error"]["message"]
                )
            if json_response["error"]["code"] == 5:
                raise IntesisHomeAuthenticationFailedException(
                    json_response["error"]["message"]
                )
            raise IntesisHomeException(json_response["error"]["message"])
        return json_response.get("data")
