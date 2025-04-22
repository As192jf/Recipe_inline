from telegram import InlineQueryResultArticle, InputTextMessageContent, Update
from telegram.ext import ApplicationBuilder, ContextTypes, InlineQueryHandler, CommandHandler
from aiohttp import web  # NEU
import os
from uuid import uuid4
from urllib.parse import quote
import logging

# Logging konfigurieren
logging.basicConfig(
    format='[%(asctime)s] %(levelname)s: %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Autorisierte Telegram-User laden
AUTHORIZED_IDS = list(map(int, os.getenv("AUTHORIZED_USERS", "").split(",")))

async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.inline_query.from_user
    user_id = user.id
    username = user.username or user.first_name

    query = update.inline_query.query.strip()

    if user_id not in AUTHORIZED_IDS:
        logger.warning(f"Unauthorized user: {username} ({user_id}) tried to use the bot.")
        return

    if not query.startswith("http"):
        logger.info(f"Ignoring non-URL query from {username}: '{query}'")
        return

    encoded_url = quote(query, safe="")
    bring_url = f"https://api.getbring.com/rest/bringrecipes/deeplink?url={encoded_url}&source=telegram&baseQuantity=4&requestedQuantity=4"

    logger.info(f"User {username} ({user_id}) → URL: {query} → Bring-URL: {bring_url}")

    result = InlineQueryResultArticle(
        id=str(uuid4()),
        title="Rezept übertragen",
        input_message_content=InputTextMessageContent(
            f'<a href="{bring_url}">Rezept übertragen.</a>',
            parse_mode="HTML"
        ),
        description="Klickbarer Bring!-Link"
    )

    try:
        await update.inline_query.answer([result], cache_time=0)
        logger.info(f"Antwort gesendet an {username}")
    except Exception as e:
        logger.error(f"Fehler beim Senden der Antwort an {username}: {e}")

# /start-Befehl für Debugging
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    username = user.username or user.first_name
    logger.info(f"/start received from {username} ({user.id})")
    await update.message.reply_text("Bot läuft und ist bereit für Inline-Anfragen!")

# Neue /ping Route für GET-Anfragen
async def ping(request):
    return web.Response(text="pong")

if __name__ == "__main__":
    token = os.getenv("BOT_TOKEN")
    webhook_url = os.getenv("WEBHOOK_URL")
    port = int(os.getenv("PORT", 10000))

    app = ApplicationBuilder().token(token).build()
    app.add_handler(InlineQueryHandler(inline_query))
    app.add_handler(CommandHandler("start", start))

    logger.info("Bot wird gestartet...")

    # Aiohttp-App mit /ping-Route
    web_app = web.Application()
    web_app.add_routes([web.get("/ping", ping)])

    app.run_webhook(
        listen="0.0.0.0",
        port=port,
        webhook_url=webhook_url,
        web_app=web_app
    )
