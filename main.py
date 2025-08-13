import asyncio
from telethon import TelegramClient, events
from telethon.sessions import StringSession
import os

# --- 1. CONFIGURE YOUR ACCOUNTS AND BOT ---

# Reads your credentials from environment variables set on Railway.app
BOT_TOKEN = os.environ.get('BOT_TOKEN')
ACCOUNTS = {
    '1': {
        'api_id': int(os.environ.get('API_ID_1', 0)),
        'api_hash': os.environ.get('API_HASH_1', ''),
        'session_string': os.environ.get('SESSION_STRING_1', None)
    },
    '2': {
        'api_id': int(os.environ.get('API_ID_2', 0)),
        'api_hash': os.environ.get('API_HASH_2', ''),
        'session_string': os.environ.get('SESSION_STRING_2', None)
    },
    # --- ADDED THIRD ACCOUNT ---
    '3': {
        'api_id': int(os.environ.get('API_ID_3', 0)),
        'api_hash': os.environ.get('API_HASH_3', ''),
        'session_string': os.environ.get('SESSION_STRING_3', None)
    }
}

online_status_tasks = {}

# --- 2. THE TELEGRAM CLIENT LOGIC ---

async def set_online_status(client):
    """A simple loop to keep a client's online status active."""
    while True:
        try:
            await client.send_read_acknowledge('me')
            print(f"[Account {client.me.id}] Status updated to online.")
            await asyncio.sleep(30)
        except Exception as e:
            print(f"Error updating status for Account {client.me.id}: {e}")
            await asyncio.sleep(60)

async def main():
    """The main function to start all clients and the control bot."""
    if not BOT_TOKEN:
        print("FATAL ERROR: BOT_TOKEN environment variable not set.")
        return

    clients = {}

    for key, config in ACCOUNTS.items():
        if config['api_id'] and config['api_hash'] and config['session_string']:
            client = TelegramClient(
                StringSession(config['session_string']),
                config['api_id'],
                config['api_hash']
            )
            print(f"Connecting to account {key} using session string...")
            await client.start()
            clients[key] = client
            client.me = await client.get_me()
            print(f"Account {key} ({client.me.first_name}) connected successfully.")
        else:
            print(f"Skipping Account {key}: Required environment variables not found.")

    if not clients:
        print("No accounts were able to connect. Please check your environment variables. Exiting.")
        return

    first_client_config = ACCOUNTS['1']
    bot = TelegramClient('bot_session', first_client_config['api_id'], first_client_config['api_hash'])
    await bot.start(bot_token=BOT_TOKEN)
    print("Control bot started successfully.")

    @bot.on(events.NewMessage(pattern='/start (.+)'))
    async def start_handler(event):
        account_key = event.pattern_match.group(1)
        if account_key in clients:
            if account_key not in online_status_tasks:
                task = asyncio.create_task(set_online_status(clients[account_key]))
                online_status_tasks[account_key] = task
                await event.reply(f"✅ Online status activated for Account {account_key}.")
            else:
                await event.reply(f"ℹ️ Account {account_key} is already active.")
        else:
            await event.reply(f"❌ Account {account_key} not found.")

    @bot.on(events.NewMessage(pattern='/stop (.+)'))
    async def stop_handler(event):
        account_key = event.pattern_match.group(1)
        if account_key in online_status_tasks:
            online_status_tasks[account_key].cancel()
            del online_status_tasks[account_key]
            await event.reply(f"🛑 Online status deactivated for Account {account_key}.")
        else:
            await event.reply(f"ℹ️ Account {account_key} is not currently active.")

    @bot.on(events.NewMessage(pattern='/status'))
    async def status_handler(event):
        if not online_status_tasks:
            await event.reply("All accounts are currently offline.")
            return
        active_accounts = ", ".join(online_status_tasks.keys())
        await event.reply(f"🟢 Active accounts: {active_accounts}")

    print("Listening for commands...")
    await bot.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
