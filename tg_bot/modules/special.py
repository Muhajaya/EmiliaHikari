import html
import json
import random
import os
import urllib
import datetime
from typing import Optional, List
import time

import pyowm
from pyowm import timeutils, exceptions
from googletrans import Translator
import wikipedia
from kbbi import KBBI

import requests
from telegram.error import BadRequest, Unauthorized
from telegram import Message, Chat, Update, Bot, MessageEntity
from telegram import ParseMode
from telegram.ext import CommandHandler, run_async, Filters
from telegram.utils.helpers import escape_markdown, mention_html

from tg_bot import dispatcher, OWNER_ID, SUDO_USERS, SUPPORT_USERS, WHITELIST_USERS, BAN_STICKER, API_WEATHER, API_ANIME
from tg_bot.__main__ import STATS, USER_INFO
from tg_bot.modules.disable import DisableAbleCommandHandler, DisableAbleRegexHandler
from tg_bot.modules.helper_funcs.extraction import extract_user
from tg_bot.modules.helper_funcs.filters import CustomFilters

RAMALAN_STRINGS = (
	"Tertawalah sepuasnya sebelum hal itu dilarang 😆",
	"Bila Anda membahagiakan seseorang, Anda sendiri akan merasa bahagia\nBegitulah dunia bekerja 😊",
	"Nostalgia masa muda hari ini akan membuat Anda tersenyum 🌸",
	"Lanjutkan terus pekerjaan Anda, niscaya akan selesai juga\nOke, saya akui ramalan hari ini agak jayus 😝",
	"Mengetahui bahwa ilusi bukanlah kenyataan tidak membuat keindahannya berkurang 💖",
	"Anda akan mengalami kejadian aneh hari ini\nDan itu tidak termasuk mendapatkan ramalan dari Emilia Hikari 😜",
	"Akhirnya ada kesempatan untuk beristirahat...\ndan mendengar ramalan dari Emilia 😉",
	"Pencarian Anda sudah selesai\nAnda telah menemukan sahabat sejati (saya) 😀",
	"Anda akan menunjukkan bahwa Anda kuat melewati tantangan demi tantangan",
	"Anda hanyalah setitik air di tengah lautan luas\nTapi setitik air pun bisa bikin gadget rusak 😱 💦",
	"Anda akan mencoba hal baru hari ini\nTapi maaf, mencoba makanan gratis di supermarket tidak termasuk 🍦🚫",
	"Kirimlah pesan ke seorang teman lama hari ini",
	"Akan ada sesuatu yang baru di lingkungan sekitar Anda 🏡",
	"Traktirlah diri sendiri 🍭",
	"Semua hal ada solusinya, kalau Anda terbuka untuk berubah",
	"Karma baik menghampiri Anda minggu ini\nTapi hati-hati, karma itu rapuh seperti barang pecah belah",
	"Habiskanlah waktu di luar rumah hari ini\nSepertinya di luar sana indah... kalau tidak hujan",
	"Jika Anda mendengarkan dengan sungguh-sungguh, angin akan memberikan semua jawaban atas pertanyaan Anda 💨",
	"Pergilah ke tempat yang belum pernah Anda kunjungi, walaupun tempat itu hanya sepelemparan batu dari rumah Anda",
	"Anda akan menerima kabar baik, tapi mungkin Anda harus mencari dari apa yang tersirat",
	"Anda akan segera menemukan apa yang Anda cari\nKalau Anda bisa menemukan kacamata Anda",
	"Pergilah ke suatu tempat baru\nApa yang akan Anda temukan pasti akan mengesankan",
	"Kesempatan akan muncul bila Anda tahu ke mana harus melihat 👀",
	"Hari ini Anda akan menjadi keren 😎\nYah, nggak terlalu beda dengan hari-hari lain 😉",
	"Hal-hal positif akan muncul di hidup Anda hari ini\nTapi jangan lupa, di dalam komposisi sebuah atom selalu ada atom negatif 🔬😀",
	"Penuhilah diri hanya dengan kebaikan, baik dalam pikiran, perkataan, perbuatan, maupun pertwitteran 🐥",
	"Bersiaplah untuk menerima hal-hal menyenangkan hari ini 😎",
	"Waktunya belajar keterampilan dan topik baru",
	"Video YouTube favorit Anda masih belum dibuat",
	"Ketika ragu, Google dulu 😉",
	"Dua hari dari sekarang, besok akan jadi kemarin 😌",
	"Perhatikan detail-detail\nPasti banyak hal menarik yang Anda bisa temukan",
	"Wah, Anda belum beruntung\nSilakan coba lagi 😉",
	"Buatlah keputusan dengan mendengarkan dan menyelaraskan hati maupun pikiran Anda",
	"Biasanya maling akan teriak maling",
	"Anda tidak akan diberi kalau tidak meminta 👐",
	"Nostalgia masa muda hari ini akan membuat Anda tersenyum 🌸",
	"Sahabat sejati Anda berada dalam jangkauan\nSebenarnya, Anda sedang membaca ramalan darinya 😊",
	"Masa depan Anda akan dipenuhi kesuksesan 💎\nTapi hati-hati, keserakahan bisa menghancurkan semuanya 💰",
	"Hari ini adalah hari esok yang Anda nantikan kemarin",
	"Bersyukur akan membuat kita bahagia\nKatakan terima kasih pada seseorang hari ini",
	"Hari ini Anda akan menjadi keren 😎\nYah, nggak terlalu beda dengan hari-hari lain 😉",
	"Hari ini, dunia akan jadi milik Anda 🌍\nJangan lupa menjadikannya indah untuk orang lain 😊",
	"Petualangan baru akan segera menghampiri Anda",
	"Semakin banyak yang Anda katakan, semakin sedikit yang akan mereka ingat",
	"Hari ini, jadilah superhero untuk seorang anak kecil",
	"Makanan yang kelihatannya aneh itu mungkin sebenarnya enak banget",
	"Hari ini, ambillah rute yang lain dari biasanya",
	"Waktunya mengekspresikan kreativitas Anda",
	"Jodoh Anda lebih dekat dari yang Anda kira 💞",
	"Waktunya belajar keterampilan dan topik baru",
	"Hal-hal positif akan muncul di hidup Anda hari ini\nTapi jangan lupa, di dalam komposisi sebuah atom selalu ada atom negatif 🔬😀",
	"Waktunya berlibur bersama orang-orang kesayangan Anda ✈️",
	"Besok akan menjadi hari yang lebih menyenangkan daripada hari Anda yang paling menyebalkan",
	"Jangan cari peruntungan di situs abal-abal atau SMS mencurigakan",
	"Kejadian yang tak terduga akan menghampiri hidup Anda",
	"Hadiah berharga tengah menanti Anda\nTapi tampaknya hadiah tersebut sangat sabar menanti",
	"Keluarga Anda sangat kangen pada Anda\nTeleponlah mereka, jangan kasih tahu ini ide saya 😉",
	"Hari yang baik untuk memperjuangkan kebenaran",
	"Semua hal ada solusinya, kalau Anda terbuka untuk berubah",
	"Hewan peliharaan akan menambah kebahagiaan Anda 🐱🐹🐔"
)

