import aiohttp


async def get_gofile_server(session: aiohttp.ClientSession):
    async with session.get('https://api.gofile.io/getServer') as r:
        data = await r.json()
        return data.get('data', {}).get('server')


async def upload_file(session: aiohttp.ClientSession, filepath: str, filename: str, account_token: str | None):
    server = await get_gofile_server(session)
    if not server:
        raise RuntimeError('Could not fetch GoFile server')
    upload_url = f'https://{server}.gofile.io/uploadFile'
    form = aiohttp.FormData()
    form.add_field('file', open(filepath, 'rb'), filename=filename)
    if account_token:
        form.add_field('accountToken', account_token)
    async with session.post(upload_url, data=form) as resp:
        return await resp.json()
