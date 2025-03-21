"""Module for defining utility functions for main application.

This module contains the miscellanous functions used in the app.
"""

import base64

from fastapi import Request, Response, status

from app_config import read_config
from graph import get_location
from location import Location

bad_auth: Response = Response(
    status_code=status.HTTP_401_UNAUTHORIZED,
    content="Incorrect username or password",
    headers={"WWW-Authenticate": "Basic"},
)


async def get_all_locations() -> list[tuple[Location, Location]] | None:
    """Return a list of tuples of (2) Locations.

    This function reads in a list of Locations from the configuration
    file.  It then creates a matching Location for each from the config
    file.  It returns a list of tuples of Locations.  The two locations
    in the tuple are (1) from config file, (2) from Microsoft Graph

    Returns:
            list[tuple[Location, Location]] or None on error

    """
    config: list[Location] = read_config()

    if len(config) == 0:
        return None

    bundled_locations: list[tuple[Location, Location]] = []

    for location in config:
        m365_location = await get_location(location)
        if m365_location is not None:
            bundle = (location, m365_location)
            bundled_locations.append(bundle)
        else:
            bundle = (location, Location())
            bundled_locations.append(bundle)

    if len(bundled_locations) > 0:
        return bundled_locations
    return None


def get_location_from_config(config: list[Location], hostname: str) -> Location | None:
    """Return the Location from the list of Locations where hostname matches display_name.

    Given a list of Locations the function will return the location object
    of the Location that matches its display_name to hostname

    Args:
        config:
            A list of Locations, generally from the config file.
        hostname:
            The hostname that is being serached for.

    Returns:
            Location where hostname == location.display_name

    """
    for loc in config:
        if loc.display_name == hostname:
            return loc
    return None


async def check_authentication(request: Request, username: str, password: str) -> tuple[bool, Response | None]:
    """Check if request has the appropriate username and password.

    Checks if the passed in request has the appropriate authorization
    provided HTTP basic authentication against the passed in username
    and password

    Args:
        request:
            The incomming HTTP Request
        username:
            The username we are checking against
        password:
            The password we are checking againast

    Returns:
            True or None, depending on if it passes or fails
            Also returns a response if it failed.

    """
    auth: str | None = request.headers.get("Authorization")
    userpass: str = username + ":" + password
    userpassenc: bytes = base64.b64encode(userpass.encode("utf-8"))
    if auth == ("Basic " + str(userpassenc, "UTF-8")):
        return True, None

    return False, bad_auth
