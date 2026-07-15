import os
import re
import imaplib
import email
import time
import telebot
from email.header import decode_header

# ------------------- CONFIGURACIÓN -------------------
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CORREO_PROVEEDOR = os.getenv("CORREO_PROVEEDOR", "imap.gmail.com")
CORREO_USUARIO = os.getenv("CORREO_USUARIO")
CORREO_CONTRASENA = os.getenv("CORREO_CONTRASENA")
ID_ADMIN = os.getenv("ID_ADMIN")

bot = telebot.TeleBot(TOKEN)
clientes_pendientes = {}

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
    if not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", correo_cliente):
        bot.send_message(m.chat.id, "⚠️ Escribe un correo válido. Intenta de nuevo con /micodigo")
        return
    
    clientes_pendientes[correo_cliente] = m.chat.id
    bot.send_message(m.chat.id, f"""✅ Correo guardado: {correo_cliente}
🔍 Estoy buscando tu código... tardaré unos segundos.
En cuanto lo encuentre te lo envío aquí mismo.
""")

# ------------------- BUSCAR CÓDIGO EN CORREOS (ADAPTADO A NETFLIX Y SIMILARES) -------------------
def buscar_codigo_en_correo():
    try:
        servidor = imaplib.IMAP4_SSL(CORREO_PROVEEDOR)
        servidor.login(CORREO_USUARIO, CORREO_CONTRASENA)
        servidor.select("INBOX")

        _, datos = servidor.search(None, 'UNSEEN')
        ids_correos = datos[0].split()

        for id_correo in ids_correos:
            _, datos_correo = servidor.fetch(id_correo, "(RFC822)")
            mensaje_correo = email.message_from_bytes(datos_correo[0][1])

            # Leer asunto y remitente
            asunto = decode_header(mensaje_correo["Subject"])[0][0]
            if isinstance(asunto, bytes):
                asunto = asunto.decode(errors='ignore')
            remitente = mensaje_correo["From"]

            # Leer todo el cuerpo del correo
            cuerpo = ""
            if mensaje_correo.is_multipart():
                for parte in mensaje_correo.walk():
                    if parte.get_content_type() == "text/plain" or parte.get_content_type() == "text/html":
                        try:
                            cuerpo += parte.get_payload(decode=True).decode(errors='ignore')
                        except:
                            continue
            else:
                cuerpo = mensaje_correo.get_payload(decode=True).decode(errors='ignore')

            # Buscar el correo del cliente en TODO el mensaje
            texto_completo = asunto + " " + remitente + " " + cuerpo
            patron_correo = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
            correos_encontrados = re.findall(patron_correo, texto_completo)

            # Buscar códigos de 4 a 6 dígitos (como el de Netflix)
            patron_codigo = r"\b\d{4,6}\b"
            codigos = re.findall(patron_codigo, cuerpo)

            if codigos and correos_encontrados:
                codigo = codigos[0]
                correo_destino = correos_encontrados[0].lower()

                # Verificar si es un cliente esperando código
                for correo_esperado, chat_id in list(clientes_pendientes.items()):
                    if correo_destino == correo_esperado.lower():
                        bot.send_message(chat_id, f"""🔑 TU CÓDIGO DE VERIFICACIÓN ES: **{codigo}**
✅ Lo encontré en el correo asociado a {correo_esperado}
Úsalo en la plataforma y listo.
""", parse_mode="Markdown")
                        del clientes_pendientes[correo_esperado]
                        print(f"✅ Código {codigo} enviado a {correo_esperado}")
                        break

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
4. Funciona con Netflix, plataformas de streaming y más
""")

@bot.message_handler(commands=['info'])
def info(m):
    bot.send_message(m.chat.id, "⚙️ Sistema adaptado para códigos de 4-6 dígitos | Funciona con correos de verificación")

# ------------------- ARRANCAR SISTEMA -------------------
if __name__ == "__main__":
    print("✅ SISTEMA ADAPTADO INICIADO - DETECTA CÓDIGOS DE NETFLIX Y SIMILARES")
    def revisar_correos_periodicamente():
        while True:
            if clientes_pendientes:
                buscar_codigo_en_correo()
            time.sleep(60)
    import threading
    threading.Thread(target=revisar_correos_periodicamente, daemon=True).start()
    
    bot.infinity_polling()
