<div align="center">

# 📱 Android GSI Mirror

**Fresh Generic System Images — compact, ready for DSU, on a fast mirror.**
**Свежие GSI-прошивки — компактные, готовые для DSU, на быстром зеркале.**

[🇬🇧 English](#-english) &nbsp;•&nbsp; [🇷🇺 Русский](#-русский)

![Auto-updated](https://img.shields.io/badge/updated-daily-brightgreen) ![Format](https://img.shields.io/badge/format-.img.xz-blue) ![Arch](https://img.shields.io/badge/arch-arm64-orange)

</div>

---

## 🇬🇧 English

### ⬇️ Downloads

<!-- GSI-LIST-EN:START -->
| ROM | Android | Build | Size | Date | Download |
|---|:---:|---|---:|---|:---:|
| **LineageOS GSI (AndyYan)** | 14 | `lineage-21.0-20260614-UNOFFICIAL-arm64_bvN.img` | 2.4 GB | 2026-06-19 | [⬇️ Download](https://drive.google.com/open?id=1KyeNeoioDQlNoRbQ3Mg0h13SS8UTRFE4) |
<!-- GSI-LIST-EN:END -->

The list updates automatically every day. Files are compressed `.img.xz` / `.img.gz` — DSU Sideloader opens them directly, nothing to unpack.

### 🧪 Try without risk — DSU Sideloader

Boot a GSI **alongside** your current system. Reboot — and you're back, all data intact.

1. Unlock the bootloader *(this wipes the phone once)*.
2. Install [DSU Sideloader](https://github.com/VegaBobo/DSU-Sideloader).
3. Pick the downloaded file (`.img.xz` works as is), set userdata to 16 GB, start the install.
4. Reboot into the GSI from the *Dynamic System* notification.

### ⚡ Permanent install — fastboot

```sh
xz -d system.img.xz   # fastboot needs a raw .img / нужен распакованный .img
adb reboot fastboot
fastboot erase system
fastboot flash system system.img
fastboot -w
fastboot reboot
```

> ⚠️ Keep a copy of your stock firmware. Camera, VoLTE or fingerprint may not work on every device. Flash at your own risk.

---

## 🇷🇺 Русский

### ⬇️ Скачать

<!-- GSI-LIST-RU:START -->
| Прошивка | Android | Сборка | Размер | Дата | Скачать |
|---|:---:|---|---:|---|:---:|
| **LineageOS GSI (AndyYan)** | 14 | `lineage-21.0-20260614-UNOFFICIAL-arm64_bvN.img` | 2.4 GB | 2026-06-19 | [⬇️ Скачать](https://drive.google.com/open?id=1KyeNeoioDQlNoRbQ3Mg0h13SS8UTRFE4) |
<!-- GSI-LIST-RU:END -->

Список обновляется автоматически каждый день. Файлы в формате `.img.xz` / `.img.gz` — DSU Sideloader открывает их сам, ничего распаковывать не нужно.

### 🧪 Попробовать без риска — DSU Sideloader

GSI запускается **рядом** с вашей системой. Перезагрузились — и вы снова в своей прошивке, данные на месте.

1. Разблокируйте загрузчик *(один раз сотрёт телефон)*.
2. Установите [DSU Sideloader](https://github.com/VegaBobo/DSU-Sideloader).
3. Выберите скачанный файл (`.img.xz` — как есть), размер userdata — 16 ГБ, запустите установку.
4. Перезагрузитесь в GSI через уведомление *Dynamic System*.

### ⚡ Установить насовсем — fastboot

```sh
xz -d system.img.xz   # fastboot needs a raw .img / нужен распакованный .img
adb reboot fastboot
fastboot erase system
fastboot flash system system.img
fastboot -w
fastboot reboot
```

> ⚠️ Сохраните стоковую прошивку. Камера, VoLTE или отпечаток могут работать не на всех устройствах. Всё на свой риск.

---

<div align="center">

<sub>Maintainer docs / Для владельца: <a href="docs/SETUP.md">docs/SETUP.md</a></sub>

</div>
