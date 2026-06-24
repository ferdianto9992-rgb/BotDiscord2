import discord
from discord.ext import tasks, commands
import asyncio
from datetime import datetime, timedelta
import os
import json

# ---------------- KONFIGURASI ----------------
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DB_FILE = "database.json"
PREFIX = "!"
ZONA_WIB = 7
ZONA_PHT = 8  # Waktu Filipina

# ---------------- FUNGSI DATABASE ----------------
def baca_database():
    if not os.path.exists(DB_FILE):
        data_awal = {
            "pengaturan": {
                "zona_waktu": ZONA_WIB,
                "channel_id": 1516729382134091796,
                "waktu_cek_menit": 1
            },
            "boss_respawn": {
                "Venatus": {"interval_jam": 10, "terakhir_muncul": None},
                "Viorent": {"interval_jam": 10, "terakhir_muncul": None},
                "LadyDalia": {"interval_jam": 18, "terakhir_muncul": None},
                "Ego": {"interval_jam": 21, "terakhir_muncul": None},
                "Shuliar": {"interval_jam": 35, "terakhir_muncul": None},
                "Larba": {"interval_jam": 35, "terakhir_muncul": None},
                "Catena": {"interval_jam": 35, "terakhir_muncul": None},
                "Livera": {"interval_jam": 24, "terakhir_muncul": None},
                "Undomiel": {"interval_jam": 24, "terakhir_muncul": None},
                "Araneo": {"interval_jam": 24, "terakhir_muncul": None},
                "Wannitas": {"interval_jam": 48, "terakhir_muncul": None},
                "Metus": {"interval_jam": 48, "terakhir_muncul": None},
                "Duplican": {"interval_jam": 48, "terakhir_muncul": None},
                "BaronBraudmore": {"interval_jam": 32, "terakhir_muncul": None},
                "Gareth": {"interval_jam": 32, "terakhir_muncul": None},
                "Amentis": {"interval_jam": 29, "terakhir_muncul": None},
                "Titore": {"interval_jam": 37, "terakhir_muncul": None},
                "GeneralAquleus": {"interval_jam": 29, "terakhir_muncul": None},
                "Ordo": {"interval_jam": 62, "terakhir_muncul": None},
                "Asta": {"interval_jam": 62, "terakhir_muncul": None},
                "Secreta": {"interval_jam": 62, "terakhir_muncul": None},
                "Supore": {"interval_jam": 62, "terakhir_muncul": None}
            },
            "boss_fixed": {
                "Benji": [{"hari": 6, "waktu": "20:00"}],
                "Clemantis": [{"hari": 0, "waktu": "10:30"}, {"hari": 3, "waktu": "18:00"}],
                "Thymele": [{"hari": 0, "waktu": "18:00"}, {"hari": 2, "waktu": "10:30"}],
                "Libitina": [{"hari": 0, "waktu": "20:00"}, {"hari": 5, "waktu": "20:00"}],
                "Saphirus": [{"hari": 6, "waktu": "16:00"}, {"hari": 1, "waktu": "10:30"}],
                "Neutro": [{"hari": 1, "waktu": "18:00"}, {"hari": 3, "waktu": "10:30"}],
                "Rakajeth": [{"hari": 6, "waktu": "18:00"}, {"hari": 1, "waktu": "21:00"}],
                "Auraq": [{"hari": 2, "waktu": "20:00"}, {"hari": 4, "waktu": "21:00"}],
                "Roderick": [{"hari": 4, "waktu": "18:00"}],
                "Milavy": [{"hari": 5, "waktu": "14:00"}],
                "Ringor": [{"hari": 5, "waktu": "16:00"}],
                "Chaiflock": [{"hari": 6, "waktu": "14:00"}],
                "Tumier": [{"hari": 6, "waktu": "18:00"}]
            }
        }
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data_awal, f, indent=4, ensure_ascii=False)
        return data_awal
    
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def simpan_database(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# ---------------- FUNGSI BANTU ----------------
def hari_ke_kode(hari_utc):
    return 0 if hari_utc == 6 else hari_utc + 1

def nama_hari(kode):
    return ["Minggu", "Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu"][kode]

def ubah_waktu_ke_utc(waktu_str):
    j, m = map(int, waktu_str.split(":"))
    return datetime.utcnow().replace(hour=j, minute=m, second=0, microsecond=0) - timedelta(hours=ZONA_WIB)

def format_sisa_waktu(delta):
    if delta.total_seconds() < 0:
        return "Sudah muncul"
    jam = int(delta.total_seconds() // 3600)
    menit = int((delta.total_seconds() % 3600) // 60)
    if jam > 0:
        return f"{jam}j {menit:02d}m lagi"
    return f"{menit}m lagi"

# ---------------- INISIALISASI BOT ----------------
data_db = baca_database()
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# ---------------- PERINTAH ----------------
@bot.event
async def on_ready():
    print(f"✅ Bot aktif sebagai: {bot.user}")
    print(f"📊 Boss Respawn: {len(data_db['boss_respawn'])} | Boss Fixed: {len(data_db['boss_fixed'])}")
    cek_spawn.start()

@bot.command(name="respawnlist", aliases=["rs"])
async def tampilkan_respawn(ctx):
    sekarang_utc = datetime.utcnow()
    sekarang_lokal = sekarang_utc + timedelta(hours=ZONA_WIB)

    pesan = "🔄 **JADWAL BOSS RESPAWN**\n"
    pesan += "──────────────────────────────────────\n"

    daftar = []
    for nama, info in data_db["boss_respawn"].items():
        interval = info["interval_jam"]
        terakhir = info["terakhir_muncul"]

        if not terakhir:
            sisa = "Belum dicatat"
            wib = "-"
            pht = "-"
        else:
            terakhir_waktu = datetime.fromisoformat(terakhir)
            berikutnya = terakhir_waktu + timedelta(hours=interval)
            if berikutnya < sekarang_utc:
                berikutnya += timedelta(hours=interval)
            berikutnya_wib = berikutnya + timedelta(hours=ZONA_WIB)
            berikutnya_pht = berikutnya + timedelta(hours=ZONA_PHT)
            sisa = format_sisa_waktu(berikutnya - sekarang_utc)
            wib = berikutnya_wib.strftime("%H:%M")
            pht = berikutnya_pht.strftime("%H:%M")

        daftar.append(f"**{nama}**\n🇮🇩 {wib} WIB | 🇵🇭 {pht} PHT\n⏳ {sisa}\n")

    pesan += "\n".join(daftar)
    await ctx.send(pesan)

@bot.command(name="fixlist", aliases=["fx"])
async def tampilkan_fix_hari_ini(ctx):
    sekarang_utc = datetime.utcnow()
    hari_sekarang = hari_ke_kode(sekarang_utc.weekday())
    nama_hari_ini = nama_hari(hari_sekarang)

    pesan = f"📅 **JADWAL BOSS FIXED - {nama_hari_ini.upper()}**\n"
    pesan += "──────────────────────────────────────\n"

    ada = False
    for nama, jadwal in data_db["boss_fixed"].items():
        for item in jadwal:
            if item["hari"] == hari_sekarang:
                j, m = map(int, item["waktu"].split(":"))
                wib = f"{j:02d}:{m:02d}"
                pht_j = (j + 1) % 24
                pht = f"{pht_j:02d}:{m:02d}"
                pesan += f"**{nama}**\n🇮🇩 {wib} WIB | 🇵🇭 {pht} PHT\n\n"
                ada = True

    if not ada:
        pesan += "Tidak ada boss fixed yang muncul hari ini."

    await ctx.send(pesan)

@bot.command(name="listall", aliases=["allboss"])
async def tampilkan_semua(ctx):
    await ctx.send("Ketik `!respawnlist` untuk daftar respawn\nKetik `!fixlist` untuk jadwal fixed hari ini")

@bot.command(name="bantuan")
async def bantuan(ctx):
    pesan = "🤖 **PERINTAH BOT NOTIFIKASI BOSS**\n"
    pesan += "`!respawnlist` / `!rs` → Daftar boss respawn + hitungan mundur\n"
    pesan += "`!fixlist` / `!fx` → Jadwal boss fixed **hanya hari ini**\n"
    pesan += "`!bantuan` → Tampilkan panduan ini\n"
    await ctx.send(pesan)

# ---------------- CEK & KIRIM NOTIFIKASI SPAWN ----------------
@tasks.loop(minutes=data_db["pengaturan"]["waktu_cek_menit"])
async def cek_spawn():
    sekarang_utc = datetime.utcnow()
    sekarang_lokal = sekarang_utc + timedelta(hours=ZONA_WIB)
    hari_sekarang = hari_ke_kode(sekarang_utc.weekday())
    channel = bot.get_channel(data_db["pengaturan"]["channel_id"])

    if not channel:
        return

    # --- Notifikasi Boss Fixed ---
    for nama, jadwal in data_db["boss_fixed"].items():
        for item in jadwal:
            if item["hari"] == hari_sekarang:
                wkt_utc = ubah_waktu_ke_utc(item["waktu"])
                if sekarang_utc >= wkt_utc and sekarang_utc < wkt_utc + timedelta(minutes=1):
                    j, m = map(int, item["waktu"].split(":"))
                    pht_j = (j + 1) % 24
                    pesan = f"📅 **BOSS FIXED SPAWN!** 📅\n\n**Nama:** {nama}\n**Hari:** {nama_hari(item['hari'])}\n🇮🇩 {j:02d}:{m:02d} WIB\n🇵🇭 {pht_j:02d}:{m:02d} PHT\n✅ Siap dikalahkan!"
                    await channel.send(pesan)
                    await asyncio.sleep(60)

    # --- Notifikasi Boss Respawn ---
    perubahan = False
    for nama, info in data_db["boss_respawn"].items():
        interval = info["interval_jam"]
        terakhir = info["terakhir_muncul"]

        if not terakhir:
            info["terakhir_muncul"] = sekarang_utc.isoformat()
            perubahan = True
            continue

        terakhir_waktu = datetime.fromisoformat(terakhir)
        berikutnya = terakhir_waktu + timedelta(hours=interval)

        if sekarang_utc >= berikutnya and sekarang_utc < berikutnya + timedelta(minutes=1):
            wib = berikutnya.strftime("%H:%M")
            pht = (berikutnya + timedelta(hours=1)).strftime("%H:%M")
            pesan = f"🔄 **BOSS RESPAWN!** 🔄\n\n**Nama:** {nama}\n**Interval:** {interval} jam\n🇮🇩 {wib} WIB\n🇵🇭 {pht} PHT\n⏱️ Waktunya untuk bertarung!"
            await channel.send(pesan)
            info["terakhir_muncul"] = sekarang_utc.isoformat()
            perubahan = True
            await asyncio.sleep(60)

    if perubahan:
        simpan_database(data_db)

# Jalankan bot
if __name__ == "__main__":
    if not TOKEN:
        print("❌ Token tidak ditemukan!")
    else:
        bot.run(TOKEN)
