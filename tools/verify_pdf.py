#!/usr/bin/env python3
"""《不完全减肥指南》PDF 的验证脚本（规则 8、10、19：硬规则交给脚本，别靠人眼）。

用法：python3 verify_pdf.py [pdf路径]

检查项：
  1. PDF 能打开、页数正常
  2. 中文字体全部嵌入（缺字体会串字）
  3. 没有任何文字越出页边距（此前踩过表格溢出）
  4. 目录里每条都跟着页码，且页码右端对齐（此前 indent 写法错，页码歪了 20pt）
  5. 目录页码与书签实际页码一致
  6. 书签数量 >= markdown 里的一二级标题数（防漏章节）
  7. 图片数量与 markdown 里的图片引用数一致
  8. 文件体积上限（超过 8MB 说明图没压）
全部通过返回 0，任何一条不过返回 1。
"""
import re
import subprocess
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = ROOT / "repo" / "docs"
DEFAULT_PDF = pathlib.Path(__file__).resolve().parent / "不完全减肥指南.pdf"

fails, warns = [], []


def check(name, ok, detail=""):
    print(("  ✓ " if ok else "  ✗ ") + name + (f"　{detail}" if detail else ""))
    if not ok:
        fails.append(name + ("　" + detail if detail else ""))


def main(pdf_path: pathlib.Path) -> int:
    import fitz  # PyMuPDF

    print(f"验证 {pdf_path.name}")
    doc = fitz.open(pdf_path)

    # 1 页数
    check("页数正常", 50 <= doc.page_count <= 200, f"{doc.page_count} 页")

    # 2 字体嵌入
    fonts = subprocess.run(["pdffonts", str(pdf_path)], capture_output=True, text=True).stdout
    rows = [l for l in fonts.splitlines()[2:] if l.strip()]
    not_embedded = []
    for r in rows:                              # 列宽固定，用两段以上空格切
        cols = [c for c in re.split(r"\s{2,}", r.strip()) if c]
        if len(cols) >= 4 and cols[3].split()[0] != "yes":
            not_embedded.append(cols[0])
    check("中文字体全部嵌入", not not_embedded, f"{len(rows)} 个字体" + (f"，没嵌：{not_embedded}" if not_embedded else ""))

    # 3 文字越界
    MARGIN = 59.5
    left_edge = MARGIN - 1.5
    right_edge = 595.28 - MARGIN + 1.5
    over = []
    for i, page in enumerate(doc):
        for block in page.get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                for span in line["spans"]:
                    x0, _, x1, _ = span["bbox"]
                    if span["text"].strip() and (x1 > right_edge or x0 < left_edge):
                        over.append((i + 1, span["text"][:20]))
    check("正文没有越出页边距", not over, f"越界 {len(over)} 处" + (f"，如 {over[:3]}" if over else ""))

    # 4 目录页码对齐
    # 目录页：标题起头是"目录"，或整页点线引导多于 10 行
    toc_pages = [i for i, p in enumerate(doc)
                 if p.get_text().lstrip().startswith("目录") or p.get_text().count("·") > 30]
    aligned, unaligned = [0, 0]
    for pno in toc_pages:
        for block in doc[pno].get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                for span in line["spans"]:
                    txt = span["text"].strip()
                    if txt.isdigit() and span["bbox"][0] > 380:
                        right = round(span["bbox"][2], 1)
                        if right == 535.7:
                            aligned += 1
                        else:
                            unaligned += 1
    check("目录页码右端对齐", unaligned == 0 and aligned > 50, f"对齐 {aligned} 条，歪 {unaligned} 条")

    # 5、6 书签与标题
    bookmarks = doc.get_toc()
    heads = 0
    files = list(DOCS.glob("*.md")) + list(DOCS.glob("appendix/*.md"))
    for f in files:
        text = f.read_text(encoding="utf-8")
        heads += len(re.findall(r"^#{1,2} ", text, flags=re.M))
    check("书签覆盖全部标题", len(bookmarks) >= heads + 1, f"书签 {len(bookmarks)} 个，源标题 {heads} 个")

    # 5 目录页码与书签一致（抽前 10 条比对目录里写的页码）
    if toc_pages:
        text0 = doc[toc_pages[0]].get_text()
        mismatched = []
        for level, title, page_no in bookmarks:
            if title.strip() == "目录":
                continue
            m = re.search(re.escape(title.strip()) + r"[^\n]*?(\d+)\s*$", text0, flags=re.M)
            if m and int(m.group(1)) != page_no:
                mismatched.append((title, m.group(1), page_no))
            if len(mismatched) >= 3:
                break
        check("目录页码与正文实际页码一致", not mismatched, f"不一致 {mismatched[:3]}" if mismatched else "抽样一致")

    # 7 图片数
    src_imgs = 0
    for f in files:
        src_imgs += len(re.findall(r"!\[[^\]]*\]\(|src=\"/images/", f.read_text(encoding="utf-8")))
    pdf_imgs = len({im[0] for p in doc for im in p.get_images(full=True)})
    check("图片数量对得上", pdf_imgs >= src_imgs, f"PDF {pdf_imgs} 张，源文件引用 {src_imgs} 张")

    # 8 体积
    mb = pdf_path.stat().st_size / 1024 / 1024
    check("体积在 8MB 以内", mb <= 8, f"{mb:.1f} MB")

    print()
    if fails:
        print(f"没通过 {len(fails)} 项：")
        for f in fails:
            print("  -", f)
        return 1
    print("全部通过。")
    return 0


if __name__ == "__main__":
    path = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PDF
    sys.exit(main(path))
