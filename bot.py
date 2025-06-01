import asyncio
import discord
import requests
import os
import json
import matplotlib.pyplot as plt
import pandas as pd
import mplfinance as mpf
import datetime
from cachetools import TTLCache
from dotenv import load_dotenv

cache = TTLCache(maxsize=100, ttl=3600)

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

def get_coin_data_from_cache_or_api(url, params=None):
    # memriksa apakah data sudah ada dalam cache
    cache_key = (url, tuple(params.items()) if params else None)  # Membuat key cache unik
    if cache_key in cache:
        return cache[cache_key]

    # Jika tidak ada, lakukan request API dan simpan dalam cache
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        cache[cache_key] = data  # Menyimpan data dalam cache
        return data
    return None

    # Fungsi untuk memuat data alert harga dari file JSON
def load_alerts():
    if os.path.exists('alerts.json'):
        with open('alerts.json', 'r') as f:
            return json.load(f)
    return {}

# Fungsi untuk menyimpan data alert harga ke file JSON
def save_alerts(alerts):
    with open('alerts.json', 'w') as f:
        json.dump(alerts, f)

# Cek harga cryptocurrency dan bandingkan dengan alert yang diset
async def check_alerts():
    alerts = load_alerts()
    for coin, alert_info in alerts.items():
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin}&vs_currencies=usd"
        data = get_coin_data_from_cache_or_api(url)
        
        if data and coin in data:
            current_price = data[coin]['usd']
            if current_price >= alert_info['price']:
                # Kirim pemberitahuan ke channel atau user
                channel = client.get_channel(alert_info['channel_id'])
                if channel:
                    await channel.send(f"🚨 **ALERT**: Harga {coin} sudah mencapai ${current_price}! (Target: ${alert_info['price']})")
                # Hapus alert setelah diberitahukan
                del alerts[coin]
                save_alerts(alerts)

class MyClient(discord.Client):
    @client.event
    async def on_ready():
        print(f'Bot berhasil login sebagai {client.user}')

        while True:
            await check_alerts()
            await asyncio.sleep(60)

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

            data = get_coin_data_from_cache_or_api(url)

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

            data = get_coin_data_from_cache_or_api(url)
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
                data = get_coin_data_from_cache_or_api(url, params)

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

        if message.content.startswith('!candle'):
            parts = message.content.split(' ')
            if len(parts) < 2:
                await message.channel.send("Format salah. Contoh: `!candle bitcoin`")
                return

            coin = parts[1].lower()
            days = 30  # Ambil data 30 hari terakhir

            # Ambil data OHLC dari CoinGecko
            url = f"https://api.coingecko.com/api/v3/coins/{coin}/ohlc?vs_currency=usd&days=30"

            try:
                raw_data = get_coin_data_from_cache_or_api(url)
                if not raw_data:
                    await message.channel.send("Data tidak ditemukan.")
                    return

                # Format data jadi DataFrame
                df = pd.DataFrame(raw_data, columns=["timestamp", "open", "high", "low", "close"])
                df["Date"] = pd.to_datetime(df["timestamp"], unit="ms")
                df.set_index("Date", inplace=True)
                df = df[["open", "high", "low", "close"]]

                # Tambahkan indikator Moving Average (MA20) dan RSI
                df['MA20'] = df['close'].rolling(window=20).mean()

                # RSI
                delta = df['close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                df['RSI'] = 100 - (100 / (1 + rs))

                # Buat dua panel: candlestick + RSI
                apds = [
                    mpf.make_addplot(df['MA20'], color='blue', width=1.2),
                    mpf.make_addplot(df['RSI'], panel=1, color='purple', ylabel='RSI')
                ]

                filename = f"{coin}_candle.png"
                mpf.plot(
                    df,
                    type='candle',
                    style='yahoo',
                    title=f'{coin.capitalize()} - Candlestick 30 Hari Terakhir',
                    ylabel='Harga (USD)',
                    addplot=apds,
                    volume=False,
                    panel_ratios=(3, 1),
                    figratio=(12, 6),
                    figscale=1.2,
                    savefig=filename
                )

                await message.channel.send(file=discord.File(filename))
                os.remove(filename)

            except Exception as e:
                await message.channel.send(f"Terjadi error: {str(e)}")

        if message.content.startswith('!help'):
            help_message = """
            **Daftar Perintah Bot:**

            1. `!say <teks>` - Mengirimkan pesan yang Anda ketikkan. Contoh: `!say Halo, dunia!`
            2. `!price <coin>` - Menampilkan harga terkini dari cryptocurrency. Contoh: `!price bitcoin`
            3. `!stats <coin>` - Menampilkan statistik lengkap tentang cryptocurrency, termasuk harga, market cap, volume, dan perubahan 24 jam. Contoh: `!stats ethereum`
            4. `!chart <coin>` - Menampilkan grafik harga cryptocurrency selama 7 hari terakhir. Contoh: `!chart bitcoin`
            5. `!candle <coin>` - Menampilkan grafik candlestick cryptocurrency dengan indikator Moving Average dan RSI untuk 30 hari terakhir. Contoh: `!candle bitcoin`

            **Catatan:** Pastikan nama koin yang Anda masukkan benar, dan jika ada kesalahan format, bot akan memberi tahu Anda.
            """

            await message.channel.send(help_message)

        if message.content.startswith('!alert set'):
            parts = message.content.split(' ')
            if len(parts) < 3:
                await message.channel.send("Format salah. Contoh: `!alert set bitcoin 50000`")
                return

            coin = parts[2].lower()
            try:
                target_price = float(parts[3])
            except ValueError:
                await message.channel.send("Harga harus berupa angka. Contoh: `!alert set bitcoin 50000`")
                return

            alerts = load_alerts()
            alerts[coin] = {
                "price": target_price,
                "channel_id": message.channel.id,
                "created_at": str(datetime.datetime.now())
            }
            save_alerts(alerts)
            await message.channel.send(f"Alert harga untuk {coin} sudah diset pada ${target_price}.")

        elif message.content.startswith('!alert list'):
            alerts = load_alerts()
            if not alerts:
                await message.channel.send("Tidak ada alert harga yang diset.")
                return
            
            alert_list = []
            for coin, alert_info in alerts.items():
                alert_list.append(f"{coin.upper()} - Target: ${alert_info['price']} - Dibuat pada: {alert_info['created_at']}")
            
            await message.channel.send("\n".join(alert_list))

        elif message.content.startswith('!alert remove'):
            parts = message.content.split(' ')
            if len(parts) < 3:
                await message.channel.send("Format salah. Contoh: `!alert remove bitcoin`")
                return

            coin = parts[2].lower()
            alerts = load_alerts()
            if coin in alerts:
                del alerts[coin]
                save_alerts(alerts)
                await message.channel.send(f"Alert untuk {coin} telah dihapus.")
            else:
                await message.channel.send(f"Tidak ada alert untuk {coin} yang ditemukan.")
                
client.run(TOKEN)