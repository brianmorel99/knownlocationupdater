from configparser import SectionProxy
from azure.identity.aio import ClientSecretCredential
from msgraph import GraphServiceClient
from msgraph.generated.models.o_data_errors.o_data_error import ODataError
from msgraph.generated.models.ip_named_location import IpNamedLocation
from msgraph.generated.models.i_pv4_cidr_range import IPv4CidrRange
from location import Location


class Graph:
    settings: SectionProxy
    client_credential: ClientSecretCredential
    app_client: GraphServiceClient

    def __init__(self, config: SectionProxy):
        self.settings = config
        client_id = self.settings['clientId']
        tenant_id = self.settings['tenantId']
        client_secret = self.settings['clientSecret']

        self.client_credential = ClientSecretCredential(
            tenant_id, client_id, client_secret)
        self.app_client = GraphServiceClient(
            self.client_credential)  # type: ignore


async def check_named_location(location: Location, new_ip_address: str) -> str:

    azure_settings = {
        'clientId': location.client_id,
        'tenantId': location.tenant_id,
        'clientSecret': location.client_secret,
    }

    graph: Graph = Graph(azure_settings)

    try:
        result = await graph.app_client.identity.conditional_access.named_locations.get()

        index = -1

        for idx, x in enumerate(result.value):
            if x.id == location.location_id:
                index = idx
        loc = result.value[index]

        iprange = loc.ip_ranges[0]
        if iprange.cidr_address == (new_ip_address + '/32'):
            return "Unchanged"
        else:
            body = update_ip_address(new_ip_address)
            result = await graph.app_client.identity.conditional_access.named_locations.by_named_location_id(loc.id).patch(body)
            return "Updated"

    except ODataError as odata_error:
        print('Error:')
        if odata_error.error:
            print(odata_error.error.code, odata_error.error.message)


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
        result = await graph.app_client.identity.conditional_access.named_locations.get()

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
