#!/usr/bin/env python3
"""把 VitePress 的 markdown 源拼成一本 A4 的 PDF：封面 → 版权页 → 目录 → 正文 → 附录。"""
import re
import subprocess
import pathlib

ROOT = pathlib.Path("/Users/macbook/cola/outputs/不完全减肥指南-开源书")
DOCS = ROOT / "repo" / "docs"
PUB = DOCS / "public"
OUT_PDF = ROOT / "PDF版" / "不完全减肥指南.pdf"
COVER = ROOT / "PDF版" / "封面.png"

ORDER = [
    ("index.md", "关于这本书"),
    ("ch00-my-account.md", None),
    ("ch01-myths.md", None),
    ("ch02-one-rule.md", None),
    ("ch03-eating.md", None),
    ("ch04-training.md", None),
    ("ch05-first-30-days.md", None),
    ("ch06-plateau.md", None),
    ("ch07-after.md", None),
    ("ch08-safety.md", None),
    ("ch09-fact-check.md", None),
    ("epilogue.md", None),
    ("appendix/a-food-table.md", None),
    ("appendix/b-faq.md", None),
    ("appendix/c-glossary.md", None),
    ("appendix/d-who-to-follow.md", None),
    ("appendix/e-sources.md", None),
]


def md2html(path: pathlib.Path) -> str:
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"^---\n.*?\n---\n", "", text, flags=re.S)      # 去掉 VitePress frontmatter
    out = subprocess.run(
        ["pandoc", "-f", "markdown", "-t", "html5", "--wrap=none"],
        input=text, capture_output=True, text=True, check=True,
    ).stdout
    return out


def fix_links(html: str) -> str:
    # 站内链接在 PDF 里点不过去，只留文字
    html = re.sub(r'<a href="/(?!images/)[^"]*"[^>]*>(.*?)</a>', r"\1", html, flags=re.S)
    return html


IMG_RE = re.compile(r"<img\b([^>]*?)/?>")


IMG_CACHE = ROOT / "PDF版" / "_img"
IMG_CACHE.mkdir(exist_ok=True)
MAX_PX = 1600


def _shrink(path: pathlib.Path) -> pathlib.Path:
    """大于 1600px 或 PNG 的图转成 JPEG，PDF 体积能小一个量级。"""
    from PIL import Image
    out = IMG_CACHE / (path.stem + ".jpg")
    if out.exists() and out.stat().st_mtime >= path.stat().st_mtime:
        return out
    im = Image.open(path).convert("RGB")
    if im.width > MAX_PX:
        im = im.resize((MAX_PX, round(im.height * MAX_PX / im.width)), Image.LANCZOS)
    im.save(out, "JPEG", quality=88, progressive=True, optimize=True)
    return out


def _src_abs(src: str) -> str:
    if not src.startswith("/images/"):
        return src
    path = PUB / src.lstrip("/")
    if path.suffix.lower() in (".png", ".jpg", ".jpeg"):
        path = _shrink(path)
    return "file://" + str(path)


def _attrs(raw: str) -> dict:
    return dict(re.findall(r'(\w+)="([^"]*)"', raw))


def img_to_figure(html: str) -> str:
    """图片路径改成绝对 file://，并把独立成段的图包成 figure + 说明。"""

    def one(m):
        a = _attrs(m.group(1))
        src = _src_abs(a.get("src", ""))
        alt = a.get("alt", "")
        w = a.get("width", "")
        if w and w.isdigit() and int(w) <= 120:            # 小头像，保持行内原尺寸
            return f'<img src="{src}" width="{w}" height="{a.get("height", w)}" alt="{alt}" class="avatar">'
        return f'<img src="{src}" alt="{alt}">'

    html = IMG_RE.sub(one, html)

    # <p><img ...></p> → <figure><img><figcaption></figure>
    def wrap(m):
        img = m.group(1)
        if 'class="avatar"' in img:
            return m.group(0)
        alt = _attrs(img[4:].rsplit(">", 1)[0]).get("alt", "").strip()
        cap = f"<figcaption>{alt}</figcaption>" if alt else ""
        return f"<figure>{img}{cap}</figure>"

    html = re.sub(r"<p>\s*(<img\b[^>]*>)\s*</p>", wrap, html, flags=re.S)

    # 小头像被 pandoc 拆成了独立段落，合回后面的名字段，保持行内
    html = re.sub(
        r'<p>\s*(<img\b[^>]*class="avatar"[^>]*>)\s*</p>\s*<p>',
        lambda m: "<p>" + m.group(1) + " ",
        html,
    )

    # 附 D：每个博主一块，块与块之间留白隔开
    if 'class="avatar"' in html:
        parts = re.split(r'(?=<p><img\b[^>]*class="avatar")', html)
        if len(parts) > 2:
            html = parts[0] + "".join(f'<div class="creator">{x}</div>' for x in parts[1:])
    return html


