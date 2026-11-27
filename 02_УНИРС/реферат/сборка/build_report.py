"""Собирает главы варианта № 7 в Markdown, DOCX и PDF."""

import argparse
from io import BytesIO
import os
from pathlib import Path
import re
import subprocess
from tempfile import TemporaryDirectory
import unicodedata

from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Mm, Pt
from docx.text.paragraph import Paragraph


CHAPTER_DIR = Path(__file__).resolve().parents[1]
CHAPTERS = (
    "00_Титульный_лист.md",
    "01_Введение.md",
    "02_Теоретическая_часть.md",
    "03_Расчет_утяжеления.md",
    "04_Расчет_плотности_бентонита.md",
    "05_Расчет_разбавления.md",
    "06_Анализ_результатов.md",
    "07_Заключение.md",
    "08_Литература.md",
)
STEM = "Реферат_вариант_07"
SUBMISSION_STEM = f"{STEM}_К_СДАЧЕ"


def run(*args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)


def combine(output):
    chapters = [(CHAPTER_DIR / path).read_text(encoding="utf-8").strip() for path in CHAPTERS]
    headings = [
        (len(mark), title)
        for chapter in chapters[1:]
        for mark, title in re.findall(r"^(#{1,2}) (.+)$", chapter, re.MULTILINE)
    ]
    entries = [
        "  " * (level - 1) + "- " + re.sub(r"^(\d+)\.", r"\1\\.", title)
        for level, title in headings
    ]
    chapters.insert(1, "# Содержание\n\n" + "\n".join(entries))
    text = "\n\n".join(chapters) + "\n"
    image_dir = Path(os.path.relpath(CHAPTER_DIR / "иллюстрации", output.parent)).as_posix()
    output.write_text(text.replace("](иллюстрации/", f"]({image_dir}/"), encoding="utf-8")
    return headings


def configure_style(style, *, size=14, indent=0, spacing=1.5,
                    align=WD_ALIGN_PARAGRAPH.LEFT, before=0, after=0):
    style.font.name = "Times New Roman"
    fonts = style.element.get_or_add_rPr().rFonts
    for attribute in ("asciiTheme", "hAnsiTheme", "eastAsiaTheme", "csTheme", "cstheme"):
        fonts.attrib.pop(qn(f"w:{attribute}"), None)
    style.font.size = Pt(size)
    style.font.color.rgb = None
    fmt = style.paragraph_format
    fmt.alignment = align
    fmt.first_line_indent = Mm(indent)
    fmt.line_spacing = spacing
    fmt.space_before = Pt(before)
    fmt.space_after = Pt(after)
    fmt.widow_control = True


def reference_doc(path):
    doc = Document(BytesIO(run("pandoc", "--print-default-data-file=reference.docx",
                               stdout=subprocess.PIPE).stdout))
    section = doc.sections[0]
    section.page_width, section.page_height = Mm(210), Mm(297)
    section.left_margin, section.right_margin = Mm(30), Mm(15)
    section.top_margin = section.bottom_margin = Mm(20)
    section.footer_distance = Mm(10)
    section.different_first_page_header_footer = True

    styles = {style.name: style for style in doc.styles}
    for name in ("Normal", "Body Text", "First Paragraph", "Bibliography"):
        configure_style(styles[name], indent=12.5, align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    for name in ("Heading 1", "Heading 2", "TOC Heading"):
        style = styles[name]
        configure_style(style, before=9, after=5)
        style.font.bold = True
        style.font.italic = False
        style.paragraph_format.keep_with_next = True
    for name in ("Figure", "Captioned Figure", "Caption", "Image Caption", "Table Caption"):
        configure_style(styles[name], size=12, spacing=1.15,
                        align=WD_ALIGN_PARAGRAPH.CENTER, before=4, after=4)
    configure_style(styles["Compact"], size=12, spacing=1.12)
    for align, name in ((WD_ALIGN_PARAGRAPH.CENTER, "Cover Center"),
                        (WD_ALIGN_PARAGRAPH.RIGHT, "Cover Right")):
        configure_style(doc.styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH), align=align)
    configure_style(doc.styles.add_style("Display Math", WD_STYLE_TYPE.PARAGRAPH),
                    spacing=1.0, align=WD_ALIGN_PARAGRAPH.CENTER, before=2, after=2)
    for level in (1, 2):
        style = doc.styles.add_style(f"TOC {level}", WD_STYLE_TYPE.PARAGRAPH)
        configure_style(style, after=4)
        style.paragraph_format.left_indent = Mm(8 * (level - 1))
        style.paragraph_format.tab_stops.add_tab_stop(Mm(164), WD_TAB_ALIGNMENT.RIGHT,
                                                    WD_TAB_LEADER.DOTS)
    doc.save(path)


