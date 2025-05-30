import discord
import requests
import os
import matplotlib.pyplot as plt
import datetime
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

        if message.content.startswith('!chart'):
            parts = message.content.split(' ')
            if len(parts) < 2:
                await message.channel.send("Format salah. Contoh: `!chart bitcoin`")
                return

            coin = parts[1].lower()
            url = f"https://api.coingecko.com/api/v3/coins/{coin}/market_chart"
            params = {"vs_currency": "usd", "days": "7"}

            try:
                response = requests.get(url, params=params)
                data = response.json()

                if "prices" not in data:
                    await message.channel.send("Data tidak ditemukan. Pastikan nama coin valid, contoh: `!chart bitcoin`")
                    return

                # Ambil data harga dan waktu
                prices = data["prices"]
                timestamps = [datetime.datetime.fromtimestamp(p[0] / 1000) for p in prices]
                values = [p[1] for p in prices]

                # Buat grafik
                plt.figure(figsize=(10, 4))
                plt.plot(timestamps, values, marker='o', color='blue', linewidth=2)
                plt.title(f"Harga {coin.capitalize()} 7 Hari Terakhir")
                plt.xlabel("Tanggal")
                plt.ylabel("Harga (USD)")
                plt.grid(True)
                plt.xticks(rotation=45)
                plt.tight_layout()

                filename = f"{coin}_chart.png"
                plt.savefig(filename)
                plt.close()

                # Kirim ke Discord
                await message.channel.send(file=discord.File(filename))

                # Hapus file setelah dikirim
                os.remove(filename)

            except Exception as e:
                await message.channel.send(f"Terjadi error: {str(e)}")

client.run(TOKEN)