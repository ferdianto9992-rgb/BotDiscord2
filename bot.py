@tasks.loop(seconds=15)
async def cek_spawn():
    sekarang_utc = datetime.now(UTC_TZ)
    channel = bot.get_channel(data_db["pengaturan"]["channel_id"])
    if not channel:
        return

    # Bersihkan catatan pesan lama lebih dari 3 jam
    for k in list(pesan_terkirim.keys()):
        if (sekarang_utc - pesan_terkirim[k]).total_seconds() > 10800:
            del pesan_terkirim[k]

    for nama, info in data_db["boss_respawn"].items():
        if not info["terakhir_muncul"]:
            continue

        terakhir_utc = datetime.fromisoformat(info["terakhir_muncul"])
        berikutnya_utc = terakhir_utc + timedelta(hours=info["interval_jam"])

        # Lewati waktu yang sudah lewat, lompat ke siklus berikutnya
        while berikutnya_utc <= sekarang_utc:
            berikutnya_utc += timedelta(hours=info["interval_jam"])

        selisih_menit = (berikutnya_utc - sekarang_utc).total_seconds() / 60
        kunci = f"{nama}_{berikutnya_utc.strftime('%Y%m%d%H%M')}"
        wib = berikutnya_utc.astimezone(WIB_TZ)
        pht = berikutnya_utc.astimezone(PHT_TZ)

        # 🔔 Peringatan 10 menit sebelum - Hanya terpicu tepat di rentang ini
        if 9.8 <= selisih_menit <= 10.2 and f"{kunci}_10" not in pesan_terkirim:
            pesan_terkirim[f"{kunci}_10"] = sekarang_utc
            await channel.send(f"⏰ @everyone\n{nama} akan muncul dalam 10 menit!\n🇮🇩 {wib:%H:%M} WIB | 🇵🇭 {pht:%H:%M} PHT")

        # 🔔 Peringatan 5 menit sebelum
        elif 4.8 <= selisih_menit <= 5.2 and f"{kunci}_5" not in pesan_terkirim:
            pesan_terkirim[f"{kunci}_5"] = sekarang_utc
            await channel.send(f"⚠️ @everyone\n{nama} akan muncul dalam 5 menit!\n🇮🇩 {wib:%H:%M} WIB | 🇵🇭 {pht:%H:%M} PHT")

        # 🔔 Saat spawn
        elif -0.2 <= selisih_menit <= 0.2 and f"{kunci}_spawn" not in pesan_terkirim:
            pesan_terkirim[f"{kunci}_spawn"] = sekarang_utc
            await channel.send(f"🔄 @everyone\n{nama} sudah muncul!\n🇮🇩 {wib:%H:%M} WIB | 🇵🇭 {pht:%H:%M} PHT", view=TandaiMatiView(nama))
