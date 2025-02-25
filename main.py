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

    config = read_config()
    return templates.TemplateResponse(request=request, name="locations.html", context={"configs": config})


@app.post("/admin")
async def admin_post(request: Request,
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

    for x in config:
        if x.location_id == location_id:
            x.display_name = display_name
            x.ip_address = ip_address
            x.is_trusted = is_trusted
            x.client_id = client_id
            x.client_secret = client_secret
            x.tenant_id = tenant_id

    write_config(config)

    return RedirectResponse(url='/admin', status_code=302)


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


@app.get("/list")
async def list_get(request: Request):
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
        return templates.TemplateResponse(request=request, name="list_locations.html", context={"configs": config})


async def main():
    LOGGING_CONFIG["formatters"]["default"]["fmt"] = "%(asctime)s [%(name)s] %(levelprefix)s %(message)s"
    LOGGING_CONFIG["formatters"]["access"][
        "fmt"] = '%(asctime)s [%(name)s] %(levelprefix)s %(client_addr)s - "%(request_line)s" %(status_code)s'
    config = uvicorn.Config("main:app", port=8080, log_level="info")
    server = uvicorn.Server(config)

    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())
