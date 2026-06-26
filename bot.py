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
                "channel_id": 1516422050032521316,
                "waktu_cek_menit": 1
            },
            "boss_respawn": {
                "Venatus": {"interval_jam": 10, "terakhir_muncul": "2026-06-24T08:31:00"},
                "Viorent": {"interval_jam": 10, "terakhir_muncul": "2026-06-24T08:37:00"},
                "LadyDalia": {"interval_jam": 18, "terakhir_muncul": "2026-06-23T21:03:00"},
                "Ego": {"interval_jam": 21, "terakhir_muncul": "2026-06-24T08:55:00"},
                "Shuliar": {"interval_jam": 35, "terakhir_muncul": "2026-06-24T05:24:00"},
                "Larba": {"interval_jam": 35, "terakhir_muncul": None},
                "Catena": {"interval_jam": 35, "terakhir_muncul": None},
                "Livera": {"interval_jam": 24, "terakhir_muncul": "2026-06-24T06:38:00"},
                "Undomiel": {"interval_jam": 24, "terakhir_muncul": "2026-06-24T07:36:00"},
                "Araneo": {"interval_jam": 24, "terakhir_muncul": "2026-06-24T07:01:00"},
                "Wannitas": {"interval_jam": 48, "terakhir_muncul": "2026-06-22T12:54:00"},
                "Metus": {"interval_jam": 48, "terakhir_muncul": "2026-06-23T15:19:00"},
                "Duplican": {"interval_jam": 48, "terakhir_muncul": "2026-06-23T14:09:00"},
                "BaronBraudmore": {"interval_jam": 32, "terakhir_muncul": "2026-06-24T08:50:00"},
                "Gareth": {"interval_jam": 32, "terakhir_muncul": "2026-06-24T01:25:00"},
                "Amentis": {"interval_jam": 29, "terakhir_muncul": "2026-06-24T06:33:00"},
                "Titore": {"interval_jam": 37, "terakhir_muncul": None},
                "GeneralAquleus": {"interval_jam": 29, "terakhir_muncul": "2026-06-24T06:54:00"},
                "Ordo": {"interval_jam": 62, "terakhir_muncul": None},
                "Asta": {"interval_jam": 62, "terakhir_muncul": None},
                "Secreta": {"interval_jam": 62, "terakhir_muncul": None},
                "Supore": {"interval_jam": 62, "terakhir_muncul": None}
            },
            "boss_fixed": {
                "Clemantis": [{"hari": 1, "waktu": "10:30"}, {"hari": 4, "waktu": "18:00"}],
                "Thymele": [{"hari": 1, "waktu": "18:00"}, {"hari": 3, "waktu": "10:30"}],
                "Libitina": [{"hari": 1, "waktu": "20:00"}, {"hari": 5, "waktu": "20:00"}],
                "Saphirus": [{"hari": 2, "waktu": "10:30"}, {"hari": 0, "waktu": "16:00"}],
                "Neutro": [{"hari": 2, "waktu": "18:00"}, {"hari": 4, "waktu": "10:30"}],
                "Rakajeth": [{"hari": 2, "waktu": "21:00"}, {"hari": 0, "waktu": "18:00"}],
                "Auraq": [{"hari": 3, "waktu": "20:00"}, {"hari": 5, "waktu": "21:00"}],
                "Roderick": [{"hari": 5, "waktu": "18:00"}],
                "Milavy": [{"hari": 6, "waktu": "14:00"}],
                "Ringor": [{"hari": 6, "waktu": "16:00"}],
                "Chaiflock": [{"hari": 0, "waktu": "14:00"}],
                "Tumier": [{"hari": 0, "waktu": "18:00"}],
                "Benji": [{"hari": 0, "waktu": "20:00"}]
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
def hari_ke_kode(waktu):
    return waktu.weekday() + 1 if waktu.weekday() != 6 else 0

def nama_hari(kode):
    return ["Minggu", "Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu"][kode]

def ubah_waktu_ke_utc(waktu_str):
    j, m = map(int, waktu_str.split(":"))
    sekarang_wib = datetime.utcnow() + timedelta(hours=ZONA_WIB)
    waktu_lokal = sekarang_wib.replace(hour=j, minute=m, second=0, microsecond=0)
    return waktu_lokal - timedelta(hours=ZONA_WIB)

def format_sisa_waktu(delta):
    if delta.total_seconds() < 0:
        return "Sudah muncul"
    total_detik = int(delta.total_seconds())
    jam = total_detik // 3600
    menit = (total_detik % 3600) // 60
    if jam > 0:
        return f"{jam}j {menit:02d}m lagi"
    return f"{menit}m lagi"

# ---------------- TOMBOL INTERAKTIF ----------------
class TandaiMatiView(View):
    def __init__(self, nama_boss):
        super().__init__(timeout=1800)  # Tombol aktif 30 menit penuh
        self.nama_boss = nama_boss
        self.sudah_diklik = False

    @discord.ui.button(label="✅ Sudah Mati", style=discord.ButtonStyle.success)
    async def sudah_mati(self, interaction: discord.Interaction, button: Button):
        if self.sudah_diklik:
            return await interaction.response.send_message(
                "⚠️ Data sudah dicatat, tidak bisa diklik lagi!", ephemeral=True
            )

        self.sudah_diklik = True
        button.disabled = True
        button.label = "✅ Sudah Dicatat"
        button.style = discord.ButtonStyle.secondary

        sekarang_utc = datetime.utcnow()
        data_db["boss_respawn"][self.nama_boss]["terakhir_muncul"] = sekarang_utc.isoformat()
        simpan_database(data_db)

        interval = data_db["boss_respawn"][self.nama_boss]["interval_jam"]
        berikutnya = sekarang_utc + timedelta(hours=interval)
        berikutnya_wib = berikutnya + timedelta(hours=ZONA_WIB)
        berikutnya_pht = berikutnya + timedelta(hours=ZONA_PHT)

        await interaction.response.edit_message(view=self)

        await interaction.followup.send(
            f"✅ **{self.nama_boss}** sudah ditandai mati!\n"
            f"Berikutnya muncul: 🇮🇩 {berikutnya_wib.strftime('%H:%M')} WIB | 🇵🇭 {berikutnya_pht.strftime('%H:%M')} PHT",
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
    daftar_boss = []

    for nama, info in data_db["boss_respawn"].items():
        interval = info["interval_jam"]
        terakhir = info["terakhir_muncul"]

        if not terakhir:
            continue

        terakhir_waktu = datetime.fromisoformat(terakhir)
        berikutnya = terakhir_waktu + timedelta(hours=interval)
        while berikutnya <= sekarang_utc:
            berikutnya += timedelta(hours=interval)

        berikutnya_wib = berikutnya + timedelta(hours=ZONA_WIB)
        berikutnya_pht = berikutnya + timedelta(hours=ZONA_PHT)
        sisa = format_sisa_waktu(berikutnya - sekarang_utc)

        daftar_boss.append({
            "waktu": berikutnya,
            "nama": nama,
            "wib": berikutnya_wib.strftime('%H:%M'),
            "pht": berikutnya_pht.strftime('%H:%M'),
            "sisa": sisa
        })

    daftar_boss.sort(key=lambda x: x["waktu"])

    if not daftar_boss:
        pesan += "Belum ada jadwal boss yang diatur."
    else:
        for b in daftar_boss:
            pesan += f"**{b['nama']}**\n🇮🇩 {b['wib']} WIB | 🇵🇭 {b['pht']} PHT\n⏳ {b['sisa']}\n\n"

    await ctx.send(pesan)

@bot.command(name="fixlist", aliases=["fx"])
async def tampilkan_fix_hari_ini(ctx):
    sekarang_wib = datetime.utcnow() + timedelta(hours=ZONA_WIB)
    hari_sekarang = hari_ke_kode(sekarang_wib)
    nama_hari_ini = nama_hari(hari_sekarang)

    pesan = f"📅 **JADWAL BOSS FIXED - {nama_hari_ini.upper()}**\n──────────────────────────────────────\n"
    ada = False

    for nama, jadwal in data_db["boss_fixed"].items():
        for item in jadwal:
            if item["hari"] == hari_sekarang:
                j, m = map(int, item["waktu"].split(":"))
                wib = f"{j:02d}:{m:02d}"
                pht = f"{(j + 1) % 24:02d}:{m:02d}"
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

    sekarang_lokal = datetime.utcnow() + timedelta(hours=ZONA_WIB)
    waktu_lokal = sekarang_lokal.replace(hour=jam, minute=menit, second=0, microsecond=0)
    if waktu_lokal > sekarang_lokal:
        waktu_lokal -= timedelta(days=1)

    waktu_utc = waktu_lokal - timedelta(hours=ZONA_WIB)
    data_db["boss_respawn"][nama_boss]["terakhir_muncul"] = waktu_utc.isoformat()
    simpan_database(data_db)

    interval = data_db["boss_respawn"][nama_boss]["interval_jam"]
    berikutnya = waktu_utc + timedelta(hours=interval)
    berikutnya_wib = berikutnya + timedelta(hours=ZONA_WIB)
    berikutnya_pht = berikutnya + timedelta(hours=ZONA_PHT)

    await ctx.send(
        f"✅ **{nama_boss}** berhasil diatur!\n"
        f"Terakhir mati: {waktu_lokal.strftime('%d/%m/%Y %H:%M')} WIB\n"
        f"Berikutnya: 🇮🇩 {berikutnya_wib.strftime('%H:%M')} WIB | 🇵🇭 {berikutnya_pht.strftime('%H:%M')} PHT"
    )

@bot.command(name="bantuan", aliases=["b", "menu"])
async def bantuan(ctx):
    pesan = "🤖 **PERINTAH BOT JADWAL BOSS**\n"
    pesan += "`!rs` / `!respawnlist` → Lihat jadwal boss yang sudah diatur\n"
    pesan += "`!fx` / `!fixlist` → Jadwal boss tetap hari ini\n"
    pesan += "`!sr Nama 8 30` → Atur waktu mati boss (akan muncul otomatis)\n"
    pesan += "`!bantuan` / `!b` / `!menu` → Bantuan\n"
    await ctx.send(pesan)

# ---------------- CEK & KIRIM NOTIFIKASI ----------------
# ✅ Diubah: Cek setiap 15 detik agar sangat akurat
@tasks.loop(seconds=15)
async def cek_spawn():
    sekarang_utc = datetime.utcnow()
    sekarang_wib = sekarang_utc + timedelta(hours=ZONA_WIB)
    hari_sekarang = hari_ke_kode(sekarang_wib)
    channel = bot.get_channel(data_db["pengaturan"]["channel_id"])

    if not channel:
        return

    # --- Notifikasi Boss Fixed ---
    for nama, jadwal in data_db["boss_fixed"].items():
        for item in jadwal:
            if item["hari"] == hari_sekarang:
                wkt_utc = ubah_waktu_ke_utc(item["waktu"])
                selisih_menit = (wkt_utc - sekarang_utc).total_seconds() / 60

                # ✅ Kondisi diperhalus agar tepat dan tidak terlewat
                if 9.9 < selisih_menit < 10.1:
                    await channel.send(f"@everyone ⏰ **PENGINGAT!** {nama} akan muncul dalam 10 menit!")
                elif 4.9 < selisih_menit < 5.1:
                    await channel.send(f"@everyone ⏰ **PENGINGAT!** {nama} akan muncul dalam 5 menit!")
                elif abs(selisih_menit) < 1.5:
                    j, m = map(int, item["waktu"].split(":"))
                    await channel.send(
                        f"@everyone 📅 **BOSS FIXED SPAWN!** 📅\n\n"
                        f"**{nama}**\n🇮🇩 {j:02d}:{m:02d} WIB\n🇵🇭 {(j+1)%24:02d}:{m:02d} PHT\n✅ Siap dikalahkan!"
                    )

    # --- Notifikasi Boss Respawn ---
    for nama, info in data_db["boss_respawn"].items():
        if not info["terakhir_muncul"]:
            continue

        interval = info["interval_jam"]
        terakhir = datetime.fromisoformat(info["terakhir_muncul"])
        berikutnya = terakhir + timedelta(hours=interval)
        while berikutnya <= sekarang_utc:
            berikutnya += timedelta(hours=interval)

        selisih_menit = (berikutnya - sekarang_utc).total_seconds() / 60

        # ✅ Kondisi diperbaiki agar tidak meleset
        if 9.9 < selisih_menit < 10.1:
            await channel.send(f"@everyone ⏰ **PENGINGAT!** {nama} akan muncul dalam 10 menit!")
        elif 4.9 < selisih_menit < 5.1:
            await channel.send(f"@everyone ⏰ **PENGINGAT!** {nama} akan muncul dalam 5 menit!")
        elif abs(selisih_menit) < 1.5:
            wib = berikutnya.strftime("%H:%M")
            pht = (berikutnya + timedelta(hours=1)).strftime("%H:%M")
            view = TandaiMatiView(nama)
            await channel.send(
                f"@everyone 🔄 **BOSS RESPAWN!** 🔄\n\n"
                f"**{nama}**\n🇮🇩 {wib} WIB\n🇵🇭 {pht} PHT\n⏱️ Waktunya bertarung!",
                view=view
            )

# Jalankan bot
if __name__ == "__main__":
    if not TOKEN:
        print("❌ Token tidak ditemukan!")
    else:
        bot.run(TOKEN)
