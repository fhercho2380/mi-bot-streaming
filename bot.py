import os
import re
import imaplib
import email
import time
import json
import telebot
from email.header import decode_header

# ------------------- CONFIGURACIÓN -------------------
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CORREO_PROVEEDOR = os.getenv("CORREO_PROVEEDOR", "imap.gmail.com")
CORREO_USUARIO = os.getenv("CORREO_USUARIO")
CORREO_CONTRASENA = os.getenv("CORREO_CONTRASENA")
ID_ADMIN = int(os.getenv("ID_ADMIN"))

bot = telebot.TeleBot(TOKEN)
ARCHIVO_CLIENTES = "clientes.json"
clientes_pendientes = {}

# ------------------- FUNCIONES DE GUARDADO -------------------
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
    clave = str(chat_id)
    if clave not in datos:
        datos[clave] = {
            "nombre": nombre_usuario,
            "activo": False,
            "vip": False,
            "correo": "",
            "enlaces": []  # Aquí se guardan los enlaces/cuentas asignadas
        }
        guardar_clientes(datos)
        return True
    return False

def cliente_esta_activo(chat_id):
    return cargar_clientes().get(str(chat_id), {}).get("activo", False)

# ------------------- COMANDOS DE ADMINISTRADOR -------------------
@bot.message_handler(commands=['activar'])
def activar(m):
    if m.chat.id != ID_ADMIN: return
    try:
        idc = str(int(m.text.split()[1]))
        datos = cargar_clientes()
        if idc in datos:
            datos[idc]["activo"] = True
            guardar_clientes(datos)
            bot.send_message(m.chat.id, f"✅ Cliente {idc} activado correctamente")
            bot.send_message(int(idc), "🎉 Tu cuenta ha sido activada, ya puedes usar el bot.")
    except:
        bot.send_message(m.chat.id, "⚠️ Formato: `/activar ID_DEL_CLIENTE`")

@bot.message_handler(commands=['desactivar'])
def desactivar(m):
    if m.chat.id != ID_ADMIN: return
    try:
        idc = str(int(m.text.split()[1]))
        datos = cargar_clientes()
        if idc in datos:
            datos[idc]["activo"] = False
            guardar_clientes(datos)
            bot.send_message(m.chat.id, f"✅ Cliente {idc} desactivado")
            bot.send_message(int(idc), "🔒 Tu cuenta ha sido desactivada temporalmente.")
    except:
        bot.send_message(m.chat.id, "⚠️ Formato: `/desactivar ID_DEL_CLIENTE`")

@bot.message_handler(commands=['vip'])
def vip(m):
    if m.chat.id != ID_ADMIN: return
    try:
        idc = str(int(m.text.split()[1]))
        datos = cargar_clientes()
        if idc in datos:
            datos[idc]["vip"] = True
            guardar_clientes(datos)
            bot.send_message(m.chat.id, f"✅ Cliente {idc} marcado como VIP")
            bot.send_message(int(idc), "⭐ ¡Tu cuenta es ahora VIP! Tienes acceso a todos tus enlaces.")
    except:
        bot.send_message(m.chat.id, "⚠️ Formato: `/vip ID_DEL_CLIENTE`")

@bot.message_handler(commands=['asignarcorreo'])
def asignar_correo(m):
    if m.chat.id != ID_ADMIN: return
    try:
        partes = m.text.strip().split()
        if len(partes) != 3: raise ValueError()
        idc = partes[1]
        correo = partes[2].lower()
        if not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", correo):
            bot.send_message(m.chat.id, "❌ Correo no válido")
            return
        datos = cargar_clientes()
        if idc in datos:
            datos[idc]["correo"] = correo
            guardar_clientes(datos)
            bot.send_message(m.chat.id, f"✅ Correo `{correo}` asignado a {idc}")
            bot.send_message(int(idc), f"📧 Correo asignado: `{correo}`", parse_mode="Markdown")
    except:
        bot.send_message(m.chat.id, "⚠️ Formato: `/asignarcorreo ID correo@ejemplo.com`")

