import discord
from discord.ext import tasks, commands
from discord.ui import View, Button
import asyncio
from datetime import datetime, timedelta, timezone
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
                "channel_id": 1516422050032521316
            },
            "boss_respawn": {
                "Venatus": {"interval_jam": 10, "terakhir_mati": "2026-06-26T08:31:00+00:00"},
                "Viorent": {"interval_jam": 10, "terakhir_mati": "2026-06-26T08:37:00+00:00"},
                "LadyDalia": {"interval_jam": 18, "terakhir_mati": "2026-06-26T03:31:00+00:00"},
                "Ego": {"interval_jam": 21, "terakhir_mati": "2026-06-26T03:55:00+00:00"},
                "Shuliar": {"interval_jam": 35, "terakhir_mati": "2026-06-26T03:24:00+00:00"},
                "Larba": {"interval_jam": 35, "terakhir_mati": None},
                "Catena": {"interval_jam": 35, "terakhir_mati": None},
                "Livera": {"interval_jam": 24, "terakhir_mati": "2026-06-26T04:38:00+00:00"},
                "Undomiel": {"interval_jam": 24, "terakhir_mati": "2026-06-26T05:36:00+00:00"},
                "Araneo": {"interval_jam": 24, "terakhir_mati": "2026-06-26T06:12:00+00:00"},
                "Wannitas": {"interval_jam": 48, "terakhir_mati": "2026-06-26T05:54:00+00:00"},
                "Metus": {"interval_jam": 48, "terakhir_mati": "2026-06-26T08:19:00+00:00"},
                "Duplican": {"interval_jam": 48, "terakhir_mati": "2026-06-26T07:09:00+00:00"},
                "BaronBraudmore": {"interval_jam": 32, "terakhir_mati": "2026-06-26T03:50:00+00:00"},
                "Gareth": {"interval_jam": 32, "terakhir_mati": "2026-06-26T02:25:00+00:00"},
                "Amentis": {"interval_jam": 29, "terakhir_mati": "2026-06-26T03:33:00+00:00"},
                "Titore": {"interval_jam": 37, "terakhir_mati": None},
                "GeneralAquleus": {"interval_jam": 29, "terakhir_mati": "2026-06-26T03:54:00+00:00"},
                "Ordo": {"interval_jam": 62, "terakhir_mati": None},
                "Asta": {"interval_jam": 62, "terakhir_mati": None},
                "Secreta": {"interval_jam": 62, "terakhir_mati": None},
                "Supore": {"interval_jam": 62, "terakhir_mati": None}
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

def ubah_ke_utc(jam: int, menit: int):
    sekarang_wib = datetime.now(timezone.utc) + timedelta(hours=ZONA_WIB)
    target_wib = sekarang_wib.replace(hour=jam, minute=menit, second=0, microsecond=0)
    if target_wib > sekarang_wib:
        target_wib -= timedelta(days=1)
    return target_wib - timedelta(hours=ZONA_WIB)

# ---------------- TOMBOL INTERAKTIF ----------------
class TandaiMatiView(View):
    def __init__(self, nama_boss):
        super().__init__(timeout=1800) # Aktif 30 menit
        self.nama_boss = nama_boss
        self.sudah_diklik = False

    @discord.ui.button(label="✅ Sudah Mati", style=discord.ButtonStyle.success)
    async def sudah_mati(self, interaction: discord.Interaction, button: Button):
        if self.sudah_diklik:
            return await interaction.response.send_message("⚠️ Sudah dicatat!", ephemeral=True)
        
        self.sudah_diklik = True
        button.disabled = True
        button.label = "✅ Sudah Dicatat"
        button.style = discord.ButtonStyle.secondary

        sekarang_utc = datetime.now(timezone.utc)
        data_db["boss_respawn"][self.nama_boss]["terakhir_mati"] = sekarang_utc.isoformat()
        simpan_database(data_db)

        interval = data_db["boss_respawn"][self.nama_boss]["interval_jam"]
        berikutnya_utc = sekarang_utc + timedelta(hours=interval)
        berikutnya_wib = berikutnya_utc + timedelta(hours=ZONA_WIB)
        berikutnya_pht = berikutnya_utc + timedelta(hours=ZONA_PHT)

        await interaction.response.edit_message(view=self)
        await interaction.followup.send(
            f"✅ **{self.nama_boss}** sudah ditandai mati!\n"
            f"Berikutnya: 🇮🇩 {berikutnya_wib.strftime('%H:%M')} WIB | 🇵🇭 {berikutnya_pht.strftime('%H:%M')} PHT"
        )

# ---------------- INISIALISASI ----------------
data_db = baca_database()
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents)
pesan_terkirim = {"respawn": {}, "fixed": {}}

# ---------------- PERINTAH ----------------
@bot.event
async def on_ready():
    print(f"✅ Bot aktif: {bot.user}")
    cek_spawn.start()

