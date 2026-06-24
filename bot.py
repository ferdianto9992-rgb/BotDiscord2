import discord
from discord.ext import tasks, commands
from discord.ui import View, Button
import asyncio
from datetime import datetime, timedelta
import os
import json

# ---------------- KONFIGURASI ----------------
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DB_FILE = "database.json"
PREFIX = "!"
ZONA_WIB = 7
ZONA_PHT = 8

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
                "Venatus": {"interval_jam": 10, "terakhir_muncul": "2026-06-24T11:31:00"},
                "Viorent": {"interval_jam": 10, "terakhir_muncul": "2026-06-24T11:43:00"},
                "LadyDalia": {"interval_jam": 18, "terakhir_muncul": "2026-06-24T04:03:00"},
                "Ego": {"interval_jam": 21, "terakhir_muncul": "2026-06-24T08:54:00"},
                "Shuliar": {"interval_jam": 35, "terakhir_muncul": "2026-06-23T15:24:00"},
                "Larba": {"interval_jam": 35, "terakhir_muncul": None},
                "Catena": {"interval_jam": 35, "terakhir_muncul": None},
                "Livera": {"interval_jam": 24, "terakhir_muncul": "2026-06-24T06:38:00"},
                "Undomiel": {"interval_jam": 24, "terakhir_muncul": "2026-06-24T07:36:00"},
                "Araneo": {"interval_jam": 24, "terakhir_muncul": "2026-06-24T07:01:00"},
                "Wannitas": {"interval_jam": 48, "terakhir_muncul": "2026-06-24T12:55:00"},
                "Metus": {"interval_jam": 48, "terakhir_muncul": "2026-06-23T15:19:00"},
                "Duplican": {"interval_jam": 48, "terakhir_muncul": "2026-06-23T14:10:00"},
                "BaronBraudmore": {"interval_jam": 32, "terakhir_muncul": "2026-06-23T16:50:00"},
                "Gareth": {"interval_jam": 32, "terakhir_muncul": "2026-06-24T09:27:00"},
                "Amentis": {"interval_jam": 29, "terakhir_muncul": "2026-06-24T04:33:00"},
                "Titore": {"interval_jam": 37, "terakhir_muncul": None},
                "GeneralAquleus": {"interval_jam": 29, "terakhir_muncul": "2026-06-24T11:54:00"},
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

# ---------------- TOMBOL INTERAKTIF ----------------
class TandaiMatiView(View):
    def __init__(self, nama_boss):
        super().__init__(timeout=None)
        self.nama_boss = nama_boss

    @discord.ui.button(label="✅ Sudah Mati", style=discord.ButtonStyle.success)
    async def sudah_mati(self, interaction: discord.Interaction, button: Button):
        sekarang_utc = datetime.utcnow()
        data_db["boss_respawn"][self.nama_boss]["terakhir_muncul"] = sekarang_utc.isoformat()
        simpan_database(data_db)

        interval = data_db["boss_respawn"][self.nama_boss]["interval_jam"]
        berikutnya = sekarang_utc + timedelta(hours=interval)
        berikutnya_wib = berikutnya + timedelta(hours=ZONA_WIB)
        berikutnya_pht = berikutnya + timedelta(hours=ZONA_PHT)

        await interaction.response.send_message(
            f"✅ **{self.nama_boss}** sudah ditandai mati!\n"
            f"Berikutnya akan muncul: 🇮🇩 {berikutnya_wib.strftime('%H:%M')} WIB | 🇵🇭 {berikutnya_pht.strftime('%H:%M')} PHT",
            ephemeral=False
        )

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
    pesan = "🔄 **JADWAL BOSS RESPAWN**\n──────────────────────────────────────\n"

    for nama, info in data_db["boss_respawn"].items():
        interval = info["interval_jam"]
        terakhir = info["terakhir_muncul"]

        if not terakhir:
            pesan += f"**{nama}**\n⏳ Belum diatur\n\n"
            continue

        terakhir_waktu = datetime.fromisoformat(terakhir)
        berikutnya = terakhir_waktu + timedelta(hours=interval)
        if berikutnya < sekarang_utc:
            berikutnya += timedelta(hours=interval)

        berikutnya_wib = berikutnya + timedelta(hours=ZONA_WIB)
        berikutnya_pht = berikutnya + timedelta(hours=ZONA_PHT)
        sisa = format_sisa_waktu(berikutnya - sekarang_utc)

        pesan += f"**{nama}**\n🇮🇩 {berikutnya_wib.strftime('%H:%M')} WIB | 🇵🇭 {berikutnya_pht.strftime('%H:%M')} PHT\n⏳ {sisa}\n\n"

    await ctx.send(pesan)

@bot.command(name="fixlist", aliases=["fx"])
async def tampilkan_fix_hari_ini(ctx):
    sekarang_utc = datetime.utcnow()
    hari_sekarang = hari_ke_kode(sekarang_utc.weekday())
    nama_hari_ini = nama_hari(hari_sekarang)

    pesan = f"📅 **JADWAL BOSS FIXED - {nama_hari_ini.upper()}**\n──────────────────────────────────────\n"
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

