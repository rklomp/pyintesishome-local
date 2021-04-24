"""Basic usage example and testing of pyintesishome_local."""
import argparse
import asyncio

import aiohttp

from pyintesishome_local import IntesisHomeApi, IntesisHomeEntity


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("host", type=str, help="IP address or hostname")
    parser.add_argument("user", choices=["admin", "operator"])
    parser.add_argument("password", help="password")

    args = parser.parse_args()

    async with aiohttp.ClientSession() as session:
        api = IntesisHomeApi(session, args.host)
        if not await api.authenticate(args.user, args.password):
            print("Authentication Failed!")
            return

        intesishome = IntesisHomeEntity(api)
        await intesishome.get_datapoints()
        print(intesishome.get_fan_speed_list(None))
        print(await intesishome.get_values())
        await intesishome.set_power_on(None)
        await asyncio.sleep(10)
        await intesishome.set_power_off(None)


asyncio.run(main())
