import html
import json
import random
import PIL
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
import base64
from PIL import Image

import requests
from telegram.error import BadRequest, Unauthorized
from telegram import Message, Chat, Update, Bot, MessageEntity
from telegram import ParseMode
from telegram.ext import CommandHandler, run_async, Filters, MessageHandler
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
	"Biasanya maling akan teriak maling"
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
def cuaca(bot: Bot, update: Update, args: List[str]):
	location = " ".join(args)
	if location.lower() == bot.first_name.lower():
		update.effective_message.reply_text("Saya akan terus mengawasi di saat senang maupun sedih!")
		bot.send_sticker(update.effective_chat.id, BAN_STICKER)
		return

	try:
		bot.sendChatAction(update.effective_chat.id, "typing") # Bot typing before send message
		owm = pyowm.OWM(API_WEATHER, language='id')
		observation = owm.weather_at_place(location)
		cuacanya = observation.get_weather()
		obs = owm.weather_at_place(location)
		lokasi = obs.get_location()
		lokasinya = lokasi.get_name()
		# statusnya = cuacanya._detailed_status
		temperatur = cuacanya.get_temperature(unit='celsius')['temp']
		fc = owm.three_hours_forecast(location)
		besok = fc.get_weather_at(timeutils.tomorrow(5))
		# statusbesok = besok._detailed_status
		temperaturbesok = besok.get_temperature(unit='celsius')['temp']

		# Simbol cuaca
		statusnya = ""
		cuacaskrg = cuacanya.get_weather_code()
		if cuacaskrg < 232: # Hujan badai
			statusnya += "⛈️ "
		elif cuacaskrg < 321: # Gerimis
			statusnya += "🌧️ "
		elif cuacaskrg < 504: # Hujan terang
			statusnya += "🌦️ "
		elif cuacaskrg < 531: # Hujan berawan
			statusnya += "⛈️ "
		elif cuacaskrg < 622: # Bersalju
			statusnya += "🌨️ "
		elif cuacaskrg < 781: # Atmosfer
			statusnya += "🌪️ "
		elif cuacaskrg < 800: # Cerah
			statusnya += "🌤️ "
		elif cuacaskrg < 801: # Sedikit berawan
			statusnya += "⛅️ "
		elif cuacaskrg < 804: # Berawan
			statusnya += "☁️ "
		statusnya += cuacanya._detailed_status
					
		statusbesok = ""
		cuacaskrg = besok.get_weather_code()
		if cuacaskrg < 232: # Hujan badai
			statusbesok += "⛈️ "
		elif cuacaskrg < 321: # Gerimis
			statusbesok += "🌧️ "
		elif cuacaskrg < 504: # Hujan terang
			statusbesok += "🌦️ "
		elif cuacaskrg < 531: # Hujan berawan
			statusbesok += "⛈️ "
		elif cuacaskrg < 622: # Bersalju
			statusbesok += "🌨️ "
		elif cuacaskrg < 781: # Atmosfer
			statusbesok += "🌪️ "
		elif cuacaskrg < 800: # Cerah
			statusbesok += "🌤️ "
		elif cuacaskrg < 801: # Sedikit berawan
			statusbesok += "⛅️ "
		elif cuacaskrg < 804: # Berawan
			statusbesok += "☁️ "
		statusbesok += besok._detailed_status
					

		cuacabsk = besok.get_weather_code()

		update.message.reply_text("{} hari ini sedang {}, sekitar {}°C.\n".format(lokasinya,
				statusnya, temperatur) +
				"Untuk besok pada pukul 06:00, akan {}, sekitar {}°C".format(statusbesok, temperaturbesok))

	except exceptions.not_found_error.NotFoundError:
		update.effective_message.reply_text("Maaf, lokasi tidak ditemukan 😞")
	except pyowm.exceptions.api_call_error.APICallError:
		update.effective_message.reply_text("Tulis lokasi untuk mengecek cuacanya")
	else:
		return

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
			bot.sendChatAction(update.effective_chat.id, "typing") # Bot typing before send message
			mentahan = "{}".format(tekstr)
			teks1,teks2 = mentahan.split("text=")
			teks1a = "{}".format(teks2)
			teks1b,teks2b = teks1a.split(", pronunciation")
			print(msg.reply_to_message.text)
			message.reply_text("{}".format(teks1b))
		else:
			args = update.effective_message.text.split(None, 2)
			target = args[1]
			teks = args[2]
			message = update.effective_message
			trl = Translator()
			deteksibahasa = trl.detect(teks)
			tekstr = trl.translate(teks, dest=target)
			bot.sendChatAction(update.effective_chat.id, "typing") # Bot typing before send message
			mentahan = "{}".format(tekstr)
			teks1,teks2 = mentahan.split("text=")
			teks1a = "{}".format(teks2)
			teks1b,teks2b = teks1a.split(", pronunciation")
			message.reply_text("Diterjemahkan dari `{}` ke `{}`:\n`{}`".format(deteksibahasa.lang, target, teks1b), parse_mode=ParseMode.MARKDOWN)

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
def anime(bot: Bot, update: Update):
	msg = update.effective_message
	chat_id = update.effective_chat.id
	if msg.reply_to_message:
		msg = update.effective_message
		message = update.effective_message
		if msg.reply_to_message.photo:
			doc_id = msg.reply_to_message.photo[-1].file_id
			bot.sendChatAction(update.effective_chat.id, "record_video")
			newFile = bot.get_file(doc_id)
			newFile.download('anime.jpg')
		elif msg.reply_to_message.document:
			doc_id = msg.reply_to_message.document.thumb.file_id
			bot.sendChatAction(update.effective_chat.id, "record_video")
			newFile = bot.get_file(doc_id)
			newFile.download('anime.jpg')
		elif msg.reply_to_message.sticker:
			doc_id = msg.reply_to_message.sticker.thumb.file_id
			bot.sendChatAction(update.effective_chat.id, "record_video")
			newFile = bot.get_file(doc_id)
			newFile.download('anime.jpg')
		elif msg.reply_to_message.video:
			doc_id = msg.reply_to_message.video.thumb.file_id
			bot.sendChatAction(update.effective_chat.id, "record_video")
			newFile = bot.get_file(doc_id)
			newFile.download('anime.jpg')
		else:
			update.effective_message.reply_text("Balas pesan gambar/gif/video/stiker untuk mencari info animenya")
			return

		ngecek = bot.sendMessage(chat_id, "Sebentar ya, lagi di cari tau 🤥", parse_mode='markdown', reply_to_message_id=message.message_id)
		# Ubah ukurannya
		basewidth = 300
		img = Image.open('anime.jpg')
		if not img.mode == 'RGB':
			img = img.convert('RGB')
		wpercent = (basewidth / float(img.size[0]))
		hsize = int((float(img.size[1]) * float(wpercent)))
		img = img.resize((basewidth, hsize), PIL.Image.ANTIALIAS)
		img.save('anime.jpg')

		foto = open('anime.jpg', 'rb')
		img = foto.read()
		b64 = base64.b64encode(img)

		script = 'curl -X POST https://whatanime.ga/api/search?token=b4c29ee1c0cfa71f54d85ccd71a5db3a5757f8db -d "image=data:image/jpeg;base64,$(base64 -w 0 anime.jpg)" > hasil.txt'
		bot.sendChatAction(update.effective_chat.id, "record_video")
		test = os.system(script)
		with open("hasil.txt", "r") as f:
			for line in f:
				d = json.loads(line)
				docs = d['docs']
				try:
					animenya = docs[0]
				except IndexError:
					bot.deleteMessage(chat_id, ngecek.message_id)
					msg.reply_text("Maaf, saya tidak tahu anime itu 😥")
					return
				mirip = animenya['similarity']*100
				kemiripan = str(mirip)[:5]
				hasilnya = "*Menurut saya {}%*".format(kemiripan)
				hasilnya += "\nAnime: `{}` / `{}` / `{}`".format(animenya['title_native'], animenya['title_romaji'], animenya['title_english'])
				detiknya = str(animenya['at'])
				detiknya = str(datetime.timedelta(seconds=int(detiknya.split('.')[0])))
				hasilnya += "\nEpisode: `{}` - `{}`".format(animenya['episode'], detiknya)
				if animenya['season']:
					hasilnya += "\nMusim: `{}`".format(animenya['season'])
				else:
					pass
				try:
					hasilnya += "\nSinonim: `{sinonimnya}`".format(sinonimnya=animenya['synonyms'][0])
				except:
					hasilnya += "\nSinonim: `{sinonimnya}`".format(sinonimnya="Tidak ada")
				if animenya['is_adult'] == 'true':
					hasilnya += "\nKonten dewasa: `Ya`"
				else:
					hasilnya += "\nKonten dewasa: `Tidak`"
				NamaEncoded = urllib.parse.quote(animenya['filename'], safe='')
				LinkURL = "https://whatanime.ga/preview.php?anilist_id={anilist_id}&file={NamaEncoded}&t={at}&token={tokenthumb}".format(anilist_id=animenya['anilist_id'], NamaEncoded=NamaEncoded, at=animenya['at'], tokenthumb=animenya['tokenthumb'])
				f = open('anime-preview.mp4','wb')
				f.write(requests.get(LinkURL).content)
				f.close()
				captionvideo = "*Menurut saya {}%*\nAnime `{}` / `{}` di episode `{}` pada `{}`".format(kemiripan, animenya['title_native'], animenya['title_romaji'], animenya['episode'], detiknya)
				bot.deleteMessage(chat_id, ngecek.message_id)
				bot.sendVideo(chat_id, video=open('anime-preview.mp4', 'rb'), caption=captionvideo, parse_mode='markdown', reply_to_message_id=message.message_id)
				try:
					if animenya['mal_id']:
						buttoninline = """{
										  "inline_keyboard": [
											[
											  {
												"text": "AniList",
												"url": "https://anilist.co/anime/""" + str(animenya['anilist_id']) + """"
											  },
											  {
												"text": "MyAnimeList",
												"url": "https://myanimelist.net/anime/""" + str(animenya['mal_id']) + """"
											  }
											]
										  ]
										}"""
						bot.sendMessage(chat_id, hasilnya, parse_mode='markdown', reply_to_message_id=message.message_id, reply_markup=buttoninline)
					else:
						buttoninline = """{
									  "inline_keyboard": [
										[
										  {
											"text": "AniList",
											"url": "https://anilist.co/anime/""" + str(animenya['anilist_id']) + """"
										  }
										]
									  ]
									}"""
						bot.sendMessage(chat_id, hasilnya, parse_mode='markdown', reply_to_message_id=message.message_id, reply_markup=buttoninline)
				except KeyError:
					bot.sendMessage(chat_id, hasilnya, parse_mode='markdown', reply_to_message_id=message.message_id)

	else:
		bot.sendChatAction(chat_id, "typing")
		msg.reply_text('Balas pesan untuk mencari tahu info animenya')

