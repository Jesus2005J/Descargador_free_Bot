# bot.py
import os
import threading
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import yt_dlp
from flask import Flask

# ------------------ Keepalive para Render ------------------
_health = Flask(__name__)

@_health.get("/")
def home():
    return "OK"

def run_health():
    port = int(os.environ.get("PORT", "10000"))
    _health.run(host="0.0.0.0", port=port)

threading.Thread(target=run_health, daemon=True).start()

# ------------------ Telegram Bot ------------------
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise ValueError("❌ No se encontró TOKEN en Environment Variables!")

# Carpeta para guardar cookies de usuarios
os.makedirs("cookies_users", exist_ok=True)

# ------------------ Handlers ------------------

# /start
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "¡Hola! 🤖\n"
        "Envíame un link de video para descargarlo.\n"
        "Si el video requiere login, sube tu archivo cookies.txt primero usando el chat."
    )

# Recibir cookies
async def receive_cookies(update: Update, context: CallbackContext):
    file = update.message.document
    if file and file.file_name.endswith(".txt"):
        path = f"cookies_users/{update.effective_user.id}.txt"
        await file.get_file().download(path)
        await update.message.reply_text("✅ Cookies guardadas correctamente.")
    else:
        await update.message.reply_text("❌ Solo se aceptan archivos .txt de cookies.")

# Borrar cookies
async def delete_cookies(update: Update, context: CallbackContext):
    path = f"cookies_users/{update.effective_user.id}.txt"
    if os.path.exists(path):
        os.remove(path)
        await update.message.reply_text("🗑️ Cookies eliminadas correctamente.")
    else:
        await update.message.reply_text("⚠️ No se encontraron cookies guardadas.")

# Descargar video
async def download_video(update: Update, context: CallbackContext):
    url = update.message.text.strip()
    user_id = update.effective_user.id
    cookies_path = f"cookies_users/{user_id}.txt"

    await update.message.reply_text("📥 Descargando... espera un momento.")

    ydl_opts = {
        "format": "bestvideo[height<=720]+bestaudio/best",
        "outtmpl": f"{user_id}_video.%(ext)s"
    }

    if os.path.exists(cookies_path):
        ydl_opts["cookiefile"] = cookies_path

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        await update.message.reply_text("✅ Video descargado exitosamente.")
        # Para enviar el video al usuario:
        # await update.message.reply_video(open(f"{user_id}_video.mp4", "rb"))
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

# ------------------ Main ------------------
def main():
    app = Application.builder().token(TOKEN).build()

    # 1️⃣ Comandos siempre primero
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("delete_cookies", delete_cookies))

    # 2️⃣ Documentos (cookies)
    app.add_handler(MessageHandler(filters.Document.FileExtension("txt"), receive_cookies))

    # 3️⃣ Texto (videos)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))

    app.run_polling()

if __name__ == "__main__":
    main()
