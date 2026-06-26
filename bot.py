import discord
from discord.ext import tasks, commands
from discord.ui import View, Button
from datetime import datetime, timedelta, timezone
import os
import json

# ---------------- KONFIGURASI ----------------
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DB_FILE = "database.json"
PREFIX = "!"
ZONA_WIB = 7
ZONA_PHT = 8
WIB_TZ = timezone(timedelta(hours=ZONA_WIB))
PHT_TZ = timezone(timedelta(hours=ZONA_PHT))
UTC_TZ = timezone.utc

# ---------------- FUNGSI DATABASE ----------------
def baca_database():
    if not os.path.exists(DB_FILE):
        data_awal = {
            "pengaturan": {
                "zona_waktu": ZONA_WIB,
                "channel_id": 1516422050032521316
            },
            "boss_respawn": {
                "Venatus": {"interval_jam": 10, "terakhir_muncul": "2026-06-26T10:39:00+00:00"},
                "Viorent": {"interval_jam": 10, "terakhir_muncul": "2026-06-26T10:45:00+00:00"},
                "LadyDalia": {"interval_jam": 18, "terakhir_muncul": "2026-06-26T03:31:00+00:00"},
                "Ego": {"interval_jam": 21, "terakhir_muncul": "2026-06-26T03:07:00+00:00"},
                "Shuliar": {"interval_jam": 35, "terakhir_muncul": "2026-06-24T05:24:00+00:00"},
                "Larba": {"interval_jam": 35, "terakhir_muncul": "2026-06-26T03:51:00+00:00"},
                "Catena": {"interval_jam": 35, "terakhir_muncul": None},
                "Livera": {"interval_jam": 24, "terakhir_muncul": "2026-06-26T06:46:00+00:00"},
                "Undomiel": {"interval_jam": 24, "terakhir_muncul": "2026-06-26T07:49:00+00:00"},
                "Araneo": {"interval_jam": 24, "terakhir_muncul": "2026-06-26T07:12:00+00:00"},
                "Wannitas": {"interval_jam": 48, "terakhir_muncul": "2026-06-26T13:00:00+00:00"},
                "Metus": {"interval_jam": 48, "terakhir_muncul": "2026-06-23T15:19:00+00:00"},
                "Duplican": {"interval_jam": 48, "terakhir_muncul": "2026-06-23T14:09:00+00:00"},
                "BaronBraudmore": {"interval_jam": 32, "terakhir_muncul": "2026-06-25T17:01:00+00:00"},
                "Gareth": {"interval_jam": 32, "terakhir_muncul": "2026-06-24T01:26:00+00:00"},
                "Amentis": {"interval_jam": 29, "terakhir_muncul": "2026-06-26T09:59:00+00:00"},
                "Titore": {"interval_jam": 37, "terakhir_muncul": "2026-06-26T14:28:00+00:00"},
                "GeneralAquleus": {"interval_jam": 29, "terakhir_muncul": "2026-06-25T12:32:00+00:00"},
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
    sekarang_wib = datetime.now(WIB_TZ)
    target_wib = sekarang_wib.replace(hour=jam, minute=menit, second=0, microsecond=0)
    return target_wib.astimezone(UTC_TZ)

def format_sisa_waktu(delta: timedelta):
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
    async def sudah_mati(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.sudah_diklik:
            return await interaction.response.send_message("⚠️ Sudah dicatat sebelumnya!", ephemeral=True)
        
        self.sudah_diklik = True
        button.disabled = True
        button.label = "✅ Dicatat"
        button.style = discord.ButtonStyle.secondary

        sekarang_utc = datetime.now(UTC_TZ)
        data_db["boss_respawn"][self.nama_boss]["terakhir_muncul"] = sekarang_utc.isoformat()
        simpan_database(data_db)

        interval = data_db["boss_respawn"][self.nama_boss]["interval_jam"]
        berikutnya_utc = sekarang_utc + timedelta(hours=interval)
        berikutnya_wib = berikutnya_utc.astimezone(WIB_TZ)
        berikutnya_pht = berikutnya_utc.astimezone(PHT_TZ)

        await interaction.response.edit_message(view=self)
        await interaction.followup.send(
            f"✅ **{self.nama_boss}** dicatat mati\n"
            f"➡️ Muncul berikutnya: 🇮🇩 {berikutnya_wib:%H:%M} WIB | 🇵🇭 {berikutnya_pht:%H:%M} PHT"
        )

# ---------------- INISIALISASI ----------------
data_db = baca_database()
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents)
pesan_terkirim = {}

# ---------------- PERINTAH ----------------
@bot.event
async def on_ready():
    print(f"✅ Bot aktif: {bot.user}")
    print(f"📊 Boss Respawn: {len(data_db['boss_respawn'])} | Boss Tetap: {len(data_db['boss_fixed'])}")
    cek_spawn.start()

@bot.command(name="respawnlist", aliases=["rs"])
async def tampilkan_jadwal(ctx):
    sekarang_utc = datetime.now(UTC_TZ)
    daftar = []

    for nama, info in data_db["boss_respawn"].items():
        if not info["terakhir_muncul"]:
            continue

        terakhir_utc = datetime.fromisoformat(info["terakhir_muncul"])
        interval = info["interval_jam"]
        berikutnya_utc = terakhir_utc + timedelta(hours=interval)

        # Maju sampai lewat waktu sekarang
        while berikutnya_utc <= sekarang_utc:
            berikutnya_utc += timedelta(hours=interval)

        berikutnya_wib = berikutnya_utc.astimezone(WIB_TZ)
        berikutnya_pht = berikutnya_utc.astimezone(PHT_TZ)
        sisa = format_sisa_waktu(berikutnya_utc - sekarang_utc)

        daftar.append({
            "waktu": berikutnya_utc,
            "nama": nama,
            "wib": berikutnya_wib.strftime("%H:%M"),
            "pht": berikutnya_pht.strftime("%H:%M"),
            "sisa": sisa
        })

    daftar.sort(key=lambda x: x["waktu"])

    teks = "🔄 **JADWAL BOSS RESPAWN**\n────────────────────────────\n"
    if not daftar:
        teks += "Belum ada data yang dicatat."
    else:
        for b in daftar:
            teks += f"**{b['nama']}**\n🇮🇩 {b['wib']} WIB | 🇵🇭 {b['pht']} PHT\n⏳ {b['sisa']}\n\n"

    await ctx.send(teks)

@bot.command(name="setrespawn", aliases=["sr"])
async def catat_waktu_mati(ctx, *, teks: str):
    bagian = teks.strip().split()
    if len(bagian) < 3:
        return await ctx.send("❌ Format: `!sr NamaBoss JJ MM` | Contoh: `!sr GeneralAquleus 19 32`")

    try:
        jam = int(bagian[-2])
        menit = int(bagian[-1])
    except:
        return await ctx.send("❌ Jam dan menit harus angka! Contoh: `!sr Larba 10 51`")

    nama_input = "".join(bagian[:-2]).lower()
    peta_nama = {n.lower().replace(" ", ""): n for n in data_db["boss_respawn"].keys()}

    if nama_input not in peta_nama:
        return await ctx.send(f"❌ Boss tidak ditemukan. Pilihan: {', '.join(data_db['boss_respawn'].keys())}")

    nama_boss = peta_nama[nama_input]
    waktu_utc = ubah_waktu_wib_ke_utc(jam, menit)
    data_db["boss_respawn"][nama_boss]["terakhir_muncul"] = waktu_utc.isoformat()
    simpan_database(data_db)

    interval = data_db["boss_respawn"][nama_boss]["interval_jam"]
    berikutnya_utc = waktu_utc + timedelta(hours=interval)
    berikutnya_wib = berikutnya_utc.astimezone(WIB_TZ)
    berikutnya_pht = berikutnya_utc.astimezone(PHT_TZ)

    await ctx.send(
        f"✅ **{nama_boss}** dicatat mati jam {jam:02d}:{menit:02d} WIB\n"
        f"➡️ Muncul berikutnya: 🇮🇩 {berikutnya_wib:%H:%M} WIB | 🇵🇭 {berikutnya_pht:%H:%M} PHT"
    )

@bot.command(name="fixlist", aliases=["fx"])
async def jadwal_tetap(ctx):
    sekarang_wib = datetime.now(WIB_TZ)
    hari_ini = hari_ke_kode(sekarang_wib)
    teks = f"📅 **JADWAL BOSS TETAP - {nama_hari(hari_ini).upper()}**\n────────────────────────────\n"
    ada = False

    for nama, jadwal in data_db["boss_fixed"].items():
        for item in jadwal:
            if item["hari"] == hari_ini:
                j, m = map(int, item["waktu"].split(":"))
                teks += f"**{nama}**\n🇮🇩 {j:02d}:{m:02d} WIB | 🇵🇭 {(j+1)%24:02d}:{m:02d} PHT\n\n"
                ada = True

    if not ada:
        teks += "Tidak ada jadwal hari ini."
    await ctx.send(teks)

@bot.command(name="bantuan", aliases=["b", "menu"])
async def bantuan(ctx):
    await ctx.send(
        "🤖 **PERINTAH BOT**\n"
        "`!rs` → Lihat semua jadwal respawn\n"
        "`!sr Nama JJ MM` → Catat waktu mati\n"
        "`!fx` → Jadwal boss tetap hari ini\n"
        "`!bantuan` → Bantuan"
    )

@tasks.loop(seconds=15)
async def cek_spawn():
    sekarang_utc = datetime.now(UTC_TZ)
    channel = bot.get_channel(data_db["pengaturan"]["channel_id"])
    if not channel:
        return

    # Bersihkan riwayat pesan lama
    for k in list(pesan_terkirim.keys()):
        if (sekarang_utc - pesan_terkirim[k]).total_seconds() > 10800:
            del pesan_terkirim[k]

    # Cek boss respawn
    for nama, info in data_db["boss_respawn"].items():
        if not info["terakhir_muncul"]:
            continue

        terakhir_utc = datetime.fromisoformat(info["terakhir_muncul"])
        interval = info["interval_jam"]
        berikutnya_utc = terakhir_utc + timedelta(hours=interval)

        # ✅ Semua waktu sudah punya zona UTC, tidak ada error lagi
        while berikutnya_utc <= sekarang_utc:
            berikutnya_utc += timedelta(hours=interval)

        selisih_menit = (berikutnya_utc - sekarang_utc).total_seconds() / 60
        kunci = f"{nama}_{berikutnya_utc.strftime('%Y%m%d%H%M')}"

        if 8 <= selisih_menit <= 11 and f"{kunci}_10" not in pesan_terkirim:
            pesan_terkirim[f"{kunci}_10"] = sekarang_utc
            await channel.send(f"⏰ **PENGINGAT!** {nama} muncul dalam 10 menit!")
        elif 3 <= selisih_menit <= 6 and f"{kunci}_5" not in pesan_terkirim:
            pesan_terkirim[f"{kunci}_5"] = sekarang_utc
            await channel.send(f"⏰ **PENGINGAT!** {nama} muncul dalam 5 menit!")
        elif -1 <= selisih_menit <= 2 and f"{kunci}_spawn" not in pesan_terkirim:
            pesan_terkirim[f"{kunci}_spawn"] = sekarang_utc
            wib = berikutnya_utc.astimezone(WIB_TZ)
            pht = berikutnya_utc.astimezone(PHT_TZ)
            await channel.send(
                f"🔄 **RESPAWN!** {nama} sudah muncul!\n"
                f"🇮🇩 {wib:%H:%M} WIB | 🇵🇭 {pht:%H:%M} PHT",
                view=TandaiMatiView(nama)
            )

if __name__ == "__main__":
    if not TOKEN:
        print("❌ Token tidak ditemukan!")
    else:
        bot.run(TOKEN)
