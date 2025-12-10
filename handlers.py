import os
import tempfile
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import aiohttp

from bot.db import get_user, set_user_token
from bot.utils import human_readable_size, progress_bar
from bot.gofile import upload_file as gofile_upload
from bot.pixeldrain import upload_file as pixeldrain_upload

pending_set = {}


def settings_keyboard_for_user(user_id: int):
    doc = get_user(user_id)
    go_tick = "✅" if doc.get('gofile_token') else "❌"
    pd_tick = "✅" if doc.get('pixeldrain_key') else "❌"
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"GoFile API: {go_tick}", callback_data='noop')],
        [InlineKeyboardButton(f"Pixeldrain API: {pd_tick}", callback_data='noop')],
        [InlineKeyboardButton('Set GoFile Token', callback_data='set_gofile'), 
         InlineKeyboardButton('Remove GoFile', callback_data='remove_gofile')],
        [InlineKeyboardButton('Set Pixeldrain Key', callback_data='set_pixeldrain'), 
         InlineKeyboardButton('Remove Pixeldrain', callback_data='remove_pixeldrain')],
        [InlineKeyboardButton('Close', callback_data='close_settings')]
    ])
    return kb


@Client.on_message(filters.command("start"))
async def start_handler(client, message):
    text = (
        "Hi! I can upload files to <b>GoFile</b> or <b>Pixeldrain</b>.\n\n"
        "Supported:\n"
        "• GoFile (account token optional)\n"
        "• Pixeldrain (API key optional)\n\n"
        "Use <code>/settings</code> to add your API token for a smoother upload experience."
    )
    await message.reply_text(text, disable_web_page_preview=True)


@Client.on_message(filters.command('help'))
async def help_handler(client, message):
    await message.reply_text('Owner: @Franited')


@Client.on_message(filters.command('settings'))
async def settings_cmd(client, message):
    kb = settings_keyboard_for_user(message.from_user.id)
    await message.reply_text('Settings:', reply_markup=kb)


@Client.on_callback_query()
async def callbacks(client, cb):
    data = cb.data
    uid = cb.from_user.id
    
    if data == 'noop':
        await cb.answer()
        return
        
    if data == 'set_gofile':
        pending_set[uid] = {'kind': 'gofile'}
        await cb.message.edit_text('Please send the GoFile account token (or `none` to cancel).')
        await cb.answer()
        return
        
    if data == 'set_pixeldrain':
        pending_set[uid] = {'kind': 'pixeldrain'}
        await cb.message.edit_text('Please send the Pixeldrain API key (or `none` to cancel).')
        await cb.answer()
        return
        
    if data == 'remove_gofile':
        set_user_token(uid, 'gofile_token', None)
        await cb.message.edit_text('GoFile token removed.', reply_markup=settings_keyboard_for_user(uid))
        await cb.answer('Removed')
        return
        
    if data == 'remove_pixeldrain':
        set_user_token(uid, 'pixeldrain_key', None)
        await cb.message.edit_text('Pixeldrain key removed.', reply_markup=settings_keyboard_for_user(uid))
        await cb.answer('Removed')
        return
        
    if data == 'close_settings':
        await cb.message.delete()
        await cb.answer()
        return
        
    await cb.answer()


@Client.on_message(filters.text & ~filters.command(['start', 'help', 'settings']))
async def text_handler(client, message):
    uid = message.from_user.id
    if uid in pending_set:
        kind = pending_set[uid]['kind']
        token = message.text.strip()
        if token.lower() in ('none', 'cancel'):
            pending_set.pop(uid, None)
            await message.reply_text('Cancelled.', reply_markup=settings_keyboard_for_user(uid))
            return
        if kind == 'gofile':
            set_user_token(uid, 'gofile_token', token)
            await message.reply_text('GoFile token saved.', reply_markup=settings_keyboard_for_user(uid))
        else:
            set_user_token(uid, 'pixeldrain_key', token)
            await message.reply_text('Pixeldrain key saved.', reply_markup=settings_keyboard_for_user(uid))
        pending_set.pop(uid, None)


@Client.on_message(filters.document | filters.video | filters.audio | filters.photo)
async def file_handler(client, message):
    uid = message.from_user.id
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton('GoFile', callback_data='choose_gofile'), 
         InlineKeyboardButton('Pixeldrain', callback_data='choose_pixeldrain')],
        [InlineKeyboardButton('Cancel', callback_data='cancel_upload')]
    ])
    prompt = await message.reply_text('Choose host to upload to:', reply_markup=kb)
    
    if not hasattr(client, 'storage'):
        client.storage = {}
    client.storage[uid] = {'message': message, 'prompt': prompt}


