"""Module is the main program for Named Locations.

This module contains a FastAPI server that accepts incomming requests to
the root path from DDNS functions on routers to automate the updating of
Microsoft Named Locations for locations with DHCP.  It connects to
Microsoft Azure with the Python Graph SDK.

"""

from __future__ import annotations

import asyncio
import base64
import logging

import uvicorn
from fastapi import FastAPI, Form, Request, status
from fastapi.responses import RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from uvicorn.config import LOGGING_CONFIG

from app_config import read_config, write_config
from graph import get_current_location_ip, get_location, set_named_location_ip
from location import Location, get_location_index_by_id, get_location_index_by_name

app = FastAPI()
templates = Jinja2Templates(directory="templates")

ddns_username = ""
ddns_password = ""
admin_username = ""
admin_password = ""
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


# Main Endpoint, used by the DDNS on the routers to send messages to.
@app.get("/")
async def catch_all(request: Request, hostname: str = "", myip: str = "") -> Response:
    """Process inbound request from router with DDNS message and apply.

    Default / Root route for handling inbound messages from routers using
    DDNS protocals to notify this server of updated IP addresses.

    Args:
        request:
            The incomming HTTP Request
        hostname:
            HTTP Query parameter with the hostname of the Location to be updated.
        myip:
            HTTP Query parameter with new IP address for Location object.

    Returns:
            Response object to send back to the caller.

    """
    # Get a handle to the main logger.
    logger: logging.Logger = logging.getLogger("uvicorn.error")

    # Check to see if the request had the correct HTTP Basic Auth, if not return error.
    authorized, response = await check_authentication(request, ddns_username, ddns_password)
    if not authorized:
        logger.info("Invalid Authentication", extra=request.client.host)
        return response

    # Read the configuration from file and store as a list of Locations
    config: list[Location] = read_config()

    # Get the index to the location with the same name.
    index: int | None = get_location_index_by_name(config, hostname)

    # Get the current IP address for the Location from Microsoft
    current_ip: str | None = await get_current_location_ip(config[index])

    # Check the new IP received vs the configuration and Microsoft
    # If current_ip from Microsoft is None, Error Out
    # If it is the same between the receive IP and Microsoft, respond No Change
    # If the new IP doesn't match Microsoft, update the config and Microsoft with new IP
    if current_ip is None:
        return Response(status_code=status.HTTP_400_BAD_REQUEST, content="Invalid Data")

    if current_ip == myip:
        return Response(status_code=status.HTTP_200_OK, content="nochg " + myip)

    config[index].ip_address = myip
    write_config(config)
    resp = await set_named_location_ip(config[index], myip)
    if not resp:
        logger.error("Updating IP on Microsoft Failed", extra={"host": request.client.host, "url": request.url})
        return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content="Internal Server Error")

    return Response(status_code=status.HTTP_200_OK, content="good " + myip)


# Just an Admin landing page with links to the functions.
@app.get("/admin")
async def admin_get(request: Request) -> Response:
    """Admin function to return a response with helpful links.

    Function produces a landing page for administrators with the correct
    username and password.  Returns a response with an HTML file with
    common links

    Args:
        request:
            The incomming HTTP Request

    Returns:
            Response object to send back to the caller.

    """
    # Get a handle to the main logger.
    logger: logging.Logger = logging.getLogger("uvicorn.error")

    # Check to see if the request had the correct HTTP Basic Auth, if not return error.
    authorized, response = await check_authentication(request, admin_username, admin_password)
    if not authorized:
        logger.info("Invalid Authentication", extra={"host": request.client.host})
        return response

    # Send the template HTML file as response.
    return templates.TemplateResponse(request=request, name="admin.html", context={})


