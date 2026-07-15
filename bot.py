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

# 👇 SOLO AQUÍ PONES TUS PALABRAS O FRASES EXACTAS
PALABRAS_ASUNTO = [
    "Tu código de inicio de sesión",
    "TU PALABRA 2",
    "TU PALABRA 3"
    # Agrega más líneas si necesitas más
]

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
            "enlaces": []
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
            bot.send_message(int(idc), "⭐ ¡Tu cuenta es ahora VIP!")
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
            bot.send_message(int(idc), "📥 Nuevo acceso agregado. Usa /cuentas para verlo.")
    except:
        bot.send_message(m.chat.id, "⚠️ Formato: `/agregarenlace ID TU_DATO_AQUI`")

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
""", parse_mode="Markdown")

        bot.send_message(ID_ADMIN, f"""📥 **NUEVO CLIENTE**
👤 {nombre}
🆔 `{chat_id}`
@ {usuario}

Comandos:
`/activar {chat_id}`
`/asignarcorreo {chat_id} correo@ejemplo.com`
""", parse_mode="Markdown")
    else:
        if cliente_esta_activo(chat_id):
            bot.send_message(chat_id, f"""✅ Bienvenido {nombre} 🟢

📂 `/cuentas` → Ver tus accesos
🔑 `/micodigo` → Obtener código de verificación
ℹ️ `/info` → Ver tus datos
❓ `/ayuda` → ¿Cómo funciona?
""", parse_mode="Markdown")
        else:
            bot.send_message(chat_id, "⚠️ Cuenta pendiente de activación.")

@bot.message_handler(commands=['cuentas'])
def ver_cuentas(m):
    chat_id = m.chat.id
    if not cliente_esta_activo(chat_id):
        bot.send_message(chat_id, "❌ Cuenta no activada.")
        return
    datos = cargar_clientes().get(str(chat_id), {})
    enlaces = datos.get("enlaces", [])
    if not enlaces:
        bot.send_message(chat_id, "📂 **MIS CUENTAS**\n⚠️ Aún no tienes accesos asignados.", parse_mode="Markdown")
        return
    texto = "📂 **MIS CUENTAS Y ACCESOS**\n\n"
    for i, item in enumerate(enlaces, 1):
        texto += f"🔹 {i}. {item}\n"
    bot.send_message(chat_id, texto, parse_mode="Markdown")

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
    bot.send_message(m.chat.id, "🔍 Buscando código... solo en los asuntos que tú definiste... ⏳")

# 🔎 FUNCIÓN: SOLO BUSCA EN LOS ASUNTOS QUE TÚ DIGAS
def buscar_codigo_en_correo():
    try:
        servidor = imaplib.IMAP4_SSL(CORREO_PROVEEDOR)
        servidor.login(CORREO_USUARIO, CORREO_CONTRASENA)
        servidor.select("INBOX")

        _, datos = servidor.search(None, 'UNSEEN')
        ids_correos = datos[0].split()

        for id_correo in ids_correos:
            _, datos_correo = servidor.fetch(id_correo, "(BODY[HEADER.FIELDS (SUBJECT FROM)])")
            mensaje_correo = email.message_from_bytes(datos_correo[0][1])

            asunto_raw = decode_header(mensaje_correo["Subject"])[0][0]
            if isinstance(asunto_raw, bytes):
                asunto = asunto_raw.decode(errors="ignore").lower().strip()
            else:
                asunto = str(asunto_raw).lower().strip()

            # ✅ SOLO CONTINÚA SI EL ASUNTO TIENE ALGUNA DE TUS PALABRAS
            if not any(palabra.lower() in asunto for palabra in PALABRAS_ASUNTO):
                continue

            # 🔍 Busca solo códigos de 4 a 6 dígitos en el asunto
            codigos = re.findall(r"\b\d{4,6}\b", asunto)
            remitente = mensaje_correo["From"]
            correos_encontrados = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", remitente)

            if codigos and correos_encontrados:
                codigo = codigos[0]
                correo_encontrado = correos_encontrados[0].lower()
                if correo_encontrado in clientes_pendientes:
                    chat_id = clientes_pendientes.pop(correo_encontrado)
                    if cliente_esta_activo(chat_id):
                        bot.send_message(chat_id, f"""🔑 **TU CÓDIGO ES: `{codigo}`**
✅ Encontrado en asunto: `{asunto}`
📧 Correo: `{correo_encontrado}`
""", parse_mode="Markdown")

        servidor.close()
        servidor.logout()
    except Exception as e:
        print(f"❌ Error: {e}")

@bot.message_handler(commands=['info'])
def ver_info(m):
    d = cargar_clientes().get(str(m.chat.id), {})
    if not d:
        bot.send_message(m.chat.id, "❌ No registrado.")
        return
    estado = "🟢 ACTIVO" if d.get("activo") else "🔴 INACTIVO"
    tipo = "⭐ VIP" if d.get("vip") else "👤 Normal"
    bot.send_message(m.chat.id, f"""📋 **TUS DATOS**
🆔 ID: `{m.chat.id}`
📌 Estado: {estado}
📧 Correo: `{d.get("correo", "Sin asignar")}`
🔢 Accesos: {len(d.get("enlaces", []))}
""", parse_mode="Markdown")

@bot.message_handler(commands=['ayuda'])
def ayuda(m):
    bot.send_message(m.chat.id, """❓ **¿Cómo funciona?**
1. `/start` → Registrarse
2. Esperar activación
3. `/cuentas` → Ver accesos
4. `/micodigo` → Buscar código solo en asuntos autorizados
""", parse_mode="Markdown")

# ------------------- INICIAR BOT -------------------
if __name__ == "__main__":
    print("✅ Bot listo: solo busca en los asuntos que tú definas")
    def revisar_correos():
        while True:
            if clientes_pendientes:
                buscar_codigo_en_correo()
            time.sleep(30)
    import threading
    threading.Thread(target=revisar_correos, daemon=True).start()
    bot.infinity_polling()
