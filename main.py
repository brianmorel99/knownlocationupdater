import asyncio
import uvicorn
import base64
from graph import check_named_location, check_current_ip
from app_config import read_config, write_config
from location import Location
from fastapi import FastAPI, Request, status, Form
from fastapi.responses import Response, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory="templates")

ddns_username = ""
ddns_password = ""
admin_username = ''
admin_password = ''


def get_location_from_config(config: list[Location], hostname: str) -> Location:
    for i, loc in enumerate(config):
        if loc.display_name == hostname:
            return config[i]


async def check_authentication(request: Request, username: str, password: str):
    auth = request.headers.get('Authorization')
    userpass = username + ":" + password
    userpassenc = base64.b64encode(userpass.encode('utf-8'))
    if auth == ("Basic " + str(userpassenc, 'UTF-8')):
        return True
    else:
        return False


@app.get("/")
async def catch_all(request: Request, hostname: str = "", myip: str = ""):

    if not await check_authentication(request, ddns_username, ddns_password):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content="Incorrect username or password"
        )

    config = read_config()
    loc = get_location_from_config(config, hostname)

    loc_status = await check_named_location(loc, myip)
    if loc_status == "Updated":
        for x in config:
            if x.display_name == hostname:
                x.ip_address = myip
        write_config(config)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content="good " + myip
        )
    elif loc_status == "Unchanged":
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content="nochg " + myip
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content="Invalid Data"
        )


@app.get("/admin")
async def administration(request: Request):
    if not await check_authentication(request, admin_username, admin_password):

        return Response(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )

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

    if not await check_authentication(request, admin_username, admin_password):

        return Response(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )

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
async def administration(request: Request):
    if not await check_authentication(request, admin_username, admin_password):

        return Response(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )

    return templates.TemplateResponse(request=request, name="add_location.html")


@app.post("/add")
async def admin_post(request: Request,
                     location_id: str = Form(),
                     display_name: str = Form(),
                     ip_address: str = Form(),
                     is_trusted: bool = Form(False),
                     client_id: str = Form(),
                     client_secret: str = Form(),
                     tenant_id: str = Form()
                     ):

    if not await check_authentication(request, admin_username, admin_password):

        return Response(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )

    config: list[Location] = read_config()

    loc = Location(location_id = location_id,
                   display_name = display_name,
                   ip_address = ip_address,
                   is_trusted = is_trusted,
                   client_id = client_id,
                   client_secret = client_secret,
                   tenant_id = tenant_id
                   )
    config.append(loc)
    write_config(config)

    return RedirectResponse(url='/admin', status_code=302)


async def main():
    config = uvicorn.Config("main:app", port=8080, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())
