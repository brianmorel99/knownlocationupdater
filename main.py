import asyncio
import uvicorn
import base64
from graph import check_named_location
from app_config import read_config, write_config
from fastapi import FastAPI, Request, status
from fastapi.responses import Response, JSONResponse
from fastapi.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory="templates")

ddns_username = ""
ddns_password = ""
admin_username = ''
admin_password = ''


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
    loc_status = await check_named_location(config, hostname, myip)
    if loc_status == "Updated":
        for x in config:
            if x['display_name'] == hostname:
                x['ip_address'] = myip
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
    print(config)
    return templates.TemplateResponse(request=request, name="locations.html", context={"configs": config['locations']})

async def main():
    config = uvicorn.Config("main:app", port=8080, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())
