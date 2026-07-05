from fpdf import FPDF
from fpdf.fonts import FontFace
from typing import Dict, Any
import os


def _set_font(pdf: FPDF, lang: str, font_path: str, size: int, style: str = ""):
    if lang == "bn" and os.path.exists(font_path):
        pdf.set_font("NotoSansBengali", "", size)
    else:
        pdf.set_font("helvetica", style, size)


def create_procurement_pdf(data: Dict[str, Any], lang: str = "en") -> bytes:
    pdf = FPDF()

    # Register Unicode font for Bengali
    font_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "NotoSansBengali-Regular.ttf"
    )
    if os.path.exists(font_path):
        pdf.add_font("NotoSansBengali", style="", fname=font_path)

    pdf.add_page()

    def set_font(size: int, style: str = ""):
        _set_font(pdf, lang, font_path, size, style)

    set_font(14, "B")

    title = (
        "EMERGENCY PROCUREMENT & REQUISITION REPORT"
        if lang == "en"
        else "জরুরী সংগ্রহ ও চাহিদা প্রতিবেদন"
    )
    subtitle = (
        "Zone B: Chittagong Division - Post-Cyclone Triage"
        if lang == "en"
        else "জোন বি: চট্টগ্রাম বিভাগ - ঘূর্ণিঝড় পরবর্তী ট্রায়াজ"
    )

    pdf.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT", align="C")
    set_font(10, "I")
    pdf.cell(0, 5, subtitle, new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(5)

    set_font(11, "B")
    pdf.cell(40, 8, "GPS Location:" if lang == "en" else "জিপিএস অবস্থান:")
    set_font(11, "")
    verified_str = (
        ("Yes" if data["exif_verified"] else "No")
        if lang == "en"
        else ("হ্যাঁ" if data["exif_verified"] else "না")
    )
    pdf.cell(
        0,
        8,
        f"{data['gps']} (EXIF Verified: {verified_str})",
        new_x="LMARGIN",
        new_y="NEXT",
    )

    set_font(11, "B")
    pdf.cell(40, 8, "Damage Class:" if lang == "en" else "ক্ষতির শ্রেণী:")
    set_font(11, "")
    pdf.cell(
        0,
        8,
        f"{data['damage_type']} (Final Severity: {data['final_severity']})",
        new_x="LMARGIN",
        new_y="NEXT",
    )
    pdf.ln(5)

    set_font(12, "B")
    bom_title = (
        "Deterministic Bill of Materials (Zone B Rates Applied)"
        if lang == "en"
        else "নির্ধারিত সামগ্রীর বিল (জোন বি রেট প্রযোজ্য)"
    )
    pdf.cell(0, 10, bom_title, new_x="LMARGIN", new_y="NEXT")
    set_font(10, "")

    headings_style = (
        FontFace()
        if (lang == "bn" and os.path.exists(font_path))
        else FontFace(emphasis="BOLD")
    )
    with pdf.table(
        col_widths=(20, 70, 20, 30),
        text_align=("C", "L", "C", "R"),
        headings_style=headings_style,
    ) as table:
        headings = table.row()
        headers_en = ["Item Code", "Material Description", "Quantity", "Cost (BDT)"]
        headers_bn = ["আইটেম কোড", "বিবরণ", "পরিমাণ", "খরচ (BDT)"]
        for header in (headers_en if lang == "en" else headers_bn):
            if lang == "bn":
                headings.cell(header)
            else:
                headings.cell(header, style=FontFace(emphasis="BOLD"))
        for item in data["bom"]:
            row = table.row()
            row.cell(item["code"])
            row.cell(item["item"])
            row.cell(str(item["quantity"]))
            row.cell(f"{item['cost_bdt']:,.2f}")

    pdf.ln(5)
    set_font(11, "B")
    total_val_str = (
        f"Total Estimated Requisition Value: BDT {data['total_cost']:,.2f}"
        if lang == "en"
        else f"মোট আনুমানিক খরচ: BDT {data['total_cost']:,.2f}"
    )
    pdf.cell(0, 10, total_val_str, align="R", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(10)
    set_font(8, "I")
    disclaimer = f"Report Reference ID: {data['report_hash']}\nDISCLAIMER: Material volumes calculated deterministically. Requires validation."
    pdf.multi_cell(0, 5, disclaimer)

    return bytes(pdf.output())
