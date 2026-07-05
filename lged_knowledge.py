"""
lged_knowledge.py
Deterministic Engineering Engine for LGED Zone B (Chittagong Division)
Cites official LGED Internal Reference Codes and Standard Structural Specs.
Reference: BNBC 2020 Structural Assessment Criteria
"""

import math
from typing import Dict, List, Tuple

# LGED ZONE B APPROVED SCHEDULE OF RATES (2023-2025 BASELINE)
RATES_BDT_ZONE_B = {
    "opc_cement_bag_50kg": {"code": "Internal-Ref-1.0", "rate": 550, "unit": "bag"},
    "rebar_60_grade_kg": {"code": "Internal-Ref-2.1", "rate": 114, "unit": "kg"},
    "sylhet_sand_cft": {"code": "Internal-Ref-3.2", "rate": 35, "unit": "cft"},
    "brick_chips_20mm_cft": {"code": "Internal-Ref-4.1", "rate": 150, "unit": "cft"},
    "geotextile_sand_bag_175kg": {
        "code": "Internal-Ref-5.0",
        "rate": 450,
        "unit": "bag",
    },
    "shoring_prop_rental": {"code": "Internal-Ref-6.1", "rate": 1200, "unit": "prop"},
    "gabion_mesh_sqm": {"code": "Internal-Ref-7.4", "rate": 850, "unit": "sqm"},
    "timber_formwork_sqm": {"code": "Internal-Ref-8.1", "rate": 350, "unit": "sqm"},
    "waterproofing_membrane_sqm": {
        "code": "Internal-Ref-9.2",
        "rate": 600,
        "unit": "sqm",
    },
    "dewatering_pump_rental_day": {
        "code": "Internal-Ref-10.1",
        "rate": 2500,
        "unit": "day",
    },
}

CUMEC_TO_CFT = 35.3147
DRY_VOLUME_MULTIPLIER = 1.54  # Dry materials compact when hydrated


def calculate_m20_concrete(volume_cumec: float) -> Dict[str, float]:
    """Calculates M20 Grade Concrete (1:1.5:3) constituents."""
    dry_volume = volume_cumec * DRY_VOLUME_MULTIPLIER
    total_ratio_parts = 5.5  # 1 + 1.5 + 3

    cement_volume = (1 / total_ratio_parts) * dry_volume
    cement_bags = math.ceil(cement_volume / 0.035)  # 0.035m3 per 50kg bag
    sand_cft = ((1.5 / total_ratio_parts) * dry_volume) * CUMEC_TO_CFT
    aggregate_cft = ((3 / total_ratio_parts) * dry_volume) * CUMEC_TO_CFT

    return {
        "Cement (OPC 50kg Bags)": cement_bags,
        "Fine Aggregate / Sylhet Sand (cft)": round(sand_cft, 2),
        "Coarse Aggregate / 20mm Brick Chips (cft)": round(aggregate_cft, 2),
    }


def calculate_rebar_requirements(infra_type: str, volume_cumec: float) -> int:
    """
    Applies structural estimation thumb rules for reinforcement steel.
    Reference: BNBC 2020, Volumetric estimation principles.
    NOTE: These are Class 5 estimates and are NOT a substitute for structural design.
    """
    # Heavy reinforcement for primary compression members
    if "Column" in infra_type or "Pier" in infra_type or "Abutment" in infra_type:
        # Assumption: ~2.5-3.5% steel by volume. Density of steel ~7850 kg/m3.
        # 300 kg/m3 is a reasonable high-end estimate for heavily reinforced columns.
        return math.ceil(volume_cumec * 300)

    # Flexural reinforcement for beams, slabs, and decks
    elif (
        "Bridge" in infra_type
        or "Beam" in infra_type
        or "Culvert" in infra_type
        or "Slab" in infra_type
    ):
        # Assumption: ~1.5-2.5% steel by volume.
        # 200-250 kg/m3 is a typical range for flexural members.
        return math.ceil(volume_cumec * 225)

    # Light reinforcement for retaining walls and foundations
    elif "Retaining Wall" in infra_type or "Foundation" in infra_type:
        # Assumption: ~1.0-1.5% steel by volume.
        return math.ceil(volume_cumec * 150)

    # Minimal/temperature reinforcement for non-structural or mass concrete
    else:
        # Paved Roadway, etc.
        return math.ceil(volume_cumec * 100)