def append_field_code(paragraph, code, *, starts=False, separates=False, ends=False):
    run_element = paragraph.add_run()._r
    if starts:
        begin = OxmlElement("w:fldChar")
        begin.set(qn("w:fldCharType"), "begin")
        run_element.append(begin)
    if code:
        code_element = OxmlElement("w:instrText")
        code_element.set(qn("xml:space"), "preserve")
        code_element.text = f" {code} "
        run_element.append(code_element)
    if separates or ends:
        marker = OxmlElement("w:fldChar")
        marker.set(qn("w:fldCharType"), "separate" if separates else "end")
        run_element.append(marker)


def bookmark_for(paragraph):
    sibling = paragraph._p.getprevious()
    if sibling is not None and sibling.tag == qn("w:bookmarkStart"):
        return sibling.get(qn("w:name"))
    return None


def add_contents(doc, chapter_headings, pages):
    paragraphs = doc.paragraphs
    index = next(i for i, p in enumerate(paragraphs) if p.text == "Содержание")
    contents = paragraphs[index]
    for paragraph in paragraphs[index + 1:]:
        if paragraph.style.name == "Heading 1":
            break
        paragraph._p.getparent().remove(paragraph._p)
    for element in list(doc.element.body):
        if element.tag == qn("w:sdt") and any(
            "TOC" in (instruction.text or "")
            for instruction in element.iter(qn("w:instrText"))
        ):
            doc.element.body.remove(element)

    contents.style = doc.styles["TOC Heading"]
    contents.paragraph_format.page_break_before = True
    contents.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cursor = contents._p
    for index, (heading, page) in enumerate(zip(chapter_headings, pages, strict=True)):
        element = OxmlElement("w:p")
        cursor.addnext(element)
        paragraph = Paragraph(element, doc._body)
        paragraph.style = doc.styles["TOC 1" if heading.style.name == "Heading 1" else "TOC 2"]
        if index == 0:
            append_field_code(paragraph, r'TOC \o "1-2" \h \z', starts=True, separates=True)
        label = paragraph.add_run(heading.text)
        if page:
            label.add_tab()
            label.add_text(str(page))
        anchor = bookmark_for(heading)
        if anchor:
            link = OxmlElement("w:hyperlink")
            link.set(qn("w:anchor"), anchor)
            element.append(link)
            link.append(label._r)
        cursor = element
    append_field_code(paragraph, "", ends=True)


