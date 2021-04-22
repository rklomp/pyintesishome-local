from setuptools import setup

VERSION = "0.1.0"

setup(
    name="pyintesishome-local",
    version=VERSION,
    author="René Klomp",
    author_email="",
    install_requires=["aiohttp>3,<4"],
    python_requires=">=3.8",
)
