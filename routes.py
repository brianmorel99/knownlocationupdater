"""Module for defining all the FastAPI routes.

This module contains all the functions for the routes of the main application.
"""

import logging
import os
from typing import Annotated

from fastapi import APIRouter, Form, Request, Response, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app_config import read_config, write_config
from graph import get_current_location_ip, set_named_location_ip
from location import Location, get_location_index_by_id, get_location_index_by_name
from utils import check_authentication, get_all_locations

templates = Jinja2Templates(directory="templates")

ddns_username: str | None = os.getenv("DDNS_USERNAME")
ddns_password: str | None = os.getenv("DDNS_PASSWORD")
admin_username: str | None = os.getenv("ADMIN_USERNAME")
admin_password: str | None = os.getenv("ADMIN_PASSWORD")

my_router = APIRouter()


@my_router.get("/")
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
        logger.info("Invalid Authentication")
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


@my_router.get("/admin")
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


@my_router.get("/list-m365")
async def list_get_m365(request: Request) -> Response:
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


@my_router.get("/list")
async def list_get(request: Request) -> Response:
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


@my_router.get("/add")
async def add_location_get(request: Request) -> Response:
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


@my_router.post("/add")
async def add_location_post(
    request: Request,
    location_id: Annotated[str, Form()],
    display_name: Annotated[str, Form()],
    ip_address: Annotated[str, Form()],
    is_trusted: Annotated[bool, Form()],
    client_id: Annotated[str, Form()],
    client_secret: Annotated[str, Form()],
    tenant_id: Annotated[str, Form()],
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


@my_router.get("/edit/{id_number}")
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


@my_router.post("/edit/{id_number}")
async def edit_location_post(
    request: Request,
    location_id: Annotated[str, Form()],
    display_name: Annotated[str, Form()],
    ip_address: Annotated[str, Form()],
    client_id: Annotated[str, Form()],
    client_secret: Annotated[str, Form()],
    tenant_id: Annotated[str, Form()],
    id_number: str,
    is_trusted: Annotated[bool, Form()] = False,  # noqa: FBT002
) -> Response:
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


@my_router.get("/update/{id_number}")
async def update_location_get(request: Request, id_number: str = id) -> Response:
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


@my_router.get("/delete/{id_number}")
async def delete_location_get(request: Request, id_number: str) -> Response:
    """Return a Location form filled in with current data of Location id.

    This function returns a response with a form that is pre-populated
    with Location "id" data.  This allows for first confirmation of
    deleting the location.

    Args:
        request:
            The incomming HTTP Request
        id_number:
            The Location ID of the Location to delete.

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

    action: str = "/delete/" + configs[index].location_id

    return templates.TemplateResponse(
        request=request,
        name="delete_location.html",
        context={"config": configs[index], "action": action},
    )


@my_router.post("/delete/{id_number}")
async def delete_location_post(
    request: Request,
    id_number: str,
    deletion_confirmed: Annotated[bool, Form()] = False,  # noqa: FBT002

) -> Response:
    """Take in the first confirmation of Location delete.

    This function is called after the first confirmation of Location delete.  It will give the user
    a last chance to cancel or process the delete if it receives the second confirmation.

    Args:
        request:
            The incomming HTTP Request
        deletion_confirmed:
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

    if deletion_confirmed:
        logger.info("Received an delete request 2nd confirmation, Location_ID: %s", configs[index].location_id)
        logger.info("Deleting Location: %s", configs[index])
        del configs[index]
        write_config(configs)
        return RedirectResponse(url="/list", status_code=302)

    logger.info("Received an delete request 1st confirmation, Location_ID: %s", configs[index].location_id)
    action: str = "/delete/" + configs[index].location_id

    return templates.TemplateResponse(
        request=request,
        name="delete_location_confirm.html",
        context={"config": configs[index], "action": action},
    )