def add_ids(html: str, counter: list) -> tuple[str, list]:
    """给 h1/h2 加锚点，同时收集目录条目。"""
    entries = []

    def repl(m):
        level, attrs, inner = m.group(1), m.group(2), m.group(3)
        counter[0] += 1
        hid = f"h{counter[0]}"
        plain = re.sub(r"<[^>]+>", "", inner).strip()
        if level in ("1", "2"):
            entries.append((int(level), hid, plain))
        return f'<h{level} id="{hid}"{attrs}>{inner}</h{level}>'

    html = re.sub(r"<h([12])([^>]*)>(.*?)</h\1>", repl, html, flags=re.S)
    return html, entries


CSS = """
@page {
  size: A4;
  margin: 24mm 21mm 20mm 21mm;
  @bottom-center {
    content: counter(page);
    font-family: "Songti SC"; font-size: 9pt; color: #7a7a72;
  }
  @top-right {
    content: string(runhead);
    font-family: "Songti SC"; font-size: 8.5pt; color: #9a9a90;
  }
}
@page cover { margin: 0; @bottom-center { content: none } @top-right { content: none } }
@page front { @bottom-center { content: none } @top-right { content: none } }
@page toc  { @top-right { content: none } }

html { font-family: "Songti SC", serif; font-size: 10.5pt; color: #23231f; }
body { margin: 0; line-height: 1.78; }

section.cover { page: cover; }
section.cover img { display: block; width: 210mm; height: 297mm; }

section.front { page: front; }
section.toc { page: toc; break-before: page; }

h1 {
  font-family: "Hiragino Sans GB", sans-serif;
  font-size: 19pt; line-height: 1.35; font-weight: 600;
  margin: 0 0 8mm 0; break-before: page; break-after: avoid;
  string-set: runhead content();
  padding-bottom: 4mm; border-bottom: 1.2pt solid #a63a2b;
}
h2 {
  font-family: "Hiragino Sans GB", sans-serif;
  font-size: 13pt; font-weight: 600; margin: 8mm 0 3mm; break-after: avoid;
}
h3 { font-family: "Hiragino Sans GB", sans-serif; font-size: 11pt; font-weight: 600; margin: 6mm 0 2mm; break-after: avoid; }
p { margin: 0 0 2.2mm; text-align: justify; text-indent: 2em; }
strong { font-weight: 700; }
em { font-style: normal; text-decoration: underline; text-underline-offset: 3px; }
ul, ol { margin: 0 0 3.5mm 0; padding-left: 6mm; }
li { margin-bottom: 1.6mm; }
blockquote {
  margin: 4mm 0; padding: 3mm 4mm; border-left: 2pt solid #c9b79b;
  background: #faf7f0; font-size: 10pt; color: #3a3a33;
}
blockquote p:last-child { margin-bottom: 0; }
blockquote p, .front-body p, td p, li p { text-indent: 0; }
hr { border: none; border-top: 0.6pt solid #d8d3c6; margin: 6mm 0; }

figure { margin: 6mm 0 7.5mm; break-inside: avoid; text-align: center; }
figure img { max-width: 100%; max-height: 105mm; }
figcaption { font-size: 8.8pt; color: #6c6c62; margin-top: 2.6mm; text-align: center; letter-spacing: 0.02em; }
p > img { max-width: 100%; }
.creator { margin-top: 7mm; padding-top: 3mm; }
.creator + .creator { border-top: 0.5pt solid #ded8c8; }
img.avatar { width: 11mm; height: 11mm; vertical-align: middle; border-radius: 50%; margin-right: 3mm; }

table {
  width: 100%; border-collapse: collapse; font-size: 9.2pt; margin: 4mm 0 5mm;
  break-inside: auto;
}
thead { display: table-header-group; }
th, td { border: 0.5pt solid #cfc9bb; padding: 1.6mm 2mm; text-align: left; vertical-align: top; line-height: 1.55; }
th { background: #f2eee4; font-weight: 600; }
tr { break-inside: avoid; }

code { font-family: "SF Mono", monospace; font-size: 9.2pt; background: #f2efe6; padding: 0 1px; }

/* 印前页 */
.front-inner { padding-top: 30mm; }
.front-title { font-family: "Hiragino Sans GB", sans-serif; font-size: 16pt; font-weight: 600; letter-spacing: 2px; }
.front-sub { color: #6c6c62; margin-top: 3mm; font-size: 10pt; }
.front-body { margin-top: 26mm; font-size: 9.8pt; line-height: 2; color: #33332d; }
.front-body dt { font-family: "Hiragino Sans GB", sans-serif; font-size: 9pt; color: #8a8a80; margin-top: 5mm; }
.front-body dd { margin: 1mm 0 0 0; }
.rule { border-top: 0.8pt solid #a63a2b; width: 40mm; margin: 8mm 0; }
.small { font-size: 8.8pt; color: #6c6c62; line-height: 1.9; }

/* 目录 */
.toc h1 { break-before: avoid; border-bottom: none; string-set: nothing ""; font-size: 17pt; }
.toc ol { list-style: none; padding-left: 0; margin-top: 6mm; }
.toc li { margin: 0; font-size: 10pt; }
.toc li.lv1 { margin-top: 4.2mm; font-family: "Hiragino Sans GB", sans-serif; font-weight: 600; }
.toc li.lv2 { font-size: 9.4pt; color: #3f3f38; }
.toc .ind { display: inline-block; width: 7mm; }
.toc a { color: inherit; text-decoration: none; display: block; }
.toc a::after { content: leader("·") " " target-counter(attr(href), page); color: #8a8a80; }
"""


