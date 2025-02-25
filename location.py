class Location:
    client_id: str = ""
    client_secret: str = ""
    display_name: str = ""
    ip_address: str = ""
    is_trusted: bool = ""
    location_id: str = ""
    tenant_id: str = ""

    def __init__(self,
                 client_id: str = "",
                 client_secret: str = "",
                 display_name: str = "",
                 ip_address: str = "",
                 is_trusted: bool = "",
                 location_id: str = "",
                 tenant_id: str = ""
                 ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.display_name = display_name
        self.ip_address = ip_address
        self.is_trusted = is_trusted
        self.location_id = location_id
        self.tenant_id = tenant_id
    
    def __repr__(self):
        output = f'Client ID: {self.client_id}\n'
        output += f'Client Secret: {self.client_secret}\n'
        output += f'Display Name: {self.display_name}\n'
        output += f'IP Address: {self.ip_address}\n'
        output += f'Is Trusted: {self.is_trusted}\n'
        output += f'Location ID: {self.location_id}\n'
        output += f'Tenant ID: {self.tenant_id}\n\n'
        return output

def get_location_index_by_name(configs: list[Location], name: str) -> int | None:
    for index, config in enumerate(configs):
        if config.display_name == name:
            return index
    return None

def get_location_index_by_id(configs: list[Location], id: str) -> int | None:
    for index, config in enumerate(configs):
        if config.client_id == id:
            return index
    return None
