import os
import telebot

# Obtener el token de forma segura (lo pondrás en Koyeb luego)
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

# === COMANDOS BÁSICOS (IGUAL QUE EN EL CURSO) ===
@bot.message_handler(commands=['start'])
def bienvenida(mensaje):
    bot.reply_to(mensaje, "¡Hola! Soy tu bot de streaming 🎥. Ya estoy funcionando 24/7.")

@bot.message_handler(commands=['ayuda'])
def ayuda(mensaje):
    bot.reply_to(mensaje, "Comandos disponibles:\n/start - Iniciar\n/ayuda - Ver esto")

# === AQUÍ AGREGARÁS LUEGO LO QUE ENSEÑE EL VIDEO ===
# Todo lo que el curso te muestre lo pones aquí, sin cambiar nada más

# Mantener el bot encendido siempre
if __name__ == "__main__":
    print("✅ Bot activo y escuchando...")
    bot.infinity_polling()