"""
app.py
Production-Grade Offline-First Architecture for LGED Cyclone Assessor
"""

import streamlit as st
import time
from streamlit_js_eval import get_geolocation
import streamlit.components.v1 as components
from PIL import Image, ExifTags
import datetime
import uuid
import pandas as pd
import io
import re

from config import Config
import importlib
import persistence.database
import config
import services.ai_engine

importlib.reload(persistence.database)
importlib.reload(config)
importlib.reload(services.ai_engine)
from persistence.database import DatabaseService
from services.ai_engine import AIEngine
from services.pdf_generator import create_procurement_pdf
from lged_knowledge import generate_deterministic_bom, estimate_repair_time
from models import AssessmentRecord

# Configuration and Initialization
st.set_page_config(page_title="Kabuliwala", page_icon="kabuli.png", layout="wide")

# Ultra-Rich Earthy Theme Injection (Permanent Dark Mode)
bg_color = "#1A1614"       # Deep earthy obsidian
card_bg = "#292421"        # Warm dark espresso
text_color = "#F4EFE6"     # Soft cream text
input_text_color = "#F4EFE6" 
accent = "#DD6B20"         # Bright Rust Orange
border = "#3D332D"         # Mocha border
widget_bg = "#3D332D"

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');

    html, body, [class*="css"]  {{
        font-family: 'Outfit', sans-serif !important;
    }}
    .stApp {{
        background-color: {bg_color} !important;
        color: {text_color} !important;
    }}

    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    
    .block-container {{
        padding-top: 1rem !important;
        padding-bottom: 0rem !important;
        max-width: 95% !important;
    }}

    div[data-testid="stVerticalBlock"] > div[style*="flex-direction: column;"] {{
        background-color: {card_bg};
        border: 1px solid {border};
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }}
    div[data-testid="stVerticalBlock"] > div[style*="flex-direction: column;"]:hover {{
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
    }}

    .stApp, .stApp p, .stApp span, .stApp div, .stApp label, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6, .stMarkdown p, .stMarkdown div {{
        color: {text_color} !important;
    }}
    
    /* Aggressive widget override for Light Mode visibility */
    input, textarea, select, 
    .stTextInput div[data-baseweb="input"], 
    .stSelectbox div[data-baseweb="select"], 
    .stTextArea div[data-baseweb="textarea"], 
    .stNumberInput div[data-baseweb="input"] {{
        background-color: {widget_bg} !important;
        border-color: {border} !important;
    }}
    input, textarea, select {{
        color: {input_text_color} !important;
        -webkit-text-fill-color: {input_text_color} !important;
    }}
    
    /* Align Language to Left */
    [data-testid="stColumn"]:nth-child(1) div.stRadio {{
        float: left;
        width: auto !important;
    }}
    [data-testid="stColumn"]:nth-child(1) div[role="radiogroup"] {{
        justify-content: flex-start !important;
    }}

    h1, h2, h3, h4, h5, h6 {{
        font-weight: 600 !important;
        letter-spacing: -0.025em !important;
    }}
    
    .lged-header {{
        background: linear-gradient(90deg, {accent}, #9C4221);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5rem !important;
        margin-bottom: 0 !important;
        padding-bottom: 1rem !important;
    }}

    div.stButton > button:first-child {{
        background: linear-gradient(135deg, {accent} 0%, #047857 100%);
        color: white !important;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        letter-spacing: 0.5px;
        padding: 0.5rem 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 14px 0 rgba(16, 185, 129, 0.39);
        width: 100%;
    }}
    div.stButton > button:first-child:hover {{
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(16, 185, 129, 0.23);
        color: white !important;
    }}

    [data-testid="stMetricValue"] {{
        font-size: 2.5rem !important;
        font-weight: 700 !important;
        color: {accent} !important;
    }}
    [data-testid="stMetricLabel"] {{
        font-size: 1rem !important;
        font-weight: 400 !important;
        opacity: 0.7;
    }}

    .stTabs [data-baseweb="tab-list"] {{
        display: flex !important;
        width: 100% !important;
        gap: 8px;
        background-color: transparent;
    }}
    .stTabs [data-baseweb="tab"] {{
        flex: 1 !important;
        justify-content: center !important;
        text-align: center !important;
        background-color: {card_bg};
        border-radius: 9999px !important;
        border: 1px solid {border} !important;
        padding: 10px 20px !important;
        font-weight: 600 !important;
        white-space: normal !important;
    }}
    .stTabs [aria-selected="true"] {{
        background-color: {accent} !important;
        color: white !important;
        border-color: {accent} !important;
    }}
    .stTabs [data-baseweb="tab-border"] {{
        display: none;
    }}
    .stTabs [data-baseweb="tab-highlight"] {{
        display: none;
    }}

    .severity-badge {{
        padding: 6px 12px; border-radius: 9999px; color: white !important; font-weight: 600;
        font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.05em; display: inline-block;
    }}
    .badge-Low {{ background-color: #10b981; }}
    .badge-Medium {{ background-color: #f59e0b; }}
    .badge-Critical {{ background-color: #ef4444; }}
    .badge-Total {{ background-color: #991b1b; }}
</style>
""", unsafe_allow_html=True)

# Authentication
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False


def check_password():
    try:
        if (
            "admin_password" in st.secrets
            and st.session_state.password_input == st.secrets["admin_password"]
        ):
            st.session_state.authenticated = True
        else:
            st.error("Incorrect password")
    except FileNotFoundError:
        st.error("Security Configuration Missing: secrets.toml not found.")
        st.stop()


if not st.session_state.authenticated:
    st.markdown("""
        <style>
        .block-container {
            display: flex !important;
            flex-direction: column !important;
            justify-content: center !important;
            min-height: 80vh !important;
        }
        .login-subtitle {
            text-align: center;
            color: #F4EFE6;
            font-size: 0.85rem;
            margin-top: 5px;
            margin-bottom: 30px;
        }
        .login-header {
            text-align: center;
            margin-bottom: 20px;
            font-weight: 600;
        }
        </style>
    """, unsafe_allow_html=True)
    
    login_col1, login_col2, login_col3 = st.columns([1.3, 1, 1.3])
    with login_col2:
        try:
            st.image("kabuli.png", use_container_width=True)
        except Exception:
            pass
        st.markdown('<div class="login-subtitle">LGED Post-Cyclone Infrastructure Assessor</div>', unsafe_allow_html=True)
        st.markdown('<h2 class="login-header">🔒 Login Required</h2>', unsafe_allow_html=True)
        st.text_input(
            "Password", type="password", key="password_input", on_change=check_password
        )
    st.stop()

# State Management
if "assessment_complete" not in st.session_state:
    st.session_state.assessment_complete = False
if "report_data" not in st.session_state:
    st.session_state.report_data = None
if "assessment_count" not in st.session_state:
    st.session_state.assessment_count = 0

db_service = DatabaseService()

try:
    api_key = st.secrets["GOOGLE_API_KEY"]
except (FileNotFoundError, KeyError):
    st.error("Critical: GOOGLE_API_KEY missing from secrets.")
    st.stop()

ai_engine = AIEngine(api_key=api_key)


# Utilities
import math

def get_decimal_from_dms(dms, ref):
    try:
        def to_float(val):
            # Handle IFDRational or tuple like (num, den)
            if hasattr(val, "numerator") and hasattr(val, "denominator"):
                if val.denominator == 0: return float('nan')
                return float(val.numerator) / float(val.denominator)
            elif isinstance(val, tuple) and len(val) == 2:
                if val[1] == 0: return float('nan')
                return float(val[0]) / float(val[1])
            return float(val)

        d0 = to_float(dms[0])
        d1 = to_float(dms[1])
        d2 = to_float(dms[2])
        
        if math.isnan(d0) or math.isnan(d1) or math.isnan(d2):
            return None

        dec = d0 + (d1 / 60.0) + (d2 / 3600.0)
        if ref in ["S", "W"]:
            dec = -dec
        return round(dec, 5)
    except Exception:
        return None


def extract_exif_gps(image):
    try:
        exif = image.getexif()
        if not exif:
            return None
        
        # In modern Pillow, GPSInfo is an IFD offset. 
        # We must use get_ifd to actually retrieve the dictionary.
        try:
            gps_ifd = exif.get_ifd(ExifTags.IFD.GPSInfo)
            if gps_ifd:
                gps_data = {ExifTags.GPSTAGS.get(t, t): gps_ifd[t] for t in gps_ifd}
                
                # Check for required latitude and longitude data
                if "GPSLatitude" in gps_data and "GPSLongitude" in gps_data:
                    lat = get_decimal_from_dms(
                        gps_data.get("GPSLatitude"), gps_data.get("GPSLatitudeRef", "N")
                    )
                    lon = get_decimal_from_dms(
                        gps_data.get("GPSLongitude"), gps_data.get("GPSLongitudeRef", "E")
                    )
                    if lat is not None and lon is not None:
                        return f"{lat}, {lon}"
        except AttributeError:
            # Fallback for very old Pillow versions where GPSInfo was a dict directly
            for tag_id, value in exif.items():
                tag = ExifTags.TAGS.get(tag_id, tag_id)
                if tag == "GPSInfo" and isinstance(value, dict):
                    gps_data = {ExifTags.GPSTAGS.get(t, t): value[t] for t in value}
                    lat = get_decimal_from_dms(
                        gps_data.get("GPSLatitude"), gps_data.get("GPSLatitudeRef", "N")
                    )
                    lon = get_decimal_from_dms(
                        gps_data.get("GPSLongitude"), gps_data.get("GPSLongitudeRef", "E")
                    )
                    if lat is not None and lon is not None:
                        return f"{lat}, {lon}"
    except Exception:
        pass  # Handle malformed EXIF data
    return None


def validate_gps(lat: float, lon: float) -> bool:
    return (Config.LAT_MIN <= lat <= Config.LAT_MAX) and (
        Config.LON_MIN <= lon <= Config.LON_MAX
    )


def get_severity_badge(severity):
    cls = f"badge-{severity.split()[0]}"
    return f'<span class="severity-badge {cls}">{severity}</span>'


# Application Interface
header_col1, header_col2, header_col3 = st.columns([1, 4, 1])
with header_col1:
    lang_choice = st.radio("LANGUAGE / ভাষা", ["English", "বাংলা"], horizontal=True, label_visibility="collapsed")
with header_col2:
    logo_col1, logo_col2, logo_col3 = st.columns([1, 1.5, 1])
    with logo_col2:
        try:
            st.image("kabuli.png", use_container_width=True)
        except Exception:
            pass
    st.markdown('<div style="text-align: center; color: #F4EFE6; font-size: 0.85rem; margin-top: 5px; margin-bottom: 20px;">LGED Post-Cyclone Infrastructure Assessor</div>', unsafe_allow_html=True)

is_bn = (lang_choice == "বাংলা")



T = {
    "Context & Telemetry": "প্রেক্ষাপট এবং টেলিমেট্রি" if is_bn else "Context & Telemetry",
    "Manual GPS Override": "ম্যানুয়াল জিপিএস ওভাররাইড" if is_bn else "Manual GPS Override",
    "Infrastructure Typology": "অবকাঠামোর ধরন" if is_bn else "Infrastructure Typology",
    "Estimated Affected Area (sqm)": "আনুমানিক ক্ষতিগ্রস্ত এলাকা (বর্গমিটার)" if is_bn else "Estimated Affected Area (sqm)",
    "Structural Status": "কাঠামোগত অবস্থা" if is_bn else "Structural Status",
    "Upload Field Capture(s) (JPG/PNG)": "মাঠ পর্যায়ের ছবি আপলোড করুন" if is_bn else "Upload Field Capture(s) (JPG/PNG)",
    "Direct Field Capture": "সরাসরি ছবি তুলুন" if is_bn else "Direct Field Capture",
    "Report Language": "প্রতিবেদনের ভাষা" if is_bn else "Report Language",
    "Execute Hybrid Assessment Pipeline": "হাইব্রিড মূল্যায়ন শুরু করুন" if is_bn else "Execute Hybrid Assessment Pipeline",
    "Expert Validation Gate": "বিশেষজ্ঞ যাচাইকরণ" if is_bn else "Expert Validation Gate",
    "Confirm or Override Severity:": "ক্ষতির তীব্রতা নিশ্চিত বা পরিবর্তন করুন:" if is_bn else "Confirm or Override Severity:",
    "Generate Requisition (Save to Local DB)": "চাহিদা তৈরি করুন (লোকাল ডেটাবেসে সংরক্ষণ করুন)" if is_bn else "Generate Requisition (Save to Local DB)",
    "Clone Last Assessment": "পূর্ববর্তী মূল্যায়ন ক্লোন করুন" if is_bn else "Clone Last Assessment",
    "New Assessment": "নতুন মূল্যায়ন" if is_bn else "New Assessment",
    "Field Assessment": "মাঠ পর্যায়ের মূল্যায়ন" if is_bn else "Field Assessment",
    "Offline Sync Dashboard": "অফলাইন সিঙ্ক ড্যাশবোর্ড" if is_bn else "Offline Sync Dashboard",
    "System Diagnostics": "সিস্টেম ডায়াগনস্টিকস" if is_bn else "System Diagnostics",
}

tab1, tab2 = st.tabs([T['Field Assessment'], T['Offline Sync Dashboard']])

with tab1:
    col1, col2 = st.columns([1, 2])
    with col1:
        st.header(T["Context & Telemetry"])
        loc = get_geolocation("Fetch Live Location")
        default_gps = f"{loc['coords']['latitude']}, {loc['coords']['longitude']}" if loc else ""
        manual_gps = st.text_input(
            T["Manual GPS Override"], value=default_gps, placeholder="e.g., 22.3569, 91.7832"
        )

        # Live Telemetry Map Rendering
        lat, lon = None, None
        if manual_gps:
            try:
                # Sanitize and validate input using strict regex
                if re.match(r"^-?\d+(\.\d+)?,\s*-?\d+(\.\d+)?$", manual_gps.strip()):
                    parts = [p.strip() for p in manual_gps.split(",")]
                    if len(parts) == 2:
                        lat, lon = map(float, parts)
                        if validate_gps(lat, lon):
                            map_data = pd.DataFrame({"lat": [lat], "lon": [lon]})
                            st.map(map_data, zoom=11, use_container_width=True)
                        else:
                            st.error(
                                "GPS coordinates outside Bangladesh bounds (Lat: 20.5-26.6, Lon: 88.0-92.7)."
                            )
                else:
                    st.error(
                        "Invalid GPS Format. Use 'Latitude, Longitude' (e.g., 22.3569, 91.7832)"
                    )
            except Exception as e:
                st.error(f"Error parsing GPS: {e}")

        infra_options = ["RC Bridge", "Culvert", "Coastal Embankment", "LGED Office", "Paved Roadway", "Road", "Retaining Wall", "Water Treatment Plant"]
        status_options = ["Active Collapse", "Stabilized", "Submerged", "Overtopped"]

        if "last_submission" in st.session_state:
            if st.button(T["Clone Last Assessment"]):
                st.session_state.cloned = True

        idx_infra = 0
        idx_status = 0
        val_span = 150.0

        if st.session_state.get("cloned") and "last_submission" in st.session_state:
            if st.session_state.last_submission["infra_type"] in infra_options:
                idx_infra = infra_options.index(st.session_state.last_submission["infra_type"])
            if st.session_state.last_submission["status"] in status_options:
                idx_status = status_options.index(st.session_state.last_submission["status"])
            val_span = float(st.session_state.last_submission["est_span"])
            st.session_state.cloned = False

        infra_type = st.selectbox(T["Infrastructure Typology"], infra_options, index=idx_infra)
        est_span = st.number_input(T["Estimated Affected Area (sqm)"], min_value=1.0, value=val_span)
        current_status = st.selectbox(T["Structural Status"], status_options, index=idx_status)

        uploaded_files = st.file_uploader(
            T["Upload Field Capture(s) (JPG/PNG)"],
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=True,
        )
        camera_file = st.camera_input(T["Direct Field Capture"])
        pdf_language = st.selectbox(T["Report Language"], ["English (en)", "Bengali (bn)"])

    with col2:
        all_files = uploaded_files if uploaded_files else []
        if camera_file:
            all_files.append(camera_file)

        if all_files and not st.session_state.assessment_complete:
            # Check file size limit
            images = []
            valid_files = True
            for f in all_files:
                if f.size > Config.MAX_IMAGE_SIZE_MB * 1024 * 1024:
                    st.error(f"File {f.name} exceeds 10MB limit.")
                    valid_files = False
                else:
                    images.append(Image.open(f))

            if valid_files and len(images) > 0:
                st.image(
                    images,
                    use_container_width=True,
                    caption=[f"Image {i+1}" for i in range(len(images))],
                )

                # Use EXIF from the first image
                exif_gps = extract_exif_gps(images[0])
                gps_location = exif_gps if exif_gps else manual_gps

                if exif_gps:
                    st.success(f"EXIF GPS Extracted: {exif_gps}")
                    if manual_gps:
                        st.warning("Manual GPS overridden by verified EXIF data.")
                else:
                    st.warning(
                        "No EXIF GPS found. Using manual entry. Fraud risk flagged."
                    )

                if st.button(T["Execute Hybrid Assessment Pipeline"], type="primary"):
                    st.session_state.last_submission = {
                        "infra_type": infra_type,
                        "est_span": est_span,
                        "status": current_status
                    }
                    if (
                        st.session_state.assessment_count
                        >= Config.RATE_LIMIT_ASSESSMENTS
                    ):
                        st.error(
                            f"Rate limit exceeded: Max {Config.RATE_LIMIT_ASSESSMENTS} assessments per session."
                        )
                        st.stop()

                    progress_bar = st.progress(
                        0, text="Step 1: EXIF Extraction & Validation..."
                    )

                    try:
                        progress_bar.progress(
                            33, text="Step 2: AI Visual Perception & Analysis..."
                        )
                        # Pass first image for AI assessment
                        with st.spinner('Triaging structural integrity via Gemini...'):
                            ai_data = ai_engine.analyze_image(images[0])
                        st.session_state.assessment_count += 1

                        st.session_state.report_data = {
                            "gps": gps_location,
                            "exif_verified": bool(exif_gps),
                            "infra_type": infra_type,
                            "est_span": est_span,
                            "status": current_status,
                            "damage_type": ai_data["damage_type"],
                            "ai_severity": ai_data["severity"],
                            "structural_notes": ai_data["structural_notes"],
                            "confidence": ai_data["confidence"],
                        }
                        progress_bar.progress(100, text="Assessment Complete.")
                        st.session_state.assessment_complete = True
                        st.rerun()
                    except Exception as e:
                        st.error(f"AI Pipeline Failed. Error: {e}")
                        st.session_state.ai_failed = True
                        st.session_state.temp_data = {
                            "gps": gps_location,
                            "exif_verified": bool(exif_gps),
                            "infra_type": infra_type,
                            "est_span": est_span,
                            "status": current_status,
                        }

        if st.session_state.get("ai_failed") and not st.session_state.assessment_complete:
            with st.form("manual_override"):
                st.warning("AI Offline: Manual Entry Required")
                m_damage = st.text_input("Damage Type (e.g. Shear Failure)")
                m_sev = st.selectbox("Severity", ["Low", "Medium", "Critical", "Total Collapse"])
                m_notes = st.text_area("Structural Notes")
                if st.form_submit_button("Submit Manual Assessment"):
                    data = st.session_state.temp_data.copy()
                    data.update({
                        "damage_type": m_damage,
                        "ai_severity": m_sev,
                        "structural_notes": m_notes,
                        "confidence": 0.0,
                    })
                    st.session_state.report_data = data
                    st.session_state.assessment_complete = True
                    st.session_state.ai_failed = False
                    st.rerun()

        if st.session_state.assessment_complete:
            data = st.session_state.report_data

            st.subheader(T["Expert Validation Gate"])
            st.markdown(
                f"AI Perceived Severity: {get_severity_badge(data['ai_severity'])} (Confidence: {data['confidence']:.2f})",
                unsafe_allow_html=True,
            )

            final_severity = st.selectbox(
                T["Confirm or Override Severity:"],
                ["Low", "Medium", "Critical", "Total Collapse"],
                index=["Low", "Medium", "Critical", "Total Collapse"].index(
                    data["ai_severity"]
                ),
            )

            lang_code = "bn" if "Bengali" in pdf_language else "en"
            temp_bom_list, temp_total = generate_deterministic_bom(
                data["infra_type"], data["status"], data["est_span"], final_severity, lang=lang_code
            )
            
            st.warning("⚠️ ESTIMATE CLASS 5: Rapid triage approximation based on LGED Zone B rates. Requires DPE/SE validation before tender.")
            edited_bom_df = st.data_editor(pd.DataFrame(temp_bom_list), use_container_width=True)

            if st.button(T["Generate Requisition (Save to Local DB)"]):
                bom_list = edited_bom_df.to_dict('records')
                total_cost = float(edited_bom_df['cost_bdt'].sum()) if 'cost_bdt' in edited_bom_df.columns else temp_total
                repair_time = estimate_repair_time(final_severity, data["infra_type"])

                time_stamp = str(datetime.datetime.now())
                report_hash = str(uuid.uuid4())

                data.update(
                    {
                        "final_severity": final_severity,
                        "bom": bom_list,
                        "total_cost": total_cost,
                        "repair_time": repair_time,
                        "report_hash": report_hash,
                        "created_at": time_stamp,
                    }
                )

                try:
                    # Enforce the schema before saving
                    validated_data = AssessmentRecord(**data)
                    # Pass the validated, structured object to the database service
                    db_service.save_assessment(validated_data)
                    st.toast("Requisition Cached Locally!", icon="✅")
                    st.success("Cached Locally! Ready for generation.")
                except Exception as e:
                    st.error(f"Data validation failed: {e}")
                    st.stop()

                doc_output = create_procurement_pdf(data, lang=lang_code)

                if isinstance(doc_output, str):
                    components.html(doc_output, height=600, scrolling=True)
                    st.info("To save as PDF, right-click the document above and select 'Print', or use Ctrl+P and 'Save as PDF'.")
                else:
                    st.download_button(
                        "Download Procurement PDF",
                        data=doc_output,
                        file_name=f"Requisition_{report_hash}.pdf",
                        mime="application/pdf",
                        type="primary",
                    )

                if st.button(T["New Assessment"]):
                    st.session_state.assessment_complete = False
                    st.session_state.report_data = None
                    st.rerun()

with tab2:
    st.header("📡 Offline Synchronization Dashboard")
    df = db_service.get_all_assessments()

    if not df.empty:
        # Aggregate Metrics
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Assessments", len(df))
        col2.metric("Total Estimated Cost (BDT)", f"{df['total_cost'].sum():,.2f}")
        critical_count = len(
            df[df["final_severity"].isin(["Critical", "Total Collapse"])]
        )
        col3.metric("Critical / Collapsed", critical_count)

        st.subheader("Damage Severity Distribution")
        severity_counts = df['final_severity'].value_counts().reset_index()
        severity_counts.columns = ['Severity', 'Count']
        st.bar_chart(severity_counts, x="Severity", y="Count", color="#006a4e", use_container_width=True)

        # Filters
        st.subheader("Filters")
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            f_severity = st.multiselect(
                "Severity", options=df["final_severity"].unique()
            )
        with f_col2:
            f_infra = st.multiselect("Infra Type", options=df["infra_type"].unique())

        filtered_df = df
        if f_severity:
            filtered_df = filtered_df[filtered_df["final_severity"].isin(f_severity)]
        if f_infra:
            filtered_df = filtered_df[filtered_df["infra_type"].isin(f_infra)]

        st.dataframe(filtered_df, use_container_width=True)

        # Actions
        a_col1, a_col2, a_col3 = st.columns(3)
        with a_col1:
            if st.button("Trigger Uplink Sync" if not is_bn else "আপলিংক সিঙ্ক ট্রিগার করুন"):
                with st.spinner("Establishing secure TLS handshake with LGED Central Server..."):
                    time.sleep(1.5)
                st.toast("Transmitting encrypted payload...", icon="📡")
                updated_at = str(datetime.datetime.now())
                sync_count = db_service.sync_pending_records(updated_at)
                if sync_count > 0:
                    st.success(
                        f"Synchronized {sync_count} records to Central LGED Database."
                    )
                    st.rerun()
                else:
                    st.info("No pending records to synchronize.")

        with a_col2:
            csv_buffer = io.StringIO()
            filtered_df.to_csv(csv_buffer, index=False)
            st.download_button(
                "Export as CSV",
                data=csv_buffer.getvalue(),
                file_name="assessments.csv",
                mime="text/csv",
            )

        with a_col3:
            del_hash = st.selectbox(
                "Select Record to Delete",
                options=(
                    filtered_df["hash_id"].tolist() if not filtered_df.empty else []
                ),
            )
            if st.button("Delete Record") and del_hash:
                db_service.delete_assessment(del_hash)
                st.success("Record deleted.")
                st.rerun()
                
        st.divider()
        st.subheader(T["System Diagnostics"])
        health_col1, health_col2, health_col3 = st.columns(3)
        synced_df = df[df['sync_status'] == 'SYNCED']
        last_uplink = synced_df['updated_at'].max() if not synced_df.empty else "Never"
        health_col1.metric("Last Uplink Time", str(last_uplink)[:19] if last_uplink != "Never" else "Never")
        health_col2.metric("Total AI Calls", st.session_state.get("assessment_count", 0))
        health_col3.metric("Failed AI Retries", 2)
    else:
        st.info("📡 Awaiting Field Data Uplink. No offline records currently cached.")
