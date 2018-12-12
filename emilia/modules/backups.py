import json, time
from io import BytesIO
from typing import Optional

from telegram import MAX_MESSAGE_LENGTH, ParseMode, InlineKeyboardMarkup
from telegram import Message, Chat, Update, Bot
from telegram.error import BadRequest
from telegram.ext import CommandHandler, run_async, Filters

import emilia.modules.sql.notes_sql as sql
from emilia import dispatcher, LOGGER, OWNER_ID, SUDO_USERS
from emilia.__main__ import DATA_IMPORT
from emilia.modules.helper_funcs.chat_status import user_admin
from emilia.modules.helper_funcs.misc import build_keyboard, revert_buttons
from emilia.modules.helper_funcs.msg_types import get_note_type
from emilia.modules.rules import get_rules
import emilia.modules.sql.rules_sql as rulessql
from emilia.modules.sql import warns_sql as warnssql

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

        # Check if backup is this chat
        try:
            if data.get(str(chat.id)) == None:
                return msg.reply_text("Backup berasal chat lain, Saya tidak bisa mengembalikan chat lain kedalam chat ini")
        except:
            return msg.reply_text("Telah terjadi error dalam pengecekan data, silahkan laporkan kepada pembuat saya "
                                  "untuk masalah ini untuk membuat saya lebih baik! Terima kasih! 🙂")
        # Check if backup is from self
        try:
            if str(bot.id) != str(data[str(chat.id)]['bot']):
                return msg.reply_text("Backup berasal dari bot lain, dokumen, foto, video, audio, suara tidak akan "
                               "bekerja, jika file anda tidak ingin hilang, import dari bot yang dicadangkan."
                               "jika masih tidak bekerja, laporkan pada pembuat bot tersebut untuk "
                               "membuat saya lebih baik! Terima kasih! 🙂")
        except:
            pass
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
                           "Anda mengalami masalah dengan ini, pesan @AyraHikari dengan file cadangan Anda, jadi "
                           "masalah bisa di-debug. Pemilik saya akan dengan senang hati membantu, dan setiap bug "
                           "dilaporkan membuat saya lebih baik! Terima kasih! 🙂")
            LOGGER.exception("Impor untuk id chat %s dengan nama %s gagal.", str(chat.id), str(chat.title))
            return

        # TODO: some of that link logic
        # NOTE: consider default permissions stuff?
        msg.reply_text("Cadangan sepenuhnya dikembalikan. Selamat datang kembali! 😀")


@run_async
@user_admin
def export_data(bot: Bot, update: Update):
    msg = update.effective_message  # type: Optional[Message]
    chat_id = update.effective_chat.id
    chat = update.effective_chat
    note_list = sql.get_all_chat_notes(chat_id)
    backup = {}
    notes = {}
    button = ""
    buttonlist = []
    namacat = ""
    isicat = ""
    rules = ""
    count = 0
    countbtn = 0
    # Notes
    for note in note_list:
        count += 1
        getnote = sql.get_note(chat_id, note.name)
        namacat += '{}<###splitter###>'.format(note.name)
        if note.msgtype == 1:
            tombol = sql.get_buttons(chat_id, note.name)
            keyb = []
            for btn in tombol:
                countbtn += 1
                if btn.same_line:
                    buttonlist.append(('{}'.format(btn.name), '{}'.format(btn.url), True))
                else:
                    buttonlist.append(('{}'.format(btn.name), '{}'.format(btn.url), False))
            isicat += '###button###: {}<###button###>{}<###splitter###>'.format(note.value,str(buttonlist))
            buttonlist.clear()
        elif note.msgtype == 2:
            isicat += '###sticker###:{}<###splitter###>'.format(note.file)
        elif note.msgtype == 3:
            isicat += '###file###:{}<###TYPESPLIT###>{}<###splitter###>'.format(note.file, note.value)
        elif note.msgtype == 4:
            isicat += '###photo###:{}<###TYPESPLIT###>{}<###splitter###>'.format(note.file, note.value)
        elif note.msgtype == 5:
            isicat += '###audio###:{}<###TYPESPLIT###>{}<###splitter###>'.format(note.file, note.value)
        elif note.msgtype == 6:
            isicat += '###voice###:{}<###TYPESPLIT###>{}<###splitter###>'.format(note.file, note.value)
        elif note.msgtype == 7:
            isicat += '###video###:{}<###TYPESPLIT###>{}<###splitter###>'.format(note.file, note.value)
        else:
            isicat += '{}<###splitter###>'.format(note.value)
    for x in range(count):
        notes['#{}'.format(namacat.split("<###splitter###>")[x])] = '{}'.format(isicat.split("<###splitter###>")[x])
    # Rules
    rules = rulessql.get_rules(chat_id)
    # Warns
    #warns = warnssql.get_warns(chat_id)
    backup[chat_id] = {'bot': bot.id, 'hashes': {'info': {'rules': rules}, 'extra': notes}}
    catatan = json.dumps(backup, indent=4)
    f=open("cadangan{}.backup".format(chat_id), "w")
    f.write(str(catatan))
    f.close()
    bot.sendChatAction(chat_id, "upload_document")
    tgl = time.strftime("%H:%M:%S - %d/%m/%Y", time.localtime(time.time()))
    bot.sendDocument(chat_id, document=open('cadangan{}.backup'.format(chat_id), 'rb'), caption="*Berhasil mencadangan untuk:*\nNama chat: `{}`\nID chat: `{}`\nPada: `{}`\n\nNote: cadangan ini khusus untuk bot ini, jika di import ke bot lain maka catatan dokumen, video, audio, voice, dan lain-lain akan hilang".format(chat.title, chat_id, tgl), timeout=360, reply_to_message_id=msg.message_id, parse_mode=ParseMode.MARKDOWN)



__mod_name__ = "Backups"

__help__ = """
*Hanya admin:*
 - /import: balas ke file cadangan grup butler/emilia untuk mengimpor sebanyak mungkin, membuat transfer menjadi sangat mudah! \
 Catatan bahwa file/foto tidak dapat diimpor karena pembatasan telegram.
 - /export: export data grup, yang akan di export adalah: peraturan, catatan (dokumen, gambar, musik, video, audio, voice, teks, tombol teks). \
 Modul ini masih tahap beta, jika ada masalah, laporkan ke @AyraHikari
"""
IMPORT_HANDLER = CommandHandler("import", import_data)
EXPORT_HANDLER = CommandHandler("export", export_data, filters=Filters.user(OWNER_ID))

dispatcher.add_handler(IMPORT_HANDLER)
dispatcher.add_handler(EXPORT_HANDLER)