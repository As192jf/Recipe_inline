from telegram import InlineQueryResultArticle, InputTextMessageContent, Update
from telegram.ext import ApplicationBuilder, ContextTypes, InlineQueryHandler
import os
from uuid import uuid4
from urllib.parse import quote

AUTHORIZED_IDS = list(map(int, os.getenv("AUTHORIZED_USERS", "").split(",")))

async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.inline_query.from_user.id
    if user_id not in AUTHORIZED_IDS:
        return

    query = update.inline_query.query.strip()
    if not query.startswith("http"):
        return

    encoded_url = quote(query, safe="")
    bring_url = f"https://api.getbring.com/rest/bringrecipes/deeplink?url={encoded_url}&source=telegram&baseQuantity=4&requestedQuantity=4"

    result = InlineQueryResultArticle(
        id=str(uuid4()),
        title="Rezept übertragen",
        input_message_content=InputTextMessageContent(
            f"[Rezept übertragen.]({bring_url})",
            parse_mode="Markdown"
        ),
        description="Klickbarer Bring!-Link"
    )

    await update.inline_query.answer([result], cache_time=0)

if __name__ == "__main__":
    token = os.getenv("BOT_TOKEN")
    webhook_url = os.getenv("WEBHOOK_URL")
    port = int(os.getenv("PORT", 10000))

    app = ApplicationBuilder().token(token).build()
    app.add_handler(InlineQueryHandler(inline_query))

    app.run_webhook(
        listen="0.0.0.0",
        port=port,
        webhook_url=webhook_url
    )
