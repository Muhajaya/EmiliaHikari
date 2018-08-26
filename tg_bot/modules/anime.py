import os
import PIL
import base64
import json
import datetime
import urllib
from PIL import Image

import requests
from telegram.error import BadRequest, Unauthorized
from telegram import Message, Chat, Update, Bot, MessageEntity
from telegram import ParseMode
from telegram.ext import CommandHandler, run_async, Filters
from telegram.utils.helpers import escape_markdown, mention_html

from tg_bot import dispatcher, OWNER_ID, SUDO_USERS, SUPPORT_USERS, API_ANIME
from tg_bot.modules.disable import DisableAbleCommandHandler

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

		script = 'curl -X POST https://whatanime.ga/api/search?token={} -d "image=data:image/jpeg;base64,$(base64 -w 0 anime.jpg)" > hasil.txt'.format(API_ANIME)
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
				"""
				if animenya['is_adult'] == 'true':
					hasilnya += "\nKonten dewasa: `Ya`"
				else:
					hasilnya += "\nKonten dewasa: `Tidak`"
				"""
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

__help__ = """
 - /anime: balas pesan gambar/stiker anime untuk mencari tahu animenya

 Note : hasil tidak 100% benar, biasanya dari gambar screenshot anime bisa diatas 90% benar, \
 dan selain itu dibawah 90% benar
"""

__mod_name__ = "🔍 What Anime"

ANIME_HANDLER = DisableAbleCommandHandler("anime", anime)

dispatcher.add_handler(ANIME_HANDLER)