# A page for listing all Locations in the Config, including Current Microsoft Status
@app.get("/list-m365")
async def list_get_m365(request: Request) -> Response | None:
    """Return a table of Locations in an html response, including Microsoft.

    This function returns a response with a HTML page with a table of
    Locations from the current config file, and also checks Microsoft's
    current data for each location.

    Args:
        request:
            The incomming HTTP Request

    Returns:
            Response object to send back to the caller.

    """
    # Get a handle to the main logger.
    logger: logging.Logger = logging.getLogger("uvicorn.error")

    # Check to see if the request had the correct HTTP Basic Auth, if not return error.
    authorized, response = await check_authentication(request, admin_username, admin_password)
    if not authorized:
        logger.info("Invalid Authentication", extra={"host": request.client.host})
        return response

    # Get updated locations from Microsoft and Config and receive a List of Tuples
    config = await get_all_locations()

    # If the config is empty, error out
    # Else return a template passing the config as context
    if config is None:
        return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content="Internal Server Error")

    return templates.TemplateResponse(request=request, name="list_locations_m365.html", context={"configs": config})


# A page for listing all Locations in the Config, without Current Microsoft Status
@app.get("/list")
async def list_get(request: Request) -> Response | None:
    """Return a table of Locations in an html response.

    This function returns a response with a HTML page with a table of
    Locations from the current config file.

    Args:
        request:
            The incomming HTTP Request

    Returns:
            Response object to send back to the caller.

    """
    # Get a handle to the main logger.
    logger: logging.Logger = logging.getLogger("uvicorn.error")

    # Check to see if the request had the correct HTTP Basic Auth, if not return error.
    authorized, response = await check_authentication(request, admin_username, admin_password)
    if not authorized:
        logger.info("Invalid Authentication", extra={"host": request.client.host})
        return response

    # Read the config which returns a list of Locations
    configs = read_config()

    # If the config is empty, error out
    # Else return a template passing the config as context
    if configs is None:
        return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content="Internal Server Error")

    return templates.TemplateResponse(request=request, name="list_locations.html", context={"configs": configs})


@app.get("/add")
async def add_location_get(request: Request) -> Response | None:
    """Return a blank Location form for entering a new Location.

    This function returns a response with a form for adding a
    new location to the configuration.

    Args:
        request:
            The incomming HTTP Request

    Returns:
            Response object to send back to the caller.

    """
    logger: logging.Logger = logging.getLogger("uvicorn.error")

    authorized, response = await check_authentication(request, admin_username, admin_password)
    if not authorized:
        logger.info("Invalid Authentication", extra={"host": request.client.host})
        return response

    return templates.TemplateResponse(request=request, name="add_location.html")


@app.post("/add")
async def add_location_post(
    request: Request,
    location_id: str = Form(),
    display_name: str = Form(),
    ip_address: str = Form(),
    is_trusted: bool = Form(False),
    client_id: str = Form(),
    client_secret: str = Form(),
    tenant_id: str = Form(),
) -> Response:
    """Take in the submited form and create a new Location.

    This function takes the inputs from the form and creates
    a new Location object, and adds it to the configuration file.

    Args:
        request:
            The incomming HTTP Request
        location_id:
            Incomming form data
        display_name:
            Incomming form data
        ip_address:
            Incomming form data
        is_trusted:
            Incomming form data, defaults to False
        client_id:
            Incomming form data
        client_secret:
            Incomming form data
        tenant_id:
            Incomming form data

    Returns:
            Response object to redirect caller to admin page.

    """
    logger: logging.Logger = logging.getLogger("uvicorn.error")

    authorized, response = await check_authentication(request, admin_username, admin_password)
    if not authorized:
        logger.info("Invalid Authentication", extra={"host": request.client.host})
        return response

    config: list[Location] = read_config()

    loc = Location(
        location_id=location_id,
        display_name=display_name,
        ip_address=ip_address,
        is_trusted=is_trusted,
        client_id=client_id,
        client_secret=client_secret,
        tenant_id=tenant_id,
    )
    config.append(loc)
    write_config(config)

    return RedirectResponse(url="/admin", status_code=302)


