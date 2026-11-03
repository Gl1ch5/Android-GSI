"""Определяет версию прошивки (HyperOS 3.0.9, One UI 8, OxygenOS 16 …) по имени файла.
Та же логика продублирована в site/index.html (функция osVersion)."""
import re

# версия оболочки по версии Android (для прошивок, где номер не указан в имени файла)
BY_ANDROID = {
    "oneui":    ("One UI",    {"14": "6", "15": "7", "16": "8", "17": "9"}),
    "oxygenos": ("OxygenOS",  {"14": "14", "15": "15", "16": "16", "17": "17"}),
    "coloros":  ("ColorOS",   {"14": "14", "15": "15", "16": "16", "17": "17"}),
    "realmeui": ("realme UI", {"14": "5", "15": "6", "16": "7", "17": "8"}),
    "originos": ("OriginOS",  {"14": "4", "15": "5", "16": "6", "17": "7"}),
    "magicos":  ("MagicOS",   {"14": "8", "15": "9", "16": "10", "17": "11"}),
    "nothing":  ("Nothing OS", {"14": "2.5", "15": "3", "16": "4", "17": "5"}),
}


def os_version(src_file, android="?"):
    f = src_file or ""
    p = f.split("-")
    brand = p[0].lower()
    if f.endswith(("MysticGSI.zip", "MysticGSI.img", "MysticGSI.img.xz")) and len(p) > 3:
        build = p[3]
        if brand == "hyperos":
            m = re.match(r"OS(\d+)\.(\d+)\.(\d+)", build)
            return f"HyperOS {m.group(1)}.{m.group(2)}.{m.group(3)}" if m else "HyperOS"
        if brand == "pixel":
            tag = {"CANARY": " Canary", "CinnamonBun": " Beta", "Baklava": " Beta"}.get(p[2], "")
            return f"Pixel · Android {android}{tag}"
        if brand in BY_ANDROID:
            name, table = BY_ANDROID[brand]
            v = table.get(str(android))
            return f"{name} {v}" if v else name
        if brand == "flyme":
            return "Flyme"
        return p[0]
    m = re.search(r"lineage-?(\d+\.\d+)", f, re.I)
    if m:
        return f"LineageOS {m.group(1)}"
    m = re.search(r"aosp-arm64-ab-\w+-(\d+\.\d+)", f)
    if m:
        return f"AOSP {m.group(1)}"
    m = re.search(r"(?i)(?:^|[-_])v?(\d{1,2}\.\d{1,2}(?:\.\d{1,2})?)(?=[-_.])", f)
    if m:
        return m.group(1)
    return ""
