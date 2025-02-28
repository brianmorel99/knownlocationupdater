"""Helper Module for reading config.yaml.

These are a few functions that handle reading the config.yaml file,
parse it into a Location object, and add to a list of Location
The other function will convert a list of Location into YAML format,
and write out a replacement config file.

Typical usage example:

    [Locations] = read_config()
    write_config([Locations])

"""

from pathlib import Path

import yaml

from location import Location


def read_config() -> list[Location]:
    """Read config.yaml into Memory.

    Returns:
        Returns a list of Location Objects, one for each in config.yaml.

    """
    with Path("config.yml").open() as file_object:
        data: any = yaml.load(file_object, Loader=yaml.SafeLoader)

    return __parse_config(data)


def write_config(data: list[Location]) -> None:
    """Given a list of Locations, create and write a new config.yaml.

    Args:
        data: A list containing all location objects to be stored in config.yaml

    """
    locations = []
    for loc in data:
        test = vars(loc)
        locations.append(test)

    with Path("config.yml").open("w") as file_object:
        yaml.dump(locations, file_object)


def __parse_config(config_data: any) -> Location:
    loc = []

    for data in config_data:
        location = Location(
            client_id=data["client_id"],
            client_secret=data["client_secret"],
            display_name=data["display_name"],
            ip_address=data["ip_address"],
            is_trusted=data["is_trusted"],
            location_id=data["location_id"],
            tenant_id=data["tenant_id"],
        )
        loc.append(location)
    return loc