@run_async
def stickerid(bot: Bot, update: Update):
	msg = update.effective_message
	if msg.reply_to_message and msg.reply_to_message.sticker:
		update.effective_message.reply_text("Hai " +
											"[{}](tg://user?id={})".format(msg.from_user.first_name, msg.from_user.id)
											+ ", Id stiker yang anda balas adalah :\n" +
											"```{}```".format(msg.reply_to_message.sticker.file_id),
											parse_mode=ParseMode.MARKDOWN)
	else:
		update.effective_message.reply_text("Hai " + "[{}](tg://user?id={})".format(msg.from_user.first_name,
											msg.from_user.id) + ", Tolong balas pesan stiker untuk mendapatkan id stiker",
											parse_mode=ParseMode.MARKDOWN)

@run_async
def fileid(bot: Bot, update: Update):
	msg = update.effective_message
	if msg.reply_to_message and msg.reply_to_message.document:
		update.effective_message.reply_text("Hai " +
											"[{}](tg://user?id={})".format(msg.from_user.first_name, msg.from_user.id)
											+ ", Id file yang anda balas adalah :\n" +
											"```{}```".format(msg.reply_to_message.document.file_id),
											parse_mode=ParseMode.MARKDOWN)
	else:
		update.effective_message.reply_text("Hai " + "[{}](tg://user?id={})".format(msg.from_user.first_name,
											msg.from_user.id) + ", Tolong balas pesan file untuk mendapatkan id file",
											parse_mode=ParseMode.MARKDOWN)

@run_async
def getsticker(bot: Bot, update: Update):
	msg = update.effective_message
	chat_id = update.effective_chat.id
	if msg.reply_to_message and msg.reply_to_message.sticker:
		bot.sendChatAction(chat_id, "typing")
		update.effective_message.reply_text("Hai " + "[{}](tg://user?id={})".format(msg.from_user.first_name,
											msg.from_user.id) + ", Silahkan cek file yang anda minta dibawah ini."
											"\nTolong gunakan fitur ini dengan bijak!",
											parse_mode=ParseMode.MARKDOWN)
		bot.sendChatAction(chat_id, "upload_document")
		file_id = msg.reply_to_message.sticker.file_id
		newFile = bot.get_file(file_id)
		newFile.download('sticker.png')
		bot.sendDocument(chat_id, document=open('sticker.png', 'rb'))
		bot.sendChatAction(chat_id, "upload_photo")
		bot.send_photo(chat_id, photo=open('sticker.png', 'rb'))
		
	else:
		bot.sendChatAction(chat_id, "typing")
		update.effective_message.reply_text("Hai " + "[{}](tg://user?id={})".format(msg.from_user.first_name,
											msg.from_user.id) + ", Tolong balas pesan stiker untuk mendapatkan gambar stiker",
											parse_mode=ParseMode.MARKDOWN)

