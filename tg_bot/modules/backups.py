import json
from io import BytesIO
from typing import Optional

from telegram import Message, Chat, Update, Bot
from telegram.error import BadRequest
from telegram.ext import CommandHandler, run_async

from tg_bot import dispatcher, LOGGER
from tg_bot.__main__ import DATA_IMPORT
from tg_bot.modules.helper_funcs.chat_status import user_admin


@run_async
@user_admin
def import_data(bot: Bot, update):
    msg = update.effective_message  # type: Optional[Message]
    chat = update.effective_chat  # type: Optional[Chat]
    # TODO: allow uploading doc with command, not just as reply
    # only work with a doc
    if msg.reply_to_message and msg.reply_to_message.document:
        try:
            file_info = bot.get_file(msg.reply_to_message.document.file_id)
        except BadRequest:
            msg.reply_text("Coba unduh dan unggah ulang file seperti Anda sendiri sebelum mengimpor - yang ini sepertinya "
                           "rusak!")
            return

        with BytesIO() as file:
            file_info.download(out=file)
            file.seek(0)
            data = json.load(file)

        # only import one group
        if len(data) > 1 and str(chat.id) not in data:
            msg.reply_text("Ada lebih dari satu grup di file ini, dan tidak ada yang memiliki id obrolan yang sama dengan"
                           "grup ini - bagaimana cara memilih apa yang akan diimpor?")
            return

        # Select data source
        if str(chat.id) in data:
            data = data[str(chat.id)]['hashes']
        else:
            data = data[list(data.keys())[0]]['hashes']

        try:
            for mod in DATA_IMPORT:
                mod.__import_data__(str(chat.id), data)
        except Exception:
            msg.reply_text("Pengecualian terjadi saat memulihkan data Anda. Prosesnya mungkin tidak lengkap. Jika "
                           "Anda mengalami masalah dengan ini, pesan @MarieSupport dengan file cadangan Anda, jadi "
                           "masalah bisa di-debug. Pemilik saya akan dengan senang hati membantu, dan setiap bug "
                           "dilaporkan membuat saya lebih baik! Terima kasih! 🙂")
            LOGGER.exception("Impor untuk id chat %s dengan nama %s gagal.", str(chat.id), str(chat.title))
            return

        # TODO: some of that link logic
        # NOTE: consider default permissions stuff?
        msg.reply_text("Cadangan sepenuhnya diimpor. Selamat datang kembali! 😀")


@run_async
@user_admin
def export_data(bot: Bot, update: Update):
    msg = update.effective_message  # type: Optional[Message]
    msg.reply_text("")


__mod_name__ = "Backups"

__help__ = """
*Hanya admin:*
 - /import: balas ke file cadangan grup butler untuk mengimpor sebanyak mungkin, membuat transfer menjadi sangat mudah! \
 Catatan bahwa file/foto tidak dapat diimpor karena pembatasan telegram.
 - /export: !!! Ini bukan perintah, tetapi harus segera hadir!
"""
IMPORT_HANDLER = CommandHandler("import", import_data)
EXPORT_HANDLER = CommandHandler("export", export_data)

dispatcher.add_handler(IMPORT_HANDLER)
# dispatcher.add_handler(EXPORT_HANDLER)
