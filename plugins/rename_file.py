#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (c) Shrimadhav U K

# the logging things
import logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

import os
import time
import random
import shutil

# the secret configuration specific things
if bool(os.environ.get("WEBHOOK", False)):
    from sample_config import Config
else:
    from config import Config

# the Strings used for this "thing"
from translation import Translation

import pyrogram
logging.getLogger("pyrogram").setLevel(logging.WARNING)

from helper_funcs.display_progress import progress_for_pyrogram
from helper_funcs.ran_text import random_char

from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
# https://stackoverflow.com/a/37631799/4723940
from PIL import Image


@pyrogram.Client.on_message(pyrogram.filters.command(["ren"]))
async def rename_doc(bot, update):
    if update.from_user.id not in Config.AUTH_USERS:
        await bot.delete_messages(
            chat_id=update.chat.id,
            message_ids=update.message.id,
            revoke=True
        )
        return
    if (" " in update.text) and (update.reply_to_message is not None):
        cmd, file_name = update.text.split(" ", 1)
        description = Translation.CUSTOM_CAPTION_UL_FILE
        rfhf = random_char(5)
        download_location = Config.DOWNLOAD_LOCATION + "/" + f'{rfhf}' + "/"
        a = await bot.send_message(
            chat_id=update.chat.id,
            text=Translation.DOWNLOAD_FILE,
            reply_to_message_id=update.message.id
        )
        c_time = time.time()
        the_real_download_location = await bot.download_media(
            message=update.reply_to_message,
            file_name=download_location,
            progress=progress_for_pyrogram,
            progress_args=(
                Translation.DOWNLOAD_FILE,
                a,
                c_time
            )
        )
        await a.delete()
        if the_real_download_location is None:
            await bot.send_message(
                text=Translation.FILE_NOT_FOUND,
                chat_id=update.chat.id,
                reply_to_message_id=update.message.id
            )
        else:
            if "IndianMovie" in the_real_download_location:
                await bot.edit_message_text(
                    text=Translation.RENAME_403_ERR,
                    chat_id=update.chat.id,
                    message_id=a.message.id
                )
                return
            new_file_name = download_location + file_name
            os.rename(the_real_download_location, new_file_name)
            capp=file_name.split(".", 1)[0]
            up = await bot.send_message(
                text=Translation.UPLOAD_START,
                chat_id=update.chat.id,
                reply_to_message_id=update.message.id,
            )
            logger.info(the_real_download_location)
            thumb_image_path = Config.DOWNLOAD_LOCATION + "/" + str(update.from_user.id) + "_" + ".jpg"
            if not os.path.exists(thumb_image_path):
                try:
                    thumb_image_path = await take_screen_shot(new_file_name, os.path.dirname(new_file_name), random.randint(0, duration - 1))
                except:
                    thumb_image_path = None
            else:
                width = 0
                height = 0
                metadata = extractMetadata(createParser(thumb_image_path))
                if metadata.has("width"):
                    width = metadata.get("width")
                if metadata.has("height"):
                    height = metadata.get("height")
                # resize image
                # ref: https://t.me/PyrogramChat/44663
                # https://stackoverflow.com/a/21669827/4723940
                Image.open(thumb_image_path).convert("RGB").save(thumb_image_path)
                img = Image.open(thumb_image_path)
                # https://stackoverflow.com/a/37631799/4723940
                # img.thumbnail((90, 90))
                img.resize((320, height))
                img.save(thumb_image_path, "JPEG")
                # https://pillow.readthedocs.io/en/3.1.x/reference/Image.html#create-thumbnails
            c_time = time.time()
            await bot.send_document(
                chat_id=update.chat.id,
                document=new_file_name,
                thumb=thumb_image_path,
                caption=capp,
                # reply_markup=reply_markup,
                reply_to_message_id=update.reply_to_message.message.id,
                progress=progress_for_pyrogram,
                progress_args=(
                    Translation.UPLOAD_START,
                    up, 
                    c_time
                )
            )
            try:
                os.remove(new_file_name)
                os.remove(thumb_image_path)
                shutil.rmtree(download_location)
            except:
                pass
            await bot.edit_message_text(
                text=Translation.AFTER_SUCCESSFUL_UPLOAD_MSG,
                chat_id=update.chat.id,
                message_id=up.message.id,
                disable_web_page_preview=True
            )
    else:
        await bot.send_message(
            chat_id=update.chat.id,
            text=Translation.REPLY_TO_DOC_FOR_RENAME_FILE,
            reply_to_message_id=update.message.id
        )
