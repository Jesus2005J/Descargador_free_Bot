# --- keepalive para Render (añádelo arriba de todo) ---
import os, threading
from flask import Flask

_health = Flask(__name__)

@_health.get("/")
def home():
    return "OK"

def run_health():
    port = int(os.environ.get("PORT", "10000"))
    _health.run(host="0.0.0.0", port=port)

# Lanza el servidor HTTP en paralelo antes de iniciar el bot
threading.Thread(target=run_health, daemon=True).start()

# (tu código del bot sigue abajo como siempre; al final haces .run_polling())

import os
import yt_dlp
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("TOKEN")  # Se tomará del entorno en Render

# Descargar video con yt-dlp
def descargar_video(url, filename="video.mp4"):
    ydl_opts = {
        "outtmpl": filename,
        "format": "bestvideo[height<=720]+bestaudio/best[height<=720]/best"
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return filename

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Hola! Mándame un link de video y lo descargo para ti.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    await update.message.reply_text("📥 Descargando... espera un momento.")

    try:
        file_name = "video.mp4"
        descargar_video(url, file_name)

        # Enviar archivo a Telegram
        with open(file_name, "rb") as video:
            await update.message.reply_video(video)

        os.remove(file_name)  # Borrar después de enviar
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()

if __name__ == "__main__":
    main()

