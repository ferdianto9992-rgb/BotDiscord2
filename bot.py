import discord
from discord.ext import tasks, commands
import asyncio
from datetime import datetime, timedelta
import os
import json

# ---------------- KONFIGURASI ----------------
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DB_FILE = "database.json"
PREFIX = "!"  # Awalan perintah

# ---------------- FUNGSI DATABASE ----------------
def baca_database():
    if not os.path.exists(DB_FILE):
        data_awal = {
            "pengaturan": {
                "zona_waktu": 7,
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

# ---------------- INISIALISASI ----------------
data_db = baca_database()
ZONA = data_db["pengaturan"]["zona_waktu"]

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

def ke_waktu_utc(waktu_str):
    j, m = map(int, waktu_str.split(":"))
    return datetime.utcnow().replace(hour=j, minute=m, second=0, microsecond=0) - timedelta(hours=ZONA)

def hari_ke_kode(hari_utc):
    return 0 if hari_utc == 6 else hari_utc + 1

def nama_hari(kode):
    return ["Minggu", "Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu"][kode]

# ---------------- PERINTAH DISCORD ----------------
@bot.event
async def on_ready():
    print(f"✅ Bot aktif sebagai: {bot.user}")
    print(f"📊 Boss Respawn: {len(data_db['boss_respawn'])} | Boss Fixed: {len(data_db['boss_fixed'])}")
    cek_spawn.start()

@bot.command(name="daftar_boss")
async def daftar_boss(ctx):
    pesan = "📋 **DAFTAR BOSS & JADWAL SPAWN**\n\n🔄 **BOSS RESPAWN BERKALA:**\n"
    for nama, info in data_db["boss_respawn"].items():
        pesan += f"• {nama} → setiap {info['interval_jam']} jam\n"
    
    pesan += "\n📅 **BOSS WAKTU TETAP:**\n"
    for nama, jadwal in data_db["boss_fixed"].items():
        wkt = [f"{nama_hari(j['hari'])} jam {j['waktu']}" for j in jadwal]
        pesan += f"• {nama} → {', '.join(wkt)}\n"
    
    await ctx.send(pesan)

@bot.command(name="cek_waktu")
async def cek_waktu(ctx, *, nama_boss=None):
    if not nama_boss:
        return await ctx.send("⚠️ Gunakan: `!cek_waktu [NamaBoss]`\nContoh: `!cek_waktu Venatus`")
    
    nama_boss = nama_boss.strip()
    if nama_boss in data_db["boss_respawn"]:
        info = data_db["boss_respawn"][nama_boss]
        terakhir = info["terakhir_muncul"]
        if not terakhir:
            return await ctx.send(f"🔄 **{nama_boss}**: Belum tercatat, akan dihitung mulai sekarang.")
        terakhir_waktu = datetime.fromisoformat(terakhir) + timedelta(hours=ZONA)
        berikutnya = terakhir_waktu + timedelta(hours=info["interval_jam"])
        await ctx.send(f"🔄 **{nama_boss}**\nTerakhir muncul: {terakhir_waktu.strftime('%H:%M %d-%m-%Y')}\nBerikutnya: {berikutnya.strftime('%H:%M %d-%m-%Y')} WIB")
    elif nama_boss in data_db["boss_fixed"]:
        jadwal = data_db["boss_fixed"][nama_boss]
        daftar = [f"{nama_hari(j['hari'])} pukul {j['waktu']} WIB" for j in jadwal]
        await ctx.send(f"📅 **{nama_boss}**\nMuncul pada:\n• " + "\n• ".join(daftar))
    else:
        await ctx.send(f"❌ Boss bernama **{nama_boss}** tidak ditemukan.")

@bot.command(name="bantuan")
async def bantuan(ctx):
    pesan = "🤖 **PERINTAH BOT NOTIFIKASI BOSS**\n"
    pesan += "`!daftar_boss` → Lihat semua daftar boss dan jadwalnya\n"
    pesan += "`!cek_waktu [NamaBoss]` → Cek kapan boss berikutnya muncul\n"
    pesan += "`!bantuan` → Tampilkan daftar perintah ini\n"
    await ctx.send(pesan)

# ---------------- CEK WAKTU SPAWN ----------------
@tasks.loop(minutes=data_db["pengaturan"]["waktu_cek_menit"])
async def cek_spawn():
    sekarang_utc = datetime.utcnow()
    sekarang_lokal = sekarang_utc + timedelta(hours=ZONA)
    hari_sekarang = hari_ke_kode(sekarang_utc.weekday())
    channel = bot.get_channel(data_db["pengaturan"]["channel_id"])

    if not channel:
        return

    # --- CEK BOSS FIXED TIME ---
    for nama, jadwal in data_db["boss_fixed"].items():
        for item in jadwal:
            if item["hari"] == hari_sekarang:
                wkt = ke_waktu_utc(item["waktu"])
                if sekarang_utc >= wkt and sekarang_utc < wkt + timedelta(minutes=1):
                    pesan = f"📅 **BOSS FIXED SPAWN!** 📅\n\n**Nama:** {nama}\n**Hari:** {nama_hari(item['hari'])}\n**Waktu:** {item['waktu']} WIB\n✅ Siap untuk dikalahkan!"
                    await channel.send(pesan)
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
            pesan = f"🔄 **BOSS RESPAWN!** 🔄\n\n**Nama:** {nama}\n**Interval:** {interval} jam\n**Muncul:** {sekarang_lokal.strftime('%H:%M %d-%m-%Y')} WIB\n⏱️ Bersiaplah!"
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
