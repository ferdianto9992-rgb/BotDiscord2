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
        data = json.load(f)
        # Pastikan semua waktu punya zona UTC agar tidak bingung
        for nama, info in data["boss_respawn"].items():
            if info["terakhir_muncul"] and "+00:00" not in info["terakhir_muncul"]:
                info["terakhir_muncul"] += "+00:00"
        return data

def simpan_database(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# ---------------- FUNGSI BANTU ----------------
def hari_ke_kode(waktu):
    return waktu.weekday() + 1 if waktu.weekday() != 6 else 0

def ubah_waktu_wib_ke_utc(jam: int, menit: int):
    """Konversi jam WIB ke UTC dengan benar"""
    sekarang_utc = datetime.now(timezone.utc)
    sekarang_wib = sekarang_utc + timedelta(hours=ZONA_WIB)
    
    # Buat waktu target di zona WIB
    target_wib = sekarang_wib.replace(hour=jam, minute=menit, second=0, microsecond=0)
    
    # Jika jam yang dimasukkan lebih besar dari sekarang, berarti itu waktu kemarin
    if target_wib > sekarang_wib:
        target_wib -= timedelta(days=1)
    
    # Kembalikan ke UTC
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
            return await interaction.response.send_message("⚠️ Data sudah dicatat!", ephemeral=True)
        
        self.sudah_diklik = True
        button.disabled = True
        button.label = "✅ Sudah Dicatat"
        button.style = discord.ButtonStyle.secondary

        sekarang_utc = datetime.now(timezone.utc)
        data_db["boss_respawn"][self.nama_boss]["terakhir_muncul"] = sekarang_utc.isoformat()
        simpan_database(data_db)

        interval = data_db["boss_respawn"][self.nama_boss]["interval_jam"]
        berikutnya_utc = sekarang_utc + timedelta(hours=interval)
        berikutnya_wib = berikutnya_utc + timedelta(hours=ZONA_WIB)
        berikutnya_pht = berikutnya_utc + timedelta(hours=ZONA_PHT)

        await interaction.response.edit_message(view=self)
        await interaction.followup.send(
            f"✅ **{self.nama_boss}** sudah ditandai mati!\n"
            f"Terakhir mati: {berikutnya_wib - timedelta(hours=interval):%H:%M} WIB\n"
            f"Berikutnya muncul: 🇮🇩 {berikutnya_wib:%H:%M} WIB | 🇵🇭 {berikutnya_pht:%H:%M} PHT"
        )

# ---------------- INISIALISASI BOT ----------------
data_db = baca_database()
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# Penyimpanan pesan yang sudah dikirim agar tidak berulang
pesan_terkirim = {
    "respawn": {},
    "fixed": {}
}

# ---------------- PERINTAH ----------------
@bot.event
async def on_ready():
    print(f"✅ Bot aktif: {bot.user}")
    print(f"📋 Jumlah boss: {len(data_db['boss_respawn'])} respawn, {len(data_db['boss_fixed'])} tetap")
    cek_spawn.start()

@bot.command(name="respawnlist", aliases=["rs"])
async def tampilkan_jadwal_respawn(ctx):
    sekarang_utc = datetime.now(timezone.utc)
    pesan = "🔄 **JADWAL BOSS RESPAWN**\n────────────────────────────\n"
    daftar_boss = []

    for nama, info in data_db["boss_respawn"].items():
        if not info["terakhir_muncul"]:
            continue
        
        terakhir_utc = datetime.fromisoformat(info["terakhir_muncul"])
        interval = info["interval_jam"]
        berikutnya_utc = terakhir_utc + timedelta(hours=interval)

        # Kalau sudah lewat, majukan ke jadwal berikutnya
        while berikutnya_utc <= sekarang_utc:
            berikutnya_utc += timedelta(hours=interval)

        berikutnya_wib = berikutnya_utc + timedelta(hours=ZONA_WIB)
        berikutnya_pht = berikutnya_utc + timedelta(hours=ZONA_PHT)
        sisa = berikutnya_utc - sekarang_utc
        jam_sisa = int(sisa.total_seconds() // 3600)
        menit_sisa = int((sisa.total_seconds() % 3600) // 60)

        daftar_boss.append({
            "waktu": berikutnya_utc,
            "nama": nama,
            "wib": berikutnya_wib.strftime("%H:%M"),
            "pht": berikutnya_pht.strftime("%H:%M"),
            "sisa": f"{jam_sisa}j {menit_sisa}m lagi"
        })

    daftar_boss.sort(key=lambda x: x["waktu"])

    if not daftar_boss:
        pesan += "Belum ada waktu mati yang dicatat."
    else:
        for b in daftar_boss:
            pesan += f"**{b['nama']}**\n🇮🇩 {b['wib']} WIB | 🇵🇭 {b['pht']} PHT\n⏳ {b['sisa']}\n\n"

    await ctx.send(pesan)

@bot.command(name="setrespawn", aliases=["sr"])
async def atur_waktu_mati(ctx, nama_boss: str, jam: int, menit: int = 0):
    nama_boss = nama_boss.capitalize()
    if nama_boss not in data_db["boss_respawn"]:
        return await ctx.send(f"❌ Boss **{nama_boss}** tidak ada di daftar!")

    # Konversi jam WIB ke UTC
    waktu_utc = ubah_waktu_wib_ke_utc(jam, menit)
    data_db["boss_respawn"][nama_boss]["terakhir_muncul"] = waktu_utc.isoformat()
    simpan_database(data_db)

    # Hitung jadwal berikutnya
    interval = data_db["boss_respawn"][nama_boss]["interval_jam"]
    berikutnya_utc = waktu_utc + timedelta(hours=interval)
    berikutnya_wib = berikutnya_utc + timedelta(hours=ZONA_WIB)
    berikutnya_pht = berikutnya_utc + timedelta(hours=ZONA_PHT)

    await ctx.send(
        f"✅ **{nama_boss}** dicatat mati jam **{jam:02d}:{menit:02d} WIB**\n"
        f"Berikutnya muncul: 🇮🇩 {berikutnya_wib:%H:%M} WIB | 🇵🇭 {berikutnya_pht:%H:%M} PHT"
    )

@bot.command(name="fixlist", aliases=["fx"])
async def tampilkan_jadwal_fixed(ctx):
    sekarang_wib = datetime.now(timezone.utc) + timedelta(hours=ZONA_WIB)
    hari_sekarang = hari_ke_kode(sekarang_wib)
    nama_hari = ["Minggu", "Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu"][hari_sekarang]

    pesan = f"📅 **JADWAL BOSS TETAP - {nama_hari.upper()}**\n────────────────────────────\n"
    ada = False

    for nama, jadwal in data_db["boss_fixed"].items():
        for item in jadwal:
            if item["hari"] == hari_sekarang:
                j, m = map(int, item["waktu"].split(":"))
                pesan += f"**{nama}**\n🇮🇩 {j:02d}:{m:02d} WIB | 🇵🇭 {(j+1)%24:02d}:{m:02d} PHT\n\n"
                ada = True

    if not ada:
        pesan += "Tidak ada jadwal hari ini."

    await ctx.send(pesan)

@bot.command(name="bantuan", aliases=["b", "menu"])
async def bantuan(ctx):
    pesan = (
        "🤖 **PERINTAH BOT**\n"
        "`!rs` / `!respawnlist` → Lihat semua jadwal respawn\n"
        "`!sr NamaJam 14 48` → Catat waktu mati (contoh: !sr Undomiel 14 48)\n"
        "`!fx` / `!fixlist` → Jadwal boss tetap hari ini\n"
        "`!bantuan` → Bantuan"
    )
    await ctx.send(pesan)

# ---------------- CEK & KIRIM NOTIFIKASI ----------------
@tasks.loop(seconds=15)
async def cek_spawn():
    sekarang_utc = datetime.now(timezone.utc)
    channel = bot.get_channel(data_db["pengaturan"]["channel_id"])
    if not channel:
        return

    # --- CEK BOSS RESPAWN ---
    for nama, info in data_db["boss_respawn"].items():
        if not info["terakhir_muncul"]:
            continue

        terakhir_utc = datetime.fromisoformat(info["terakhir_muncul"])
        interval = info["interval_jam"]
        berikutnya_utc = terakhir_utc + timedelta(hours=interval)

        # Majukan jadwal kalau sudah lewat
        while berikutnya_utc <= sekarang_utc:
            berikutnya_utc += timedelta(hours=interval)

        selisih_menit = (berikutnya_utc - sekarang_utc).total_seconds() / 60
        kunci = f"{nama}_{berikutnya_utc.strftime('%Y%m%d%H%M')}"

        # Deteksi dengan jendela lebar agar tidak terlewat
        if 9.0 < selisih_menit < 11.0 and kunci not in pesan_terkirim["respawn"]:
            pesan_terkirim["respawn"][kunci] = "10m"
            await channel.send(f"@everyone ⏰ **PENGINGAT!** {nama} akan muncul dalam 10 menit!")
        
        elif 4.0 < selisih_menit < 6.0 and kunci not in pesan_terkirim["respawn"]:
            pesan_terkirim["respawn"][kunci] = "5m"
            await channel.send(f"@everyone ⏰ **PENGINGAT!** {nama} akan muncul dalam 5 menit!")
        
        elif abs(selisih_menit) < 3.0 and kunci not in pesan_terkirim["respawn"]:
            pesan_terkirim["respawn"][kunci] = "spawn"
            wib = berikutnya_utc + timedelta(hours=ZONA_WIB)
            pht = berikutnya_utc + timedelta(hours=ZONA_PHT)
            await channel.send(
                f"@everyone 🔄 **BOSS RESPAWN!** 🔄\n\n"
                f"**{nama}**\n🇮🇩 {wib:%H:%M} WIB\n🇵🇭 {pht:%H:%M} PHT\n⏱️ Waktunya bertarung!",
                view=TandaiMatiView(nama)
            )

    # --- CEK BOSS TETAP ---
    sekarang_wib = sekarang_utc + timedelta(hours=ZONA_WIB)
    hari_sekarang = hari_ke_kode(sekarang_wib)

    for nama, jadwal in data_db["boss_fixed"].items():
        for item in jadwal:
            if item["hari"] != hari_sekarang:
                continue
            
            j, m = map(int, item["waktu"].split(":"))
            target_wib = sekarang_wib.replace(hour=j, minute=m, second=0, microsecond=0)
            target_utc = target_wib - timedelta(hours=ZONA_WIB)
            selisih_menit = (target_utc - sekarang_utc).total_seconds() / 60
            kunci = f"fixed_{nama}_{j}_{m}"

            if 9.0 < selisih_menit < 11.0 and kunci not in pesan_terkirim["fixed"]:
                pesan_terkirim["fixed"][kunci] = "10m"
                await channel.send(f"@everyone ⏰ **PENGINGAT!** {nama} akan muncul dalam 10 menit!")
            
            elif 4.0 < selisih_menit < 6.0 and kunci not in pesan_terkirim["fixed"]:
                pesan_terkirim["fixed"][kunci] = "5m"
                await channel.send(f"@everyone ⏰ **PENGINGAT!** {nama} akan muncul dalam 5 menit!")
            
            elif abs(selisih_menit) < 3.0 and kunci not in pesan_terkirim["fixed"]:
                pesan_terkirim["fixed"][kunci] = "spawn"
                await channel.send(
                    f"@everyone 📅 **BOSS TETAP MUNCUL!** 📅\n\n"
                    f"**{nama}**\n🇮🇩 {j:02d}:{m:02d} WIB\n🇵🇭 {(j+1)%24:02d}:{m:02d} PHT\n✅ Siap dikalahkan!"
                )

    # Bersihkan data pesan lama agar tidak memakan memori
    for tipe in pesan_terkirim:
        hapus = []
        for k in pesan_terkirim[tipe]:
            if tipe == "respawn":
                try:
                    wkt_str = k.split("_")[1]
                    wkt = datetime.strptime(wkt_str, "%Y%m%d%H%M").replace(tzinfo=timezone.utc)
                    if (sekarang_utc - wkt).total_seconds() > 7200:
                        hapus.append(k)
                except:
                    pass
            else:
                hapus.append(k)
        for k in hapus:
            if k in pesan_terkirim[tipe]:
                del pesan_terkirim[tipe][k]

# Jalankan bot
if __name__ == "__main__":
    if not TOKEN:
        print("❌ Token tidak ditemukan!")
    else:
        bot.run(TOKEN)
