import aiohttp

PIXEL_UPLOAD = 'https://pixeldrain.com/api/file'


async def upload_file(session: aiohttp.ClientSession, filepath: str, filename: str, api_key: str | None):
    data = aiohttp.FormData()
    data.add_field('file', open(filepath, 'rb'), filename=filename)
    if api_key:
        data.add_field('key', api_key)
    async with session.post(PIXEL_UPLOAD, data=data) as resp:
        return await resp.json()