@run_async
def stiker(bot: Bot, update: Update):
	chat_id = update.effective_chat.id
	args = update.effective_message.text.split(None, 1)
	message = update.effective_message
	message.delete()
	if message.reply_to_message:
		bot.sendSticker(chat_id, args[1], reply_to_message_id=message.reply_to_message.message_id)
	else:
		bot.sendSticker(chat_id, args[1])

@run_async
def file(bot: Bot, update: Update):
	chat_id = update.effective_chat.id
	args = update.effective_message.text.split(None, 1)
	message = update.effective_message
	message.delete()
	if message.reply_to_message:
		bot.sendDocument(chat_id, args[1], reply_to_message_id=message.reply_to_message.message_id)
	else:
		bot.sendDocument(chat_id, args[1])

@run_async
def getlink(bot: Bot, update: Update, args: List[int]):
	if args:
		chat_id = int(args[0])
	else:
		update.effective_message.reply_text("Anda sepertinya tidak mengacu pada obrolan")
	chat = bot.getChat(chat_id)
	bot_member = chat.get_member(bot.id)
	if bot_member.can_invite_users:
		titlechat = bot.get_chat(chat_id).title
		invitelink = bot.get_chat(chat_id).invite_link
		update.effective_message.reply_text("Sukses mengambil link invite di grup {}. \nInvite link : {}".format(titlechat, invitelink))
	else:
		update.effective_message.reply_text("Saya tidak memiliki akses ke tautan undangan!")
	
@run_async
def leavechat(bot: Bot, update: Update, args: List[int]):
	if args:
		chat_id = int(args[0])
	else:
		update.effective_message.reply_text("Anda sepertinya tidak mengacu pada obrolan")
	try:
		chat = bot.getChat(chat_id)
		titlechat = bot.get_chat(chat_id).title
		bot.sendMessage(chat_id, "Selamat tinggal semua 😁")
		bot.leaveChat(chat_id)
		update.effective_message.reply_text("Saya telah keluar dari grup {}".format(titlechat))

	except BadRequest as excp:
		if excp.message == "Chat not found":
			update.effective_message.reply_text("Sepertinya saya sudah keluar atau di tendang di grup tersebut")
		else:
			return

@run_async
def ping(bot: Bot, update: Update):
	start_time = time.time()
	bot.sendChatAction(update.effective_chat.id, "typing") # Bot typing before send message
	end_time = time.time()
	ping_time = float(end_time - start_time)
	update.effective_message.reply_text("Pong! \n"
											"Kecepatannya : {0:.2f} detik".format(round(ping_time, 2) % 60))

@run_async
def ramalan(bot: Bot, update: Update):
	bot.sendChatAction(update.effective_chat.id, "typing") # Bot typing before send messages
	update.effective_message.reply_text(random.choice(RAMALAN_STRINGS))    

@run_async
def terjemah(bot: Bot, update: Update):
	msg = update.effective_message
	chat_id = update.effective_chat.id
	try:
		if msg.reply_to_message and msg.reply_to_message.text:
			args = update.effective_message.text.split(None, 1)
			target = args[1]
			teks = msg.reply_to_message.text
			message = update.effective_message
			trl = Translator()
			deteksibahasa = trl.detect(teks)
			tekstr = trl.translate(teks, dest=target)
			message.reply_text("Diterjemahkan dari `{}` ke `{}`:\n`{}`".format(deteksibahasa.lang, target, tekstr.text), parse_mode=ParseMode.MARKDOWN)
		else:
			args = update.effective_message.text.split(None, 2)
			target = args[1]
			teks = args[2]
			message = update.effective_message
			trl = Translator()
			deteksibahasa = trl.detect(teks)
			tekstr = trl.translate(teks, dest=target)
			message.reply_text("Diterjemahkan dari `{}` ke `{}`:\n`{}`".format(deteksibahasa.lang, target, tekstr.text), parse_mode=ParseMode.MARKDOWN)

	except IndexError:
		update.effective_message.reply_text("Balas pesan atau tulis pesan dari bahasa lain untuk "
											"diterjemahkan kedalam bahasa yang di dituju")
	except ValueError:
		update.effective_message.reply_text("Bahasa yang di tuju tidak ditemukan!")
	else:
		return


