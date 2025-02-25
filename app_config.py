import yaml


def read_config():
    with open("config.yml", "r") as file_object:
        data = yaml.load(file_object, Loader=yaml.SafeLoader)
    return data


def write_config(data):
    with open("config-new.yml", "w") as file_object:
        yaml.dump(data, file_object)
