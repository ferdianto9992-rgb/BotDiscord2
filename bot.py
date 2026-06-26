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
                "channel_id": 1516729382134091796
            },
            "boss_respawn": {
                "Venatus": {"interval_jam": 10, "terakhir_muncul": "2026-06-24T08:31:00+00:00"},
                "Viorent": {"interval_jam": 10, "terakhir_muncul": "2026-06-24T08:37:00+00:00"},
                "LadyDalia": {"interval_jam": 18, "terakhir_muncul": "2026-06-25T09:22:00+00:00"},
                "Ego": {"interval_jam": 21, "terakhir_muncul": "2026-06-25T05:58:00+00:00"},
                "Shuliar": {"interval_jam": 35, "terakhir_muncul": "2026-06-24T05:24:00+00:00"},
                "Larba": {"interval_jam": 35, "terakhir_muncul": None},
                "Catena": {"interval_jam": 35, "terakhir_muncul": None},
                "Livera": {"interval_jam": 24, "terakhir_muncul": "2026-06-24T06:38:00+00:00"},
                "Undomiel": {"interval_jam": 24, "terakhir_muncul": "2026-06-24T07:36:00+00:00"},
                "Araneo": {"interval_jam": 24, "terakhir_muncul": "2026-06-24T07:01:00+00:00"},
                "Wannitas": {"interval_jam": 48, "terakhir_muncul": "2026-06-22T12:54:00+00:00"},
                "Metus": {"interval_jam": 48, "terakhir_muncul": "2026-06-23T15:19:00+00:00"},
                "Duplican": {"interval_jam": 48, "terakhir_muncul": "2026-06-23T14:09:00+00:00"},
                "BaronBraudmore": {"interval_jam": 32, "terakhir_muncul": "2026-06-24T08:50:00+00:00"},
                "Gareth": {"interval_jam": 32, "terakhir_muncul": "2026-06-24T01:25:00+00:00"},
                "Amentis": {"interval_jam": 29, "terakhir_muncul": "2026-06-25T04:52:00+00:00"},
                "Titore": {"interval_jam": 37, "terakhir_muncul": None},
                "GeneralAquleus": {"interval_jam": 29, "terakhir_muncul": "2026-06-24T06:54:00+00:00"},
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
        for nama, info in data["boss_respawn"].items():
            if info["terakhir_muncul"] and "+00:00" not in str(info["terakhir_muncul"]):
                info["terakhir_muncul"] = str(info["terakhir_muncul"]) + "+00:00"
        return data

def simpan_database(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# ---------------- FUNGSI BANTU ----------------
def hari_ke_kode(waktu):
    return waktu.weekday() + 1 if waktu.weekday() != 6 else 0

def nama_hari(kode):
    return ["Minggu", "Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu"][kode]

def ubah_waktu_wib_ke_utc(jam: int, menit: int):
    sekarang_utc = datetime.now(timezone.utc)
    sekarang_wib = sekarang_utc + timedelta(hours=ZONA_WIB)
    target_wib = sekarang_wib.replace(hour=jam, minute=menit, second=0, microsecond=0)
    if target_wib > sekarang_wib:
        target_wib -= timedelta(days=1)
    return target_wib - timedelta(hours=ZONA_WIB)

def format_sisa_waktu(delta):
    if delta.total_seconds() < 0:
        return "Sudah muncul"
    total_detik = int(delta.total_seconds())
    jam = total_detik // 3600
    menit = (total_detik % 3600) // 60
    if jam > 0:
        return f"{jam}j {menit:02d}m lagi"
    return f"{menit}m lagi"

# ---------------- TOMBOL PENCATATAN ----------------
class TandaiMatiView(View):
    def __init__(self, nama_boss):
        super().__init__(timeout=1800)
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
            f"Berikutnya muncul: 🇮🇩 {berikutnya_wib.strftime('%H:%M')} WIB | 🇵🇭 {berikutnya_pht.strftime('%H:%M')} PHT"
        )

# ---------------- INISIALISASI ----------------
data_db = baca_database()
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# Sistem pencatat pesan yang DIPERBAIKI total
pesan_terkirim = {}

# ---------------- PERINTAH ----------------
@bot.event
async def on_ready():
    print(f"✅ Bot aktif sebagai: {bot.user}")
    print(f"📊 Jumlah boss: {len(data_db['boss_respawn'])} respawn | {len(data_db['boss_fixed'])} tetap")
    cek_spawn.start()

@bot.command(name="respawnlist", aliases=["rs"])
async def tampilkan_respawn(ctx):
    sekarang_utc = datetime.now(timezone.utc)
    pesan = "🔄 **JADWAL BOSS RESPAWN**\n────────────────────────────\n"
    daftar_boss = []

    for nama, info in data_db["boss_respawn"].items():
        if not info["terakhir_muncul"]:
            continue

        terakhir_utc = datetime.fromisoformat(info["terakhir_muncul"])
        interval = info["interval_jam"]
        berikutnya_utc = terakhir_utc + timedelta(hours=interval)

        while berikutnya_utc <= sekarang_utc:
            berikutnya_utc += timedelta(hours=interval)

        berikutnya_wib = berikutnya_utc + timedelta(hours=ZONA_WIB)
        berikutnya_pht = berikutnya_utc + timedelta(hours=ZONA_PHT)
        sisa = format_sisa_waktu(berikutnya_utc - sekarang_utc)

        daftar_boss.append({
            "waktu": berikutnya_utc,
            "nama": nama,
            "wib": berikutnya_wib.strftime("%H:%M"),
            "pht": berikutnya_pht.strftime("%H:%M"),
            "sisa": sisa
        })

    daftar_boss.sort(key=lambda x: x["waktu"])

    if not daftar_boss:
        pesan += "Belum ada jadwal yang dicatat."
    else:
        for b in daftar_boss:
            pesan += f"**{b['nama']}**\n🇮🇩 {b['wib']} WIB | 🇵🇭 {b['pht']} PHT\n⏳ {b['sisa']}\n\n"

    await ctx.send(pesan)

@bot.command(name="setrespawn", aliases=["sr"])
async def atur_waktu_mati(ctx, *, teks_input: str):
    # Pisah bagian nama dan jam/menit
    bagian = teks_input.strip().split()
    if len(bagian) < 3:
        return await ctx.send("❌ Format salah! Contoh: `!sr LadyDalia 10 31` atau `!sr Lady dalia 10 31`")

    try:
        jam = int(bagian[-2])
        menit = int(bagian[-1])
    except ValueError:
        return await ctx.send("❌ Jam dan menit harus berupa angka! Contoh: `!sr Nama 10 31`")

    nama_input = "".join(bagian[:-2]).lower()

    # Cocokkan nama secara fleksibel (tidak peka huruf besar/kecil dan spasi)
    peta_nama = {n.lower().replace(" ", ""): n for n in data_db["boss_respawn"].keys()}
    if nama_input not in peta_nama:
        daftar = ", ".join(data_db["boss_respawn"].keys())
        return await ctx.send(f"❌ Boss tidak ditemukan!\nDaftar yang tersedia: {daftar}")

    nama_boss = peta_nama[nama_input]

    # Simpan ke database
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

    waktu_utc = ubah_waktu_wib_ke_utc(jam, menit)
    data_db["boss_respawn"][nama_boss]["terakhir_muncul"] = waktu_utc.isoformat()
    simpan_database(data_db)

    interval = data_db["boss_respawn"][nama_boss]["interval_jam"]
    berikutnya_utc = waktu_utc + timedelta(hours=interval)
    berikutnya_wib = berikutnya_utc + timedelta(hours=ZONA_WIB)
    berikutnya_pht = berikutnya_utc + timedelta(hours=ZONA_PHT)

    await ctx.send(
        f"✅ **{nama_boss}** dicatat mati jam **{jam:02d}:{menit:02d} WIB**\n"
        f"Berikutnya muncul: 🇮🇩 {berikutnya_wib:%H:%M} WIB | 🇵🇭 {berikutnya_pht:%H:%M} PHT"
    )

@bot.command(name="fixlist", aliases=["fx"])
async def tampilkan_fix(ctx):
    sekarang_wib = datetime.now(timezone.utc) + timedelta(hours=ZONA_WIB)
    hari_sekarang = hari_ke_kode(sekarang_wib)
    nama_hari_ini = nama_hari(hari_sekarang)

    pesan = f"📅 **JADWAL BOSS TETAP - {nama_hari_ini.upper()}**\n────────────────────────────\n"
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
        "`!sr Nama 11 52` → Catat waktu mati (contoh Amentis: !sr Amentis 11 52)\n"
        "`!fx` / `!fixlist` → Jadwal boss tetap hari ini\n"
        "`!bantuan` → Bantuan"
    )
    await ctx.send(pesan)

