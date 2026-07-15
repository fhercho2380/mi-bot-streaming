import os
import telebot

# Token seguro desde Railway
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

# ✅ COMANDO /start (igual al video)
@bot.message_handler(commands=['start'])
def inicio(mensaje):
    bot.reply_to(mensaje, """🎥 ¡Hola! Bienvenido a tu Bot de Streaming 🎥

Estoy listo para funcionar 24/7.
Comandos disponibles:
/ayuda - Ver qué puedo hacer
/stream - Cómo usar el streaming
""")

# ✅ COMANDO /ayuda
@bot.message_handler(commands=['ayuda'])
def ayuda(mensaje):
    bot.reply_to(mensaje, """📖 Guía rápida:
✅ Envíame cualquier enlace de streaming y te lo reenvío.
✅ Usa /stream para ver los formatos compatibles.
✅ No necesitas nada más, funciona solo.
""")

# ✅ COMANDO /stream
@bot.message_handler(commands=['stream'])
def info_stream(mensaje):
    bot.reply_to(mensaje, """🔗 Enlaces compatibles:
- Archivos MP4 / MKV
- Enlaces directos de streaming
- Enlaces de YouTube, Vimeo y más

Solo envíame el enlace y lo proceso enseguida.
""")

# ✅ RESPUESTA A MENSAJES NORMALES
@bot.message_handler(func=lambda mensaje: True)
def responder(mensaje):
    texto = mensaje.text
    # Si es un enlace
    if texto.startswith("http"):
        bot.reply_to(mensaje, "✅ Enlace recibido! Preparando el streaming...")
    else:
        bot.reply_to(mensaje, "🤔 No entiendo ese mensaje. Usa /ayuda para ver qué puedo hacer.")

# Mantenemos el bot encendido siempre
if __name__ == "__main__":
    print("✅ Bot listo y funcionando!")
    bot.infinity_polling()
