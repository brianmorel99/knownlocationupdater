"""Module for interfacing with Microsoft Graph API.

This module contains all the functions for interfacing with the Graph API.
It includes functions for updating the IP addresses of Named Locations
previously configured.

Typical usage example:

    graph: Graph = Graph(azure_settings)


"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from azure.core.exceptions import ClientAuthenticationError
from azure.identity.aio import ClientSecretCredential
from msgraph import GraphServiceClient
from msgraph.generated.models.i_pv4_cidr_range import IPv4CidrRange
from msgraph.generated.models.ip_named_location import IpNamedLocation
from msgraph.generated.models.o_data_errors.o_data_error import ODataError

from location import Location

if TYPE_CHECKING:
    from configparser import SectionProxy

    from msgraph.generated.models.named_location_collection_response import NamedLocationCollectionResponse


class Graph:
    """Graph class used for communicating with Microsoft Graph API.

    This class does all the setup and permissions for connecting to
    the Graph API.

    Attributes:
        settings: SectionProxy
        client_credential: ClientSecretCredential
        app_client: GraphServiceClient


    """

    settings: SectionProxy
    client_credential: ClientSecretCredential
    app_client: GraphServiceClient

    def __init__(self, config: SectionProxy) -> None:
        """Initialize a new Graph object given SectionProxy.

        Initializes the new object with the passed in data.

        Args:
            config:
                A dictionary containing 'clientId', 'tenantId' &
                 'clientSecret' with their respective values

        Returns:
            A new Graph object

        """
        self.settings = config
        client_id: str = self.settings["clientId"]
        tenant_id: str = self.settings["tenantId"]
        client_secret: str = self.settings["clientSecret"]

        self.client_credential = ClientSecretCredential(tenant_id, client_id, client_secret)
        self.app_client = GraphServiceClient(self.client_credential)


async def get_current_location_ip(location: Location) -> str | None:
    """Retreive Microsoft's current IP address for a give location.

       Given a location object, it returns the ip_address currently
    configured for a Microsoft NamedLocation and returns it as a string.

    Args:
        location:
            A location object that we wish to check Microsoft for current IP.

    Returns:
            A string with the IP address in xxx.xxx.xxx.xxx format or
            None if there is an error

    """
    logger: logging.Logger = logging.getLogger("uvicorn.error")

    azure_settings: dict[str, str] = {
        "clientId": location.client_id,
        "tenantId": location.tenant_id,
        "clientSecret": location.client_secret,
    }

    graph: Graph = Graph(azure_settings)

    try:
        result: (
            NamedLocationCollectionResponse | None
        ) = await graph.app_client.identity.conditional_access.named_locations.get()
    except ClientAuthenticationError:
        logger.warning("Unable to check current IP for location_id : %s", location.location_id)
        return None
    except ODataError as odata_error:
        logger.warning("Graph returned an ODataError:")
        if odata_error.error:
            logger.warning(odata_error.error.code, odata_error.error.message)
        return None

    if result is None:
        logger.warning("Graph could not find a location")
        return None

    index: int = -1

    for idx, x in enumerate(result.value):
        if x.id == location.location_id:
            index = idx

    if index != -1:
        loc: IpNamedLocation = result.value[index]
        iprange: IPv4CidrRange = loc.ip_ranges[0]
        logger.info("Microsoft Shows IP: %s for Location: %s", iprange.cidr_address, location.display_name)
        return iprange.cidr_address.split("/")[0]

    logger.warning("Graph cound not find the location in the response.")
    return None


async def set_named_location_ip(location: Location, new_ip_address: str) -> bool:
    """Take given Location and new IP Address, update Microsoft.

    Given a location object, and a new IP address, update Microsoft's
    Named Location IP Address.

    Args:
        location:
            A location object that we wish to use to update Microsoft.
        new_ip_address:
            The new IP address we want to set the location to.

    Returns:
            True if successful otherwise False if an error

    """
    logger: logging.Logger = logging.getLogger("uvicorn.error")

    azure_settings: dict[str, str] = {
        "clientId": location.client_id,
        "tenantId": location.tenant_id,
        "clientSecret": location.client_secret,
    }

    graph: Graph = Graph(azure_settings)

    body = IpNamedLocation(
        odata_type="#microsoft.graph.ipNamedLocation",
        ip_ranges=[
            IPv4CidrRange(
                odata_type="#microsoft.graph.iPv4CidrRange",
                cidr_address=new_ip_address + "/32",
            ),
        ],
    )
    try:
        _ = await graph.app_client.identity.conditional_access.named_locations.by_named_location_id(
            location.location_id,
        ).patch(body)
    except ClientAuthenticationError as e:
        logger.exception("Error is %s, %s", e.error, e.message)
        return False
    except ODataError as odata_error:
        logger.exception("Graph returned an ODataError:")
        if odata_error.error:
            logger.exception(odata_error.error.code, odata_error.error.message)
        return False
    return True


async def get_location(location: Location) -> Location | None:
    """Given a Location, create a new Location object with Microsoft data.

    Given a Location object, this function will create a Location object,
    contact Microsoft Graph API, and fill inthe new Location with the values
    retrived from Microsoft

    Args:
        location:
            A location object that we wish to use to update Microsoft.

    Returns:
            A location object filled with Microsoft data.

    """
    logger: logging.Logger = logging.getLogger("uvicorn.error")

    new_location: Location = Location()
    new_location.client_id = location.client_id
    new_location.client_secret = location.client_secret
    new_location.tenant_id = location.tenant_id

    azure_settings: dict[str, str] = {
        "clientId": location.client_id,
        "tenantId": location.tenant_id,
        "clientSecret": location.client_secret,
    }

    graph: Graph = Graph(azure_settings)

    try:
        result: (
            NamedLocationCollectionResponse | None
        ) = await graph.app_client.identity.conditional_access.named_locations.get()
    except ClientAuthenticationError as e:
        logger.exception("Error is %s, %s", e.error, e.message)
        return None
    except ODataError as odata_error:
        logger.exception("Graph returned an ODataError:")
        if odata_error.error:
            logger.exception(odata_error.error.code, odata_error.error.message)
        return None

    if result is None:
        logger.warning("Graph could not find a location")
        return None

    index: int = -1

    for idx, x in enumerate(result.value):
        if x.id == location.location_id:
            index = idx

    if index != -1:
        loc: IpNamedLocation = result.value[index]
        iprange: IPv4CidrRange = loc.ip_ranges[0]

        new_location.display_name = loc.display_name
        new_location.ip_address = iprange.cidr_address.split("/")[0]
        new_location.is_trusted = loc.is_trusted
        new_location.location_id = loc.id

        return new_location

    logger.warning("Graph cound not find the location in the response.")
    return None
