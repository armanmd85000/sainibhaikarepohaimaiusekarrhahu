import os
import re
import sys
import json
import time
import pytz
import asyncio
import requests
import subprocess
import random
from pyromod import listen
from pyrogram import Client, filters
from pyrogram.errors.exceptions.bad_request_400 import StickerEmojiInvalid
from pyrogram.types.messages_and_media import message
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, InputMediaPhoto

import globals
from html_handler import html_handler
from drm_handler import drm_handler
from text_handler import text_to_txt   # <-- updated multi-file handler
from features import register_feature_handlers
from upgrade import register_upgrade_handlers
from commands import register_commands_handlers
from settings import register_settings_handlers
from broadcast import broadcast_handler, broadusers_handler
from authorisation import add_auth_user, list_auth_users, remove_auth_user
from youtube_handler import ytm_handler, y2t_handler, getcookies_handler, cookies_handler
from vars import API_ID, API_HASH, BOT_TOKEN, OWNER, CREDIT, AUTH_USERS, TOTAL_USERS, cookies_file_path

# =====================
# Initialize the bot
# =====================
bot = Client(
    "bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# =====================
# Register handlers
# =====================
register_feature_handlers(bot)
register_settings_handlers(bot)
register_upgrade_handlers(bot)
register_commands_handlers(bot)

# =====================
# START command
# =====================
@bot.on_message(filters.command("start"))
async def start(bot, m: Message):
    user_id = m.chat.id
    if user_id not in TOTAL_USERS:
        TOTAL_USERS.append(user_id)

    start_message = await bot.send_photo(
        chat_id=m.chat.id,
        photo="https://iili.io/KuCBoV2.jpg",
        caption=f"🌟 Welcome {m.from_user.mention} ! 🌟"
    )

    # Fake progress loader
    stages = [
        ("Initializing Uploader bot... 🤖", "⬜️" * 10, 0),
        ("Loading features... ⏳", "🟥" * 3 + "⬜️" * 7, 25),
        ("This may take a moment, sit back and relax! 😊", "🟧" * 5 + "⬜️" * 5, 50),
        ("Checking subscription status... 🔍", "🟨" * 8 + "⬜️" * 2, 75),
    ]
    for text, bar, percent in stages:
        await asyncio.sleep(1)
        await start_message.edit_text(
            f"🌟 Welcome {m.from_user.first_name}! 🌟\n\n{text}\n\nProgress: [{bar}] {percent}%"
        )

    # Subscription check
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✨ Commands", callback_data="cmd_command")],
        [InlineKeyboardButton("💎 Features", callback_data="feat_command"),
         InlineKeyboardButton("⚙️ Settings", callback_data="setttings")],
        [InlineKeyboardButton("💳 Plans", callback_data="upgrade_command")],
        [InlineKeyboardButton(text="📞 Contact", url=f"tg://openmessage?user_id={OWNER}"),
         InlineKeyboardButton(text="🛠️ Repo", url="https://github.com/nikhilsainiop/saini-txt-direct")]
    ])

    if m.chat.id in AUTH_USERS:
        await start_message.edit_text(
            f"🌟 Welcome {m.from_user.first_name}! 🌟\n\n"
            f"Great! You are a premium member!\n"
            f"Use button : **✨ Commands** to get started 🌟\n\n"
            f"If you face any problem contact -  [{CREDIT}](tg://openmessage?user_id={OWNER})\n",
            disable_web_page_preview=True,
            reply_markup=keyboard
        )
    else:
        await start_message.edit_text(
            f"🎉 Welcome {m.from_user.first_name} to DRM Bot! 🎉\n\n"
            f"**You are currently using the free version.** 🆓\n\n"
            f"<blockquote expandable>I'm here to make your life easier by downloading videos "
            f"from your **.txt** file 📄 and uploading them directly to Telegram!</blockquote>\n\n"
            f"**Want to get started? Press /id**\n\n💬 Contact : [{CREDIT}](tg://openmessage?user_id={OWNER}) "
            f"to Get The Subscription 🎫 and unlock the full potential of your new bot! 🔓\n",
            disable_web_page_preview=True,
            reply_markup=keyboard
        )

# =====================
# OTHER COMMANDS
# =====================
@bot.on_callback_query(filters.regex("back_to_main_menu"))
async def back_to_main_menu(client, callback_query):
    caption = f"✨ **Welcome [{callback_query.from_user.first_name}](tg://user?id={callback_query.from_user.id}) in My uploader bot**"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✨ Commands", callback_data="cmd_command")],
        [InlineKeyboardButton("💎 Features", callback_data="feat_command"),
         InlineKeyboardButton("⚙️ Settings", callback_data="setttings")],
        [InlineKeyboardButton("💳 Plans", callback_data="upgrade_command")],
        [InlineKeyboardButton(text="📞 Contact", url=f"tg://openmessage?user_id={OWNER}"),
         InlineKeyboardButton(text="🛠️ Repo", url="https://github.com/nikhilsainiop/saini-txt-direct")]
    ])
    await callback_query.message.edit_media(
        InputMediaPhoto(media="https://envs.sh/GVI.jpg", caption=caption),
        reply_markup=keyboard
    )
    await callback_query.answer()

@bot.on_message(filters.command(["id"]))
async def id_command(client, message: Message):
    await message.reply_text(f"<b>The ID of this chat is:</b>\n`{message.chat.id}`")

