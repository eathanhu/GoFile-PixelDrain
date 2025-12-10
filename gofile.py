import aiohttp


async def get_gofile_server(session: aiohttp.ClientSession):
    """Get the best GoFile server for uploading."""
    try:
        async with session.get('https://api.gofile.io/getServer') as r:
            data = await r.json()
            return data.get('data', {}).get('server')
    except Exception as e:
        raise RuntimeError(f'Could not fetch GoFile server: {e}')


async def upload_file(session: aiohttp.ClientSession, filepath: str, filename: str, account_token: str | None):
    """Upload file to GoFile."""
    server = await get_gofile_server(session)
    if not server:
        raise RuntimeError('Could not fetch GoFile server')
    
    upload_url = f'https://{server}.gofile.io/uploadFile'
    
    # Use context manager for file to ensure proper closure
    with open(filepath, 'rb') as file:
        form = aiohttp.FormData()
        form.add_field('file', file, filename=filename)
        if account_token:
            form.add_field('token', account_token)
        
        async with session.post(upload_url, data=form) as resp:
            result = await resp.json()
            if result.get('status') != 'ok':
                raise RuntimeError(f"GoFile upload failed: {result}")
            return result