def generate_deterministic_bom(
    infra_type: str, status: str, area_sqm: float, severity: str
) -> Tuple[List[Dict], float]:
    """Generates a BOM applying Severity multipliers and Zone B Rates.
    Uses BNBC 2020 Structural Assessment Criteria for severity multipliers.
    """
    bom = []
    total_cost = 0.0

    severity_multipliers = {
        "Low": 0.1,
        "Medium": 0.4,
        "Critical": 0.8,
        "Total Collapse": 1.2,
    }
    multiplier = severity_multipliers.get(severity, 0.5)

    est_volume_cumec = (area_sqm * 0.3) * multiplier

    if any(
        k in infra_type
        for k in [
            "Bridge",
            "Culvert",
            "Office",
            "Road",
            "Retaining Wall",
            "Water Treatment Plant",
        ]
    ):
        concrete_mats = calculate_m20_concrete(est_volume_cumec)
        for item, qty in concrete_mats.items():
            if "Cement" in item:
                cost = qty * RATES_BDT_ZONE_B["opc_cement_bag_50kg"]["rate"]
                code = RATES_BDT_ZONE_B["opc_cement_bag_50kg"]["code"]
            elif "Sand" in item:
                cost = qty * RATES_BDT_ZONE_B["sylhet_sand_cft"]["rate"]
                code = RATES_BDT_ZONE_B["sylhet_sand_cft"]["code"]
            elif "Coarse" in item:
                cost = qty * RATES_BDT_ZONE_B["brick_chips_20mm_cft"]["rate"]
                code = RATES_BDT_ZONE_B["brick_chips_20mm_cft"]["code"]
            else:
                cost = 0
                code = "UNKNOWN"

            bom.append({"code": code, "item": item, "quantity": qty, "cost_bdt": cost})
            total_cost += cost

        rebar_kg = calculate_rebar_requirements(infra_type, est_volume_cumec)
        rebar_cost = rebar_kg * RATES_BDT_ZONE_B["rebar_60_grade_kg"]["rate"]
        bom.append(
            {
                "code": RATES_BDT_ZONE_B["rebar_60_grade_kg"]["code"],
                "item": "60-Grade Deformed Rebar (kg)",
                "quantity": rebar_kg,
                "cost_bdt": rebar_cost,
            }
        )
        total_cost += rebar_cost

        # New material: Timber formwork
        formwork_sqm = math.ceil(area_sqm * multiplier)
        formwork_cost = formwork_sqm * RATES_BDT_ZONE_B["timber_formwork_sqm"]["rate"]
        bom.append(
            {
                "code": RATES_BDT_ZONE_B["timber_formwork_sqm"]["code"],
                "item": "Timber Formwork (sqm)",
                "quantity": formwork_sqm,
                "cost_bdt": formwork_cost,
            }
        )
        total_cost += formwork_cost

        # New material: Waterproofing (Water Treatment Plant or Submerged)
        if "Water" in infra_type or status == "Submerged":
            wp_sqm = math.ceil(area_sqm * multiplier)
            wp_cost = wp_sqm * RATES_BDT_ZONE_B["waterproofing_membrane_sqm"]["rate"]
            bom.append(
                {
                    "code": RATES_BDT_ZONE_B["waterproofing_membrane_sqm"]["code"],
                    "item": "Waterproofing Membrane (sqm)",
                    "quantity": wp_sqm,
                    "cost_bdt": wp_cost,
                }
            )
            total_cost += wp_cost

        if severity == "Critical" or status == "Active Collapse":
            props = math.ceil(area_sqm / 2.0)
            prop_cost = props * RATES_BDT_ZONE_B["shoring_prop_rental"]["rate"]
            bom.append(
                {
                    "code": RATES_BDT_ZONE_B["shoring_prop_rental"]["code"],
                    "item": "Temporary Steel Shoring Props",
                    "quantity": props,
                    "cost_bdt": prop_cost,
                }
            )
            total_cost += prop_cost

    elif "Embankment" in infra_type:
        # 175kg bag provides approx 0.9 sqm coverage, multiplied by layers required based on severity
        bags_needed = math.ceil((area_sqm / 0.9) * (2.5 * multiplier))
        bags_cost = bags_needed * RATES_BDT_ZONE_B["geotextile_sand_bag_175kg"]["rate"]
        bom.append(
            {
                "code": RATES_BDT_ZONE_B["geotextile_sand_bag_175kg"]["code"],
                "item": "175kg Geotextile Sand Bags (Filled)",
                "quantity": bags_needed,
                "cost_bdt": bags_cost,
            }
        )
        total_cost += bags_cost

        gabion_cost = (
            area_sqm * multiplier * RATES_BDT_ZONE_B["gabion_mesh_sqm"]["rate"]
        )
        bom.append(
            {
                "code": RATES_BDT_ZONE_B["gabion_mesh_sqm"]["code"],
                "item": "Gabion Wire Mesh (sqm) for Toe Protection",
                "quantity": round(area_sqm * multiplier, 2),
                "cost_bdt": gabion_cost,
            }
        )
        total_cost += gabion_cost

    # Dewatering pump rental if submerged
    if status == "Submerged":
        pump_days = 5 if severity in ["Critical", "Total Collapse"] else 2
        pump_cost = pump_days * RATES_BDT_ZONE_B["dewatering_pump_rental_day"]["rate"]
        bom.append(
            {
                "code": RATES_BDT_ZONE_B["dewatering_pump_rental_day"]["code"],
                "item": "Dewatering Pump Rental (Days)",
                "quantity": pump_days,
                "cost_bdt": pump_cost,
            }
        )
        total_cost += pump_cost

    return bom, total_cost


def estimate_repair_time(severity: str, infra_type: str) -> str:
    if severity in ["Critical", "Total Collapse"]:
        return "12 - 18 Weeks (Requires Heavy Plant Mobilization)"
    elif severity == "Medium" and "Bridge" in infra_type:
        return "6 - 8 Weeks"
    return "2 - 4 Weeks (Rapid Deployment Protocol)"