@bot.command(name="setrespawn", aliases=["sr"])
async def set_respawn_time(ctx, nama_boss: str, jam: int, menit: int = 0):
    nama_boss = nama_boss.capitalize()
    if nama_boss not in data_db["boss_respawn"]:
        return await ctx.send(f"❌ Boss **{nama_boss}** tidak ditemukan.")

    sekarang = datetime.utcnow() + timedelta(hours=ZONA_WIB)
    waktu_lokal = sekarang.replace(hour=jam, minute=menit, second=0, microsecond=0)
    if waktu_lokal > sekarang:
        waktu_lokal -= timedelta(days=1)

    waktu_utc = waktu_lokal - timedelta(hours=ZONA_WIB)
    data_db["boss_respawn"][nama_boss]["terakhir_muncul"] = waktu_utc.isoformat()
    simpan_database(data_db)

    interval = data_db["boss_respawn"][nama_boss]["interval_jam"]
    berikutnya = waktu_utc + timedelta(hours=interval)
    berikutnya_wib = berikutnya + timedelta(hours=ZONA_WIB)
    berikutnya_pht = berikutnya + timedelta(hours=ZONA_PHT)

    await ctx.send(
        f"✅ **Waktu {nama_boss} berhasil diatur!**\n"
        f"Terakhir mati: {waktu_lokal.strftime('%H:%M WIB')}\n"
        f"Berikutnya: 🇮🇩 {berikutnya_wib.strftime('%H:%M')} WIB | 🇵🇭 {berikutnya_pht.strftime('%H:%M')} PHT"
    )

@bot.command(name="bantuan", aliases=["b", "menu"])
async def bantuan(ctx):
    pesan = "🤖 **PERINTAH BOT JADWAL BOSS**\n"
    pesan += "`!rs` / `!respawnlist` → Lihat semua boss respawn\n"
    pesan += "`!fx` / `!fixlist` → Jadwal fixed hari ini saja\n"
    pesan += "`!sr Nama 8 30` → Atur waktu terakhir mati boss\n"
    pesan += "`!bantuan` / `!b` / `!menu` → Tampilkan panduan ini\n"
    pesan += "Notifikasi otomatis: -10 menit, -5 menit, dan saat spawn dengan @everyone\n"
    await ctx.send(pesan)

# ---------------- CEK & KIRIM NOTIFIKASI ----------------
@tasks.loop(minutes=1)
async def cek_spawn():
    sekarang_utc = datetime.utcnow()
    hari_sekarang = hari_ke_kode(sekarang_utc.weekday())
    channel = bot.get_channel(data_db["pengaturan"]["channel_id"])

    if not channel:
        return

    # --- Notifikasi Boss Fixed ---
    for nama, jadwal in data_db["boss_fixed"].items():
        for item in jadwal:
            if item["hari"] == hari_sekarang:
                wkt_utc = ubah_waktu_ke_utc(item["waktu"])
                selisih = (wkt_utc - sekarang_utc).total_seconds() / 60

                if abs(selisih) < 1:
                    j, m = map(int, item["waktu"].split(":"))
                    pht_j = (j + 1) % 24
                    await channel.send(
                        f"@everyone 📅 **BOSS FIXED SPAWN!** 📅\n\n"
                        f"**{nama}**\n🇮🇩 {j:02d}:{m:02d} WIB\n🇵🇭 {pht_j:02d}:{m:02d} PHT\n✅ Siap dikalahkan!"
                    )
                elif 9 < selisih < 11:
                    await channel.send(f"@everyone ⏰ **PENGINGAT!** {nama} akan muncul dalam 10 menit!")
                elif 4 < selisih < 6:
                    await channel.send(f"@everyone ⏰ **PENGINGAT!** {nama} akan muncul dalam 5 menit!")

    # --- Notifikasi Boss Respawn ---
    for nama, info in data_db["boss_respawn"].items():
        if not info["terakhir_muncul"]:
            continue

        interval = info["interval_jam"]
        terakhir = datetime.fromisoformat(info["terakhir_muncul"])
        berikutnya = terakhir + timedelta(hours=interval)
        selisih = (berikutnya - sekarang_utc).total_seconds() / 60

        if abs(selisih) < 1:
            wib = berikutnya.strftime("%H:%M")
            pht = (berikutnya + timedelta(hours=1)).strftime("%H:%M")
            view = TandaiMatiView(nama)
            await channel.send(
                f"@everyone 🔄 **BOSS RESPAWN!** 🔄\n\n"
                f"**{nama}**\n🇮🇩 {wib} WIB\n🇵🇭 {pht} PHT\n⏱️ Waktunya bertarung!",
                view=view
            )
        elif 9 < selisih < 11:
            await channel.send(f"@everyone ⏰ **PENGINGAT!** {nama} akan muncul dalam 10 menit!")
        elif 4 < selisih < 6:
            await channel.send(f"@everyone ⏰ **PENGINGAT!** {nama} akan muncul dalam 5 menit!")

# Jalankan bot
if __name__ == "__main__":
    if not TOKEN:
        print("❌ Token tidak ditemukan!")
    else:
        bot.run(TOKEN)
