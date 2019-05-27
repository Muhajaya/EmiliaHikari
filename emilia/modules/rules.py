from typing import Optional

from telegram import Message, Update, Bot, User
from telegram import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.error import BadRequest
from telegram.ext import CommandHandler, run_async, Filters
from telegram.utils.helpers import escape_markdown

import emilia.modules.sql.rules_sql as sql
from emilia import dispatcher, spamfilters
from emilia.modules.helper_funcs.chat_status import user_admin
from emilia.modules.helper_funcs.string_handling import markdown_parser


@run_async
def get_rules(bot: Bot, update: Update):
    spam = spamfilters(update.effective_message.text, update.effective_message.from_user.id, update.effective_chat.id)
    if spam == True:
        return update.effective_message.reply_text("Saya kecewa dengan anda, saya tidak akan mendengar kata-kata anda sekarang!")
    chat_id = update.effective_chat.id
    send_rules(update, chat_id)


# Do not async - not from a handler
def send_rules(update, chat_id, from_pm=False):
    bot = dispatcher.bot
    user = update.effective_user  # type: Optional[User]
    try:
        chat = bot.get_chat(chat_id)
    except BadRequest as excp:
        if excp.message == "Chat not found" and from_pm:
            bot.send_message(user.id, "Pintasan aturan untuk obrolan ini belum diatur dengan benar! Mintalah admin untuk "
                                      "perbaiki ini.")
            return
        else:
            raise

    rules = sql.get_rules(chat_id)
    text = "Peraturan untuk *{}* adalah:\n\n{}".format(escape_markdown(chat.title), rules)

    if from_pm and rules:
        bot.send_message(user.id, text, parse_mode=ParseMode.MARKDOWN)
    elif from_pm:
        bot.send_message(user.id, "Admin grup belum menetapkan aturan apa pun untuk obrolan ini. "
                                  "Bukan berarti obrolan ini tanpa hukum...!")
    elif rules:
        update.effective_message.reply_text("Hubungi saya di PM untuk mendapatkan aturan grup ini",
                                            reply_markup=InlineKeyboardMarkup(
                                                [[InlineKeyboardButton(text="Peraturan",
                                                                       url="t.me/{}?start={}".format(bot.username,
                                                                                                     chat_id))]]))
    else:
        update.effective_message.reply_text("Admin grup belum menetapkan aturan apa pun untuk obrolan ini. "
                                            "Bukan berarti obrolan ini tanpa hukum...!")


@run_async
@user_admin
def set_rules(bot: Bot, update: Update):
    spam = spamfilters(update.effective_message.text, update.effective_message.from_user.id, update.effective_chat.id)
    if spam == True:
        return update.effective_message.reply_text("Saya kecewa dengan anda, saya tidak akan mendengar kata-kata anda sekarang!")
    chat_id = update.effective_chat.id
    msg = update.effective_message  # type: Optional[Message]
    raw_text = msg.text
    args = raw_text.split(None, 1)  # use python's maxsplit to separate cmd and args
    if len(args) == 2:
        txt = args[1]
        offset = len(txt) - len(raw_text)  # set correct offset relative to command
        markdown_rules = markdown_parser(txt, entities=msg.parse_entities(), offset=offset)

        sql.set_rules(chat_id, markdown_rules)
        update.effective_message.reply_text("Berhasil mengatur aturan untuk grup ini.")


@run_async
@user_admin
def clear_rules(bot: Bot, update: Update):
    spam = spamfilters(update.effective_message.text, update.effective_message.from_user.id, update.effective_chat.id)
    if spam == True:
        return update.effective_message.reply_text("Saya kecewa dengan anda, saya tidak akan mendengar kata-kata anda sekarang!")
    chat_id = update.effective_chat.id
    sql.set_rules(chat_id, "")
    update.effective_message.reply_text("Berhasil membersihkan aturan!")


def __stats__():
    return "{} obrolan memiliki aturan yang ditetapkan.".format(sql.num_chats())


def __import_data__(chat_id, data):
    # set chat rules
    rules = data.get('info', {}).get('rules', "")
    sql.set_rules(chat_id, rules)


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    return "Obrolan ini memiliki aturan yang ditetapkan: `{}`".format(bool(sql.get_rules(chat_id)))


__help__ = """
 - /rules: dapatkan aturan untuk obrolan ini.

*Hanya admin:*
 - /setrules <aturan Anda di sini>: atur aturan untuk obrolan ini.
 - /clearrules: kosongkan aturan untuk obrolan ini.
"""

__mod_name__ = "Rules"

GET_RULES_HANDLER = CommandHandler("rules", get_rules, filters=Filters.group)
SET_RULES_HANDLER = CommandHandler("setrules", set_rules, filters=Filters.group)
RESET_RULES_HANDLER = CommandHandler("clearrules", clear_rules, filters=Filters.group)

dispatcher.add_handler(GET_RULES_HANDLER)
dispatcher.add_handler(SET_RULES_HANDLER)
dispatcher.add_handler(RESET_RULES_HANDLER)
