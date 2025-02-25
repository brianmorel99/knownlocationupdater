import yaml
from location import Location


def read_config():
    with open("config.yml", "r") as file_object:
        data = yaml.load(file_object, Loader=yaml.SafeLoader)

    locations = parse_config(data)

    return locations


def write_config(data):
    locations = []
    for loc in data:
        test = vars(loc)
        locations.append(test)

    with open("config.yml", "w") as file_object:
        yaml.dump(locations, file_object)


def parse_config(config_data):
    loc = []

    for data in config_data:
        location = Location(client_id=data['client_id'],
                            client_secret=data['client_secret'],
                            display_name=data['display_name'],
                            ip_address=data['ip_address'],
                            is_trusted=data['is_trusted'],
                            location_id=data['location_id'],
                            tenant_id=data['tenant_id'])
        loc.append(location)
    return loc
