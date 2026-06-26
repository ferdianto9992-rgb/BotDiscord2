# Ganti bagian ini saja
pesan_terkirim = {
    "respawn": {},
    "fixed": {}
}

@tasks.loop(seconds=15)
async def cek_spawn():
    sekarang_utc = datetime.now(timezone.utc)
    sekarang_wib = sekarang_utc + timedelta(hours=ZONA_WIB)
    channel = bot.get_channel(data_db["pengaturan"]["channel_id"])
    if not channel:
        return

    # Bersihkan catatan pesan yang sudah lewat 2 jam agar tidak menumpuk
    for tipe in list(pesan_terkirim.keys()):
        kunci_hapus = []
        for kunci, waktu_kirim in pesan_terkirim[tipe].items():
            if (sekarang_utc - waktu_kirim).total_seconds() > 7200:
                kunci_hapus.append(kunci)
        for k in kunci_hapus:
            del pesan_terkirim[tipe][k]

    # ---------------- CEK BOSS RESPAWN ----------------
    for nama, info in data_db["boss_respawn"].items():
        if not info["terakhir_muncul"]:
            continue

        terakhir_utc = datetime.fromisoformat(info["terakhir_muncul"].replace("Z", "+00:00"))
        interval = info["interval_jam"]
        berikutnya_utc = terakhir_utc + timedelta(hours=interval)

        while berikutnya_utc <= sekarang_utc:
            berikutnya_utc += timedelta(hours=interval)

        selisih_menit = (berikutnya_utc - sekarang_utc).total_seconds() / 60
        kunci = f"{nama}_{berikutnya_utc.strftime('%Y%m%d%H%M')}"

        if 9.0 < selisih_menit < 10.5 and kunci not in pesan_terkirim["respawn"]:
            pesan_terkirim["respawn"][kunci] = sekarang_utc
            await channel.send(f"@everyone ⏰ **PENGINGAT!** {nama} akan muncul dalam 10 menit!")

        elif 4.0 < selisih_menit < 5.5 and kunci not in pesan_terkirim["respawn"]:
            pesan_terkirim["respawn"][kunci] = sekarang_utc
            await channel.send(f"@everyone ⏰ **PENGINGAT!** {nama} akan muncul dalam 5 menit!")

        elif abs(selisih_menit) < 2.0 and kunci not in pesan_terkirim["respawn"]:
            pesan_terkirim["respawn"][kunci] = sekarang_utc
            wib = berikutnya_utc + timedelta(hours=ZONA_WIB)
            pht = berikutnya_utc + timedelta(hours=ZONA_PHT)
            await channel.send(
                f"@everyone 🔄 **BOSS RESPAWN!** 🔄\n\n**{nama}**\n🇮🇩 {wib:%H:%M} WIB\n🇵🇭 {pht:%H:%M} PHT\n⏱️ Waktunya bertarung!",
                view=TandaiMatiView(nama)
            )

    # ---------------- CEK BOSS TETAP ----------------
    hari_sekarang = hari_ke_kode(sekarang_wib)
    for nama, daftar_jadwal in data_db["boss_fixed"].items():
        for jadwal in daftar_jadwal:
            if jadwal["hari"] != hari_sekarang:
                continue

            j, m = map(int, jadwal["waktu"].split(":"))
            target_wib = sekarang_wib.replace(hour=j, minute=m, second=0, microsecond=0)
            target_utc = target_wib - timedelta(hours=ZONA_WIB)

            selisih_menit = (target_utc - sekarang_utc).total_seconds() / 60
            kunci = f"fixed_{nama}_{j}_{m}"

            if 9.0 < selisih_menit < 10.5 and kunci not in pesan_terkirim["fixed"]:
                pesan_terkirim["fixed"][kunci] = sekarang_utc
                await channel.send(f"@everyone ⏰ **PENGINGAT!** {nama} akan muncul dalam 10 menit!")

            elif 4.0 < selisih_menit < 5.5 and kunci not in pesan_terkirim["fixed"]:
                pesan_terkirim["fixed"][kunci] = sekarang_utc
                await channel.send(f"@everyone ⏰ **PENGINGAT!** {nama} akan muncul dalam 5 menit!")

            elif abs(selisih_menit) < 2.0 and kunci not in pesan_terkirim["fixed"]:
                pesan_terkirim["fixed"][kunci] = sekarang_utc
                await channel.send(
                    f"@everyone 📅 **BOSS TETAP MUNCUL!** 📅\n\n**{nama}**\n🇮🇩 {j:02d}:{m:02d} WIB\n🇵🇭 {(j+1)%24:02d}:{m:02d} PHT\n✅ Siap dikalahkan!"
                )
