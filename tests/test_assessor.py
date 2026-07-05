from lged_knowledge import (
    calculate_m20_concrete,
    generate_deterministic_bom,
    estimate_repair_time,
)
from app import validate_gps, extract_exif_gps
from PIL import Image


def test_calculate_m20_concrete():
    # 1 cumec should yield roughly predictable bags of cement
    res = calculate_m20_concrete(1.0)
    assert "Cement (OPC 50kg Bags)" in res
    assert res["Cement (OPC 50kg Bags)"] > 0
    assert "Fine Aggregate / Sylhet Sand (cft)" in res


def test_generate_deterministic_bom():
    # Test Bridge BOM
    bom, cost = generate_deterministic_bom(
        "RC Bridge", "Active Collapse", 150, "Critical"
    )
    assert len(bom) > 0
    assert cost > 0
    item_codes = [b["code"] for b in bom]
    assert "Internal-Ref-1.0" in item_codes  # Cement
    assert "Internal-Ref-6.1" in item_codes  # Shoring Props

    # Test Embankment BOM
    bom_embankment, cost_embankment = generate_deterministic_bom(
        "Coastal Embankment", "Overtopped", 200, "Medium"
    )
    item_codes_emb = [b["code"] for b in bom_embankment]
    assert "Internal-Ref-5.0" in item_codes_emb  # Sand bags


def test_estimate_repair_time():
    assert "12 - 18 Weeks" in estimate_repair_time("Critical", "RC Bridge")
    assert "6 - 8 Weeks" in estimate_repair_time("Medium", "RC Bridge")
    assert "2 - 4 Weeks" in estimate_repair_time("Low", "RC Bridge")
    assert "2 - 4 Weeks" in estimate_repair_time("Medium", "Road")


def test_gps_validation_bounds():
    assert validate_gps(23.8103, 90.4125) is True  # Dhaka (Valid)
    assert validate_gps(21.4272, 92.0058) is True  # Cox's Bazar (Valid)
    assert validate_gps(40.7128, -74.0060) is False  # New York (Invalid)
    assert validate_gps(23.0, 93.0) is False  # Out of longitude bounds


def test_exif_extraction_no_exif():
    # Create a dummy image with no EXIF
    img = Image.new("RGB", (10, 10))
    assert extract_exif_gps(img) is None


def test_bengali_pdf_generation():
    from services.pdf_generator import create_procurement_pdf

    data = {
        "gps": "22.3569, 91.7832",
        "exif_verified": True,
        "infra_type": "RC Bridge",
        "damage_type": "Shear Failure",
        "final_severity": "Critical",
        "report_hash": "TEST-1234",
        "total_cost": 150000.0,
        "bom": [
            {
                "code": "Internal-Ref-1.0",
                "item": "Cement",
                "quantity": 100,
                "cost_bdt": 55000.0,
            }
        ],
    }
    pdf_bytes = create_procurement_pdf(data, lang="bn")
    assert len(pdf_bytes) > 0
