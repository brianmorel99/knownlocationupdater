"""Module to define a Location class for holding Named Location Data.

This module contains the class definition for the Location objects used
in the program.  These objects hold the data needed to connect to Microsoft
Graph API along with the data for each Named Location.  There are also a
few helper functions defined in this file, but outside of the class.

Typical usage example:

    loc: Location = Location()
    get_location_index_by_name(configs=list[Location], name=str)
    get_location_index_by_id(configs=list[Location], id=str)

"""

from __future__ import annotations


class Location:
    """Location class for storing the required data.

    This class does contains all the data for connecting to
    the Graph API, along with the info from the Named Location

    Attributes:
        client_id: str
            The Client ID required to login to Microsoft Graph API
        client_secret: str
            The Client Secret is used for authenticating to Microsoft
        display_name: str
            The Named Location display name
        ip_address: str
            The IP Address for the Named Location
        is_trusted: bool
            Whether Microsoft considers this location as trusted
        location_id:
            The UUID for the Named Location
        tenant_id: str
            The Tenant ID for authenticating to Microsoft

    """

    client_id: str = ""
    client_secret: str = ""
    display_name: str = ""
    ip_address: str = ""
    is_trusted: bool = ""
    location_id: str = ""
    tenant_id: str = ""

    def __init__(
        self,
        client_id: str = "",
        client_secret: str = "",
        display_name: str = "",
        ip_address: str = "",
        is_trusted: bool = "",
        location_id: str = "",
        tenant_id: str = "",
    ) -> None:
        """Initialize a new Location object given the inputs.

        Initializes the new object with the passed in data.

        Args:
            client_id: str
                The Client ID required to login to Microsoft Graph API
            client_secret: str
                The Client Secret is used for authenticating to Microsoft
            display_name: str
                The Named Location display name
            ip_address: str
                The IP Address for the Named Location
            is_trusted: bool
                Whether Microsoft considers this location as trusted
            location_id:
                The UUID for the Named Location
            tenant_id: str
                The Tenant ID for authenticating to Microsoft

        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.display_name = display_name
        self.ip_address = ip_address
        self.is_trusted = is_trusted
        self.location_id = location_id
        self.tenant_id = tenant_id

    def __repr__(self) -> str:
        """Output a readable representation of the object."""
        output = f"Client ID: {self.client_id}\n"
        output += f"Client Secret: {self.client_secret}\n"
        output += f"Display Name: {self.display_name}\n"
        output += f"IP Address: {self.ip_address}\n"
        output += f"Is Trusted: {self.is_trusted}\n"
        output += f"Location ID: {self.location_id}\n"
        output += f"Tenant ID: {self.tenant_id}\n\n"
        return output


def get_location_index_by_name(configs: list[Location], name: str) -> int | None:
    """Given a list of Locations, return the index corresponding to name.

    Given a list of location objects return the index of the location in the list
    corresponding to the location with the same name.

    Args:
        configs:
            A list of location objects.
        name:
            String representing the display_name of the location being searched for.

    Returns:
            Integer index corresponding to the entry in the list.

    """
    for index, config in enumerate(configs):
        if config.display_name == name:
            return index
    return None


def get_location_index_by_id(configs: list[Location], id_number: str) -> int | None:
    """Given a list of Locations, return the index corresponding to id.

    Given a list of location objects return the index of the location in the list
    corresponding to the location with the same location_id.

    Args:
        configs:
            A list of location objects.
        id_number:
            String representing the location ID of the location being searched for.

    Returns:
            Integer index corresponding to the entry in the list.

    """
    for index, config in enumerate(configs):
        if config.location_id == id_number:
            return index
    return None
