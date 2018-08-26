if not __name__.endswith("sample_config"):
    import sys
    print("README ada untuk dibaca. Perluas konfigurasi sampel ini ke file konfigurasi, jangan hanya mengubah nama dan mengubah "
          "nilai di sini. Melakukan hal itu akan menjadi bumerang bagi Anda.\nBot berhenti.", file=sys.stderr)
    quit(1)


# Buat file config.py baru dalam dir dan impor yang sama, kemudian perpanjang kelas ini.
class Config(object):
    LOGGER = True

    # WAJIB
    API_KEY = "KUNCI ANDA DI SINI"
    OWNER_ID = "ID ANDA DI SINI"  # Jika Anda tidak tahu, jalankan bot dan lakukan /id di obrolan pribadi Anda dengannya
    OWNER_USERNAME = "USERNAME ANDA DI SINI"

    # DIREKOMENDASIKAN
    SQLALCHEMY_DATABASE_URI = 'sqldbtype://username:pw@hostname:port/db_name'  # diperlukan untuk setiap modul basis data
    MESSAGE_DUMP = None  # diperlukan untuk memastikan pesan 'simpan dari' tetap ada
    LOAD = []
    NO_LOAD = ['translation', 'rss', 'anime', 'weather']
    WEBHOOK = False
    URL = None

    # PILIHAN
    SUDO_USERS = []  # Daftar id (bukan nama pengguna) untuk pengguna yang memiliki akses sudo ke bot.
    SUPPORT_USERS = []  # Daftar id (bukan nama pengguna) untuk pengguna yang diizinkan untuk gban, tetapi juga bisa dilarang.
    WHITELIST_USERS = []  # Daftar id (bukan nama pengguna) untuk pengguna yang Wont dilarang / ditendang oleh bot.
    DONATION_LINK = None  # EG, paypal
    CERT_PATH = None
    PORT = 5000
    DEL_CMDS = False  # Apakah Anda harus menghapus perintah "blue text must click" atau tidak
    STRICT_GBAN = False
    WORKERS = 8  # Jumlah subthread yang digunakan. Ini adalah jumlah yang disarankan - lihat sendiri apa yang terbaik!
    BAN_STICKER = 'CAADAgADOwADPPEcAXkko5EB3YGYAg'  # stiker banhammer marie
    ALLOW_EXCL = False  # Mengizinkan ! perintah seperti /
    # API_OPENWEATHER = "OPENWEATHER API ANDA DI SINI"
    # API_WHATANIME = "API ANDA APA ANIME DI SINI"


class Production(Config):
    LOGGER = False


class Development(Config):
    LOGGER = True