@Client.on_callback_query(filters.regex('choose_(gofile|pixeldrain)|cancel_upload'))
async def choose_cb(client, cb):
    uid = cb.from_user.id
    data = cb.data
    
    if data == 'cancel_upload':
        await cb.message.edit_text('Cancelled.')
        await cb.answer()
        return
        
    which = 'gofile' if 'gofile' in data else 'pixeldrain'
    stored = getattr(client, 'storage', {}).get(uid)
    
    if not stored:
        await cb.answer('No file stored or session expired.', show_alert=True)
        return
        
    orig_msg = stored['message']
    await cb.message.edit_text(f'Starting: download -> upload to {which}...')

    # Get file info
    f = orig_msg.document or orig_msg.video or orig_msg.audio or orig_msg.photo
    if orig_msg.photo:
        f = orig_msg.photo
        filename = f'photo_{orig_msg.message_id}.jpg'
        total = 0  # Photos don't have file_size attribute
    else:
        filename = getattr(f, 'file_name', None) or f'{orig_msg.message_id}'
        total = getattr(f, 'file_size', 0)

    # Create temp file
    tempf = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1])
    temp_path = tempf.name
    tempf.close()

    dl_msg = await orig_msg.reply_text('Downloading...')
    start = asyncio.get_event_loop().time()
    last_update = [0]  # Use list to allow modification in nested function

    async def dl_progress(current, total_):
        now = asyncio.get_event_loop().time()
        # Update only every 2 seconds to avoid rate limits
        if now - last_update[0] < 2:
            return
        last_update[0] = now
        
        elapsed = now - start
        speed = current / elapsed if elapsed > 0 else 0
        eta = (total_ - current) / speed if speed > 0 else 0
        text = (
            f"Downloading {human_readable_size(current)}/{human_readable_size(total_)}\n"
            f"{progress_bar(current, total_)}\n"
            f"Speed: {human_readable_size(int(speed))}/s\n"
            f"ETA: {int(eta)}s"
        )
        try:
            await dl_msg.edit_text(text)
        except Exception:
            pass

    try:
        await orig_msg.download(file_name=temp_path, progress=dl_progress)
        await dl_msg.edit_text('Download complete!')
    except Exception as e:
        await dl_msg.edit_text(f'Download failed: {e}')
        try:
            os.remove(temp_path)
        except:
            pass
        await cb.answer()
        return

    # Get actual file size after download
    if total == 0:
        total = os.path.getsize(temp_path)

    upl_msg = await orig_msg.reply_text('Uploading...')
    user_doc = get_user(uid)

    async with aiohttp.ClientSession() as session:
        try:
            if which == 'pixeldrain':
                res = await pixeldrain_upload(session, temp_path, filename, user_doc.get('pixeldrain_key'))
                fid = res.get('id') or res.get('file')
                if not fid:
                    raise Exception(f"Upload failed: {res}")
                url = f'https://pixeldrain.com/u/{fid}'
                await upl_msg.edit_text(
                    f"✅ Uploaded to Pixeldrain\n\n"
                    f"📁 File: <code>{filename}</code>\n"
                    f"📦 Size: {human_readable_size(total)}\n"
                    f"🔗 Link: {url}"
                )
            else:
                res = await gofile_upload(session, temp_path, filename, user_doc.get('gofile_token'))
                data_field = res.get('data', {})
                download_page = data_field.get('downloadPage') or data_field.get('directLink')
                if not download_page:
                    raise Exception(f"Upload failed: {res}")
                await upl_msg.edit_text(
                    f"✅ Uploaded to GoFile\n\n"
                    f"📁 File: <code>{filename}</code>\n"
                    f"📦 Size: {human_readable_size(total)}\n"
                    f"🔗 Link: {download_page}"
                )
        except Exception as e:
            await upl_msg.edit_text(f'❌ Upload failed: {e}')

    # Cleanup
    try:
        os.remove(temp_path)
    except Exception:
        pass

    # Clear storage
    if hasattr(client, 'storage') and uid in client.storage:
        del client.storage[uid]

    await cb.answer()
