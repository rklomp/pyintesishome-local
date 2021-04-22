"""Basic usage example and testing of pyintesishome_local."""
import argparse
import asyncio

import aiohttp

import pyintesishome_local


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("host", type=str, help="IP address or hostname")
    parser.add_argument("user", choices=["admin", "operator"])
    parser.add_argument("password", help="password")

    args = parser.parse_args()

    async with aiohttp.ClientSession() as session:
        intesishome = pyintesishome_local.IntesisHomeApi(session, args.host)
        print(await intesishome.request("getinfo"))
        print(await intesishome.request("getavailableservices"))
        if not await intesishome.authenticate(args.user, args.password):
            print("Authentication Failed!")
            return
        print(await intesishome.request("getavailableservices"))
        print(await intesishome.request("getavailabledatapoints"))


asyncio.run(main())
