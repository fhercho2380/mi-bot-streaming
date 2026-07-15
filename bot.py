import os
import re
import imaplib
import email
import time
import telebot
from email.header import decode_header

# ------------------- CONFIGURACIÓN SEGURA -------------------
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CORREO_PROVEEDOR = os.getenv("CORREO_PROVEEDOR", "imap.gmail.com")
CORREO_USUARIO = os.getenv("CORREO_USUARIO")
CORREO_CONTRASEÑA = os.getenv("CORREO_CONTRASEÑA")
ID_ADMIN = os.getenv("ID_ADMIN") # Tu número de ID de Telegram

bot = telebot.TeleBot(TOKEN)
clientes_pendientes = {} # Guarda correos de clientes esperando código

# ------------------- MENÚ PRINCIPAL -------------------
@bot.message_handler(commands=['start'])
def bienvenida(m):
    bot.send_message(m.chat.id, """🎬 BOT DE STREAMING - SISTEMA COMPLETO
✅ Funciona 24/7
✅ Recibo tu correo y te entrego el código automáticamente

Comandos:
/start - Volver al menú
/micodigo - Obtener tu código de acceso
/ayuda - Cómo funciona
/info - Datos del sistema
""")

# ------------------- PEDIR CORREO AL CLIENTE -------------------
@bot.message_handler(commands=['micodigo'])
def pedir_correo(m):
    msg = bot.send_message(m.chat.id, "📧 Escribe el correo electrónico con el que te registraste en el servicio:")
    bot.register_next_step_handler(msg, guardar_correo_cliente)

def guardar_correo_cliente(m):
    correo_cliente = m.text.strip()
    # Validar formato de correo
    if not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", correo_cliente):
        bot.send_message(m.chat.id, "⚠️ Escribe un correo válido. Intenta de nuevo con /micodigo")
        return
    
    clientes_pendientes[correo_cliente] = m.chat.id
    bot.send_message(m.chat.id, f"""✅ Correo guardado: {correo_cliente}
🔍 Estoy buscando tu código... tardaré unos segundos.
En cuanto lo encuentre te lo envío aquí mismo.
""")

# ------------------- BUSCAR CÓDIGO EN TU CORREO (EL CORAZÓN DEL VIDEO) -------------------
def buscar_codigo_en_correo():
    try:
        # Conectar a tu correo (IMAP)
        servidor = imaplib.IMAP4_SSL(CORREO_PROVEEDOR)
        servidor.login(CORREO_USUARIO, CORREO_CONTRASEÑA)
        servidor.select("INBOX")

        # Buscar correos no leídos
        _, datos = servidor.search(None, 'UNSEEN')
        ids_correos = datos[0].split()

        for id_correo in ids_correos:
            _, datos_correo = servidor.fetch(id_correo, "(RFC822)")
            mensaje_correo = email.message_from_bytes(datos_correo[0][1])

            # Obtener remitente y asunto
            asunto = decode_header(mensaje_correo["Subject"])[0][0]
            if isinstance(asunto, bytes):
                asunto = asunto.decode()
            remitente = mensaje_correo["From"]

            # Leer contenido
            cuerpo = ""
            if mensaje_correo.is_multipart():
                for parte in mensaje_correo.walk():
                    if parte.get_content_type() == "text/plain":
                        cuerpo = parte.get_payload(decode=True).decode()
            else:
                cuerpo = mensaje_correo.get_payload(decode=True).decode()

            # Extraer correo del destinatario y código
            patron_correo = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
            correo_encontrado = re.search(patron_correo, cuerpo + " " + remitente)
            if not correo_encontrado:
                continue
            correo_cliente = correo_encontrado.group()

            # Buscar código numérico (4 a 6 dígitos)
            patron_codigo = r"\b\d{4,6}\b"
            codigos = re.findall(patron_codigo, cuerpo)
            if codigos and correo_cliente in clientes_pendientes:
                codigo = codigos[0]
                chat_id = clientes_pendientes[correo_cliente]
                
                # Enviar código al cliente
                bot.send_message(chat_id, f"""🔑 TU CÓDIGO DE VERIFICACIÓN ES: **{codigo}**
✅ Lo encontré en el correo asociado a {correo_cliente}
Úsalo en la plataforma y listo.
""", parse_mode="Markdown")
                
                # Quitar de pendientes
                del clientes_pendientes[correo_cliente]
                print(f"✅ Código {codigo} enviado a {correo_cliente}")

        servidor.close()
        servidor.logout()
    except Exception as e:
        print(f"❌ Error revisando correo: {e}")

# ------------------- OTROS COMANDOS -------------------
@bot.message_handler(commands=['ayuda'])
def ayuda(m):
    bot.send_message(m.chat.id, """📖 ¿Cómo obtengo mi código?
1. Escribe /micodigo
2. Envía el correo que usaste en el servicio
3. Yo reviso el correo y te envío el código en segundos
4. Solo tienes que ponerlo en la plataforma

🔒 Tus datos no se comparten con nadie.
""")

@bot.message_handler(commands=['info'])
def info(m):
    bot.send_message(m.chat.id, "⚙️ Sistema completo activo | Recopilación automática de códigos | Alojado en Railway")

# ------------------- ARRANCAR SISTEMA -------------------
if __name__ == "__main__":
    print("✅ SISTEMA COMPLETO INICIADO - IGUAL AL TUTORIAL")
    # Bucle para revisar correos constantemente
    import threading
    def revisar_correos_periodicamente():
        while True:
            if clientes_pendientes:
                buscar_codigo_en_correo()
            time.sleep(60) # Revisa cada 60 segundos
    threading.Thread(target=revisar_correos_periodicamente, daemon=True).start()
    
    bot.infinity_polling()
