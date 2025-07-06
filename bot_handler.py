# bot_handler.py
import logging
from telegram import Update, ForceReply
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import json
import asyncio # Import asyncio for async operations

# Import your custom modules
from crm_router import CRMRouter, load_config
from lead_parser import parse_lead_info # This import needs lead_parser.py to exist and be correct

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# --- Global state for multi-step input (simplified) ---
# In a real bot, for complex flows, use ConversationHandler or a database.
user_states = {} # {user_id: {"step": "waiting_for_name", "temp_lead_data": {}}}

# Load configuration
config = load_config()
if not config:
    raise Exception("Bot cannot start: Configuration not loaded.")

TELEGRAM_BOT_TOKEN = config['telegram_bot_token']
CRM_ROUTER = CRMRouter()


# --- Command Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}! I'm your CRM assistant. "
        "I can help you capture leads directly into your CRM. "
        "Tell me about the lead (e.g., 'Name: John Doe, Email: john.doe@example.com, Phone: 9876543210')."
        "\n\nOr use /newlead to start capturing details step-by-step.",
        reply_markup=ForceReply(selective=True),
    )
    user_states[user.id] = {"step": "initial", "temp_lead_data": {}}


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text(
        "I can help you add leads to your CRM. "
        "Just send me lead information like Name, Email, and Phone number.\n"
        "Commands:\n"
        "/start - Start interacting with the bot\n"
        "/newlead - Start a step-by-step lead capture process\n"
        "/help - Show this help message"
    )

async def new_lead_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Initiates a step-by-step lead capture."""
    user_id = update.effective_user.id
    user_states[user_id] = {"step": "waiting_for_first_name", "temp_lead_data": {}}
    await update.message.reply_text("Okay, let's create a new lead. What is the lead's **First Name**?")


# --- Message Handler ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles incoming messages for lead parsing or multi-step input."""
    user_id = update.effective_user.id
    user_message = update.message.text
    current_state = user_states.get(user_id, {"step": "initial", "temp_lead_data": {}})

    if current_state["step"] == "waiting_for_first_name":
        current_state["temp_lead_data"]["first_name"] = user_message
        current_state["step"] = "waiting_for_last_name"
        await update.message.reply_text("Got it. What is their **Last Name**?")
    elif current_state["step"] == "waiting_for_last_name":
        current_state["temp_lead_data"]["last_name"] = user_message
        current_state["step"] = "waiting_for_email"
        await update.message.reply_text("And their **Email Address** (or type 'skip')?")
    elif current_state["step"] == "waiting_for_email":
        if user_message.lower() != 'skip':
            current_state["temp_lead_data"]["email"] = user_message
        current_state["step"] = "waiting_for_phone"
        await update.message.reply_text("What is their **Phone Number** (or type 'skip')?")
    elif current_state["step"] == "waiting_for_phone":
        if user_message.lower() != 'skip':
            current_state["temp_lead_data"]["phone"] = user_message
        current_state["step"] = "waiting_for_company"
        await update.message.reply_text("What is their **Company** (or type 'skip')?")
    elif current_state["step"] == "waiting_for_company":
        if user_message.lower() != 'skip':
            current_state["temp_lead_data"]["company"] = user_message

        # Finalize and send to CRM
        await update.message.reply_text("Thanks! Attempting to add this lead to CRM...")
        await add_lead_to_crm(update, current_state["temp_lead_data"])

        # Reset state
        user_states[user_id] = {"step": "initial", "temp_lead_data": {}}

    else: # Initial or unhandled message - try parsing directly
        await update.message.reply_text("Okay, let me try to extract information from your message.")
        parsed_info = parse_lead_info(user_message)

        if any(parsed_info.values()):
            # If any info was parsed, confirm and send to CRM
            await update.message.reply_text(
                "I found the following: \n"
                f"Name: {parsed_info['name'] or 'N/A'}\n"
                f"Email: {parsed_info['email'] or 'N/A'}\n"
                f"Phone: {parsed_info['phone'] or 'N/A'}\n"
                "Attempting to add this to CRM..."
            )
            # Use parsed_info for CRM creation, which might be partial
            await add_lead_to_crm(update, parsed_info)
        else:
            await update.message.reply_text(
                "I couldn't find any clear lead information (name, email, phone) in your message. "
                "Please try again or use /newlead for step-by-step guidance."
            )

    user_states[user_id] = current_state # Update state


async def add_lead_to_crm(update: Update, lead_data: dict) -> None:
    """Helper function to route lead creation to the CRM."""
    try:
        # Add lead source
        lead_data['lead_source'] = "Telegram Bot"
        
        # In this simple example, we use the parsed data directly.
        # In a real app, you'd want to map these more carefully to CRM fields.
        result = CRM_ROUTER.create_lead_or_contact(lead_data)

        if result.get("success"):
            await update.message.reply_text(
                f"Lead/Contact successfully added to {CRM_ROUTER.selected_crm}! ID: {result.get('id')}"
            )
            logger.info(f"Lead/Contact added: {result}")
        else:
            await update.message.reply_text(
                f"Failed to add lead/contact to {CRM_ROUTER.selected_crm}. Reason: {result.get('message', 'Unknown error')}"
            )
            logger.error(f"Failed to add lead/contact: {result}")
    except Exception as e:
        await update.message.reply_text(f"An error occurred while trying to add lead to CRM: {e}")
        logger.error(f"Error in add_lead_to_crm: {e}")


def main() -> None:
    """Start the bot."""
    # Create the Application and pass your bot's token.
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("newlead", new_lead_command))

    # Add message handler (filters for text messages that are not commands)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Run the bot until the user presses Ctrl-C
    print("Bot is running... Press Ctrl-C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()