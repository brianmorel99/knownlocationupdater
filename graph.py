from configparser import SectionProxy
from azure.identity.aio import ClientSecretCredential
from azure.core.exceptions import ClientAuthenticationError
from msgraph import GraphServiceClient
from msgraph.generated.models.o_data_errors.o_data_error import ODataError
from msgraph.generated.models.ip_named_location import IpNamedLocation
from msgraph.generated.models.i_pv4_cidr_range import IPv4CidrRange
from msgraph.generated.models.named_location_collection_response import NamedLocationCollectionResponse
from msgraph.generated.models.named_location import NamedLocation
from location import Location
import logging


class Graph:
    settings: SectionProxy
    client_credential: ClientSecretCredential
    app_client: GraphServiceClient

    def __init__(self, config: SectionProxy):
        self.settings = config
        client_id: str = self.settings['clientId']
        tenant_id: str = self.settings['tenantId']
        client_secret: str = self.settings['clientSecret']

        self.client_credential = ClientSecretCredential(
            tenant_id, client_id, client_secret)
        self.app_client = GraphServiceClient(
            self.client_credential)


async def get_current_location_ip(location: Location) -> str | None:
    logger: logging.Logger = logging.getLogger('uvicorn.error')

    azure_settings: dict[str, str] = {
        'clientId': location.client_id,
        'tenantId': location.tenant_id,
        'clientSecret': location.client_secret,
    }

    graph: Graph = Graph(azure_settings)

    try:
        result: NamedLocationCollectionResponse | None = await graph.app_client.identity.conditional_access.named_locations.get()
    except ClientAuthenticationError as e:
        logger.error("Exception Line Break")
        logger.error(f"Error is {e.error}, {e.message}")
        return None
    except ODataError as odata_error:
        logger.warning('Graph returned an ODataError:')
        if odata_error.error:
            logger.warning(odata_error.error.code, odata_error.error.message)
        return None

    if result == None:
        logger.warning("Graph could not find a location")
        return None

    index: int = -1

    for idx, x in enumerate(result.value):
        if x.id == location.location_id:
            index = idx

    if index != -1:
        loc: IpNamedLocation = result.value[index]
        iprange: IPv4CidrRange = loc.ip_ranges[0]
        logger.info(
            f"Microsoft Shows IP: {iprange.cidr_address} for Location: {location.display_name}")
        return iprange.cidr_address.split('/')[0]
    else:
        logger.warning(
            "Graph cound not find the location in the response.")
        return None


async def set_named_location_ip(location: Location, new_ip_address: str) -> bool:
    logger: logging.Logger = logging.getLogger('uvicorn.error')

    azure_settings: dict[str, str] = {
        'clientId': location.client_id,
        'tenantId': location.tenant_id,
        'clientSecret': location.client_secret,
    }

    graph: Graph = Graph(azure_settings)

    body = IpNamedLocation(
        odata_type="#microsoft.graph.ipNamedLocation",
        ip_ranges=[
            IPv4CidrRange(
                odata_type="#microsoft.graph.iPv4CidrRange",
                cidr_address=new_ip_address + "/32",
            ),
        ]
    )
    try:
        result = await graph.app_client.identity.conditional_access.named_locations.by_named_location_id(location.location_id).patch(body)
    except ClientAuthenticationError as e:
        logger.error("Exception Line Break")
        logger.error(f"Error is {e.error}, {e.message}")
        return False
    except ODataError as odata_error:
        logger.warning('Graph returned an ODataError:')
        if odata_error.error:
            logger.warning(odata_error.error.code, odata_error.error.message)
        return False
    return True


async def get_location(location: Location) -> Location | None:
    logger: logging.Logger = logging.getLogger('uvicorn.error')

    new_location: Location = Location()
    new_location.client_id = location.client_id
    new_location.client_secret = location.client_secret
    new_location.tenant_id = location.tenant_id

    azure_settings: dict[str, str] = {
        'clientId': location.client_id,
        'tenantId': location.tenant_id,
        'clientSecret': location.client_secret,
    }

    graph: Graph = Graph(azure_settings)

    try:
        result: NamedLocationCollectionResponse | None = await graph.app_client.identity.conditional_access.named_locations.get()
    except ClientAuthenticationError as e:
        logger.error("Exception Line Break")
        logger.error(f"Error is {e.error}, {e.message}")
        return None
    except ODataError as odata_error:
        logger.warning('Graph returned an ODataError:')
        if odata_error.error:
            logger.warning(odata_error.error.code, odata_error.error.message)
        return None

    if result == None:
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
        new_location.ip_address = iprange.cidr_address.split('/')[0]
        new_location.is_trusted = loc.is_trusted
        new_location.location_id = loc.id

        return new_location
    else:
        logger.warning(
            "Graph cound not find the location in the response.")
        return None