def AI(bot, update):
	message = update.effective_message
	try:
		if message.reply_to_message.from_user.username == "EmiliaHikariBot":
			if message.chat.id == -1001161604147:
				try:
					teksnya = message.text
					try:
						SimsimiKey = os.environ.get('SimsimiKey', None)
						URL = "http://sandbox.api.simsimi.com/request.p?key={}&lc=id&ft=1.0&text={}".format(SimsimiKey, teksnya)
						r = requests.get(url = URL)
						data = r.json()
						if data['result'] == 509:
							update.effective_message.reply_text("Kuota token simsimi telah habis!")
							return
						respon = data['response']
						if "simsimi" in respon:
							respon = respon.replace("simsimi", "Emil")
						if "simi simi" in respon:
							respon = respon.replace("simi simi", "Emil")
						if "simi" in respon:
							respon = respon.replace("simi", "Emil")
						if "sim simi" in respon:
							respon = respon.replace("sim simi", "Emil")
						if "anak ayam" in respon:
							respon = respon.replace("anak ayam", "")
						update.effective_message.reply_text(respon)
					except:
						return
				except:
					return
	except:
		return

def setToken(bot, update):
	message = update.effective_message
	args = update.effective_message.text.split(None, 1)
	target = args[1]
	try:
		os.environ["SimsimiKey"] = target
		bot.sendMessage(update.effective_chat.id, text="Set token berhasil!\nToken sekarang adalah: `{}`".format(target), parse_mode='markdown', reply_to_message_id=message.message_id)
	except:
		update.effective_message.reply_text("Token gagal diisi!\nMungkin ada kesalahan kata pada token")

