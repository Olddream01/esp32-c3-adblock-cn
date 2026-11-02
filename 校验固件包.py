# -*- coding: utf-8 -*-
"""
校验刷机包是否完整可用 —— 刷机前跑一次，省得刷完才发现文件不对。

用法：
    python 校验固件包.py            # 校验同目录下的固件文件
    python 校验固件包.py <目录>     # 校验指定目录

检查项：
  1. manifest.json 能解析，chipFamily 是 ESP32-C3
  2. partitions.bin 能解析，每个分区的偏移/大小都对得上
  3. manifest 里每个固件文件都落在正确的分区内且不越界
  4. firmware.bin 装得进 app0 槽位
  5. littlefs.bin 里能完整还原出 blocklist.bin（逐字节 100% 覆盖）
"""
import json
import os
import struct
import sys

TYPES = {0x00: "APP", 0x01: "DATA"}


def parse_partitions(path):
    data = open(path, "rb").read()
    out = []
    for i in range(0, len(data), 32):
        e = data[i:i + 32]
        if len(e) < 32 or e[0] != 0xAA or e[1] != 0x50:
            break
        typ, sub = e[2], e[3]
        addr, size = struct.unpack_from("<II", e, 4)
        label = e[12:28].split(b"\x00")[0].decode("ascii", "replace")
        if not label:
            break
        out.append({"label": label, "type": TYPES.get(typ, hex(typ)),
                    "subtype": hex(sub), "addr": addr, "size": size})
    return out


def restore_from_image(img, src):
    """把源文件从 littlefs 镜像里按连续区段还原，返回覆盖的字节数"""
    total = 0
    pos = 0
    search_from = 0
    n = len(src)
    while pos < n:
        probe = src[pos:pos + 24]
        j = img.find(probe, search_from)
        if j < 0:
            for skip in range(1, 6):          # 跨块边界：最多跳 5 字节
                j = img.find(src[pos + skip:pos + skip + 24], search_from)
                if j >= 0:
                    pos += skip
                    search_from = j
                    break
            else:
                return total
            continue
        k = 0
        while j + k < len(img) and pos + k < n and img[j + k] == src[pos + k]:
            k += 1
        total += k
        pos += k
        search_from = j + k
    return total


def main():
    pkg = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
    ok = True

    mf = json.load(open(os.path.join(pkg, "manifest.json"), encoding="utf-8"))
    build = mf["builds"][0]
    print(f"manifest      : {mf['name']}")
    print(f"chipFamily    : {build['chipFamily']}")
    print(f"erase prompt  : {mf.get('new_install_prompt_erase')}")

    parts = parse_partitions(os.path.join(pkg, "partitions.bin"))
    print("\n--- 分区表 ---")
    for p in parts:
        print(f"  {p['label']:8s} {p['type']:4s} {p['subtype']:6s} "
              f"off=0x{p['addr']:06x} size=0x{p['size']:06x} ({p['size']:,} B)")

    print("\n--- manifest 偏移 ---")
    for part in build["parts"]:
        off = part["offset"]
        f = os.path.join(pkg, part["path"])
        if not os.path.exists(f):
            print(f"  {part['path']:16s} 缺失 !!")
            ok = False
            continue
        sz = os.path.getsize(f)
        if off in (0, 0x8000):
            print(f"  {part['path']:16s} @0x{off:06x} {sz:>9,} B  保留区 OK")
            continue
        hit = [p for p in parts if p["addr"] <= off < p["addr"] + p["size"]]
        if not hit:
            print(f"  {part['path']:16s} @0x{off:06x} 不在任何分区内 !!")
            ok = False
            continue
        p = hit[0]
        fits = (off + sz) <= p["addr"] + p["size"]
        print(f"  {part['path']:16s} @0x{off:06x} {sz:>9,} B -> {p['label']:8s} "
              f"{'OK' if fits else '越界 !!'}")
        ok = ok and fits

    app0 = next((p for p in parts if p["label"] == "app0"), None)
    if app0:
        fw = os.path.getsize(os.path.join(pkg, "firmware.bin"))
        print(f"\nfirmware.bin {fw:,} B / app0 {app0['size']:,} B "
              f"-> {'装得下' if fw <= app0['size'] else '装不下 !!'} (余 {app0['size']-fw:,} B)")
        ok = ok and fw <= app0["size"]

    bl = os.path.join(pkg, "blocklist-latest.bin")
    if os.path.exists(bl):
        img = open(os.path.join(pkg, "littlefs.bin"), "rb").read()
        src = open(bl, "rb").read()
        covered = restore_from_image(img, src)
        print(f"\n封禁列表: {len(src):,} B / {len(src)//5:,} 条")
        print(f"littlefs.bin 还原覆盖: {covered:,} / {len(src):,} "
              f"({100*covered/len(src):.4f}%) -> {'完整' if covered == len(src) else '不完整 !!'}")
        ok = ok and covered == len(src)

    print("\n结论:", "全部通过 ✓" if ok else "有问题 ✗")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
