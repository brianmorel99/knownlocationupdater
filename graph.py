from configparser import SectionProxy
from azure.identity.aio import ClientSecretCredential
from msgraph import GraphServiceClient
from msgraph.generated.models.o_data_errors.o_data_error import ODataError
from msgraph.generated.models.ip_named_location import IpNamedLocation
from msgraph.generated.models.i_pv4_cidr_range import IPv4CidrRange

class Graph:
    settings: SectionProxy
    client_credential: ClientSecretCredential
    app_client: GraphServiceClient

    def __init__(self, config: SectionProxy):
        self.settings = config
        client_id = self.settings['clientId']
        tenant_id = self.settings['tenantId']
        client_secret = self.settings['clientSecret']

        self.client_credential = ClientSecretCredential(tenant_id, client_id, client_secret)
        self.app_client = GraphServiceClient(self.client_credential) # type: ignore

async def check_named_location(config, hostname, ip_address):
    index = -1
    for idx, host in enumerate(config['locations']):
        if host['display_name'] == hostname:
            host_id = host['location_id']
            index = idx

    if index != -1:
        azure_settings = {
            'clientId': config['locations'][index]['client_id'],
            'tenantId': config['locations'][index]['tenant_id'],
            'clientSecret': config['locations'][index]['client_secret'],
        }

        graph: Graph = Graph(azure_settings)

        try:
            result = await graph.app_client.identity.conditional_access.named_locations.get()
            for idx, x in enumerate(result.value):
                if x.id == host_id:
                    index = idx
            location = result.value[index]

            iprange = location.ip_ranges[0]
            if iprange.cidr_address == (ip_address + '/32'):
                return "Unchanged"
            else:
                body = update_ip_address(ip_address)
                result = await graph.app_client.identity.conditional_access.named_locations.by_named_location_id(location.id).patch(body)
                return "Updated"

        except ODataError as odata_error:
            print('Error:')
            if odata_error.error:
                print(odata_error.error.code, odata_error.error.message)
    else:
        return "Not Found"


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

    for idx, _ in enumerate(config['locations']):

        azure_settings = {
            'clientId': config['locations'][idx]['client_id'],
            'tenantId': config['locations'][idx]['tenant_id'],
            'clientSecret': config['locations'][idx]['client_secret'],
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
