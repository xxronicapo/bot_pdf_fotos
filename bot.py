import os
from fpdf import FPDF
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

USER_SESSIONS = {}  # Guarda fotos y titulo para cada usuario

TOKEN = os.getenv("8563969039:AAFlK4oCOL104vx9enzOa5QSx5KOuXxTPY0")  # Render guardará el token aquí


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    USER_SESSIONS[update.effective_user.id] = {"photos": [], "title": None}

    await update.message.reply_text(
        "👋 Hola! Envíame *una o varias fotos*.\n"
        "Cuando estés listo, escribe el nombre del PDF.\n"
        "Y después escribe: *crear pdf*"
    )


async def recibir_foto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in USER_SESSIONS:
        USER_SESSIONS[user_id] = {"photos": [], "title": None}

    photo_file = await update.message.photo[-1].get_file()

    path = f"temp_{user_id}_{len(USER_SESSIONS[user_id]['photos'])}.jpg"
    await photo_file.download_to_drive(path)

    USER_SESSIONS[user_id]["photos"].append(path)

    await update.message.reply_text("📸 Foto recibida. Envía otra o escribe *crear pdf*.")


async def texto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    msg = update.message.text.lower()

    if msg == "crear pdf":
        await crear_pdf(update, context)
        return

    USER_SESSIONS[user_id]["title"] = update.message.text
    await update.message.reply_text("📝 Nombre guardado. Ahora escribe *crear pdf*.")


async def crear_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    session = USER_SESSIONS.get(user_id, None)

    if not session or not session["photos"]:
        await update.message.reply_text("❌ No tengo fotos para crear el PDF.")
        return

    title = session["title"] or "Documento"
    pdf_name = f"{title}.pdf"

    pdf = FPDF()
    pdf.set_auto_page_break(0)

    for img in session["photos"]:
        pdf.add_page()
        pdf.image(img, 0, 0, 210, 297)

    pdf.output(pdf_name)

    await update.message.reply_document(open(pdf_name, "rb"))

    # limpiar
    for f in session["photos"]:
        os.remove(f)

    os.remove(pdf_name)

    USER_SESSIONS[user_id] = {"photos": [], "title": None}

    await update.message.reply_text("✅ PDF creado y enviado.")


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, recibir_foto))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, texto))

    app.run_polling()


if __name__ == "__main__":
    main()
