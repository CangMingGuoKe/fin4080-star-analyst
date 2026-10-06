# -*- coding: utf-8 -*-
"""Markdown -> DOCX converter for the FIN4080 Project 10 documents.

Headings use Word's built-in Heading styles and the table of contents is a real
TOC field, so the contents page is clickable. Page numbers are filled in by
opening the file once in Word (see refresh_toc.ps1) rather than by this script.

Usage:
    python md2docx.py <src.md> <dst.docx> [en]

Passing "en" as the third argument switches heading font to Arial, which suits
the English documents; the body stays Times New Roman either way.
"""
import os
import re
import sys

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

sys.stdout.reconfigure(encoding='utf-8')

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'Project10_明星分析师_研究方案.md')
DST = os.path.join(HERE, 'Project10_明星分析师_研究方案.docx')
if len(sys.argv) > 1:
    SRC = sys.argv[1]
if len(sys.argv) > 2:
    DST = sys.argv[2]

CN, CN_H = '宋体', '黑体'
if len(sys.argv) > 3 and sys.argv[3] == 'en':
    CN_H = 'Arial'
EN, EN_MONO = 'Times New Roman', 'Consolas'
BODY_PT, TBL_PT = 12, 10.5
BLACK = RGBColor(0, 0, 0)
GREY = RGBColor(0x80, 0x80, 0x80)


def style_run(run, cn=CN, en=EN, size=None, bold=None, italic=None):
    if size is not None:
        run.font.size = size
    if bold is not None:
        run.font.bold = bold
    if italic is not None:
        run.font.italic = italic
    run.font.name = en
    rPr = run._element.get_or_add_rPr()
    rf = rPr.get_or_add_rFonts()
    rf.set(qn('w:ascii'), en)
    rf.set(qn('w:hAnsi'), en)
    rf.set(qn('w:eastAsia'), cn)
    run.font.color.rgb = BLACK


TOKEN = re.compile(r'(\*\*.+?\*\*|`[^`]+`|\*[^\s*][^*]*?\*)')


def add_inline(par, text, size=Pt(BODY_PT), cn=CN, en=EN, bold=False):
    for part in TOKEN.split(text):
        if not part:
            continue
        if part.startswith('**') and part.endswith('**') and len(part) > 4:
            style_run(par.add_run(part[2:-2]), cn, en, size, True)
        elif part.startswith('`') and part.endswith('`') and len(part) > 2:
            style_run(par.add_run(part[1:-1]), cn, EN_MONO, Pt(size.pt - 1))
        elif part.startswith('*') and part.endswith('*') and len(part) > 2:
            style_run(par.add_run(part[1:-1]), cn, en, size, None, True)
        else:
            style_run(par.add_run(part), cn, en, size, bold if bold else None)


def add_rule(doc):
    p = doc.add_paragraph()
    pPr = p._p.get_or_add_pPr()
    pbdr = OxmlElement('w:pBdr')
    e = OxmlElement('w:bottom')
    e.set(qn('w:val'), 'single')
    e.set(qn('w:sz'), '6')
    e.set(qn('w:space'), '1')
    e.set(qn('w:color'), 'BFBFBF')
    pbdr.append(e)
    pPr.append(pbdr)
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)


def add_toc(doc):
    lbl = doc.add_paragraph()
    add_inline(lbl, '目录' if CN_H == '黑体' else 'Contents',
               size=Pt(15), cn=CN_H, bold=True)
    lbl.paragraph_format.space_before = Pt(6)
    lbl.paragraph_format.space_after = Pt(6)
    p = doc.add_paragraph()
    r = p.add_run()
    b = OxmlElement('w:fldChar')
    b.set(qn('w:fldCharType'), 'begin')
    r._r.append(b)
    it = OxmlElement('w:instrText')
    it.set(qn('xml:space'), 'preserve')
    it.text = 'TOC \\o "1-2" \\h \\z \\u'
    r._r.append(it)
    sp = OxmlElement('w:fldChar')
    sp.set(qn('w:fldCharType'), 'separate')
    r._r.append(sp)
    t = OxmlElement('w:t')
    t.text = 'Open in Word and update the field to build the contents.'
    r._r.append(t)
    e = OxmlElement('w:fldChar')
    e.set(qn('w:fldCharType'), 'end')
    r._r.append(e)
    style_run(r, size=Pt(BODY_PT))


def repeat_header(t):
    trPr = t.rows[0]._tr.get_or_add_trPr()
    th = OxmlElement('w:tblHeader')
    th.set(qn('w:val'), 'true')
    trPr.append(th)


def no_row_split(t):
    for row in t.rows:
        row._tr.get_or_add_trPr().append(OxmlElement('w:cantSplit'))


