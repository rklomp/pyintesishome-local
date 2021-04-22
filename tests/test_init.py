"""Test pyintesishome_local classes."""
import logging

import aiohttp
import pytest

import pyintesishome_local


_LOGGER = logging.getLogger(__name__)


class TestIntesisHomeApi:
    @pytest.fixture(autouse=True)
    def _setup(self, mock_aioresponse):
        self.host = "1.1.1.1"
        self.api_url = f"http://{self.host}/api.cgi"
        self.username = "admin"
        self.password = "password"
        mock_aioresponse.post(self.api_url, payload={})

    async def test_auth(self):
        session = aiohttp.ClientSession()
        pyintesishome = pyintesishome_local.IntesisHomeApi(session, self.host)
        assert pyintesishome
