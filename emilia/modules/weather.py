import pyowm
from pyowm import timeutils, exceptions
from telegram import Message, Chat, Update, Bot
from telegram.ext import run_async

from emilia import dispatcher, updater, API_WEATHER, spamfilters
from emilia.modules.disable import DisableAbleCommandHandler

@run_async
def cuaca(bot, update, args):
    spam = spamfilters(update.effective_message.text, update.effective_message.from_user.id)
    if spam == True:
        return update.effective_message.reply_text("Saya kecewa dengan anda, saya tidak akan mendengar kata-kata anda sekarang!")
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
        temperatur = cuacanya.get_temperature(unit='celsius')['temp']
        fc = owm.three_hours_forecast(location)
        besok = fc.get_weather_at(timeutils.tomorrow(5))
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

    except pyowm.exceptions.api_call_error.APICallError:
        update.effective_message.reply_text("Tulis lokasi untuk mengecek cuacanya")
    except pyowm.exceptions.api_response_error.NotFoundError:
        update.effective_message.reply_text("Maaf, lokasi tidak ditemukan 😞")
    else:
        return


__help__ = """
 - /cuaca <kota>: mendapatkan info cuaca di tempat tertentu
"""

__mod_name__ = "Cuaca"

CUACA_HANDLER = DisableAbleCommandHandler("cuaca", cuaca, pass_args=True)

dispatcher.add_handler(CUACA_HANDLER)
