import discord
from discord.ext import tasks
import asyncio
from datetime import datetime, timedelta
import os
import json

# ---------------- KONFIGURASI ----------------
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DB_FILE = "database.json"

# ---------------- FUNGSI DATABASE ----------------
def baca_database():
    if not os.path.exists(DB_FILE):
        raise FileNotFoundError("File database.json tidak ditemukan!")
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def simpan_database(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# ---------------- INISIALISASI ----------------
data_db = baca_database()
ZONA = data_db["pengaturan"]["zona_waktu"]
intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

def ke_waktu_utc(waktu_str):
    j, m = map(int, waktu_str.split(":"))
    return datetime.utcnow().replace(hour=j, minute=m, second=0, microsecond=0) - timedelta(hours=ZONA)

def hari_ke_kode(hari_utc):
    return 0 if hari_utc == 6 else hari_utc + 1

# ---------------- CEK WAKTU SPAWN ----------------
@bot.event
async def on_ready():
    print(f"✅ Bot aktif sebagai: {bot.user}")
    print(f"📊 Boss Respawn: {len(data_db['boss_respawn'])} | Boss Fixed: {len(data_db['boss_fixed'])}")
    cek_spawn.start()

@tasks.loop(minutes=data_db["pengaturan"]["waktu_cek_menit"])
async def cek_spawn():
    sekarang_utc = datetime.utcnow()
    sekarang_lokal = sekarang_utc + timedelta(hours=ZONA)
    hari_sekarang = hari_ke_kode(sekarang_utc.weekday())
    channel = bot.get_channel(data_db["pengaturan"]["channel_id"])

    if not channel:
        print("❌ Channel tidak ditemukan! Cek ID di database.json")
        return

    # --- CEK BOSS FIXED TIME ---
    for nama, jadwal in data_db["boss_fixed"].items():
        for item in jadwal:
            if item["hari"] == hari_sekarang:
                wkt = ke_waktu_utc(item["waktu"])
                if sekarang_utc >= wkt and sekarang_utc < wkt + timedelta(minutes=1):
                    pesan = f"📅 **BOSS FIXED SPAWN!** 📅\n\n**Nama:** {nama}\n**Waktu:** {item['waktu']} WIB\n**Hari:** {'Minggu' if item['hari']==0 else ['Senin','Selasa','Rabu','Kamis','Jumat','Sabtu'][item['hari']-1]}\n✅ Siap untuk dikalahkan!"
                    await channel.send(pesan)
                    print(f"📤 Notifikasi Fixed: {nama} - {item['waktu']}")
                    await asyncio.sleep(60)

    # --- CEK BOSS RESPAWN BERKALA ---
    perubahan = False
    for nama, info in data_db["boss_respawn"].items():
        interval = info["interval_jam"]
        terakhir = info["terakhir_muncul"]

        if terakhir is None:
            info["terakhir_muncul"] = sekarang_utc.isoformat()
            perubahan = True
            continue

        terakhir_waktu = datetime.fromisoformat(terakhir)
        berikutnya = terakhir_waktu + timedelta(hours=interval)

        if sekarang_utc >= berikutnya and sekarang_utc < berikutnya + timedelta(minutes=1):
            pesan = f"🔄 **BOSS RESPAWN!** 🔄\n\n**Nama:** {nama}\n**Interval:** {interval} jam\n**Muncul lagi:** {sekarang_lokal.strftime('%H:%M %d-%m-%Y')} WIB\n⏱️ Bersiaplah!"
            await channel.send(pesan)
            info["terakhir_muncul"] = sekarang_utc.isoformat()
            perubahan = True
            print(f"📤 Notifikasi Respawn: {nama} - Interval {interval}j")
            await asyncio.sleep(60)

    if perubahan:
        simpan_database(data_db)

# Jalankan bot
if __name__ == "__main__":
    if not TOKEN:
        print("❌ Token tidak ditemukan! Masukkan di variabel Railway.")
    else:
        bot.run(TOKEN)