def prepare_docx(pandoc_docx, output, headings, pages):
    doc = Document(pandoc_docx)
    doc.core_properties.title = "Расчёты при измерении плотности бурового раствора"
    doc.core_properties.subject = "Промывка скважин и буровые растворы. Вариант № 7"
    doc.core_properties.author = ""
    doc.core_properties.last_modified_by = ""
    doc.core_properties.language = "ru-RU"
    doc.core_properties.comments = ""
    cover = []
    for paragraph in doc.paragraphs:
        if paragraph.text == "Содержание":
            break
        cover.append(paragraph)
    cover_spaces = [16, 4, 104, 5, 13, 5, 67, 8, 145]
    for index, (paragraph, before) in enumerate(zip(cover, cover_spaces, strict=True)):
        paragraph.style = doc.styles["Cover Right" if index in (6, 7) else "Cover Center"]
        paragraph.paragraph_format.space_before = Pt(before)
    title_set = {title for _, title in headings}
    chapter_headings = [p for p in doc.paragraphs if p.text in title_set and
                        p.style.name in {"Heading 1", "Heading 2"} and p.text != "Содержание"]
    if [p.text for p in chapter_headings] != [title for _, title in headings]:
        raise ValueError("Порядок заголовков Word отличается от порядка глав.")
    chapter_headings[0].paragraph_format.page_break_before = True
    add_contents(doc, chapter_headings, pages)

    for paragraph in doc.paragraphs:
        if re.match(r"Таблица\s+\d+\s+[-—–]", paragraph.text):
            paragraph.style = doc.styles["Table Caption"]
            paragraph.paragraph_format.keep_with_next = True
        if paragraph._p.xpath(".//w:drawing"):
            paragraph.paragraph_format.keep_with_next = True
        if next(paragraph._p.iter(qn("m:oMathPara")), None) is not None:
            paragraph.style = doc.styles["Display Math"]
            previous = paragraph._p.getprevious()
            if previous is not None and previous.tag == qn("w:p"):
                lead = Paragraph(previous, doc._body)
                if lead.text.strip():
                    lead.paragraph_format.keep_with_next = True
    for table in doc.tables:
        table.rows[0]._tr.get_or_add_trPr().append(OxmlElement("w:tblHeader"))
        last_row = len(table.rows) - 1
        for row_index, row in enumerate(table.rows):
            row._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    paragraph.style = doc.styles["Compact"]
                    paragraph.paragraph_format.keep_with_next = row_index < last_row

    page_number = doc.sections[0].footer.paragraphs[0]
    page_number.alignment = WD_ALIGN_PARAGRAPH.CENTER
    append_field_code(page_number, "PAGE", starts=True)
    append_field_code(page_number, "", ends=True)
    doc.save(output)


def export_pdf(docx, output_dir, profile):
    run("soffice", f"-env:UserInstallation={profile.as_uri()}", "--headless",
        "--convert-to", "pdf", "--outdir", str(output_dir), str(docx),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    pdf = output_dir / docx.with_suffix(".pdf").name
    if not pdf.is_file():
        raise FileNotFoundError(pdf)
    return pdf


def normalized(text):
    return " ".join(unicodedata.normalize("NFKC", text).split())


def find_pages(pdf, headings):
    text = run("pdftotext", "-layout", str(pdf), "-", stdout=subprocess.PIPE).stdout
    pages = [normalized(page) for page in text.decode().split("\f")]
    found = []
    for _, title in headings:
        page = next((i for i, page_text in enumerate(pages[2:], start=3)
                     if normalized(title) in page_text), None)
        if page is None:
            raise ValueError(f"В PDF не найден заголовок «{title}».")
        found.append(page)
    return found


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=CHAPTER_DIR.parent / "output")
    parser.add_argument("--markdown-only", action="store_true")
    args = parser.parse_args()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    markdown = output / (STEM + ".md")
    headings = combine(markdown)
    if args.markdown_only:
        return

    with TemporaryDirectory() as scratch:
        scratch = Path(scratch)
        reference = scratch / "reference.docx"
        pandoc_docx = scratch / "source.docx"
        probe = scratch / "pagination.docx"
        reference_doc(reference)
        run("pandoc", "--from=markdown-smart", "--metadata=lang:ru-RU", "--toc", "--toc-depth=2",
            f"--reference-doc={reference}", f"--resource-path={output}",
            str(markdown), "-o", str(pandoc_docx))

        prepare_docx(pandoc_docx, probe, headings, [""] * len(headings))
        pages = find_pages(export_pdf(probe, scratch, scratch / "office"), headings)
        docx = output / (SUBMISSION_STEM + ".docx")
        prepare_docx(pandoc_docx, docx, headings, pages)
        pdf = export_pdf(docx, scratch, scratch / "office")
        if find_pages(pdf, headings) != pages:
            raise ValueError("Обновление оглавления изменило пагинацию.")
        (output / pdf.name).write_bytes(pdf.read_bytes())


if __name__ == "__main__":
    main()
