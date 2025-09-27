import os
import asyncio
from pyrogram import Client
from pyrogram.types import Message

async def text_to_txt(bot: Client, message: Message):
    user_id = str(message.from_user.id)
    await message.reply_text(
        "<b>Welcome! Send me multiple texts one by one to convert into `.txt` files.\n"
        "After sending all texts, type <code>/done</code> to start uploading.</b>"
    )

    files = []

    while True:
        input_message: Message = await bot.listen(message.chat.id)

        # Finish input
        if input_message.text and input_message.text.lower() == "/done":
            await input_message.delete()
            break

        # Ignore non-text
        if not input_message.text:
            await message.reply_text("❌ Please send plain text or /done to finish.")
            continue

        text_data = input_message.text.strip()
        await input_message.delete()

        # Ask for filename
        ask_name = await message.reply_text("🔄 Send file name or send /d for default name.")
        inputn: Message = await bot.listen(message.chat.id)
        raw_textn = inputn.text.strip()
        await inputn.delete()
        await ask_name.delete()

        if raw_textn == "/d":
            custom_file_name = f"txt_file_{len(files)+1}"
        else:
            custom_file_name = raw_textn

        txt_file = os.path.join("downloads", f"{custom_file_name}.txt")
        os.makedirs(os.path.dirname(txt_file), exist_ok=True)

        with open(txt_file, "w", encoding="utf-8") as f:
            f.write(text_data)

        files.append(txt_file)
        await message.reply_text(f"✅ Added `{custom_file_name}.txt` to upload queue.")

    # Process uploads
    for file_path in files:
        retries = 3
        success = False
        while retries > 0 and not success:
            try:
                await message.reply_document(
                    document=file_path,
                    caption=f"`{os.path.basename(file_path)}`\n\n📥 Uploaded successfully!"
                )
                success = True
            except Exception as e:
                retries -= 1
                if retries > 0:
                    await message.reply_text(
                        f"⚠️ Retry {4-retries}/3 for {os.path.basename(file_path)} due to error: {e}"
                    )
                    await asyncio.sleep(2)
                else:
                    await message.reply_text(
                        f"❌ Failed to upload {os.path.basename(file_path)} after 3 retries."
                    )
        os.remove(file_path)