def build() -> None:
    body_parts = []
    toc_items = []
    counter = [0]

    for fname, title_override in ORDER:
        html = fix_links(img_to_figure(md2html(DOCS / fname)))
        if title_override:                      # 首页那篇没有一级标题，补一个
            html = f"<h1>{title_override}</h1>" + html
        html, entries = add_ids(html, counter)
        toc_items.extend(entries)
        body_parts.append(f'<section class="part">{html}</section>')

    toc_html = ['<section class="toc"><h1 class="plain">目录</h1><ol>']
    for level, hid, text in toc_items:
        cls = "lv1" if level == 1 else "lv2"
        ind = '<span class="ind"></span>' if level == 2 else ''
        toc_html.append(f'<li class="{cls}"><a href="#{hid}">{ind}{text}</a></li>')
    toc_html.append("</ol></section>")

    front = """
<section class="front"><div class="front-inner">
  <div class="front-title">不完全减肥指南</div>
  <div class="front-sub">给普通人的一套减重方法 · 网页版同步更新</div>
  <div class="rule"></div>
  <div class="front-body">
    <dl>
      <dt>作者</dt><dd>Simonlin</dd>
      <dt>公众号</dt><dd>Simonlin的精神世界</dd>
      <dt>在线读</dt><dd>https://simonlin000.github.io/incomplete-weight-loss-guide/</dd>
      <dt>源代码</dt><dd>https://github.com/simonlin000/incomplete-weight-loss-guide</dd>
      <dt>版本</dt><dd>2026 年 10 月 30 日 · 第 1 版</dd>
      <dt>许可</dt><dd>文字 CC BY-NC-SA 4.0　｜　代码 MIT</dd>
    </dl>
    <div class="rule"></div>
    <p class="small">这本书写的是减重的一般方法和一个人的实践记录，不是医疗建议。有基础病、在吃药、怀孕或哺乳、有进食障碍史，先找医生。书里凡是标 C 的段落，都是机制推断或个人经验，不是证据。<br>
    所有实质结论后面都挂着编号，编号对应附录 E 的来源条目。哪一条你核不到，或者挪不动脚，去 GitHub 提一个 issue，我改了会在变更记录里写清改了什么、为什么改。</p>
  </div>
</div></section>
"""

    from PIL import Image as _I
    cover_jpg = IMG_CACHE / "cover.jpg"
    _I.open(COVER).convert("RGB").save(cover_jpg, "JPEG", quality=92, progressive=True, optimize=True)
    COVER_JPG = cover_jpg
    html = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>不完全减肥指南</title>
<meta name="author" content="Simonlin">
<meta name="description" content="给普通人的一套减重方法：怎么算、怎么吃、怎么练。每条结论标证据等级，来源可核。">
<meta name="keywords" content="减重,减肥,热量缺口,减脂,不完全减肥指南,Simonlin">
<style>{CSS}</style></head>
<body>
<section class="cover"><img src="file://{COVER_JPG}" alt="封面"></section>
{front}
{''.join(toc_html)}
{''.join(body_parts)}
</body></html>"""

    html_path = ROOT / "PDF版" / "_print.html"
    html_path.write_text(html, encoding="utf-8")

    from weasyprint import HTML
    HTML(string=html, base_url=str(ROOT)).write_pdf(str(OUT_PDF))
    print(f"PDF: {OUT_PDF}  ({OUT_PDF.stat().st_size} bytes)")
    print(f"目录条目 {len(toc_items)} 条")

    txt = OUT_PDF.read_text(errors="ignore")
    print("cups" if "cups" in txt else "")


if __name__ == "__main__":
    build()
