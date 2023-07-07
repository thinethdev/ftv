import os
import logging
import asyncio
from pyrogram import Client, filters, errors
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from info import START_MSG, CHANNELS, ADMINS, AUTH_CHANNEL, CUSTOM_FILE_CAPTION, PICS
from utils import Media, get_file_details
from pyrogram.errors import UserNotParticipant
from db import add_user, add_group, all_users, all_groups, users, remove_user
from pyrogram.errors.exceptions.flood_420 import FloodWait
logger = logging.getLogger(__name__)

                    
@Client.on_message(filters.command("start"))
async def start(bot, cmd):
    add_user(cmd.from_user.id)
    usr_cmdall1 = cmd.text
    if usr_cmdall1.startswith("/start subinps"):
        if AUTH_CHANNEL:
            invite_link = "https://t.me/FTv4U"
            try:
                user = await bot.get_chat_member(int(AUTH_CHANNEL), cmd.from_user.id)
                if user.status == "kicked":
                    await bot.send_message(
                        chat_id=cmd.from_user.id,
                        text="Sorry Sir, You are Banned to use me.",
                        disable_web_page_preview=True
                    )
                    return
            except UserNotParticipant:
                ident, file_id = cmd.text.split("_-_-_-_")
                try_again = [[InlineKeyboardButton("🤖 Join Main Channel", url=invite_link)],
                             [InlineKeyboardButton(" 🔄 Try Again", callback_data=f"checksub#{file_id}")]]
                await bot.send_message(chat_id=cmd.from_user.id,text="**Please Join My Main Channel to use this Bot!**",reply_markup=InlineKeyboardMarkup(try_again))
                return
            except Exception:
                await bot.send_message(
                    chat_id=cmd.from_user.id,
                    text="Something went Wrong.",
                    disable_web_page_preview=True
                )
                return
        try:
            ident, file_id = cmd.text.split("_-_-_-_")
            filedetails = await get_file_details(file_id)
            for files in filedetails:
                title = files.file_name
                size=files.file_size
                f_caption1=files.caption
                if CUSTOM_FILE_CAPTION:
                    try:
                        f_caption=f"📂 File name: <code>{title}</code>\n\n📌 Powered by:  {CUSTOM_FILE_CAPTION}"
                    except Exception as e:
                        print(e)
                        f_caption=f_caption
                if f_caption is None:
                    f_caption = f"{files.file_name}"
                buttons = [
                    [
                        InlineKeyboardButton('🔍 Search again', url= 'https://t.me/CineGang4U'),
                        InlineKeyboardButton('👨‍💻 Developer', url='https://t.me/akalankanime1')
                    ]
                    ]
                await bot.send_cached_media(
                    chat_id=cmd.from_user.id,
                    file_id=file_id,
                    caption=f_caption,
                    reply_markup=InlineKeyboardMarkup(buttons)
                    )
        except Exception as err:
            await cmd.reply_text(f"Something went wrong!\n\n**Error:** `{err}`")
    elif len(cmd.command) > 1 and cmd.command[1] == 'subscribe':
        invite_link = "https://t.me/FTv4U"
        await bot.send_message(
            chat_id=cmd.from_user.id,
            text="**Please Join My Main Channel to use this Bot!**",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("🤖 Join Main Channel", url=invite_link)
                    ]
                ]
            )
        )
    else:
        await cmd.reply_photo(
            photo = PICS,
            caption = START_MSG,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton('Main Channel', url= 'https://t.me/FTv4U'),
                        InlineKeyboardButton('Main Group', url='https://t.me/CineGang4U'),
                    ],
                   [
                       InlineKeyboardButton('Franchise Hub', url='https://t.me/Franchise4U'),
                       InlineKeyboardButton('👨‍💻 Devloper', url='https://t.me/akalankanime1'),
                    ],
                     [
                        InlineKeyboardButton("About", callback_data="about")
                    ]
                ]
            )
        )
@Client.on_message(filters.command('cmd') & filters.user(ADMINS))
async def cmd(bot, message):
    await bot.send_message(chat_id=message.from_user.id,text="Here is bot commands👇👇\n\n/channel\n/index\n/total\n/logger\n/delete\n\n/stats\n/bcast")

