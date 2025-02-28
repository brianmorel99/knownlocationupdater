"""Module is the main program for Named Locations.

This module contains a FastAPI server that accepts incomming requests to
the root path from DDNS functions on routers to automate the updating of
Microsoft Named Locations for locations with DHCP.  It connects to
Microsoft Azure with the Python Graph SDK.

"""

from __future__ import annotations

import asyncio
import logging

import uvicorn
from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from uvicorn.config import LOGGING_CONFIG

import routes

app = FastAPI()
templates = Jinja2Templates(directory="templates")

env_var_loaded = (
    routes.ddns_username is None
    or routes.ddns_password is None
    or routes.admin_password is None
    or routes.admin_username is None
)

app.include_router(routes.my_router)


async def main() -> None:
    """Run the program.

    This main function is the base function for running the program.

    """
    LOGGING_CONFIG["formatters"]["default"]["fmt"] = "%(asctime)s [%(name)s] %(levelprefix)s %(message)s"
    LOGGING_CONFIG["formatters"]["access"]["fmt"] = (
        '%(asctime)s [%(name)s] %(levelprefix)s %(client_addr)s - "%(request_line)s" %(status_code)s'
    )
    config = uvicorn.Config("main:app", port=8080, log_level="info")
    server = uvicorn.Server(config)

    logger: logging.Logger = logging.getLogger("uvicorn.error")

    if env_var_loaded:
        logger.error("Required Environment Variables Not Set")
    else:
        await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
