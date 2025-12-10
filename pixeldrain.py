import aiohttp

PIXEL_UPLOAD = 'https://pixeldrain.com/api/file'


async def upload_file(session: aiohttp.ClientSession, filepath: str, filename: str, api_key: str | None):
    """Upload file to Pixeldrain."""
    # Use context manager for file to ensure proper closure
    with open(filepath, 'rb') as file:
        data = aiohttp.FormData()
        data.add_field('file', file, filename=filename)
        
        headers = {}
        if api_key:
            headers['Authorization'] = f'Basic {api_key}'
        
        async with session.post(PIXEL_UPLOAD, data=data, headers=headers) as resp:
            result = await resp.json()
            if not result.get('success', True) and 'id' not in result:
                raise RuntimeError(f"Pixeldrain upload failed: {result}")
            return result