@Client.on_message(filters.command('channel') & filters.user(ADMINS))
async def channel_info(bot, message):
    """Send basic information of channel"""
    if isinstance(CHANNELS, (int, str)):
        channels = [CHANNELS]
    elif isinstance(CHANNELS, list):
        channels = CHANNELS
    else:
        raise ValueError("Unexpected type of CHANNELS")

    text = '📑 **Indexed channels/groups**\n'
    for channel in channels:
        chat = await bot.get_chat(channel)
        if chat.username:
            text += '\n@' + chat.username
        else:
            text += '\n' + chat.title or chat.first_name

    text += f'\n\n**Total:** {len(CHANNELS)}'

    if len(text) < 4096:
        await message.reply(text)
    else:
        file = 'Indexed channels.txt'
        with open(file, 'w') as f:
            f.write(text)
        await message.reply_document(file)
        os.remove(file)

@Client.on_message(filters.command('total') & filters.user(ADMINS))
async def total(bot, message):
    """Show total files in database"""
    msg = await message.reply("Processing...⏳", quote=True)
    try:
        total = await Media.count_documents()
        await msg.edit(f'📁 Saved files: {total}')
    except Exception as e:
        logger.exception('Failed to check total files')
        await msg.edit(f'Error: {e}')


@Client.on_message(filters.command('logger') & filters.user(ADMINS))
async def log_file(bot, message):
    """Send log file"""
    try:
        await message.reply_document('TelegramBot.log')
    except Exception as e:
        await message.reply(str(e))


@Client.on_message(filters.command('delete') & filters.user(ADMINS))
async def delete(bot, message):
    """Delete file from database"""
    reply = message.reply_to_message
    if reply and reply.media:
        msg = await message.reply("Processing...⏳", quote=True)
    else:
        await message.reply('Reply to file with /delete which you want to delete', quote=True)
        return

    for file_type in ("document", "video", "audio"):
        media = getattr(reply, file_type, None)
        if media is not None:
            break
    else:
        await msg.edit('This is not supported file format')
        return

    result = await Media.collection.delete_one({
        'file_name': media.file_name,
        'file_size': media.file_size,
        'mime_type': media.mime_type
    })
    if result.deleted_count:
        await msg.edit('File is successfully deleted from database')
    else:
        await msg.edit('File not found in database')
@Client.on_message(filters.command('about'))
async def bot_info(bot, message):
    buttons = [
        [
            InlineKeyboardButton('Channel', url='https://t.me/FTv4U'),
            InlineKeyboardButton('👨‍💻 Devloper', url='https://t.me/akalankanime1')
        ]
        ]
    
    await message.reply(text="This is 1.0 Version of this Filter Bot.There will be more updates soon...\n\n\nSpecial thanks for\n<code>@TroJanZheX for their repo</code>", reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True)

@Client.on_message(filters.command("stats") & filters.user(ADMINS))
async def dbtool(_, message):
    xx = all_users()
    x = all_groups()
    tot = int(xx + x)
    await message.reply_text(text=f"""
🍀 Chats Stats 🍀
🙋‍♂️ Users : `{xx}`
👥 Groups : `{x}`
🚧 Total users & groups : `{tot}` """)
    
#bcast    
@Client.on_message(filters.command("bcast") & filters.user(ADMINS))
async def bcast(_, m):
    allusers = users
    lel = await m.reply_text("`⚡️ Processing...`")
    success = 0
    failed = 0
    deactivated = 0
    blocked = 0
    for usrs in allusers.find():
        try:
            userid = usrs["user_id"]
            #print(int(userid))
            if m.command[0] == "bcast":
                await m.reply_to_message.copy(int(userid))
            success +=1
        except FloodWait as ex:
            await asyncio.sleep(ex.value)
            if m.command[0] == "bcast":
                await m.reply_to_message.copy(int(userid))
        except errors.InputUserDeactivated:
            deactivated +=1
            remove_user(userid)
        except errors.UserIsBlocked:
            blocked +=1
        except Exception as e:
            print(e)
            failed +=1

    await lel.edit(f"✅Successfull to `{success}` users.\n❌ Faild to `{failed}` users.\n👾 Found `{blocked}` Blocked users \n👻 Found `{deactivated}` Deactivated users.")