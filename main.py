import asyncio
import uvicorn
import base64
from graph import check_named_location
from app_config import read_config, write_config
from fastapi import Depends, FastAPI, Request, status
from fastapi.responses import JSONResponse

app = FastAPI()
username = "samsa"
password = "samsa"

@app.middleware("http")
async def check_authentication(request: Request, call_next):
    auth = request.headers.get('Authorization')
    userpass = username + ":" + password
    userpassenc = base64.b64encode(userpass.encode('utf-8'))
    if auth == ("Basic " + str(userpassenc, 'UTF-8')):
       print("Authorized")
    else:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content="Incorrect username or password"
        )
    
    return await call_next(request)


@app.get("/")
async def catch_all(request: Request, hostname: str = "", myip: str = ""):
    print("Hostname :" + hostname)
    print("IP Address: " + myip)
    config = read_config()
    loc_status = await check_named_location(config, hostname, myip)
    if loc_status == "Updated":
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
    
    

async def main():
    config = read_config()
    # status = await check_named_location(config, 'prschesaning.homeip.net', '174.84.114.106')
    # print(status)
    # await list_named_locations(config)
    config = uvicorn.Config("main:app", port=8080, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())