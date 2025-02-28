import asyncio
import uvicorn
import base64
import logging
from graph import get_current_location_ip, set_named_location_ip, get_location
from app_config import read_config, write_config
from location import Location, get_location_index_by_id, get_location_index_by_name
from fastapi import FastAPI, Request, status, Form
from fastapi.responses import Response, RedirectResponse
from fastapi.templating import Jinja2Templates
from uvicorn.config import LOGGING_CONFIG

app = FastAPI()
templates = Jinja2Templates(directory="templates")

ddns_username = ""
ddns_password = ""
admin_username = ''
admin_password = ''
bad_auth: Response = Response(
    status_code=status.HTTP_401_UNAUTHORIZED,
    content="Incorrect username or password",
    headers={"WWW-Authenticate": "Basic"},
)


async def get_all_locations() -> list[tuple[Location, Location]] | None:
    config: list[Location] = read_config()

    bundled_locations: list[tuple[Location, Location]] = list()

    for location in config:
        m365_location = await get_location(location)
        if m365_location != None:
            bundle = (location, m365_location)
            bundled_locations.append(bundle)
    if len(bundled_locations) > 0:
        return bundled_locations
    else:
        return None


def get_location_from_config(config: list[Location], hostname: str) -> Location:
    for i, loc in enumerate(config):
        if loc.display_name == hostname:
            return config[i]


async def check_authentication(request: Request, username: str, password: str) -> tuple[bool, Response | None]:
    auth = request.headers.get('Authorization')
    userpass = username + ":" + password
    userpassenc = base64.b64encode(userpass.encode('utf-8'))
    if auth == ("Basic " + str(userpassenc, 'UTF-8')):
        return True, None
    else:
        return False, bad_auth


@app.get("/")
async def catch_all(request: Request, hostname: str = "", myip: str = ""):
    logger: logging.Logger = logging.getLogger('uvicorn.error')

    authorized, response = await check_authentication(
        request, ddns_username, ddns_password)
    if not authorized:
        logger.info(f"Invalid Authentication from {request.client.host}")
        return response

    config: list[Location] = read_config()
    index: int | None = get_location_index_by_name(config, hostname)

    current_ip: str | None = await get_current_location_ip(config[index])

    if current_ip == None:
        return Response(status_code=status.HTTP_400_BAD_REQUEST, content="Invalid Data")
    elif current_ip == myip:
        return Response(status_code=status.HTTP_200_OK, content="nochg " + myip)
    else:
        config[index].ip_address = myip
        write_config(config)
        if await set_named_location_ip(config[index], myip):
            logger.error(
                f"Updating IP on Microsoft Failed - {request.client.host} - {request.url}")
            return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content="Internal Server Error")
        else:
            return Response(status_code=status.HTTP_200_OK, content="good " + myip)


@app.get("/admin")
async def admin_get(request: Request):
    logger: logging.Logger = logging.getLogger('uvicorn.error')

    authorized, response = await check_authentication(
        request, admin_username, admin_password)
    if not authorized:
        logger.info(f"Invalid Authentication from {request.client.host}")
        return response
  
    return templates.TemplateResponse(request=request, name="admin.html", context={})


@app.get("/list-m365")
async def list_get_m365(request: Request):
    logger: logging.Logger = logging.getLogger('uvicorn.error')

    authorized, response = await check_authentication(
        request, admin_username, admin_password)
    if not authorized:
        logger.info(f"Invalid Authentication from {request.client.host}")
        return response

    config = await get_all_locations()
    if config == None:
        return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content="Internal Server Error")
    else:
        return templates.TemplateResponse(request=request, name="list_locations_m365.html", context={"configs": config})


@app.get("/list")
async def list_get(request: Request):
    logger: logging.Logger = logging.getLogger('uvicorn.error')

    authorized, response = await check_authentication(
        request, admin_username, admin_password)
    if not authorized:
        logger.info(f"Invalid Authentication from {request.client.host}")
        return response

    configs = read_config()
    if configs == None:
        return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content="Internal Server Error")
    else:
        return templates.TemplateResponse(request=request, name="list_locations.html", context={"configs": configs})

