import discord
import requests
import os
from dotenv import load_dotenv

intents = discord.Intents.default()

client = discord.Client(intents=intents)

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

class MyClient(discord.Client):
    @client.event
    async def on_ready():
        print(f'Bot berhasil login sebagai {client.user}')

    @client.event
    async def on_message(message):
        if message.author.bot:
            return

        if message.content.startswith('!say'):
            parts = message.content.split(' ')
            if len(parts) < 2:
                await message.channel.send("Format salah. Contoh: `!say Halo`")
                return
            
            message_to_send = ' '.join(parts[1:])
            await message.channel.send(message_to_send)

        if message.content.startswith('!price'):
            parts = message.content.split(' ')
            if len(parts) < 2:
                await message.channel.send("Format salah. Contoh: `!price bitcoin`")
                return

            coin = parts[1].lower()
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin}&vs_currencies=usd"

            response = requests.get(url)
            data = response.json()

            if coin in data:
                price = data[coin]['usd']
                await message.channel.send(f"Harga {coin.upper()} saat ini: ${price}")
            else:
                await message.channel.send("Koin tidak ditemukan. Coba masukkan nama coin lain.")

client.run(TOKEN)