# ✅ NUEVO: COMANDO PARA ASIGNAR ENLACES / CUENTAS
@bot.message_handler(commands=['agregarenlace'])
def agregar_enlace(m):
    if m.chat.id != ID_ADMIN: return
    try:
        texto = m.text.strip().split(maxsplit=2)
        if len(texto) < 3: raise ValueError()
        idc = str(int(texto[1]))
        enlace = texto[2]
        datos = cargar_clientes()
        if idc in datos:
            datos[idc]["enlaces"].append(enlace)
            guardar_clientes(datos)
            bot.send_message(m.chat.id, f"✅ Enlace agregado al cliente {idc}")
            bot.send_message(int(idc), "📥 Se te ha agregado un nuevo acceso. Usa /cuentas para verlo.")
        else:
            bot.send_message(m.chat.id, "❌ Cliente no encontrado")
    except:
        bot.send_message(m.chat.id, "⚠️ Formato: `/agregarenlace ID_DEL_CLIENTE Tu_enlace_o_datos_aqui`")

@bot.message_handler(commands=['borrarenlaces'])
def borrar_enlaces(m):
    if m.chat.id != ID_ADMIN: return
    try:
        idc = str(int(m.text.split()[1]))
        datos = cargar_clientes()
        if idc in datos:
            datos[idc]["enlaces"] = []
            guardar_clientes(datos)
            bot.send_message(m.chat.id, f"✅ Todos los enlaces borrados para {idc}")
    except:
        bot.send_message(m.chat.id, "⚠️ Formato: `/borrarenlaces ID_DEL_CLIENTE`")

# ------------------- COMANDOS PARA EL CLIENTE -------------------
@bot.message_handler(commands=['start'])
def bienvenida(m):
    chat_id = m.chat.id
    nombre = m.from_user.first_name or "Sin nombre"
    usuario = m.from_user.username or "Sin usuario"
    es_nuevo = registrar_cliente(chat_id, nombre)

    if es_nuevo:
        bot.send_message(chat_id, f"""👋 ¡Hola {nombre}!
✅ Te has registrado correctamente
🆔 Tu ID: `{chat_id}`

⚠️ Tu cuenta está pendiente de activación.
En cuanto el administrador te dé de alta podrás usar todas las funciones.
""", parse_mode="Markdown")

        bot.send_message(ID_ADMIN, f"""📥 **NUEVO CLIENTE REGISTRADO**
👤 Nombre: {nombre}
🆔 ID: `{chat_id}`
🔹 Usuario: @{usuario}

Comandos para administrarlo:
`/activar {chat_id}`
`/asignarcorreo {chat_id} correo@ejemplo.com`
`/agregarenlace {chat_id} TU_ENLACE_AQUI`
""", parse_mode="Markdown")
    else:
        if cliente_esta_activo(chat_id):
            bot.send_message(chat_id, f"""✅ Bienvenido de nuevo {nombre} 🟢

**Comandos disponibles:**
📂 `/cuentas` → Ver tus accesos y enlaces
🔑 `/micodigo` → Obtener código de verificación
ℹ️ `/info` → Ver tus datos
❓ `/ayuda` → ¿Cómo funciona?
""", parse_mode="Markdown")
        else:
            bot.send_message(chat_id, "⚠️ Tu cuenta está pendiente de activación.")

# ✅ NUEVO: COMANDO /CUENTAS PARA EL CLIENTE
@bot.message_handler(commands=['cuentas'])
def ver_cuentas(m):
    chat_id = m.chat.id
    if not cliente_esta_activo(chat_id):
        bot.send_message(chat_id, "❌ Tu cuenta no está activada. No puedes ver tus accesos.")
        return

    datos = cargar_clientes().get(str(chat_id), {})
    enlaces = datos.get("enlaces", [])

    if not enlaces:
        bot.send_message(chat_id, """📂 **MIS CUENTAS**
⚠️ Aún no tienes accesos asignados.
Contacta al administrador para que te agregue.
""", parse_mode="Markdown")
        return

    # Mostrar lista tal cual en la imagen
    texto = "📂 **MIS CUENTAS Y ACCESOS**\n\n"
    for i, item in enumerate(enlaces, 1):
        texto += f"🔹 {i}. {item}\n"

    texto += "\n✅ Actualizado por el administrador"

    bot.send_message(chat_id, texto, parse_mode="Markdown", disable_web_page_preview=False)

