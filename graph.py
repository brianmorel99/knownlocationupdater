from configparser import SectionProxy
from azure.identity.aio import ClientSecretCredential
from msgraph import GraphServiceClient
from msgraph.generated.models.o_data_errors.o_data_error import ODataError
from msgraph.generated.models.ip_named_location import IpNamedLocation
from msgraph.generated.models.i_pv4_cidr_range import IPv4CidrRange
from msgraph.generated.models.named_location_collection_response import NamedLocationCollectionResponse
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
            self.client_credential)  # type: ignore


async def check_named_location(location: Location, new_ip_address: str) -> str:
    logger: logging.Logger = logging.getLogger('uvicorn.error')

    azure_settings: dict[str, str] = {
        'clientId': location.client_id,
        'tenantId': location.tenant_id,
        'clientSecret': location.client_secret,
    }

    graph: Graph = Graph(azure_settings)

    try:
        result: NamedLocationCollectionResponse | None = await graph.app_client.identity.conditional_access.named_locations.get()

        if result == None:
            logger.warning("Location does not exist")

        index = -1

        for idx, x in enumerate(result.value):
            if x.id == location.location_id:
                index = idx
        loc: IpNamedLocation = result.value[index]

        iprange: IPv4CidrRange = loc.ip_ranges[0]
        if iprange.cidr_address == (new_ip_address + '/32'):
            return "Unchanged"
        else:
            body = update_ip_address(new_ip_address)
            result = await graph.app_client.identity.conditional_access.named_locations.by_named_location_id(loc.id).patch(body)
            return "Updated"

    except ODataError as odata_error:
        logger.warning('ODataError from Microsoft Graph')
        if odata_error.error:
            logger.warning(odata_error.error.code, odata_error.error.message)


def update_ip_address(ipaddr):
    request_body = IpNamedLocation(
        odata_type="#microsoft.graph.ipNamedLocation",
        ip_ranges=[
            IPv4CidrRange(
                odata_type="#microsoft.graph.iPv4CidrRange",
                cidr_address=ipaddr + "/32",
            ),
        ]
    )
    return request_body


async def list_named_locations(config):

    for idx, _ in enumerate(config):

        azure_settings = {
            'clientId': config[idx]['client_id'],
            'tenantId': config[idx]['tenant_id'],
            'clientSecret': config[idx]['client_secret'],
        }

        graph: Graph = Graph(azure_settings)

        try:
            result = await graph.app_client.identity.conditional_access.named_locations.get()
            for location in result.value:
                print("Location ID: ", location.id)
                print("Display Name: ", location.display_name)
                iprange = location.ip_ranges[0]
                print("IP Address:", iprange.cidr_address)
                print("Is Trusted: ", location.is_trusted)

        except ODataError as odata_error:
            print('Error:')
            if odata_error.error:
                print(odata_error.error.code, odata_error.error.message)


async def check_current_ip(location: Location):
    azure_settings = {
        'clientId': location.client_id,
        'tenantId': location.tenant_id,
        'clientSecret': location.client_secret,
    }

    graph: Graph = Graph(azure_settings)

    try:
        result: NamedLocationCollectionResponse | None = await graph.app_client.identity.conditional_access.named_locations.get()

        index = -1
        for idx, x in enumerate(result.value):
            if x.id == location.location_id:
                index = idx
        loc = result.value[index]

        iprange = loc.ip_ranges[0]
        if iprange.cidr_address == (location.ip_address + '/32'):
            return "Unchanged"
        else:
            return iprange.cidr_address

    except ODataError as odata_error:
        print('Error:')
        if odata_error.error:
            print(odata_error.error.code, odata_error.error.message)


async def get_current_location_ip(location: Location) -> str:
    logger: logging.Logger = logging.getLogger('uvicorn.error')

    azure_settings: dict[str, str] = {
        'clientId': location.client_id,
        'tenantId': location.tenant_id,
        'clientSecret': location.client_secret,
    }

    graph: Graph = Graph(azure_settings)

    try:
        result: NamedLocationCollectionResponse | None = await graph.app_client.identity.conditional_access.named_locations.get()

        if result == None:
            logger.warning("Graph could not find a location")

        index: int = -1

        for idx, x in enumerate(result.value):
            if x.id == location.location_id:
                index = idx

        if index != -1:
            loc: IpNamedLocation = result.value[index]
            iprange: IPv4CidrRange = loc.ip_ranges[0]
            logger.info(f"Microsoft Shows IP: {iprange.cidr_address} for Location: {location.display_name}")
            return iprange.cidr_address.split('/')[0]
        else:
            logger.warning(
                "Graph cound not find the location in the response.")

    except ODataError as odata_error:
        logger.warning('Graph returned an ODataError:')
        if odata_error.error:
            logger.warning(odata_error.error.code, odata_error.error.message)
