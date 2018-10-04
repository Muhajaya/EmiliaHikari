import html
from typing import Optional, List

from telegram import Message, Chat, Update, Bot, User
from telegram.error import BadRequest
from telegram.ext import run_async, CommandHandler, Filters
from telegram.utils.helpers import mention_html

from tg_bot import dispatcher, BAN_STICKER, LOGGER
from tg_bot.modules.disable import DisableAbleCommandHandler
from tg_bot.modules.helper_funcs.chat_status import bot_admin, user_admin, is_user_ban_protected, can_restrict, \
    is_user_admin, is_user_in_chat
from tg_bot.modules.helper_funcs.extraction import extract_user_and_text
from tg_bot.modules.helper_funcs.string_handling import extract_time
from tg_bot.modules.log_channel import loggable


@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def ban(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("Anda sepertinya tidak mengacu pada pengguna.")
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("Saya tidak dapat menemukan pengguna ini 😣")
            return ""
        else:
            raise

    if is_user_ban_protected(chat, user_id, member):
        message.reply_text("Saya benar-benar berharap bisa banned orang ini... 😞")
        return ""

    if user_id == bot.id:
        message.reply_text("Saya tidak akan BAN diri saya sendiri, apakah kamu gila? 😠")
        return ""

    check = bot.getChatMember(chat.id, user.id)
    if check['can_restrict_members'] == False:
        message.reply_text("Anda tidak punya hak untuk membatasi seseorang.")
        return ""

    log = "<b>{}:</b>" \
          "\n#BANNED" \
          "\n<b>Admin:</b> {}" \
          "\n<b>Pengguna:</b> {} (<code>{}</code>)".format(html.escape(chat.title),
                                                       mention_html(user.id, user.first_name),
                                                       mention_html(member.user.id, member.user.first_name),
                                                       member.user.id)
    if reason:
        log += "\n<b>Alasan:</b> {}".format(reason)

    try:
        chat.kick_member(user_id)
        bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker
        message.reply_text("Terbanned! 😝")
        return log

    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text('Terbanned! 😝', quote=False)
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR membanned pengguna %s di obrolan %s (%s) disebabkan oleh %s", user_id, chat.title, chat.id,
                             excp.message)
            message.reply_text("Yah sial, aku tidak bisa banned pengguna itu 😒")

    return ""


@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def temp_ban(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("Anda sepertinya tidak mengacu pada pengguna.")
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("Saya tidak dapat menemukan pengguna ini")
            return ""
        else:
            raise

    if is_user_ban_protected(chat, user_id, member):
        message.reply_text("Saya benar-benar berharap bisa banned orang ini... 😞")
        return ""

    if user_id == bot.id:
        message.reply_text("Saya tidak akan BAN diri saya sendiri, apakah kamu gila?")
        return ""

    check = bot.getChatMember(chat.id, user.id)
    if check['can_restrict_members'] == False:
        message.reply_text("Anda tidak punya hak untuk membatasi seseorang.")
        return ""

    if not reason:
        message.reply_text("Anda belum menetapkan waktu untuk banned pengguna ini!")
        return ""
    
    split_reason = reason.split(None, 1)

    time_val = split_reason[0].lower()
    if len(split_reason) > 1:
        reason = split_reason[1]
    else:
        reason = ""
        
        bantime = extract_time(message, time_val)
        
        if not bantime:
            return ""

    log = "<b>{}:</b>" \
          "\n#TEMP BANNED" \
          "\n<b>Admin:</b> {}" \
          "\n<b>Pengguna:</b> {} (<code>{}</code>)" \
          "\n<b>Waktu:</b> {}".format(html.escape(chat.title),
                                     mention_html(user.id, user.first_name),
                                     mention_html(member.user.id, member.user.first_name),
                                     member.user.id,
                                     time_val)
    if reason:
        log += "\n<b>Reason:</b> {}".format(reason)

    try:
        chat.kick_member(user_id, until_date=bantime)
        bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker
        message.reply_text("Banned! Pengguna diblokir untuk {}.".format(time_val))
        return log

    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text("Banned! Pengguna diblokir untuk {}.".format(time_val), quote=False)
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR banning user %s in chat %s (%s) due to %s", user_id, chat.title, chat.id,
                             excp.message)
            message.reply_text("Yah sial, aku tidak bisa menendang pengguna itu 😒")

    return ""


