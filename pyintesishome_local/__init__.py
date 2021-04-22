"""A python3 library to communicate locally with IntesisHome devices

Source: https://github.com/rklomp/pyintesishome-local
"""
from aiohttp import ClientResponse, ClientSession


API_URL = "api.cgi"


class IntesisHomeApi:
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
        self.request("login", username=username, password=password)

    async def request(self, command: str, **kwargs) -> ClientResponse:
        """Make a request."""
        payload = {"command": command, "data": kwargs}
        cookies = {"Intesis-Webserver": f"{'sessionID': {self._session_id}}"}

        return await self.websession.post(
            f"{self.host}/{API_URL}", json=payload, cookies=cookies
        )
