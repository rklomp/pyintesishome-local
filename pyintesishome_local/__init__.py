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

CMD_LOGIN = "login"
CMD_GET_INFO = "getinfo"
CMD_SET_DP_VALUE = "setdatapointvalue"
CMD_GET_DP_VALUE = "getdatapointvalue"
CMD_GET_AVAIL_DP = "getavailabledatapoints"

TEXT_VALUES_FANSPEED = {
    0: "Auto",
    1: "Speed 1",
    2: "Speed 2",
    3: "Speed 3",
    4: "Speed 4",
    5: "Speed 5",
    6: "Speed 6",
    7: "Speed 7",
    8: "Speed 8",
    9: "Speed 9",
    10: "Speed 10",
}
TEXT_VALUES_MODES = {0: "auto", 1: "heat", 2: "dry", 3: "fan", 4: "cool"}
TEXT_VALUES_ONOFF = {0: "Off", 1: "On"}
TEXT_VALUES_REMOTE = {0: "Remote Enabled", 1: "Remote Disabled"}
TEXT_VALUES_VANES = {
    0: "Auto",
    1: "Position 1",
    2: "Position 2",
    3: "Position 3",
    4: "Position 4",
    5: "Position 5",
    6: "Position 6",
    7: "Position 7",
    8: "Position 8",
    9: "Position 9",
    10: "Swing",
    11: "Swirl",
    12: "Wide",
}
ID_VALUES_FANSPEED = {v: k for k, v in TEXT_VALUES_FANSPEED.items()}
ID_VALUES_MODES = {v: k for k, v in TEXT_VALUES_MODES.items()}
ID_VALUES_ONOFF = {v: k for k, v in TEXT_VALUES_ONOFF.items()}
ID_VALUES_REMOTE = {v: k for k, v in TEXT_VALUES_REMOTE.items()}
ID_VALUES_VANES = {v: k for k, v in TEXT_VALUES_VANES.items()}

UID_MAP = {
    "on_off": {"uid": 1, "map": TEXT_VALUES_ONOFF, "unit": ""},
    "user_mode": {"uid": 2, "map": TEXT_VALUES_MODES, "unit": ""},
    "fan_speed": {"uid": 4, "map": TEXT_VALUES_FANSPEED, "unit": ""},
    "vane_up_down_position": {"uid": 5, "map": TEXT_VALUES_VANES, "unit": ""},
    "vane_left_right_position": {"uid": 6, "map": TEXT_VALUES_VANES, "unit": ""},
    "user_setpoint": {"uid": 9, "map": {}, "unit": "C"},
    "return_path_temperature": {"uid": 10, "map": {}, "unit": "C"},
    "remote_disable": {"uid": 12, "map": TEXT_VALUES_REMOTE, "unit": ""},
    "on_time": {"uid": 13, "map": {}, "unit": "h"},
    "alarm_status": {"uid": 14, "map": TEXT_VALUES_ONOFF, "unit": ""},
    "error_code": {"uid": 15, "map": {}, "unit": ""},
    "quiet_mode": {"uid": 34, "map": TEXT_VALUES_ONOFF, "unit": ""},
    "min_temperature_setpoint": {"uid": 35, "map": {}, "unit": "C"},
    "max_temperature_setpoint": {"uid": 36, "map": {}, "unit": "C"},
    "outdoor_temperature": {"uid": 37, "map": {}, "unit": "C"},
    "climate_working_mode": {"uid": 42, "map": {}, "unit": ""},
    "maintenance_time": {"uid": 181, "map": {}, "unit": "h"},
    "maintenance_config": {"uid": 182, "map": {}, "unit": "h"},
    "maintenance_filter_time": {"uid": 183, "map": {}, "unit": "h"},
    "maintenance_filter_config": {"uid": 184, "map": {}, "unit": "h"},
}


def get_uid(name: str):
    """Lookup uid using name."""
    return UID_MAP[name]["uid"]


class IntesisHomeApi:
    """API wrapper to communicate locally with IntesisHome devices."""

    def __init__(
        self,
        websession: ClientSession,
        host: str,
    ):
        self.websession: ClientSession = websession
        self.host: str = host
        self._username: str = "guest"
        self._password: str = ""
        self._session_id: str = ""

    async def authenticate(self, username: str, password: str) -> bool:
        """Authenticate using username and password."""
        try:
            response = await self._request(
                CMD_LOGIN, username=username, password=password
            )
            self._session_id = response["id"].get("sessionID")
        except IntesisHomeAuthenticationFailedException:
            return False

        self._username = username
        self._password = password
        return True

    async def _request(self, command: str, **kwargs) -> dict:
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

    async def request(self, command: str, **kwargs) -> dict:
        """Make a request."""
        try:
            return await self._request(command, **kwargs)
        except IntesisHomeUnauthenticatedException:
            # Try to reauthenticate once
            await self.authenticate(self._username, self._password)

        return await self._request(command, **kwargs)


