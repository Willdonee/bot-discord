import discord
import requests
import os
from dotenv import load_dotenv

intents = discord.Intents.default()
intents.message_content = True
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

        if message.content.startswith('!stats'):
            parts = message.content.split(' ')
        
            if len(parts) < 2:
                await message.channel.send("Format salah. Contoh: `!stats bitcoin`")
                return

            coin = parts[1].lower()
            url = f"https://api.coingecko.com/api/v3/coins/{coin}"

            response = requests.get(url)
            if response.status_code != 200:
                await message.channel.send("Gagal mengambil data. Periksa nama koin kamu.")
                return

            data = response.json()
            try:
                name = data['name']
                symbol = data['symbol'].upper()
                price = data['market_data']['current_price']['usd']
                market_cap = data['market_data']['market_cap']['usd']
                volume = data['market_data']['total_volume']['usd']
                change_24h = data['market_data']['price_change_percentage_24h']
                supply = data['market_data']['circulating_supply']

                msg = (
                    f"📊 Statistik untuk **{name} ({symbol})**:\n"
                    f"💰 Harga Saat Ini: ${price:,.2f}\n"
                    f"📈 Market Cap: ${market_cap:,.0f}\n"
                    f"📊 Volume 24h: ${volume:,.0f}\n"
                    f"📉 Perubahan 24h: {change_24h:.2f}%\n"
                    f"🔁 Total Supply: {supply:,.0f}"
                )
                await message.channel.send(msg)
            except KeyError:
                await message.channel.send("Data tidak lengkap atau coin tidak ditemukan.")


    

client.run(TOKEN)