@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def kick(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("Saya tidak dapat menemukan pengguna ini")
            return ""
        else:
            raise

    if is_user_ban_protected(chat, user_id):
        message.reply_text("Saya benar-benar berharap bisa banned orang ini... 😞")
        return ""

    if user_id == bot.id:
        message.reply_text("Yahhh aku tidak akan melakukan itu 😝")
        return ""

    check = bot.getChatMember(chat.id, user.id)
    if check['can_restrict_members'] == False:
        message.reply_text("Anda tidak punya hak untuk membatasi seseorang.")
        return ""

    res = chat.unban_member(user_id)  # unban on current user = kick
    if res:
        bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker
        message.reply_text("Tertendang! 😝")
        log = "<b>{}:</b>" \
              "\n#KICKED" \
              "\n<b>Admin:</b> {}" \
              "\n<b>Pengguna:</b> {} (<code>{}</code>)".format(html.escape(chat.title),
                                                           mention_html(user.id, user.first_name),
                                                           mention_html(member.user.id, member.user.first_name),
                                                           member.user.id)
        log += "\n<b>Alasan:</b> {}".format(reason)

        return log

    else:
        message.reply_text("Yah sial, aku tidak bisa menendang pengguna itu 😒")

    return ""


@run_async
@bot_admin
@can_restrict
def kickme(bot: Bot, update: Update):
    user_id = update.effective_message.from_user.id
    if is_user_admin(update.effective_chat, user_id):
        update.effective_message.reply_text("Saya berharap saya bisa... tetapi Anda seorang admin 😒")
        return

    res = update.effective_chat.unban_member(user_id)  # unban on current user = kick
    if res:
        update.effective_message.reply_text("Tidak masalah 😊")
    else:
        update.effective_message.reply_text("Hah? Aku tidak bisa 🙄")


@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def unban(bot: Bot, update: Update, args: List[str]) -> str:
    message = update.effective_message  # type: Optional[Message]
    user = update.effective_user  # type: Optional[User]
    chat = update.effective_chat  # type: Optional[Chat]

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("Saya tidak dapat menemukan pengguna ini")
            return ""
        else:
            raise

    if user_id == bot.id:
        message.reply_text("Bagaimana saya akan unban diri saya sendiri jika saya tidak ada di sini...? 🤔")
        return ""

    if is_user_in_chat(chat, user_id):
        message.reply_text("Mengapa Anda mencoba unbanned seseorang yang sudah ada di obrolan? 😑")
        return ""

    check = bot.getChatMember(chat.id, user.id)
    if check['can_restrict_members'] == False:
        message.reply_text("Anda tidak punya hak untuk membatasi seseorang.")
        return ""

    chat.unban_member(user_id)
    message.reply_text("Ya, pengguna ini dapat bergabung! 😁")

    log = "<b>{}:</b>" \
          "\n#UNBANNED" \
          "\n<b>Admin:</b> {}" \
          "\n<b>Pengguna:</b> {} (<code>{}</code>)".format(html.escape(chat.title),
                                                       mention_html(user.id, user.first_name),
                                                       mention_html(member.user.id, member.user.first_name),
                                                       member.user.id)
    if reason:
        log += "\n<b>Alasan:</b> {}".format(reason)

    return log


__help__ = """
 - /kickme: menendang pengguna yang mengeluarkan perintah

*Hanya admin:*
 - /ban <userhandle>: banned seorang pengguna. (via pegangan, atau balasan)
 - /tban <userhandle> x(m/h/d): melarang pengguna untuk x waktu. (via pegangan, atau balasan). m = menit, h = jam, d = hari.
 - /unban <userhandle>: unbanned seorang pengguna. (via pegangan, atau balasan)
 - /kick <userhandle>: menendang seorang pengguna, (via pegangan, atau balasan)
"""

__mod_name__ = "Banned"

BAN_HANDLER = CommandHandler("ban", ban, pass_args=True, filters=Filters.group)
TEMPBAN_HANDLER = CommandHandler(["tban", "tempban"], temp_ban, pass_args=True, filters=Filters.group)
KICK_HANDLER = CommandHandler("kick", kick, pass_args=True, filters=Filters.group)
UNBAN_HANDLER = CommandHandler("unban", unban, pass_args=True, filters=Filters.group)
KICKME_HANDLER = DisableAbleCommandHandler("kickme", kickme, filters=Filters.group)

dispatcher.add_handler(BAN_HANDLER)
dispatcher.add_handler(TEMPBAN_HANDLER)
dispatcher.add_handler(KICK_HANDLER)
dispatcher.add_handler(UNBAN_HANDLER)
dispatcher.add_handler(KICKME_HANDLER)
