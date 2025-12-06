from aiohttp import web

async def handle(request):
    return web.Response(text="Bot is Running!")

async def web_server():
    web_app = web.Application(client_max_size=30000000)
    web_app.add_routes([web.get('/', handle)])
    return web_app