class IntesisHomeEntity:
    """Entity to model the IntesisHome device.

    This class will be used in Home Assistant to provide a replacement controller
    for IntesisHome from https://github.com/jnimmo/pyIntesisHome/"""

    def __init__(
        self,
        api: IntesisHomeApi,
    ):
        self.is_connected = True
        self._api: IntesisHomeApi = api
        self._info: dict = {}
        self._values: dict = {}
        self._datapoints: dict = {}
        self.device_type: str = "IntesisHomeLocal"

    async def get_info(self) -> dict:
        """Get device info."""
        response = await self._api.request(CMD_GET_INFO)
        self._info = response["info"]
        return self._info

    def _value(self, name: str) -> Any:
        """Get value of based on name."""
        return self._values.get(get_uid(name))

    async def get_value(self, name: str) -> dict:
        """Get entity value by uid."""
        response = await self._api.request(CMD_GET_DP_VALUE, uid=get_uid(name))
        return response["dpval"]["value"]

    async def get_values(self) -> dict:
        """Get all entity values."""
        response = await self._api.request(CMD_GET_DP_VALUE, uid="all")
        self._values = {dpval["uid"]: dpval["value"] for dpval in response["dpval"]}
        return self._values

    async def get_datapoints(self) -> dict:
        """Get all available datapoints."""
        response = await self._api.request(CMD_GET_AVAIL_DP)
        self._datapoints = {
            dpoint["uid"]: dpoint for dpoint in response["dp"]["datapoints"]
        }
        return self._datapoints

    def _has_datapoint(self, datapoint: str):
        """Entity has a datapoint."""
        return get_uid(datapoint) in self._datapoints

    def has_setpoint_control(self, device_id) -> bool:
        """Entity supports setpoint control."""
        return self._has_datapoint("user_setpoint")

    def has_vertical_swing(self, device_id) -> bool:
        """Entity supports vertical swing."""
        return self._has_datapoint("vane_up_down_position")

    def has_horizontal_swing(self, device_id) -> bool:
        """Entity supports horizontal swing."""
        return self._has_datapoint("vane_left_right_position")

    def get_fan_speed_list(self, device_id) -> list:
        """Get possible entity fan speeds."""
        return [
            TEXT_VALUES_FANSPEED[i]
            for i in self._datapoints[get_uid("fan_speed")]["descr"]["states"]
        ]

    def get_fan_speed(self, device_id):
        """Get the entity fan speed."""
        value = self._value("fan_speed")
        return TEXT_VALUES_FANSPEED.get(value)

    async def set_fan_speed(self, device_id, speed: str) -> None:
        """Set the entity fan speed."""
        await self._api.request(
            CMD_SET_DP_VALUE,
            uid=get_uid("fan_speed"),
            value=ID_VALUES_FANSPEED.get(speed),
        )

    def get_vertical_swing(self, device_id):
        """Get the entity vertical swing."""
        value = self._value("vane_up_down_position")
        return TEXT_VALUES_VANES.get(value)

    async def set_vertical_vane(self, device_id, vane: str) -> None:
        """Set the entity vertical swing."""
        await self._api.request(
            CMD_SET_DP_VALUE,
            uid=get_uid("vane_up_down_position"),
            value=ID_VALUES_VANES.get(vane),
        )

    def get_horizontal_swing(self, device_id):
        """Get the entity horizontal swing."""
        value = self._value("vane_left_right_position")
        return TEXT_VALUES_VANES.get(value)

    async def set_horizontal_vane(self, device_id, vane: str) -> None:
        """Set the entity horizontal swing."""
        await self._api.request(
            CMD_SET_DP_VALUE,
            uid=get_uid("vane_left_right_position"),
            value=ID_VALUES_VANES.get(vane),
        )

    def get_mode_list(self, device_id) -> list:
        """Get possible entity modes."""
        return [
            TEXT_VALUES_MODES[i]
            for i in self._datapoints[get_uid("user_mode")]["descr"]["states"]
        ]

    def get_mode(self, device_id):
        """Get the entity mode."""
        value = self._value("user_mode")
        return TEXT_VALUES_MODES.get(value)

    async def set_mode(self, device_id, mode: str) -> None:
        """Set the entity mode."""
        await self._api.request(
            CMD_SET_DP_VALUE,
            uid=get_uid("user_mode"),
            value=ID_VALUES_MODES.get(mode),
        )

    def get_preset_mode(self, device_id):
        """Get the entity preset_mode."""
        return self._value("climate_working_mode")

    def is_on(self, device_id) -> bool:
        """Entity is on."""
        return bool(self._value("on_off"))

    async def set_power_on(self, device_id) -> None:
        """Turn the entity on."""
        await self._api.request(CMD_SET_DP_VALUE, uid=get_uid("on_off"), value=1)

    async def set_power_off(self, device_id) -> None:
        """Turn the entity off."""
        await self._api.request(CMD_SET_DP_VALUE, uid=get_uid("on_off"), value=0)

    def get_min_setpoint(self, device_id) -> float:
        """Get the entity minimum setpoint."""
        return int(self._value("min_temperature_setpoint")) / 10

    def get_max_setpoint(self, device_id) -> float:
        """Get the entity maximum setpoint."""
        return int(self._value("max_temperature_setpoint")) / 10

    def get_temperature(self, device_id) -> float:
        """Get the entity temperature."""
        return int(self._value("return_path_temperature")) / 10

    def get_setpoint(self, device_id) -> float:
        """Get the entity set temperature."""
        return int(self._value("user_setpoint")) / 10

    async def set_temperature(self, device_id, setpoint) -> None:
        """Set the entity temperature."""
        set_temp = int(setpoint) * 10

        await self._api.request(
            CMD_SET_DP_VALUE, uid=get_uid("user_setpoint"), value=set_temp
        )

    def get_outdoor_temperature(self, device_id):
        """Get the entity outdoor temperature."""
        return self._value("outdoor_temperature")

    def get_rssi(self, device_id):
        """Get the entity rssi."""
        return self._info.get("rssi")

    def get_run_hours(self, device_id):
        """Get the entity on time."""
        return self._value("on_time")

    def get_heat_power_consumption(self, device_id):
        """Get the entity heat power consumption."""

    def get_cool_power_consumption(self, device_id):
        """Get the entity cool power consumption."""