def split_row(line):
    s = line.strip()
    if s.startswith('|'):
        s = s[1:]
    if s.endswith('|'):
        s = s[:-1]
    return [c.strip() for c in s.split('|')]


def is_sep(line):
    s = line.strip()
    return s.startswith('|') and set(s) <= set('|-: \t') and '-' in s


def main():
    lines = open(SRC, encoding='utf-8').read().split('\n')

    doc = Document()
    sec = doc.sections[0]
    sec.page_height, sec.page_width = Cm(29.7), Cm(21.0)
    sec.top_margin = sec.bottom_margin = Cm(2.3)
    sec.left_margin = sec.right_margin = Cm(2.2)

    normal = doc.styles['Normal']
    normal.font.name = EN
    normal.font.size = Pt(BODY_PT)
    normal.element.get_or_add_rPr().get_or_add_rFonts().set(qn('w:eastAsia'), CN)
    normal.paragraph_format.line_spacing = 1.32
    normal.paragraph_format.space_after = Pt(5)

    fp = sec.footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = fp.add_run()
    b = OxmlElement('w:fldChar')
    b.set(qn('w:fldCharType'), 'begin')
    r._r.append(b)
    it = OxmlElement('w:instrText')
    it.set(qn('xml:space'), 'preserve')
    it.text = ' PAGE '
    r._r.append(it)
    e = OxmlElement('w:fldChar')
    e.set(qn('w:fldCharType'), 'end')
    r._r.append(e)
    style_run(r, size=Pt(9))
    r.font.color.rgb = GREY

    n_h = n_t = n_p = 0
    toc_done = False
    is_zh = CN_H == '黑体'
    i, n = 0, len(lines)

    while i < n:
        s = lines[i].strip()
        if not s:
            i += 1
            continue

        if s == '---' and not (i > 0 and lines[i - 1].strip().startswith('|')):
            add_rule(doc)
            i += 1
            continue

        if s.startswith('```'):
            i += 1
            code = []
            while i < n and not lines[i].strip().startswith('```'):
                code.append(lines[i].rstrip())
                i += 1
            i += 1
            while code and not code[-1].strip():
                code.pop()
            for ci, cl in enumerate(code):
                p = doc.add_paragraph()
                p.paragraph_format.left_indent = Cm(0.4)
                p.paragraph_format.right_indent = Cm(0.2)
                p.paragraph_format.space_before = Pt(5 if ci == 0 else 0)
                p.paragraph_format.space_after = Pt(7 if ci == len(code) - 1 else 0)
                p.paragraph_format.line_spacing = 1.0
                style_run(p.add_run(cl if cl.strip() else ' '),
                          cn=CN, en=EN_MONO, size=Pt(10))
                pPr = p._p.get_or_add_pPr()
                shd = OxmlElement('w:shd')
                shd.set(qn('w:val'), 'clear')
                shd.set(qn('w:fill'), 'F4F4F4')
                pPr.append(shd)
                pbdr = OxmlElement('w:pBdr')
                if ci == 0:
                    t = OxmlElement('w:top')
                    t.set(qn('w:val'), 'single')
                    t.set(qn('w:sz'), '6')
                    t.set(qn('w:space'), '2')
                    t.set(qn('w:color'), 'D0D0D0')
                    pbdr.append(t)
                if ci == len(code) - 1:
                    bo = OxmlElement('w:bottom')
                    bo.set(qn('w:val'), 'single')
                    bo.set(qn('w:sz'), '6')
                    bo.set(qn('w:space'), '2')
                    bo.set(qn('w:color'), 'D0D0D0')
                    pbdr.append(bo)
                for side in ('left', 'right'):
                    e2 = OxmlElement('w:' + side)
                    e2.set(qn('w:val'), 'single')
                    e2.set(qn('w:sz'), '6')
                    e2.set(qn('w:space'), '4')
                    e2.set(qn('w:color'), 'D0D0D0')
                    pbdr.append(e2)
                pPr.append(pbdr)
                n_p += 1
            continue

        if s.startswith('|') and i + 1 < n and is_sep(lines[i + 1]):
            hdr = split_row(lines[i])
            body, j = [], i + 2
            while j < n and lines[j].strip().startswith('|'):
                body.append(split_row(lines[j]))
                j += 1
            ncol = len(hdr)
            body = [row + [''] * (ncol - len(row)) if len(row) < ncol else row[:ncol]
                    for row in body]
            t = doc.add_table(rows=1, cols=ncol)
            t.style = 'Table Grid'
            t.alignment = WD_TABLE_ALIGNMENT.CENTER
            t.autofit = True
            for k, cell in enumerate(t.rows[0].cells):
                cell.text = ''
                add_inline(cell.paragraphs[0], hdr[k], size=Pt(TBL_PT), bold=True)
                cell.paragraphs[0].paragraph_format.space_after = Pt(2)
                cell.paragraphs[0].paragraph_format.line_spacing = 1.15
            for row in body:
                for k, cell in enumerate(t.add_row().cells):
                    cell.text = ''
                    add_inline(cell.paragraphs[0], row[k], size=Pt(TBL_PT))
                    cell.paragraphs[0].paragraph_format.space_after = Pt(2)
                    cell.paragraphs[0].paragraph_format.line_spacing = 1.15
            for cell in t.rows[0].cells:
                shd = OxmlElement('w:shd')
                shd.set(qn('w:val'), 'clear')
                shd.set(qn('w:fill'), 'F2F2F2')
                cell._tc.get_or_add_tcPr().append(shd)
            repeat_header(t)
            no_row_split(t)
            doc.add_paragraph().paragraph_format.space_after = Pt(0)
            n_t += 1
            i = j
            continue

        m = re.match(r'^(#{1,3})\s+(.*)$', s)
        if m:
            lvl, txt = len(m.group(1)), m.group(2)
            # 副标题只做居中排版，不进入目录
            subtitle = (txt.startswith('明星分析师荐股')
                        or txt.startswith('Market Reactions to Star Analyst'))
            if lvl == 1:
                p = doc.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                add_inline(p, txt, size=Pt(18), cn=CN_H, bold=True)
                p.paragraph_format.space_after = Pt(4)
            elif lvl == 2 and subtitle:
                p = doc.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                add_inline(p, txt, size=Pt(15), cn=CN_H, bold=True)
                p.paragraph_format.space_after = Pt(10)
            else:
                if not toc_done:
                    add_toc(doc)
                    toc_done = True
                p = doc.add_paragraph(style='Heading 1' if lvl == 2 else 'Heading 2')
                add_inline(p, txt, size=Pt(15 if lvl == 2 else 13), cn=CN_H, bold=True)
                p.paragraph_format.space_before = Pt(14 if lvl == 2 else 10)
                p.paragraph_format.space_after = Pt(6)
                p.paragraph_format.keep_with_next = True
            n_h += 1
            i += 1
            continue

        if s.startswith('>'):
            blk = []
            while i < n and lines[i].strip().startswith('>'):
                blk.append(lines[i].strip()[1:].strip())
                i += 1
            groups, cur = [], []
            for x in blk:
                if x == '':
                    if cur:
                        groups.append(cur)
                        cur = []
                else:
                    cur.append(x)
            if cur:
                groups.append(cur)
            for gi, g in enumerate(groups):
                p = doc.add_paragraph()
                p.paragraph_format.left_indent = Cm(0.6)
                p.paragraph_format.space_before = Pt(4 if gi == 0 else 0)
                p.paragraph_format.space_after = Pt(5 if gi == len(groups) - 1 else 0)
                add_inline(p, ' '.join(g), size=Pt(BODY_PT))
                pPr = p._p.get_or_add_pPr()
                pbdr = OxmlElement('w:pBdr')
                e3 = OxmlElement('w:left')
                e3.set(qn('w:val'), 'single')
                e3.set(qn('w:sz'), '18')
                e3.set(qn('w:space'), '6')
                e3.set(qn('w:color'), 'A6A6A6')
                pbdr.append(e3)
                pPr.append(pbdr)
                n_p += 1
            continue

        if re.match(r'^[-*]\s+', s):
            p = doc.add_paragraph(style='List Bullet')
            add_inline(p, re.sub(r'^[-*]\s+', '', s))
            p.paragraph_format.space_after = Pt(3)
            n_p += 1
            i += 1
            continue

        if re.match(r'^\d+\.\s+', s):
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Cm(0.75)
            p.paragraph_format.first_line_indent = Cm(-0.75)
            p.paragraph_format.space_after = Pt(4)
            add_inline(p, s)
            n_p += 1
            i += 1
            continue

        p = doc.add_paragraph()
        add_inline(p, s)
        n_p += 1
        i += 1

    doc.save(DST)

    d2 = Document(DST)
    heads = [q.text for q in d2.paragraphs if q.style.name.startswith('Heading')]
    print('saved: %s' % DST)
    print('headings=%d tables=%d paragraphs=%d toc=%s' % (n_h, n_t, n_p, toc_done))
    print('reopened: paras=%d tables=%d' % (len(d2.paragraphs), len(d2.tables)))
    print('first TOC entries: %s' % heads[:5])


main()