@bot.on_message(filters.private & filters.command(["info"]))
async def info(bot: Client, update: Message):
    text = (
        f"╭────────────────╮\n"
        f"│✨ **Your Telegram Info** ✨ \n"
        f"├────────────────\n"
        f"├🔹**Name :** `{update.from_user.first_name} {update.from_user.last_name or ''}`\n"
        f"├🔹**User ID :** @{update.from_user.username}\n"
        f"├🔹**TG ID :** `{update.from_user.id}`\n"
        f"├🔹**Profile :** {update.from_user.mention}\n"
        f"╰────────────────╯"
    )
    await update.reply_text(text, disable_web_page_preview=True)

@bot.on_message(filters.command(["logs"]))
async def send_logs(client: Client, m: Message):
    try:
        with open("logs.txt", "rb") as file:
            sent = await m.reply_text("**📤 Sending you ....**")
            await m.reply_document(document=file)
            await sent.delete()
    except Exception as e:
        await m.reply_text(f"**Error sending logs:**\n<blockquote>{e}</blockquote>")

@bot.on_message(filters.command(["reset"]))
async def restart_handler(_, m):
    if m.chat.id == OWNER:
        await m.reply_text("𝐁𝐨𝐭 𝐢𝐬 𝐑𝐞𝐬𝐞𝐭𝐢𝐧𝐠...", True)
        os.execl(sys.executable, sys.executable, *sys.argv)

@bot.on_message(filters.command(["stop"]))
async def cancel_handler(client: Client, m: Message):
    if m.chat.id not in AUTH_USERS:
        await bot.send_message(
            m.chat.id,
            f"<blockquote>__**Oops! You are not a Premium member**__\n"
            f"__**PLEASE /upgrade YOUR PLAN**__\n"
            f"__**Send me your user id for authorization**__\n"
            f"__**Your User id** __- `{m.chat.id}`</blockquote>"
        )
    else:
        if globals.processing_request:
            globals.cancel_requested = True
            await m.delete()
            cancel_message = await m.reply_text("**🚦 Process cancel request received. Stopping after current process...**")
            await asyncio.sleep(30)
            await cancel_message.delete()
        else:
            await m.reply_text("**⚡ No active process to cancel.**")

# Auth
@bot.on_message(filters.command("addauth"))
async def call_add_auth_user(client: Client, message: Message):
    await add_auth_user(client, message)

@bot.on_message(filters.command("users"))
async def call_list_auth_users(client: Client, message: Message):
    await list_auth_users(client, message)

@bot.on_message(filters.command("rmauth"))
async def call_remove_auth_user(client: Client, message: Message):
    await remove_auth_user(client, message)

# Broadcast
@bot.on_message(filters.command("broadcast"))
async def call_broadcast_handler(client: Client, message: Message):
    await broadcast_handler(client, message)

@bot.on_message(filters.command("broadusers"))
async def call_broadusers_handler(client: Client, message: Message):
    await broadusers_handler(client, message)

# Cookies
@bot.on_message(filters.command("cookies"))
async def call_cookies_handler(client: Client, m: Message):
    await cookies_handler(client, m)

@bot.on_message(filters.command(["t2t"]))
async def call_text_to_txt(bot: Client, m: Message):
    await text_to_txt(bot, m)   # multi-file handler now

@bot.on_message(filters.command(["y2t"]))
async def call_y2t_handler(bot: Client, m: Message):
    await y2t_handler(bot, m)

@bot.on_message(filters.command(["ytm"]))
async def call_ytm_handler(bot: Client, m: Message):
    await ytm_handler(bot, m)

@bot.on_message(filters.command("getcookies"))
async def call_getcookies_handler(client: Client, m: Message):
    await getcookies_handler(client, m)

@bot.on_message(filters.command(["t2h"]))
async def call_html_handler(bot: Client, message: Message):
    await html_handler(bot, message)

# DRM auto handler
@bot.on_message(filters.private & (filters.document | filters.text))
async def call_drm_handler(bot: Client, m: Message):
    await drm_handler(bot, m)

# =====================
# Owner Notify + Commands
# =====================
def notify_owner():
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={"chat_id": OWNER, "text": "𝐁𝐨𝐭 𝐑𝐞𝐬𝐭𝐚𝐫𝐭𝐞𝐝 𝐒𝐮𝐜𝐜𝐞𝐬𝐬𝐟𝐮𝐥𝐥𝐲 ✅"}
    )

def reset_and_set_commands():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/setMyCommands"
    requests.post(url, json={"commands": []})
    commands = [
        {"command": "start", "description": "✅ Check Alive the Bot"},
        {"command": "stop", "description": "🚫 Stop the ongoing process"},
        {"command": "id", "description": "🆔 Get Your ID"},
        {"command": "info", "description": "ℹ️ Check Your Information"},
        {"command": "cookies", "description": "📁 Upload YT Cookies"},
        {"command": "y2t", "description": "🔪 YouTube → .txt Converter"},
        {"command": "ytm", "description": "🎶 YouTube → .mp3 downloader"},
        {"command": "t2t", "description": "📟 Text → .txt Generator (multi-file)"},
        {"command": "t2h", "description": "🌐 .txt → .html Converter"},
        {"command": "logs", "description": "👁️ View Bot Activity"},
        {"command": "broadcast", "description": "📢 Broadcast to All Users"},
        {"command": "broadusers", "description": "👨‍❤️‍👨 All Broadcasting Users"},
        {"command": "addauth", "description": "▶️ Add Authorisation"},
        {"command": "rmauth", "description": "⏸️ Remove Authorisation"},
        {"command": "users", "description": "👨‍👨‍👧‍👦 All Premium Users"},
        {"command": "reset", "description": "✅ Reset the Bot"}
    ]
    requests.post(url, json={"commands": commands})

# =====================
# RUN BOT
# =====================
if __name__ == "__main__":
    reset_and_set_commands()
    notify_owner()

bot.run()
