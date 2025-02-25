import asyncio
from graph import check_named_location
from app_config import read_config, write_config



async def main():

    config = read_config()
    status = await check_named_location(config, 'prschesaning.homeip.net', '174.84.114.106')
    print(status)
    # await list_named_locations(config)

   

# Run main
asyncio.run(main())