# ---------------- CEK & KIRIM NOTIFIKASI ----------------
@tasks.loop(seconds=15)
async def cek_spawn():
    sekarang_utc = datetime.now(timezone.utc)
    sekarang_wib = sekarang_utc + timedelta(hours=ZONA_WIB)
    channel = bot.get_channel(data_db["pengaturan"]["channel_id"])
    if not channel:
        return

    # Bersihkan catatan pesan yang sudah lebih dari 3 jam
    for kunci in list(pesan_terkirim.keys()):
        if (sekarang_utc - pesan_terkirim[kunci]).total_seconds() > 10800:
            del pesan_terkirim[kunci]

    # --- CEK BOSS RESPAWN ---
    for nama, info in data_db["boss_respawn"].items():
        if not info["terakhir_muncul"]:
            continue

        terakhir_utc = datetime.fromisoformat(info["terakhir_muncul"])
        interval = info["interval_jam"]
        berikutnya_utc = terakhir_utc + timedelta(hours=interval)

        while berikutnya_utc <= sekarang_utc:
            berikutnya_utc += timedelta(hours=interval)

        selisih_menit = (berikutnya_utc - sekarang_utc).total_seconds() / 60
        waktu_str = berikutnya_utc.strftime("%Y%m%d%H%M")

        kunci_10 = f"respawn_{nama}_{waktu_str}_10"
        kunci_5 = f"respawn_{nama}_{waktu_str}_5"
        kunci_spawn = f"respawn_{nama}_{waktu_str}_spawn"

        if 9.0 <= selisih_menit <= 10.0 and kunci_10 not in pesan_terkirim:
            pesan_terkirim[kunci_10] = sekarang_utc
            await channel.send(f"@everyone ⏰ **PENGINGAT!** {nama} akan muncul dalam 10 menit!")

        elif 4.0 <= selisih_menit <= 5.0 and kunci_5 not in pesan_terkirim:
            pesan_terkirim[kunci_5] = sekarang_utc
            await channel.send(f"@everyone ⏰ **PENGINGAT!** {nama} akan muncul dalam 5 menit!")

        elif abs(selisih_menit) <= 1.0 and kunci_spawn not in pesan_terkirim:
            pesan_terkirim[kunci_spawn] = sekarang_utc
            wib = berikutnya_utc + timedelta(hours=ZONA_WIB)
            pht = berikutnya_utc + timedelta(hours=ZONA_PHT)
            await channel.send(
                f"@everyone 🔄 **BOSS RESPAWN!** 🔄\n\n**{nama}**\n🇮🇩 {wib:%H:%M} WIB\n🇵🇭 {pht:%H:%M} PHT\n⏱️ Waktunya bertarung!",
                view=TandaiMatiView(nama)
            )

    # --- CEK BOSS TETAP ---
    hari_sekarang = hari_ke_kode(sekarang_wib)
    for nama, daftar_jadwal in data_db["boss_fixed"].items():
        for jadwal in daftar_jadwal:
            if jadwal["hari"] != hari_sekarang:
                continue

            j, m = map(int, jadwal["waktu"].split(":"))
            target_wib = sekarang_wib.replace(hour=j, minute=m, second=0, microsecond=0)
            target_utc = target_wib - timedelta(hours=ZONA_WIB)

            selisih_menit = (target_utc - sekarang_utc).total_seconds() / 60
            kunci_10 = f"fixed_{nama}_{j}_{m}_10"
            kunci_5 = f"fixed_{nama}_{j}_{m}_5"
            kunci_spawn = f"fixed_{nama}_{j}_{m}_spawn"

            if 9.0 <= selisih_menit <= 10.0 and kunci_10 not in pesan_terkirim:
                pesan_terkirim[kunci_10] = sekarang_utc
                await channel.send(f"@everyone ⏰ **PENGINGAT!** {nama} akan muncul dalam 10 menit!")

            elif 4.0 <= selisih_menit <= 5.0 and kunci_5 not in pesan_terkirim:
                pesan_terkirim[kunci_5] = sekarang_utc
                await channel.send(f"@everyone ⏰ **PENGINGAT!** {nama} akan muncul dalam 5 menit!")

            elif abs(selisih_menit) <= 1.0 and kunci_spawn not in pesan_terkirim:
                pesan_terkirim[kunci_spawn] = sekarang_utc
                await channel.send(
                    f"@everyone 📅 **BOSS TETAP MUNCUL!** 📅\n\n**{nama}**\n🇮🇩 {j:02d}:{m:02d} WIB\n🇵🇭 {(j+1)%24:02d}:{m:02d} PHT\n✅ Siap dikalahkan!"
                )

# Jalankan bot
if __name__ == "__main__":
    if not TOKEN:
        print("❌ Token bot tidak ditemukan!")
    else:
        bot.run(TOKEN)
