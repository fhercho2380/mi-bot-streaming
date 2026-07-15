import os
import re
import imaplib
import email
import time
import json
import telebot
from telebot.types import ReplyKeyboardRemove
from email.header import decode_header

# ------------------- CONFIGURACIÓN -------------------
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CORREO_PROVEEDOR = os.getenv("CORREO_PROVEEDOR", "imap.gmail.com")
CORREO_USUARIO = os.getenv("CORREO_USUARIO")
CORREO_CONTRASENA = os.getenv("CORREO_CONTRASENA")
ID_ADMIN = int(os.getenv("ID_ADMIN"))  # Tu ID como administrador

bot = telebot.TeleBot(TOKEN)

# Archivo donde se guardarán los clientes
ARCHIVO_CLIENTES = "clientes.json"

# ------------------- FUNCIONES DE GESTIÓN DE CLIENTES -------------------
def cargar_clientes():
    try:
        with open(ARCHIVO_CLIENTES, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def guardar_clientes(datos):
    with open(ARCHIVO_CLIENTES, "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=4, ensure_ascii=False)

def registrar_cliente(chat_id, nombre_usuario):
    datos = cargar_clientes()
    chat_id_str = str(chat_id)
    if chat_id_str not in datos:
        datos[chat_id_str] = {
            "nombre": nombre_usuario,
            "activo": False,
            "vip": False,
            "cuentas": 0,
            "correo_asociado": ""
        }
        guardar_clientes(datos)
        return True
    return False

def cliente_esta_activo(chat_id):
    datos = cargar_clientes()
    return datos.get(str(chat_id), {}).get("activo", False)

# ------------------- MENÚ PRINCIPAL / REGISTRO -------------------
@bot.message_handler(commands=['start'])
def bienvenida(m):
    chat_id = m.chat.id
    nombre = m.from_user.first_name or "Sin nombre"
    usuario = m.from_user.username or "Sin usuario"
    id_telegram = chat_id

    es_nuevo = registrar_cliente(chat_id, nombre)

    if es_nuevo:
        bot.send_message(chat_id, f"""👋 ¡Hola {nombre}!
✅ **Te has registrado correctamente**
🆔 Tu ID de Telegram: `{id_telegram}`

⚠️ Tu cuenta está pendiente de activación.
Habla con tu distribuidor o administrador para que te dé de alta.
""", parse_mode="Markdown")

        # Avisar al administrador del nuevo registro
        bot.send_message(ID_ADMIN, f"""📥 **NUEVO CLIENTE REGISTRADO**
👤 Nombre: {nombre}
🆔 ID: `{id_telegram}`
🔑 Usuario: @{usuario}

Para activarlo usa: `/activar {id_telegram}`
Para hacerlo VIP: `/vip {id_telegram}`
Para agregar cuentas: `/cuentas {id_telegram} 5`
""", parse_mode="Markdown")

    else:
        if cliente_esta_activo(chat_id):
            bot.send_message(chat_id, f"""✅ Bienvenido de nuevo {nombre}
Tu cuenta está **ACTIVA** 🟢

Comandos disponibles:
/micodigo - Obtener tu código de verificación
/info - Ver tus datos
/ayuda - ¿Cómo funciona?
""", parse_mode="Markdown")
        else:
            bot.send_message(chat_id, f"""⚠️ Hola {nombre}
Tu registro ya existe, pero **aún no está activado**.
Contacta con el administrador para que te dé de alta.
""")

# ------------------- COMANDOS PARA EL ADMINISTRADOR -------------------
@bot.message_handler(commands=['activar'])
def activar_cliente(m):
    if m.chat.id != ID_ADMIN:
        return
    try:
        id_cliente = int(m.text.split()[1])
        datos = cargar_clientes()
        if str(id_cliente) in datos:
            datos[str(id_cliente)]["activo"] = True
            guardar_clientes(datos)
            bot.send_message(m.chat.id, f"✅ Cliente `{id_cliente}` activado correctamente.")
            bot.send_message(id_cliente, "🎉 ¡Tu cuenta ha sido activada! Ya puedes usar todos los comandos.")
        else:
            bot.send_message(m.chat.id, "❌ Ese ID no está registrado.")
    except:
        bot.send_message(m.chat.id, "⚠️ Formato incorrecto. Usa: `/activar ID_DEL_CLIENTE`")

@bot.message_handler(commands=['vip'])
def vip_cliente(m):
    if m.chat.id != ID_ADMIN:
        return
    try:
        id_cliente = int(m.text.split()[1])
        datos = cargar_clientes()
        if str(id_cliente) in datos:
            datos[str(id_cliente)]["vip"] = True
            guardar_clientes(datos)
            bot.send_message(m.chat.id, f"✅ Cliente `{id_cliente}` marcado como VIP.")
            bot.send_message(id_cliente, "⭐ ¡Tu cuenta ha sido actualizada a VIP!")
        else:
            bot.send_message(m.chat.id, "❌ Ese ID no está registrado.")
    except:
        bot.send_message(m.chat.id, "⚠️ Formato incorrecto. Usa: `/vip ID_DEL_CLIENTE`")

@bot.message_handler(commands=['cuentas'])
def agregar_cuentas(m):
    if m.chat.id != ID_ADMIN:
        return
    try:
        partes = m.text.split()
        id_cliente = int(partes[1])
        cantidad = int(partes[2])
        datos = cargar_clientes()
        if str(id_cliente) in datos:
            datos[str(id_cliente)]["cuentas"] = cantidad
            guardar_clientes(datos)
            bot.send_message(m.chat.id, f"✅ Se asignaron {cantidad} cuentas al cliente `{id_cliente}`.")
            bot.send_message(id_cliente, f"📋 Se te han asignado {cantidad} cuentas disponibles.")
        else:
            bot.send_message(m.chat.id, "❌ Ese ID no está registrado.")
    except:
        bot.send_message(m.chat.id, "⚠️ Formato incorrecto. Usa: `/cuentas ID_DEL_CLIENTE CANTIDAD`")

# ------------------- COMANDO /INFO PARA VER DATOS -------------------
@bot.message_handler(commands=['info'])
def ver_info(m):
    chat_id = m.chat.id
    datos = cargar_clientes()
    if str(chat_id) not in datos:
        bot.send_message(chat_id, "❌ No estás registrado. Escribe /start primero.")
        return
    info = datos[str(chat_id)]
    estado = "🟢 ACTIVO" if info["activo"] else "🔴 INACTIVO"
    tipo = "⭐ VIP" if info["vip"] else "👤 Normal"
    bot.send_message(chat_id, f"""📋 **TUS DATOS**
🆔 ID: `{chat_id}`
👤 Estado: {estado}
🏷️ Tipo: {tipo}
📦 Cuentas disponibles: {info["cuentas"]}
""", parse_mode="Markdown")

# ------------------- SISTEMA DE BÚSQUEDA DE CÓDIGOS -------------------
clientes_pendientes = {}

@bot.message_handler(commands=['micodigo'])
def pedir_correo(m):
    if not cliente_esta_activo(m.chat.id):
        bot.send_message(m.chat.id, "❌ Tu cuenta no está activada. No puedes usar esta función.")
        return
    msg = bot.send_message(m.chat.id, "📧 Escribe el correo electrónico asociado a tu cuenta:")
    bot.register_next_step_handler(msg, guardar_correo_cliente)

def guardar_correo_cliente(m):
    if not cliente_esta_activo(m.chat.id):
        return
    correo_cliente = m.text.strip()
    if not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", correo_cliente):
        bot.send_message(m.chat.id, "⚠️ Escribe un correo válido. Intenta de nuevo con /micodigo")
        return
    clientes_pendientes[correo_cliente.lower()] = m.chat.id
    bot.send_message(m.chat.id, f"""✅ Correo guardado: `{correo_cliente}`
🔍 Buscando tu código... esperá unos segundos.
""", parse_mode="Markdown")

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

            asunto = decode_header(mensaje_correo["Subject"])[0][0]
            if isinstance(asunto, bytes):
                asunto = asunto.decode(errors='ignore')
            remitente = mensaje_correo["From"]

            cuerpo = ""
            if mensaje_correo.is_multipart():
                for parte in mensaje_correo.walk():
                    if parte.get_content_type() in ["text/plain", "text/html"]:
                        try:
                            cuerpo += parte.get_payload(decode=True).decode(errors='ignore')
                        except:
                            continue
            else:
                cuerpo = mensaje_correo.get_payload(decode=True).decode(errors='ignore')

            texto_completo = asunto + " " + remitente + " " + cuerpo
            correos_encontrados = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", texto_completo)
            codigos = re.findall(r"\b\d{4,6}\b", cuerpo)

            if codigos and correos_encontrados:
                codigo = codigos[0]
                correo_encontrado = correos_encontrados[0].lower()
                if correo_encontrado in clientes_pendientes:
                    chat_id = clientes_pendientes.pop(correo_encontrado)
                    if cliente_esta_activo(chat_id):
                        bot.send_message(chat_id, f"""🔑 **TU CÓDIGO ES: `{codigo}`**
✅ Correo asociado: `{correo_encontrado}`
""", parse_mode="Markdown")

        servidor.close()
        servidor.logout()
    except Exception as e:
        print(f"❌ Error al revisar correo: {e}")

# ------------------- INICIAR BOT -------------------
if __name__ == "__main__":
    print("✅ Bot iniciado con sistema de registro y códigos")
    def revisar_correos():
        while True:
            if clientes_pendientes:
                buscar_codigo_en_correo()
            time.sleep(60)
    import threading
    threading.Thread(target=revisar_correos, daemon=True).start()
    bot.infinity_polling()
