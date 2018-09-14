import html
from typing import Optional, List

from telegram import Message, Chat, Update, Bot, User, ParseMode
from telegram.error import BadRequest, Unauthorized
from telegram.ext import CommandHandler, RegexHandler, run_async, Filters
from telegram.utils.helpers import mention_html

from tg_bot import dispatcher, LOGGER
from tg_bot.modules.helper_funcs.chat_status import user_not_admin, user_admin
from tg_bot.modules.log_channel import loggable
from tg_bot.modules.sql import reporting_sql as sql

REPORT_GROUP = 5


@run_async
@user_admin
def report_setting(bot: Bot, update: Update, args: List[str]):
    chat = update.effective_chat  # type: Optional[Chat]
    msg = update.effective_message  # type: Optional[Message]

    if chat.type == chat.PRIVATE:
        if len(args) >= 1:
            if args[0] in ("yes", "on"):
                sql.set_user_setting(chat.id, True)
                msg.reply_text("Menghidupkan pelaporan! Anda akan diberi tahu setiap kali ada yang melaporkan sesuatu.")

            elif args[0] in ("no", "off"):
                sql.set_user_setting(chat.id, False)
                msg.reply_text("Mematikan pelaporan! Anda tidak akan mendapatkan laporan apa pun.")
        else:
            msg.reply_text("Preferensi laporan Anda saat ini: `{}`".format(sql.user_should_report(chat.id)),
                           parse_mode=ParseMode.MARKDOWN)

    else:
        if len(args) >= 1:
            if args[0] in ("yes", "on"):
                sql.set_chat_setting(chat.id, True)
                msg.reply_text("Menghidupkan pelaporan! Admin yang telah mengaktifkan laporan akan diberi tahu ketika seseorang menyebut /report "
                               "atau @admin.")

            elif args[0] in ("no", "off"):
                sql.set_chat_setting(chat.id, False)
                msg.reply_text("Mematikan pelaporan! Tidak ada admin yang akan diberitahukan ketika seseorang menyebut /report atau @admin.")
        else:
            msg.reply_text("Pengaturan obrolan saat ini adalah: `{}`".format(sql.chat_should_report(chat.id)),
                           parse_mode=ParseMode.MARKDOWN)


@run_async
@user_not_admin
@loggable
def report(bot: Bot, update: Update) -> str:
    message = update.effective_message  # type: Optional[Message]
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]

    if chat and message.reply_to_message and sql.chat_should_report(chat.id):
        reported_user = message.reply_to_message.from_user  # type: Optional[User]
        chat_name = chat.title or chat.first or chat.username
        admin_list = chat.get_administrators()

        if chat.username and chat.type == Chat.SUPERGROUP:
            msg = "<b>{}:</b>" \
                  "\n<b>Pengguna yang dilaporkan:</b> {} (<code>{}</code>)" \
                  "\n<b>Dilaporkan oleh:</b> {} (<code>{}</code>)".format(html.escape(chat.title),
                                                                      mention_html(
                                                                          reported_user.id,
                                                                          reported_user.first_name),
                                                                      reported_user.id,
                                                                      mention_html(user.id,
                                                                                   user.first_name),
                                                                      user.id)
            #link = "\n<b>Link:</b> " \
            #       "<a href=\"http://telegram.me/{}/{}\">klik disini</a>".format(chat.username, message.message_id)

            buttoninline = """{
                      "inline_keyboard": [
                      [
                        {
                        "text": "⚠️ Pesan yang dilaporkan",
                        "url": "https://t.me/""" + chat.username + "/" + str(message.message_id) + """"
                        }
                      ]
                      ]
                    }"""

            should_forward = False
            bot.send_message(chat.id, "<i>⚠️ Pesan telah di laporkan ke semua admin!</i>", parse_mode=ParseMode.HTML, reply_to_message_id=message.message_id)

        else:
            msg = "{} memanggil admin di \"{}\"!".format(mention_html(user.id, user.first_name),
                                                               html.escape(chat_name))
            #link = ""
            buttoninline = ""

            should_forward = True
            bot.send_message(chat.id, "<i>⚠️ Pesan telah di laporkan ke semua admin!</i>", parse_mode=ParseMode.HTML, reply_to_message_id=message.message_id)

        for admin in admin_list:
            if admin.user.is_bot:  # can't message bots
                continue

            if sql.user_should_report(admin.user.id):
                try:
                    #bot.send_message(admin.user.id, msg + link, parse_mode=ParseMode.HTML)
                    bot.send_message(admin.user.id, msg, parse_mode=ParseMode.HTML, reply_markup=buttoninline)

                    if should_forward:
                        message.reply_to_message.forward(admin.user.id)

                        if len(message.text.split()) > 1:  # If user is giving a reason, send his message too
                            message.forward(admin.user.id)

                except Unauthorized:
                    pass
                except BadRequest as excp:  # TODO: cleanup exceptions
                    LOGGER.exception("Exception while reporting user")
        return msg

    return ""


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    return "Obrolan ini disetel untuk mengirim laporan pengguna ke admin, melalui /report dan @admin: `{}`".format(
        sql.chat_should_report(chat_id))


def __user_settings__(user_id):
    return "Anda menerima laporan dari obrolan yang Anda ikuti: `{}`.\nAktifkan ini dengan /reports di PM.".format(
        sql.user_should_report(user_id))


__mod_name__ = "Pelaporan"

__help__ = """
 - /report <alasan>: membalas pesan untuk melaporkannya ke admin.
 - @admin: membalas pesan untuk melaporkannya ke admin.
CATATAN: tidak satu pun dari ini akan dipicu jika digunakan oleh admin

*Hanya admin:*
 - /reports <on/off>: ubah pengaturan laporan, atau lihat status saat ini.
   - Jika selesai di PM, matikan status Anda.
   - Jika dalam obrolan, matikan status obrolan itu.
"""

REPORT_HANDLER = CommandHandler("report", report, filters=Filters.group)
SETTING_HANDLER = CommandHandler("reports", report_setting, pass_args=True)
ADMIN_REPORT_HANDLER = RegexHandler("(?i)@admin(s)?", report)

dispatcher.add_handler(REPORT_HANDLER, REPORT_GROUP)
dispatcher.add_handler(ADMIN_REPORT_HANDLER, REPORT_GROUP)
dispatcher.add_handler(SETTING_HANDLER)