def cekToken(bot, update):
	message = update.effective_message
	try:
		SimsimiKey = os.environ.get('SimsimiKey', None)
		if SimsimiKey == None:
			update.effective_message.reply_text("Tidak ada token yang di setel")
			return
		URL = "http://sandbox.api.simsimi.com/request.p?key={}&lc=id&ft=1.0&text={}".format(SimsimiKey, "test")
		r = requests.get(url = URL)
		data = r.json()
		bot.sendMessage(update.effective_chat.id, text="Token saat ini: `{}`\nStatus token: `{}`".format(SimsimiKey, data['msg']), parse_mode='markdown', reply_to_message_id=message.message_id)
	except:
		update.effective_message.reply_text("Token gagal dicek!")

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
 - /cuaca <kota>: mendapatkan info cuaca di tempat tertentu
 - /tr <target> <teks>: terjemahkan teks yang ditulis atau di balas untuk bahasa apa saja ke bahasa yang dituju
 - /wiki <teks>: mencari teks yang ditulis dari sumber wikipedia
 - /kbbi <teks>: mencari teks yang ditulis dari kamus besar bahasa indonesia
 - /anime: balas pesan gambar anime untuk mencari tahu animenya

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
CUACA_HANDLER = DisableAbleCommandHandler("cuaca", cuaca, pass_args=True)
TERJEMAH_HANDLER = DisableAbleCommandHandler("tr", terjemah)
WIKIPEDIA_HANDLER = DisableAbleCommandHandler("wiki", wiki)
KBBI_HANDLER = DisableAbleCommandHandler("kbbi", kamusbesarbahasaindonesia)
ANIME_HANDLER = DisableAbleCommandHandler("anime", anime)
LOG_HANDLER = CommandHandler("log", log, filters=CustomFilters.sudo_filter)
ai_handler = MessageHandler(Filters.text, AI)
SetToken_HANDLER = CommandHandler("settoken", setToken, filters=CustomFilters.sudo_filter)
CetToken_HANDLER = CommandHandler("cekToken", cekToken, filters=CustomFilters.sudo_filter)

dispatcher.add_handler(PING_HANDLER)
dispatcher.add_handler(STICKERID_HANDLER)
dispatcher.add_handler(FILEID_HANDLER)
dispatcher.add_handler(GETSTICKER_HANDLER)
dispatcher.add_handler(STIKER_HANDLER)
dispatcher.add_handler(FILE_HANDLER)
dispatcher.add_handler(GETLINK_HANDLER)
dispatcher.add_handler(LEAVECHAT_HANDLER)
dispatcher.add_handler(RAMALAN_HANDLER)
dispatcher.add_handler(CUACA_HANDLER)
dispatcher.add_handler(TERJEMAH_HANDLER)
dispatcher.add_handler(WIKIPEDIA_HANDLER)
dispatcher.add_handler(KBBI_HANDLER)
dispatcher.add_handler(ANIME_HANDLER)
dispatcher.add_handler(LOG_HANDLER)
dispatcher.add_handler(ai_handler)
dispatcher.add_handler(SetToken_HANDLER)
dispatcher.add_handler(CetToken_HANDLER)