@bot.command(name="rs", aliases=["respawnlist"])
async def lihat_jadwal(ctx):
    sekarang_utc = datetime.now(timezone.utc)
    pesan = "🔄 **JADWAL BOSS RESPAWN**\n───────────────────\n"
    daftar = []
    for nama, info in data_db["boss_respawn"].items():
        if not info["terakhir_mati"]:
            continue
        terakhir = datetime.fromisoformat(info["terakhir_mati"])
        berikutnya = terakhir + timedelta(hours=info["interval_jam"])
        while berikutnya <= sekarang_utc:
            berikutnya += timedelta(hours=info["interval_jam"])
        wib = berikutnya + timedelta(hours=ZONA_WIB)
        pht = berikutnya + timedelta(hours=ZONA_PHT)
        sisa = berikutnya - sekarang_utc
        daftar.append((berikutnya, nama, wib, pht, sisa))
    
    daftar.sort()
    for _, nama, wib, pht, sisa in daftar:
        jam = sisa.total_seconds()//3600
        menit = (sisa.total_seconds()%3600)//60
        pesan += f"**{nama}**\n🇮🇩 {wib:%H:%M} WIB | 🇵🇭 {pht:%H:%M} PHT\n⏳ {int(jam)}j {int(menit)}m lagi\n\n"
    await ctx.send(pesan)

@bot.command(name="sr")
async def atur_waktu_mati(ctx, nama: str, jam: int, menit: int=0):
    nama = nama.capitalize()
    if nama not in data_db["boss_respawn"]:
        return await ctx.send("❌ Nama boss tidak ditemukan!")
    waktu_utc = ubah_ke_utc(jam, menit)
    data_db["boss_respawn"][nama]["terakhir_mati"] = waktu_utc.isoformat()
    simpan_database(data_db)
    berikutnya = waktu_utc + timedelta(hours=data_db["boss_respawn"][nama]["interval_jam"])
    wib = berikutnya + timedelta(hours=ZONA_WIB)
    pht = berikutnya + timedelta(hours=ZONA_PHT)
    await ctx.send(f"✅ {nama} dicatat mati jam {jam:02d}:{menit:02d} WIB\nBerikutnya: {wib:%H:%M} WIB / {pht:%H:%M} PHT")

# ---------------- CEK NOTIFIKASI ----------------
@tasks.loop(seconds=15)
async def cek_spawn():
    sekarang_utc = datetime.now(timezone.utc)
    sekarang_wib = sekarang_utc + timedelta(hours=ZONA_WIB)
    channel = bot.get_channel(data_db["pengaturan"]["channel_id"])
    if not channel:
        return

    # --- Boss Respawn ---
    for nama, info in data_db["boss_respawn"].items():
        if not info["terakhir_mati"]:
            continue
        terakhir = datetime.fromisoformat(info["terakhir_mati"])
        berikutnya = terakhir + timedelta(hours=info["interval_jam"])
        while berikutnya <= sekarang_utc:
            berikutnya += timedelta(hours=info["interval_jam"])
        
        selisih_menit = (berikutnya - sekarang_utc).total_seconds() / 60
        kunci = f"{nama}_{berikutnya.strftime('%Y%m%d%H%M')}"

        if 9.0 < selisih_menit < 11.0 and kunci not in pesan_terkirim["respawn"]:
            pesan_terkirim["respawn"][kunci] = "10m"
            await channel.send(f"@everyone ⏰ **PENGINGAT!** {nama} akan muncul dalam 10 menit!")
        elif 4.0 < selisih_menit < 6.0 and kunci not in pesan_terkirim["respawn"]:
            pesan_terkirim["respawn"][kunci] = "5m"
            await channel.send(f"@everyone ⏰ **PENGINGAT!** {nama} akan muncul dalam 5 menit!")
        elif abs(selisih_menit) < 3.0 and kunci not in pesan_terkirim["respawn"]:
            pesan_terkirim["respawn"][kunci] = "spawn"
            wib = berikutnya + timedelta(hours=ZONA_WIB)
            pht = berikutnya + timedelta(hours=ZONA_PHT)
            await channel.send(
                f"@everyone 🔄 **BOSS RESPAWN!** 🔄\n\n"
                f"**{nama}**\n🇮🇩 {wib:%H:%M} WIB\n🇵🇭 {pht:%H:%M} PHT\n⏱️ Waktunya bertarung!",
                view=TandaiMatiView(nama)
            )

    # Bersihkan data lama
    for tipe in pesan_terkirim:
        hapus = [k for k in pesan_terkirim[tipe] if (sekarang_utc - datetime.fromisoformat(k.split("_")[1] + "+00:00")).total_seconds() > 7200]
        for k in hapus:
            del pesan_terkirim[tipe][k]

bot.run(os.getenv("DISCORD_BOT_TOKEN"))