@run_async
def wiki(bot: Bot, update: Update):
	msg = update.effective_message
	chat_id = update.effective_chat.id
	try:
		args = update.effective_message.text.split(None, 1)
		teks = args[1]
		message = update.effective_message
		bot.sendChatAction(update.effective_chat.id, "typing") # Bot typing before send message
		wikipedia.set_lang("id")
		pagewiki = wikipedia.page(teks)
		judul = pagewiki.title
		summary = pagewiki.summary
		message.reply_text("Hasil dari {} adalah:\n\n<b>{}</b>\n{}".format(teks, judul, summary), parse_mode=ParseMode.HTML)

	except wikipedia.exceptions.PageError:
		update.effective_message.reply_text("Hasil tidak ditemukan")
	except wikipedia.exceptions.DisambiguationError:
		update.effective_message.reply_text("Hasil terlalu banyak, silahkan masukan teks dengan lengkap")
	except IndexError:
		update.effective_message.reply_text("Tulis pesan untuk mencari dari sumber wikipedia")
	else:
		return


@run_async
def kamusbesarbahasaindonesia(bot: Bot, update: Update):
	msg = update.effective_message
	chat_id = update.effective_chat.id
	try:
		args = update.effective_message.text.split(None, 1)
		teks = args[1]
		message = update.effective_message
		bot.sendChatAction(update.effective_chat.id, "typing") # Bot typing before send message
		kamusid = KBBI(teks)
		message.reply_text("Hasil dari <b>{}</b> adalah:\n{}".format(teks, kamusid), parse_mode=ParseMode.HTML)

	except IndexError:
		update.effective_message.reply_text("Tulis pesan untuk mencari dari kamus besar bahasa indonesia")
	except KBBI.TidakDitemukan:
		update.effective_message.reply_text("Hasil tidak ditemukan")
	else:
		return

@run_async
def log(bot: Bot, update: Update):
	message = update.effective_message
	eventdict = message.to_dict()
	jsondump = json.dumps(eventdict, indent=4)
	update.effective_message.reply_text(jsondump)



__help__ = """
 - /stickerid: balas pesan stiker di PM untuk mendapatkan id stiker
 - /ping: mengecek kecepatan bot
 - /getsticker: mendapatkan gambar dari stiker
 - /ramalan: cek ramalan kamu hari ini
 - /tr <target> <teks>: terjemahkan teks yang ditulis atau di balas untuk bahasa apa saja ke bahasa yang dituju
 - /wiki <teks>: mencari teks yang ditulis dari sumber wikipedia
 - /kbbi <teks>: mencari teks yang ditulis dari kamus besar bahasa indonesia

 Note : teks untuk di terjemah tidak bisa dicampur emoticon
"""

__mod_name__ = "💖 Eksklusif Emilia 💖"

STICKERID_HANDLER = DisableAbleCommandHandler("stickerid", stickerid)
FILEID_HANDLER = DisableAbleCommandHandler("fileid", fileid)
GETSTICKER_HANDLER = DisableAbleCommandHandler("getsticker", getsticker)
PING_HANDLER = DisableAbleCommandHandler("ping", ping)
STIKER_HANDLER = CommandHandler("stiker", stiker, filters=Filters.user(OWNER_ID))
FILE_HANDLER = CommandHandler("file", file, filters=Filters.user(OWNER_ID))
GETLINK_HANDLER = CommandHandler("getlink", getlink, pass_args=True, filters=Filters.user(OWNER_ID))
LEAVECHAT_HANDLER = CommandHandler("leavechat", leavechat, pass_args=True, filters=Filters.user(OWNER_ID))
RAMALAN_HANDLER = DisableAbleCommandHandler("ramalan", ramalan)
TERJEMAH_HANDLER = DisableAbleCommandHandler("tr", terjemah)
WIKIPEDIA_HANDLER = DisableAbleCommandHandler("wiki", wiki)
KBBI_HANDLER = DisableAbleCommandHandler("kbbi", kamusbesarbahasaindonesia)
LOG_HANDLER = CommandHandler("log", log, filters=CustomFilters.sudo_filter)

dispatcher.add_handler(PING_HANDLER)
dispatcher.add_handler(STICKERID_HANDLER)
dispatcher.add_handler(FILEID_HANDLER)
dispatcher.add_handler(GETSTICKER_HANDLER)
dispatcher.add_handler(STIKER_HANDLER)
dispatcher.add_handler(FILE_HANDLER)
dispatcher.add_handler(GETLINK_HANDLER)
dispatcher.add_handler(LEAVECHAT_HANDLER)
dispatcher.add_handler(RAMALAN_HANDLER)
dispatcher.add_handler(TERJEMAH_HANDLER)
dispatcher.add_handler(WIKIPEDIA_HANDLER)
dispatcher.add_handler(KBBI_HANDLER)
dispatcher.add_handler(LOG_HANDLER)
