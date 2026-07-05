"""
app.py
Production-Grade Offline-First Architecture for LGED Cyclone Assessor
"""

import streamlit as st
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
importlib.reload(persistence.database)
from persistence.database import DatabaseService
from services.ai_engine import AIEngine
from services.pdf_generator import create_procurement_pdf
from lged_knowledge import generate_deterministic_bom, estimate_repair_time
from models import AssessmentRecord

# Configuration and Initialization
st.set_page_config(page_title="Infrastructure Assessor", page_icon="🏗️", layout="wide")

# Custom CSS for LGED Branding and Badges
st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stApp { background-color: #0e1117; }
    div[data-testid="stVerticalBlock"] > div[style*="flex-direction: column;"] {
        background-color: #1f2937;
        border-radius: 8px;
        padding: 1rem;
    }
    .lged-header { color: #006a4e; font-weight: bold; } /* Bangladesh Green */
    .severity-badge {
        padding: 5px 10px; border-radius: 5px; color: white; font-weight: bold;
    }
    .badge-Low { background-color: #28a745; }
    .badge-Medium { background-color: #ffc107; color: black; }
    .badge-Critical { background-color: #fd7e14; }
    .badge-Total { background-color: #dc3545; }
    </style>
""",
    unsafe_allow_html=True,
)

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
    st.title("🔒 Login Required")
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
def get_decimal_from_dms(dms, ref):
    try:
        dec = float(dms[0]) + (float(dms[1]) / 60.0) + (float(dms[2]) / 3600.0)
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
        for tag_id, value in exif.items():
            tag = ExifTags.TAGS.get(tag_id, tag_id)
            if tag == "GPSInfo":
                gps_data = {ExifTags.GPSTAGS.get(t, t): value[t] for t in value}
                lat = get_decimal_from_dms(
                    gps_data.get("GPSLatitude"), gps_data.get("GPSLatitudeRef")
                )
                lon = get_decimal_from_dms(
                    gps_data.get("GPSLongitude"), gps_data.get("GPSLongitudeRef")
                )
                if lat and lon:
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
st.markdown(
    '<h1 class="lged-header">🏗️ LGED Post-Cyclone Infrastructure Assessor</h1>',
    unsafe_allow_html=True,
)

tab1, tab2 = st.tabs(["📸 Field Assessment", "📡 Offline Sync Dashboard"])

with tab1:
    col1, col2 = st.columns([1, 2])
    with col1:
        st.header("Context & Telemetry")
        loc = get_geolocation("Fetch Live Location")
        default_gps = f"{loc['coords']['latitude']}, {loc['coords']['longitude']}" if loc else ""
        manual_gps = st.text_input(
            "Manual GPS Override", value=default_gps, placeholder="e.g., 22.3569, 91.7832"
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

        infra_type = st.selectbox(
            "Infrastructure Typology",
            [
                "RC Bridge",
                "Culvert",
                "Coastal Embankment",
                "LGED Office",
                "Paved Roadway",
                "Road",
                "Retaining Wall",
                "Water Treatment Plant",
            ],
        )
        est_span = st.number_input(
            "Estimated Affected Area (sqm)", min_value=1, value=150
        )
        current_status = st.selectbox(
            "Structural Status",
            ["Active Collapse", "Stabilized", "Submerged", "Overtopped"],
        )
        uploaded_files = st.file_uploader(
            "Upload Field Capture(s) (JPG/PNG)",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=True,
        )
        camera_file = st.camera_input("Direct Field Capture")
        pdf_language = st.selectbox("Report Language", ["English (en)", "Bengali (bn)"])

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

                if st.button("Execute Hybrid Assessment Pipeline", type="primary"):
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

            st.subheader("Expert Validation Gate")
            st.markdown(
                f"AI Perceived Severity: {get_severity_badge(data['ai_severity'])} (Confidence: {data['confidence']:.2f})",
                unsafe_allow_html=True,
            )

            final_severity = st.selectbox(
                "Confirm or Override Severity:",
                ["Low", "Medium", "Critical", "Total Collapse"],
                index=["Low", "Medium", "Critical", "Total Collapse"].index(
                    data["ai_severity"]
                ),
            )

            if st.button("Generate Requisition (Save to Local DB)"):
                bom_list, total_cost = generate_deterministic_bom(
                    data["infra_type"], data["status"], data["est_span"], final_severity
                )
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

                # Display Editable BOM Dataframe
                st.dataframe(pd.DataFrame(bom_list), use_container_width=True)

                lang_code = "bn" if "Bengali" in pdf_language else "en"
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

                if st.button("New Assessment"):
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
            if st.button("Trigger Uplink Sync"):
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
    else:
        st.info("📡 Awaiting Field Data Uplink. No offline records currently cached.")