@app.get("/edit/{id}")
async def edit_location_get(request: Request, id_number: str) -> Response:
    """Return a Location form filled in with current data of Location id.

    This function returns a response with a form that is pre-populated
    with Location "id" data.  This allows for editing of a Location

    Args:
        request:
            The incomming HTTP Request
        id_number:
            The Location ID of the Location to edit.

    Returns:
            Response object to send back to the caller.

    """
    logger: logging.Logger = logging.getLogger("uvicorn.error")

    authorized, response = await check_authentication(request, admin_username, admin_password)
    if not authorized:
        logger.info("Invalid Authentication", extra={"host": request.client.host})
        return response

    configs: list[Location] = read_config()

    index: int | None = get_location_index_by_id(configs, id_number)

    if index is None:
        return Response(status_code=status.HTTP_400_BAD_REQUEST, content="Invalid Data")

    action: str = "/edit/" + configs[index].location_id

    return templates.TemplateResponse(
        request=request,
        name="edit_location.html",
        context={"config": configs[index], "action": action},
    )


@app.post("/edit/{id}")
async def edit_location_post(
    request: Request,
    location_id: str = Form(),
    display_name: str = Form(),
    ip_address: str = Form(),
    is_trusted: bool = Form(False),
    client_id: str = Form(),
    client_secret: str = Form(),
    tenant_id: str = Form(),
    id_number: str = id,
) -> Response | RedirectResponse:
    """Take in the submited form and updates a Location.

    This function takes the inputs from the form and updates
    the Location with the new values.

    Args:
        request:
            The incomming HTTP Request
        location_id:
            Incomming form data
        display_name:
            Incomming form data
        ip_address:
            Incomming form data
        is_trusted:
            Incomming form data, defaults to False
        client_id:
            Incomming form data
        client_secret:
            Incomming form data
        tenant_id:
            Incomming form data
        id_number:
            The Location ID to update

    Returns:
            Response object to redirect caller to admin page.

    """
    logger: logging.Logger = logging.getLogger("uvicorn.error")

    authorized, response = await check_authentication(request, admin_username, admin_password)
    if not authorized:
        logger.info("Invalid Authentication", extra={"host": request.client.host})
        return response

    configs: list[Location] = read_config()

    index: int | None = get_location_index_by_id(configs, id_number)

    if index is None:
        logger.info("Unable to find Location by ID")
        return Response(status_code=status.HTTP_400_BAD_REQUEST, content="Invalid Data")

    logger.info(
        "Received an update request",
        extra={"location": configs[index].location_id, "old_data": configs[index]},
    )

    configs[index].location_id = location_id
    configs[index].display_name = display_name
    configs[index].ip_address = ip_address
    configs[index].is_trusted = is_trusted
    configs[index].client_id = client_id
    configs[index].client_secret = client_secret
    configs[index].tenant_id = tenant_id

    logger.info("Storing new data", extra={"new_data": configs[index]})

    write_config(configs)

    return RedirectResponse(url="/list-m365", status_code=302)


@app.get("/update/{id}")
async def update_location_get(request: Request, id_number: str = id) -> Response | RedirectResponse:
    """Update Microsoft Graph API with new Location data.

    This function takes a request with an ID and updates Microsoft's
    values for the chosen location id.

    Args:
        request:
            The incomming HTTP Request
        id_number:
            The Location ID of the Location to update.

    Returns:
            Response object to send back to the caller.

    """
    logger: logging.Logger = logging.getLogger("uvicorn.error")

    authorized, response = await check_authentication(request, admin_username, admin_password)
    if not authorized:
        logger.info("Invalid Authentication", extra={"host": request.client.host})
        return response

    configs: list[Location] = read_config()

    index: int | None = get_location_index_by_id(configs, id_number)

    if index is None:
        logger.info("Unable to find Location by ID")
        return Response(status_code=status.HTTP_400_BAD_REQUEST, content="Invalid Data")

    logger.info(
        "Received an update request",
        extra={"location": configs[index].location_id, "old_data": configs[index]},
    )

    resp = await set_named_location_ip(configs[index], configs[index].ip_address)

    if not resp:
        logger.error(
            "Updating IP on Microsoft Failed",
            extra={"location_id": configs[index].location_id, "ip_address": configs[index].ip_address},
        )

        return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content="Internal Server Error")

    return RedirectResponse(url="/list-m365", status_code=302)


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

    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
