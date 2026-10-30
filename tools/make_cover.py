#!/usr/bin/env python3
"""生成 A4 封面：底图裁成 A4 比例，中文用 PIL 精确叠字。"""
from PIL import Image, ImageDraw, ImageFont

SRC = "不完全减肥指南-封面底图.png"
OUT = "封面.png"

W, H = 1654, 2339                      # A4 @ 200dpi
INK = (43, 42, 36)                     # 墨色
INK_SOFT = (74, 71, 62)
CINNABAR = (166, 58, 43)               # 朱砂
KAI = "/Users/macbook/.local/share/fonts/kami/TsangerJinKai02-W04.ttf"
SONG = "/System/Library/Fonts/Supplemental/Songti.ttc"

# 底图裁成 A4 比例（居中裁宽）
im = Image.open(SRC).convert("RGB")
sw, sh = im.size
target = W / H
if sw / sh > target:
    nw = int(round(sh * target))
    im = im.crop(((sw - nw) // 2, 0, (sw - nw) // 2 + nw, sh))
else:
    nh = int(round(sw / target))
    im = im.crop((0, (sh - nh) // 2, sw, (sh - nh) // 2 + nh))
im = im.resize((W, H), Image.LANCZOS)

d = ImageDraw.Draw(im)


def center(text, font, y, fill, tracking=0):
    if tracking:
        widths = [font.getlength(c) for c in text]
        total = sum(widths) + tracking * (len(text) - 1)
        x = (W - total) / 2
        for c, w in zip(text, widths):
            d.text((x, y), c, font=font, fill=fill)
            x += w + tracking
        return total
    w = font.getlength(text)
    d.text(((W - w) / 2, y), text, font=font, fill=fill)
    return w


# 顶部小引
f_kicker = ImageFont.truetype(KAI, 46)
center("给普通人的一套减重方法", f_kicker, int(H * 0.125), INK_SOFT, tracking=10)

# 书名
f_title = ImageFont.truetype(KAI, 176)
tw = center("不完全减肥指南", f_title, int(H * 0.175), INK, tracking=10)
assert tw <= W - 220, tw

# 朱砂细线
ly = int(H * 0.175) + 250
d.line([(W / 2 - 70, ly), (W / 2 + 70, ly)], fill=CINNABAR, width=4)

# 副题
f_sub = ImageFont.truetype(KAI, 52)
center("78 天，从 100.80 公斤到 74.65 公斤", f_sub, ly + 42, INK_SOFT, tracking=3)

# 底部纸色署名带（设计元素，不是遮罩）
BAND_TOP = int(H * 0.922)
d.rectangle([0, BAND_TOP, W, H], fill=(247, 243, 234))
d.line([(0, BAND_TOP), (W, BAND_TOP)], fill=CINNABAR, width=3)

# 底部署名
f_name = ImageFont.truetype(KAI, 58)
center("Simonlin", f_name, BAND_TOP + 38, INK, tracking=6)
f_mp = ImageFont.truetype(SONG, 34)
center("公众号   Simonlin的精神世界", f_mp, BAND_TOP + 116, INK_SOFT, tracking=2)

im.save(OUT, "PNG")
print("saved", OUT, im.size)
