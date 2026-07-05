from fpdf import FPDF
from fpdf.fonts import FontFace
from typing import Dict, Any, Union
import os

def generate_bengali_html(data: Dict[str, Any]) -> str:
    html = f"""
    <!DOCTYPE html>
    <html lang="bn">
    <head>
        <meta charset="UTF-8">
        <style>
            @media print {{
                body {{ font-family: 'Noto Sans Bengali', sans-serif; padding: 20px; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                th, td {{ border: 1px solid #000; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .text-center {{ text-align: center; }}
                .text-right {{ text-align: right; }}
                .bold {{ font-weight: bold; }}
            }}
            body {{ font-family: 'Noto Sans Bengali', sans-serif; padding: 20px; background-color: white; color: black; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            .text-center {{ text-align: center; }}
            .text-right {{ text-align: right; }}
            .bold {{ font-weight: bold; }}
            .header {{ font-size: 24px; font-weight: bold; text-align: center; color: #006a4e; }}
            .sub-header {{ font-size: 14px; text-align: center; font-style: italic; margin-bottom: 20px; }}
            .info-row {{ margin-bottom: 10px; font-size: 16px; }}
            .footer {{ margin-top: 30px; font-size: 12px; font-style: italic; color: #555; }}
        </style>
    </head>
    <body>
        <div class="header">জরুরী সংগ্রহ ও চাহিদা প্রতিবেদন</div>
        <div class="sub-header">জোন বি: চট্টগ্রাম বিভাগ - ঘূর্ণিঝড় পরবর্তী ট্রায়াজ</div>
        
        <div class="info-row"><span class="bold">জিপিএস অবস্থান:</span> {data['gps']} (EXIF Verified: {'হ্যাঁ' if data['exif_verified'] else 'না'})</div>
        <div class="info-row"><span class="bold">ক্ষতির শ্রেণী:</span> {data['damage_type']} (Final Severity: {data['final_severity']})</div>
        
        <h3 style="margin-top: 30px;">নির্ধারিত সামগ্রীর বিল (জোন বি রেট প্রযোজ্য)</h3>
        <table>
            <thead>
                <tr>
                    <th>আইটেম কোড</th>
                    <th>বিবরণ</th>
                    <th class="text-center">পরিমাণ</th>
                    <th class="text-right">খরচ (BDT)</th>
                </tr>
            </thead>
            <tbody>
"""
    for item in data['bom']:
        html += f"""
                <tr>
                    <td>{item['code']}</td>
                    <td>{item['item']}</td>
                    <td class="text-center">{item['quantity']}</td>
                    <td class="text-right">{item['cost_bdt']:,.2f}</td>
                </tr>
"""
    html += f"""
            </tbody>
        </table>
        
        <h3 class="text-right" style="margin-top: 20px;">মোট আনুমানিক খরচ: BDT {data['total_cost']:,.2f}</h3>
        
        <div class="footer">
            Report Reference ID: {data['report_hash']}<br>
            DISCLAIMER: Material volumes calculated deterministically. Requires validation.
        </div>
    </body>
    </html>
    """
    return html

def create_procurement_pdf(data: Dict[str, Any], lang: str = "en") -> Union[bytes, str]:
    if lang == "bn":
        return generate_bengali_html(data)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", "B", 14)

    title = "EMERGENCY PROCUREMENT & REQUISITION REPORT"
    subtitle = "Zone B: Chittagong Division - Post-Cyclone Triage"

    pdf.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_font("helvetica", "I", 10)
    pdf.cell(0, 5, subtitle, new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(5)

    pdf.set_font("helvetica", "B", 11)
    pdf.cell(40, 8, "GPS Location:")
    pdf.set_font("helvetica", "", 11)
    verified_str = "Yes" if data["exif_verified"] else "No"
    pdf.cell(0, 8, f"{data['gps']} (EXIF Verified: {verified_str})", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("helvetica", "B", 11)
    pdf.cell(40, 8, "Damage Class:")
    pdf.set_font("helvetica", "", 11)
    pdf.cell(0, 8, f"{data['damage_type']} (Final Severity: {data['final_severity']})", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    pdf.set_font("helvetica", "B", 12)
    bom_title = "Deterministic Bill of Materials (Zone B Rates Applied)"
    pdf.cell(0, 10, bom_title, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "", 10)

    with pdf.table(
        col_widths=(20, 70, 20, 30),
        text_align=("C", "L", "C", "R"),
        headings_style=FontFace(emphasis="BOLD"),
    ) as table:
        headings = table.row()
        headers_en = ["Item Code", "Material Description", "Quantity", "Cost (BDT)"]
        for header in headers_en:
            headings.cell(header)
        for item in data["bom"]:
            row = table.row()
            row.cell(item["code"])
            row.cell(item["item"])
            row.cell(str(item["quantity"]))
            row.cell(f"{item['cost_bdt']:,.2f}")

    pdf.ln(5)
    pdf.set_font("helvetica", "B", 11)
    total_val_str = f"Total Estimated Requisition Value: BDT {data['total_cost']:,.2f}"
    pdf.cell(0, 10, total_val_str, align="R", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(10)
    pdf.set_font("helvetica", "I", 8)
    disclaimer = f"Report Reference ID: {data['report_hash']}\nDISCLAIMER: Material volumes calculated deterministically. Requires validation."
    pdf.multi_cell(0, 5, disclaimer)

    return bytes(pdf.output())