@bot.message_handler(commands=['micodigo'])
def pedir_codigo(m):
    if not cliente_esta_activo(m.chat.id):
        bot.send_message(m.chat.id, "❌ Cuenta no activada.")
        return
    datos = cargar_clientes().get(str(m.chat.id), {})
    correo = datos.get("correo", "")
    if not correo:
        bot.send_message(m.chat.id, "⚠️ No tienes correo asignado.")
        return
    clientes_pendientes[correo.lower()] = m.chat.id
    bot.send_message(m.chat.id, f"🔍 Buscando código para: `{correo}`...", parse_mode="Markdown")

def buscar_codigo_en_correo():
    try:
        servidor = imaplib.IMAP4_SSL(CORREO_PROVEEDOR)
        servidor.login(CORREO_USUARIO, CORREO_CONTRASENA)
        servidor.select("INBOX")
        _, datos = servidor.search(None, 'UNSEEN')
        ids = datos[0].split()
        for idc in ids:
            _, data = servidor.fetch(idc, "(RFC822)")
            msg = email.message_from_bytes(data[0][1])
            cuerpo = ""
            if msg.is_multipart():
                for p in msg.walk():
                    if p.get_content_type() in ["text/plain", "text/html"]:
                        try:
                            cuerpo += p.get_payload(decode=True).decode(errors='ignore')
                        except: pass
            else:
                cuerpo = msg.get_payload(decode=True).decode(errors='ignore')
            codigos = re.findall(r"\b\d{4,6}\b", cuerpo)
            correos = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", cuerpo)
            if codigos and correos:
                cod = codigos[0]
                cor = correos[0].lower()
                if cor in clientes_pendientes:
                    chat = clientes_pendientes.pop(cor)
                    if cliente_esta_activo(chat):
                        bot.send_message(chat, f"🔑 **TU CÓDIGO ES: `{cod}`**", parse_mode="Markdown")
        servidor.close()
        servidor.logout()
    except Exception as e:
        print("Error en correo:", e)

@bot.message_handler(commands=['info'])
def ver_info(m):
    d = cargar_clientes().get(str(m.chat.id), {})
    if not d:
        bot.send_message(m.chat.id, "❌ No estás registrado.")
        return
    estado = "🟢 ACTIVO" if d.get("activo") else "🔴 INACTIVO"
    tipo = "⭐ VIP" if d.get("vip") else "👤 Normal"
    bot.send_message(m.chat.id, f"""📋 **TUS DATOS**
🆔 ID: `{m.chat.id}`
📌 Estado: {estado}
🏷️ Tipo: {tipo}
📧 Correo: `{d.get("correo", "Sin asignar")}`
🔢 Cantidad de accesos: {len(d.get("enlaces", []))}
""", parse_mode="Markdown")

@bot.message_handler(commands=['ayuda'])
def ayuda(m):
    bot.send_message(m.chat.id, """❓ **¿Cómo usar el bot?**

1. Escribe `/start` para registrarte automáticamente
2. Espera a que el administrador active tu cuenta
3. Usa `/cuentas` para ver tus accesos
4. Usa `/micodigo` cuando necesites el código de verificación

Si tienes dudas, escribe al administrador.
""", parse_mode="Markdown")

# ------------------- INICIAR BOT -------------------
if __name__ == "__main__":
    print("✅ Bot completo iniciado")
    def revisar_correos():
        while True:
            if clientes_pendientes:
                buscar_codigo_en_correo()
            time.sleep(30)  # Revisa cada 30 segundos
    import threading
    threading.Thread(target=revisar_correos, daemon=True).start()
    bot.infinity_polling()
