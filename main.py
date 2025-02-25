import asyncio
import yaml
from msgraph.generated.models.o_data_errors.o_data_error import ODataError
from graph import Graph
from msgraph.generated.models.ip_named_location import IpNamedLocation
from msgraph.generated.models.ip_range import IpRange
from msgraph.generated.models.i_pv4_cidr_range import IPv4CidrRange
from flask import Flask, request, Response


app = Flask(__name__)


def read_config():
    with open("config.yml", "r") as file_object:
        data = yaml.load(file_object, Loader=yaml.SafeLoader)
    return data


def write_config(data):
    with open("config-new.yml", "w") as file_object:
        yaml.dump(data, file_object)


async def check_named_location(config, hostname, ip_address):
    index = -1
    for idx, host in enumerate(config['locations']):
        if host['display_name'] == hostname:
            index = idx

    if index != -1:
        azure_settings = {
            'clientId': config['locations'][idx]['client_id'],
            'tenantId': config['locations'][idx]['tenant_id'],
            'clientSecret': config['locations'][idx]['client_secret'],
        }

        graph: Graph = Graph(azure_settings)

        try:
            result = await graph.app_client.identity.conditional_access.named_locations.get()
            location = result.value[0]

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


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def process_request(path):
    if request.authorization:
        if request.authorization.username == "samsa" and request.authorization.password == "samsa":
            hostname = request.args.get('hostname', '')
            ip_address = request.args.get('myip', '')
            if hostname and ip_address:
                print("Hostname: " + hostname)
                print("IP Address: " + ip_address)
            return "<p>Hello, World!</p>"
        else:
            return Response(response="Unauthorized", status=401)
    else:
        return Response(response="Unauthorized", status=401)


async def main():

    app.run(host='0.0.0.0')
    config = read_config()

    # status = await check_named_location(config, 'prschesaning.homeip.net', '174.84.114.106')
    # print(status)
    # await list_named_locations(config)


# Run main
asyncio.run(main())