@app.get("/add")
async def add_location_get(request: Request):
    logger: logging.Logger = logging.getLogger('uvicorn.error')

    authorized, response = await check_authentication(
        request, admin_username, admin_password)
    if not authorized:
        logger.info(f"Invalid Authentication from {request.client.host}")
        return response

    return templates.TemplateResponse(request=request, name="add_location.html")


@app.post("/add")
async def add_location_post(request: Request,
                            location_id: str = Form(),
                            display_name: str = Form(),
                            ip_address: str = Form(),
                            is_trusted: bool = Form(False),
                            client_id: str = Form(),
                            client_secret: str = Form(),
                            tenant_id: str = Form()
                            ):
    logger: logging.Logger = logging.getLogger('uvicorn.error')

    authorized, response = await check_authentication(
        request, admin_username, admin_password)
    if not authorized:
        logger.info(f"Invalid Authentication from {request.client.host}")
        return response

    config: list[Location] = read_config()

    loc = Location(location_id=location_id,
                   display_name=display_name,
                   ip_address=ip_address,
                   is_trusted=is_trusted,
                   client_id=client_id,
                   client_secret=client_secret,
                   tenant_id=tenant_id
                   )
    config.append(loc)
    write_config(config)

    return RedirectResponse(url='/admin', status_code=302)


@app.get("/edit")
async def edit_location_get(request: Request, id:str):
    logger: logging.Logger = logging.getLogger('uvicorn.error')

    authorized, response = await check_authentication(
        request, admin_username, admin_password)
    if not authorized:
        logger.info(f"Invalid Authentication from {request.client.host}")
        return response

    configs: list[Location] = read_config()

    index: int | None = get_location_index_by_id(configs, id)

    if index == None:
        return Response(status_code=status.HTTP_400_BAD_REQUEST, content="Invalid Data")

    return templates.TemplateResponse(request=request, name="edit_location.html", context={"config": configs[index], "action": "/edit"})

@app.get("/edit/{id}")
async def edit_location(request: Request, id:str):
    logger: logging.Logger = logging.getLogger('uvicorn.error')

    authorized, response = await check_authentication(
        request, admin_username, admin_password)
    if not authorized:
        logger.info(f"Invalid Authentication from {request.client.host}")
        return response

    configs: list[Location] = read_config()

    index: int | None = get_location_index_by_id(configs, id)

    if index == None:
        return Response(status_code=status.HTTP_400_BAD_REQUEST, content="Invalid Data")
    
    action = "/edit/" + configs[index].location_id

    return templates.TemplateResponse(request=request, name="edit_location.html", context={"config": configs[index], "action": action})


@app.post("/edit/{id}")
async def edit_location_post(request: Request,
                            location_id: str = Form(),
                            display_name: str = Form(),
                            ip_address: str = Form(),
                            is_trusted: bool = Form(False),
                            client_id: str = Form(),
                            client_secret: str = Form(),
                            tenant_id: str = Form(),
                            id: str = id
                            ):
    logger: logging.Logger = logging.getLogger('uvicorn.error')

    authorized, response = await check_authentication(
        request, admin_username, admin_password)
    if not authorized:
        logger.info(f"Invalid Authentication from {request.client.host}")
        return response

    configs: list[Location] = read_config()

    index: int | None = get_location_index_by_id(configs, id)

    if index == None:
        logger.info(f"Unable to find Location by ID")
        return Response(status_code=status.HTTP_400_BAD_REQUEST, content="Invalid Data")
    
    logger.info(f"Received an update request for {configs[index].location_id} Old data is {configs[index]}")
    
    configs[index].location_id = location_id
    configs[index].display_name = display_name
    configs[index].ip_address = ip_address
    configs[index].is_trusted = is_trusted
    configs[index].client_id = client_id
    configs[index].client_secret = client_secret
    configs[index].tenant_id = tenant_id

    logger.info(f"Storing new data: {configs[index]}")

    write_config(configs)

    return RedirectResponse(url='/admin', status_code=302)

async def main():
    LOGGING_CONFIG["formatters"]["default"]["fmt"] = "%(asctime)s [%(name)s] %(levelprefix)s %(message)s"
    LOGGING_CONFIG["formatters"]["access"][
        "fmt"] = '%(asctime)s [%(name)s] %(levelprefix)s %(client_addr)s - "%(request_line)s" %(status_code)s'
    config = uvicorn.Config("main:app", port=8080, log_level="info")
    server = uvicorn.Server(config)

    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())
