import streamlit as st
import logging
import json
import pandas as pd
from datetime import datetime
from utils.ocr_utils import PdfProcessor
from utils.llm_utils import LLMService
from utils.extraction_utils import DocumentExtractor

# ------------------- Configuration ------------------- #
class AppConfig:
    PAGE_CONFIG = {
        "page_title": "Legal OCR Console - Bates & RO Extraction",
        "page_icon": "⚖️",
        "layout": "wide",
        "initial_sidebar_state": "expanded"
    }
    
    DOCUMENT_TYPES = {
        "PDF": "PDF File (Extracted or Already OCR)",
        "TEXT": "Text File"
    }

# ------------------- Service Manager ------------------- #
class ServiceManager:
    @staticmethod
    def init_service(service_cls, name: str):
        try:
            service = service_cls()
            logging.info(f"{name} initialized successfully.")
            return service
        except Exception as e:
            logging.error(f"Failed to initialize {name}: {str(e)}", exc_info=True)
            st.error(f"Failed to initialize {name} service. Check logs.")
            st.stop()

# ------------------- Session State Manager ------------------- #
class SessionManager:
    @staticmethod
    def initialize():
        defaults = {
            'processing_stage': 1,
            'extraction_complete': False,
            'extraction_results': None,
            'document_type': None,
            'document_bytes': None,
            'document_filename': None
        }
        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value

# ------------------- UI Components ------------------- #
class UIComponents:
    @staticmethod
    def inject_custom_css():
        st.markdown("""
        <style>
                @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
                * { font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }
                .block-container { padding-top: 2rem; padding-bottom: 3rem; max-width: none; width: min(96%, 1600px); margin: 0 auto; }
                .card { background: #ffffff; padding: 30px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.06); margin-bottom: 25px; border: 1px solid #e8eaed; }
                .main-header { text-align: center; padding: 30px 0 20px 0; margin-bottom: 35px; }
                .main-title { font-size: 2.5rem; font-weight: 700; color: #1C2D4A; margin-bottom: 10px; letter-spacing: -0.5px; }
                .main-subtitle { font-size: 1.1rem; color: #5F6C7B; line-height: 1.6; max-width: 900px; margin: 0 auto; font-weight: 400; }
                .step-indicator { display: flex; justify-content: center; align-items: center; margin: 35px 0; padding: 25px; background: #f8f9fa; border-radius: 12px; }
                .step { display: flex; align-items: center; padding: 12px 20px; background: #e8eaed; color: #5F6C7B; border-radius: 8px; font-weight: 500; font-size: 0.95rem; transition: all 0.3s ease; }
                .step.active { background: #1C2D4A; color: white; box-shadow: 0 4px 12px rgba(28, 45, 74, 0.2); }
                .step.complete { background: #DAF5DB; color: #1e7e34; }
                .step-arrow { margin: 0 15px; color: #9ca3af; font-size: 1.2rem; }
                .upload-zone { text-align: center; padding: 50px 30px; background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%); border: 2px dashed #cbd5e0; border-radius: 12px; transition: all 0.3s ease; }
                .upload-zone:hover { border-color: #1C2D4A; background: #ffffff; }
                .success-badge, .info-badge, .file-badge { display: inline-flex; align-items: center; padding: 10px 20px; border-radius: 8px; font-weight: 500; margin: 15px 0; }
                .success-badge { background: #DAF5DB; color: #1e7e34; }
                .info-badge { background: #DDEBFF; color: #004085; }
                .file-badge { background: #DDEBFF; color: #004085; }
                .section-header { font-size: 2.2rem; font-weight: 700; color: #1C2D4A; margin-bottom: 20px; display: flex; align-items: center; }
                .stButton > button { background: linear-gradient(135deg, #1C2D4A 0%, #2d4a6e 100%); color: white; border: none; padding: 15px 30px; font-size: 1.05rem; font-weight: 600; border-radius: 10px; transition: all 0.3s ease; }
                .status-processing { padding: 15px; background: #FFF3CD; border-left: 4px solid #FFC107; border-radius: 6px; margin: 10px 0; font-weight: 500; }
                .status-success { padding: 15px; background: #DAF5DB; border-left: 4px solid #28a745; border-radius: 6px; margin: 10px 0; font-weight: 500; }
                .footer { text-align: center; padding: 30px 0 10px 0; margin-top: 50px; border-top: 1px solid #e8eaed; color: #9ca3af; font-size: 0.9rem; }
        </style>
        """, unsafe_allow_html=True)

    @staticmethod
    def render_header():
        st.markdown("""
            <div class="main-header">
                <div class="main-title">⚖️ Repair Order & Bates Extraction Console</div>
                <div class="main-subtitle">
                    Upload Bates-stamped legal PDFs and automatically extract Repair Orders, Bates Numbers, 
                    and Page Numbers using high-accuracy OCR. Download a structured Excel index ready for 
                    legal briefs, discovery responses, and evidence mapping.
                </div>
            </div>
        """, unsafe_allow_html=True)

    @staticmethod
    def render_step_indicator(current_stage):
        steps = [
            ("📄", "Step 1 — Upload Document", 1),
            ("🔍", "Step 2 — Analyze Document Type", 2),
            ("🧩", "Step 3 — Run Processing Pipeline", 3),
            ("📊", "Step 4 — Export Results & Summary", 4)
        ]
        
        step_html = []
        for i, (icon, label, stage) in enumerate(steps):
            if current_stage > stage:
                css_class = "complete"
            elif current_stage == stage:
                css_class = "active"
            else:
                css_class = ""
                
            step_html.append(f'<div class="step {css_class}"><span style="margin-right: 8px;">{icon}</span>{label}</div>')
            
            # Add arrow between steps (not after the last one)
            if i < len(steps) - 1:
                step_html.append('<div class="step-arrow">→</div>')
        
        st.markdown(f'<div class="step-indicator">{"".join(step_html)}</div>', unsafe_allow_html=True)

    @staticmethod
    def render_footer():
        st.markdown('<div class="footer">Built for Litigation Workflows — Bates Indexing Automation<br></div>', unsafe_allow_html=True)

# ------------------- Section Renderers ------------------- #
class SectionRenderer:
    @staticmethod
    def config_sidebar():
        with st.sidebar:
            st.markdown("### ⚙️ Configuration Panel")
            st.markdown("---")
            st.markdown("**Output Format**")
            output_format = st.radio("Select export format:", ("Excel", "CSV"), help="Choose how you want to download the extracted data")
            st.markdown("---")
            
        return output_format

    @staticmethod
    def render_upload_section():
        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<div class="section-header"><span class="section-icon">📁</span>Document Upload</div>', unsafe_allow_html=True)
            
            content_col, help_col = st.columns([1.35, 0.65], gap="medium")
            with content_col:
                document_type = st.selectbox(
                    "Select Document Type:",
                    list(AppConfig.DOCUMENT_TYPES.values()),
                    index=0,
                    help="Select whether you're uploading a PDF file or a plain text file",
                    label_visibility="collapsed"
                )
                
                st.session_state.document_type = document_type
                
                is_pdf = document_type == AppConfig.DOCUMENT_TYPES["PDF"]
                accepted_types = ["pdf"] if is_pdf else ["txt"]
                file_type_label = "PDF" if is_pdf else "Text"
                recommendation = "✨ Recommended: Bates-stamped court-ready PDF documents" if is_pdf else "✨ Upload a plain text file (.txt) containing document content"
                
                st.markdown("<br>", unsafe_allow_html=True)
                uploaded_file = st.file_uploader(f"Upload {file_type_label} File", type=accepted_types, help=recommendation, key="file_uploader")
                
            with help_col:
                st.markdown("""
                    <div style="background: #F8FAFF; border: 1px solid #E1E7EF; border-radius: 10px; padding: 15px; height: 100%;">
                        <p style="margin-bottom: 6px; font-weight: 600; color: #1C2D4A;">Upload Tips</p>
                        <ul style="margin: 0; padding-left: 18px; color: #5F6C7B;">
                            <li>Use a Bates-stamped PDF for optimal extraction.</li>
                            <li>Ensure the document is landscape for consistent page numbers.</li>
                            <li>Text uploads should be UTF-8 encoded and named with the Bates range.</li>
                            <li>Select “CSV” if you plan to ingest into spreadsheets quickly.</li>
                        </ul>
                    </div>
                """, unsafe_allow_html=True)
            
            if uploaded_file:
                logging.info(f"File uploaded: {uploaded_file.name}, type: {file_type_label}")
                file_size_mb = uploaded_file.size / (1024 * 1024)
                
                st.markdown(f"""
                    <div class="success-badge">✅ {file_type_label} File Uploaded Successfully</div>
                    <div class="file-badge">📄 {uploaded_file.name} — {file_size_mb:.2f} MB</div>
                """, unsafe_allow_html=True)
                
                # Check if this is a new file or document type change - clear old state if so
                is_new_file = ('document_bytes' not in st.session_state or 
                              st.session_state.get('document_filename') != uploaded_file.name)
                is_document_type_change = (st.session_state.get('document_type') != document_type)
                
                if is_new_file or is_document_type_change:
                    # Clear previous extraction results and processing state
                    st.session_state.extraction_results = None
                    st.session_state.extraction_complete = False
                    st.session_state.processing_stage = 1
                    
                    logging.info(f"Cleared previous session state. Reason: {'New file' if is_new_file else 'Document type changed'}")
                
                # Store new file
                uploaded_file.seek(0)
                st.session_state.document_bytes = uploaded_file.read()
                st.session_state.document_filename = uploaded_file.name
                
                logging.info(f"Stored {uploaded_file.name} in session_state with document type: {document_type}")
                
                st.markdown('</div>', unsafe_allow_html=True)
                return True
            
            st.markdown('</div>', unsafe_allow_html=True)
            return False

    @staticmethod
    def render_processing_section():
        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<div class="section-header"><span class="section-icon">🚀</span>Processing Engine</div>', unsafe_allow_html=True)
            
            st.markdown("""
                <p style="color: #5F6C7B; margin-bottom: 20px;">
                    Click the button below to start the Processing engine. The system will automatically identify the document type,
                    run a custom processing pipeline for that document, extract Ba  tes Numbers and Repair Order Numbers,
                    and then prepare an indexed sheet in the output format selected in the configuration panel on the left.
                </p>
            """, unsafe_allow_html=True)
            
            process_clicked = st.button("🚀 Process Document", width="stretch", type="primary")
            st.markdown('</div>', unsafe_allow_html=True)
            return process_clicked

    @staticmethod
    def render_quick_tips_panel():
        stage = st.session_state.get('processing_stage', 1)
        stage_descriptions = {
            1: "Waiting for your document",
            2: "Identifying document type",
            3: "Running the processing pipeline",
            4: "Extraction complete — ready to export"
        }
        stage_label = stage_descriptions.get(stage, "Ready")
        selected_type = st.session_state.get('document_type') or "Not selected yet"

        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<div class="section-header"><span class="section-icon">💡</span>Workflow Tips</div>', unsafe_allow_html=True)
            st.markdown(f"""
                <div style="padding: 12px; background: #F1F5FF; border-radius: 10px; border: 1px dashed #CDD7E5; margin-bottom: 12px;">
                    <strong style="color: #1C2D4A;">Current Stage:</strong> {stage_label}<br>
                    <small style="color: #5F6C7B;">Document Type: <strong>{selected_type}</strong></small>
                </div>
                <p style="color: #5F6C7B; margin-bottom: 12px;">Follow these quick reminders to maximize accuracy:</p>
                <ul style="padding-left: 20px; color: #5F6C7B; margin-top: 0;">
                    <li>PDFs are preferred for page-level OCR; keep scans straight and high contrast.</li>
                    <li>Upload the entire Bates range so Repair Orders align with the right pages.</li>
                    <li>Choose Excel when you need formulas preserved, CSV for lightweight sharing.</li>
                    <li>Use the search panel below to verify specific Bates or Repair Order numbers before exporting.</li>
                </ul>
            """, unsafe_allow_html=True)

            if st.session_state.extraction_complete:
                st.markdown("""
                    <div style="padding: 12px; background: #DAF5DB; border-left: 4px solid #28a745; border-radius: 8px; margin-top: 12px;">
                        ✅ Extraction captured — move to the download panel to get your index.
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                    <div style="padding: 12px; background: #FFF3CD; border-left: 4px solid #FFC107; border-radius: 8px; margin-top: 12px;">
                        ⏳ Click “Process Document” when you’re ready. The system will auto-detect page types and start OCR work.
                    </div>
                """, unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)

    @staticmethod
    def render_extraction_summary():
        if not st.session_state.extraction_complete or not st.session_state.extraction_results:
            return

        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<div class="section-header"><span class="section-icon">📊</span>Extraction Summary</div>', unsafe_allow_html=True)
            
            results = st.session_state.extraction_results
            responses = results.get("responses", [])
            total_pages = results.get("total_pages", 0)
            
            repair_orders_found = sum(1 for row in responses if str(row.get("repair_order_number", "")).strip())
            bates_numbers = {row.get("bate_number") for row in responses if row.get("bate_number")}
            bates_found = len(bates_numbers)
            pages_with_issues = results.get("pages_with_issues", [])
            
            metrics = [
                ("📄 Total Pages Processed", f"{total_pages:,}"),
                ("🔧 Repair Orders Extracted", f"{repair_orders_found:,}"),
                ("📋 Bates Numbers Found", f"{bates_found:,}")
            ]
            
            for i in range(0, len(metrics), 3):
                cols = st.columns(3)
                for col, (label, value) in zip(cols, metrics[i:i+3]):
                    with col:
                        st.metric(label, value)
            
            # Display pages with issues
            st.markdown("<br>", unsafe_allow_html=True)
            if pages_with_issues:
                st.markdown("### ⚠️ Pages with Issues")
                st.markdown("""
                    <p style="color: #5F6C7B; margin-bottom: 15px;">
                        The following pages had issues during processing (no Bate number found or multiple Bate numbers detected):
                    </p>
                """, unsafe_allow_html=True)
                
                # Display pages in a nice format
                if len(pages_with_issues) <= 20:
                    # Show all pages if 20 or fewer
                    pages_str = ", ".join([f"Page {page}" for page in sorted(pages_with_issues)])
                    st.markdown(f"""
                        <div style="padding: 15px; background: #FFF3CD; border-left: 4px solid #FFC107; border-radius: 6px; margin: 10px 0;">
                            <strong>Affected Pages:</strong> {pages_str}
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    # Show first 20 and count for larger lists
                    first_20 = sorted(pages_with_issues)[:20]
                    pages_str = ", ".join([f"Page {page}" for page in first_20])
                    st.markdown(f"""
                        <div style="padding: 15px; background: #FFF3CD; border-left: 4px solid #FFC107; border-radius: 6px; margin: 10px 0;">
                            <strong>Affected Pages (showing first 20 of {len(pages_with_issues)}):</strong> {pages_str}...
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Show full list in expander
                    with st.expander(f"📋 View All {len(pages_with_issues)} Pages with Issues"):
                        pages_list = sorted(pages_with_issues)
                        # Display in columns for better readability
                        num_cols = 5
                        for i in range(0, len(pages_list), num_cols):
                            cols = st.columns(num_cols)
                            for j, col in enumerate(cols):
                                if i + j < len(pages_list):
                                    with col:
                                        st.markdown(f"**Page {pages_list[i + j]}**")
            
            st.markdown('</div>', unsafe_allow_html=True)

    @staticmethod
    def render_download_section():
        if not st.session_state.extraction_complete or not st.session_state.extraction_results:
            return

        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<div class="section-header"><span class="section-icon">⬇️</span> Download Results</div>', unsafe_allow_html=True)
            
            results = st.session_state.extraction_results
            export_bytes = results.get("export_bytes", b"")
            export_format = results.get("export_format", "Excel")
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            if export_format == "CSV":
                index_filename = f"extraction_results_{timestamp}.csv"
                index_mime = "text/csv"
            else:
                index_filename = f"extraction_results_{timestamp}.xlsx"
                index_mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.download_button(
                    label="📊 Download Index Sheet",
                    data=export_bytes,
                    file_name=index_filename,
                    mime=index_mime,
                    width="stretch"
                )
            
            with col2:
                json_data = json.dumps(results['responses'], indent=2)
                st.download_button(
                    label="📄 Download Raw JSON",
                    data=json_data,
                    file_name=f"extraction_raw_{timestamp}.json",
                    mime="application/json",
                    width="stretch"
                )
            
            # Display pages with issues information
            st.markdown("<br>", unsafe_allow_html=True)
            pages_with_issues = results.get("pages_with_issues", [])
            
            with st.expander("⚠️ Pages with Issues", expanded=True):
                if pages_with_issues:
                    st.markdown("""
                        <p style="color: #5F6C7B; margin-bottom: 15px;">
                            The following pages had issues during processing (no Bate number found or multiple Bate numbers detected):
                        </p>
                    """, unsafe_allow_html=True)
                    
                    # Display pages in a nice format
                    if len(pages_with_issues) <= 30:
                        # Show all pages if 30 or fewer
                        pages_list = sorted(pages_with_issues)
                        # Display in columns for better readability
                        num_cols = 5
                        for i in range(0, len(pages_list), num_cols):
                            cols = st.columns(num_cols)
                            for j, col in enumerate(cols):
                                if i + j < len(pages_list):
                                    with col:
                                        st.markdown(f"**Page {pages_list[i + j]}**")
                    else:
                        # Show first 30 and count for larger lists
                        pages_list = sorted(pages_with_issues)
                        first_30 = pages_list[:30]
                        num_cols = 5
                        for i in range(0, len(first_30), num_cols):
                            cols = st.columns(num_cols)
                            for j, col in enumerate(cols):
                                if i + j < len(first_30):
                                    with col:
                                        st.markdown(f"**Page {first_30[i + j]}**")
                        
                        st.markdown(f"<br><strong>... and {len(pages_list) - 30} more pages</strong>", unsafe_allow_html=True)
                        st.markdown(f"<p style='color: #5F6C7B;'>Total pages with issues: {len(pages_list)}</p>", unsafe_allow_html=True)
                else:
                    st.markdown("""
                        <div style="padding: 15px; background: #DAF5DB; border-left: 4px solid #28a745; border-radius: 6px; margin: 10px 0;">
                            <strong>✅ No Issues Detected:</strong> All pages were processed successfully with valid Bate numbers.
                        </div>
                    """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)

    @staticmethod
    def render_data_viewer_section():
        if not st.session_state.extraction_complete or not st.session_state.extraction_results:
            return

        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<div class="section-header"><span class="section-icon">🔍</span> Data Viewer & Search</div>', unsafe_allow_html=True)
            
            results = st.session_state.extraction_results
            responses = results.get("responses", [])
            
            if not responses:
                st.warning("No data available to display.")
                st.markdown('</div>', unsafe_allow_html=True)
                return
            
            # Convert responses to DataFrame
            df = pd.DataFrame(responses)
            
            # Add search controls
            st.markdown("""
                <p style="color: #5F6C7B; margin-bottom: 20px;">
                    Use the search controls below to find and highlight specific records in your extracted data.
                </p>
            """, unsafe_allow_html=True)
            
            # Create two columns for search type and search input
            col1, col2 = st.columns([1, 2])
            
            with col1:
                search_type = st.selectbox(
                    "Search By:",
                    ["Bate Number", "Repair Order Number"],
                    help="Select the field you want to search",
                    key="search_type_selector"
                )
            
            with col2:
                if search_type == "Bate Number":
                    placeholder_text = "Enter Bate Number (e.g., AARON0001302)"
                    search_icon = "🏷️"
                    column_to_search = "bate_number"
                else:
                    placeholder_text = "Enter Repair Order Number (e.g., 12345)"
                    search_icon = "🔧"
                    column_to_search = "repair_order_number"
                
                search_term = st.text_input(
                    f"{search_icon} Search {search_type}:",
                    placeholder=placeholder_text,
                    help=f"Enter a {search_type} to highlight all matching rows",
                    key="search_input",
                    label_visibility="collapsed"
                )
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Display dataframe with highlighting (Exact match search)
            if search_term and search_term.strip():
                search_value = search_term.strip().upper()
                
                # Check if the column exists
                if column_to_search in df.columns:
                    # Create a mask for exact matching rows (case-insensitive)
                    mask = df[column_to_search].astype(str).str.upper() == search_value
                    
                    matching_count = mask.sum()
                    
                    if matching_count > 0:
                        # Show success message
                        st.success(f"✅ Found {matching_count} row(s) matching '{search_term}'")
                        
                        # Apply styling to highlight matching rows
                        def highlight_rows(row):
                            row_value = str(row[column_to_search]).upper()
                            
                            if row_value == search_value:
                                return ['background-color: #FFF3CD; font-weight: bold'] * len(row)
                            return [''] * len(row)
                        
                        styled_df = df.style.apply(highlight_rows, axis=1)
                        st.dataframe(styled_df, width="stretch", height=450)
                        
                    else:
                        st.warning(f"⚠️ No rows found matching '{search_term}'")
                        st.dataframe(df, width="stretch", height=450)
                else:
                    st.error(f"❌ Column '{column_to_search}' not found in the data.")
                    st.dataframe(df, width="stretch", height=450)
            else:
                # Display full dataframe without highlighting
                st.info(f"💡 Enter a {search_type} above to search and highlight matching rows.")
                st.dataframe(df, width="stretch", height=450)
            
            # Display statistics
            col_stat1, col_stat2, col_stat3 = st.columns(3)
            
            with col_stat1:
                st.markdown(f"""
                    <div style="padding: 12px; background: #DDEBFF; border-radius: 8px; text-align: center;">
                        <div style="font-size: 0.85rem; color: #5F6C7B; margin-bottom: 4px;">Total Rows</div>
                        <div style="font-size: 1.5rem; font-weight: 700; color: #1C2D4A;">{len(df)}</div>
                    </div>
                """, unsafe_allow_html=True)
            
            with col_stat2:
                unique_bates = df['bate_number'].nunique() if 'bate_number' in df.columns else 0
                st.markdown(f"""
                    <div style="padding: 12px; background: #DAF5DB; border-radius: 8px; text-align: center;">
                        <div style="font-size: 0.85rem; color: #5F6C7B; margin-bottom: 4px;">Unique Bates</div>
                        <div style="font-size: 1.5rem; font-weight: 700; color: #1C2D4A;">{unique_bates}</div>
                    </div>
                """, unsafe_allow_html=True)
            
            with col_stat3:
                unique_ros = df['repair_order_number'].nunique() if 'repair_order_number' in df.columns else 0
                st.markdown(f"""
                    <div style="padding: 12px; background: #FFF3CD; border-radius: 8px; text-align: center;">
                        <div style="font-size: 0.85rem; color: #5F6C7B; margin-bottom: 4px;">Unique ROs</div>
                        <div style="font-size: 1.5rem; font-weight: 700; color: #1C2D4A;">{unique_ros}</div>
                    </div>
                """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)

# ------------------- Processing Logic ------------------- #
class DocumentProcessor:
    def __init__(self, extraction_service, output_format):
        self.extraction_service = extraction_service
        self.output_format = output_format

    def process_pdf(self, pdf_bytes):
        try:
            st.markdown('<div class="status-processing">🔄 Analyzing the document type</div>', unsafe_allow_html=True)
            
            extracted_res = self.extraction_service.is_text_based_pdf(pdf_bytes)
            bate_dict, pages_with_issues = self.extraction_service.process_structured_ocr_pdf(extracted_res)
            
            if not bate_dict:
                logging.error("Processing returned no response dictionary.")
                st.error("❌ Processing failed. Please try again.", icon="❌")
                return None

            logging.info("Processing completed successfully.")
            st.markdown('<div class="status-success">✅ Processing complete!</div>', unsafe_allow_html=True)

            formatted_data, export_bytes = self.extraction_service.format_data_for_excel_or_csv(
                bate_dict, self.output_format
            )

            total_pages = extracted_res.get("Total pages", 0)
            st.session_state.extraction_results = {
                "total_pages": total_pages,
                "num_chunks": 1,
                "responses": formatted_data,
                "pages_with_issues": pages_with_issues,
                "export_bytes": export_bytes,
                "export_format": self.output_format,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            st.session_state.extraction_complete = True
            st.session_state.processing_stage = 4

            return formatted_data

        except Exception as e:
            logging.error(f"Error processing PDF: {str(e)}", exc_info=True)
            st.error(f"❌ Error processing PDF: {str(e)}", icon="❌")
            return None

    def process_text(self, text_bytes, file_name):
        try:
            st.markdown('<div class="status-processing">🔄 Processing text file...</div>', unsafe_allow_html=True)
            
            # Decode text bytes to string
            text_content = text_bytes.decode('utf-8')

            # Calling the function to get all the repair order names
            repair_orders = self.extraction_service.processing_txt_file(text_content)
            if len(repair_orders) == 0:
                logging.error("No repair orders found in the text file.")
                st.error("❌ No repair orders found in the text file.", icon="❌")
                return None
            
            # Extract Bates numbers from the document name
            logging.info(f"Extracting the bate number from the file name {file_name}")
            bate_numbers = self.extraction_service.extract_aaron_code(file_name, is_filename=True)
            if len(bate_numbers) == 0:
                logging.error(f"No Bates numbers found in the document name: {file_name}")
                st.error("❌ No Bates numbers found in the document name.", icon="❌")
                return None
            logging.info(f"Text processing: Found {len(bate_numbers)} Bates numbers, {len(repair_orders)} repair orders")
            st.markdown('<div class="status-success">✅ Processing complete!</div>', unsafe_allow_html=True)

            # Preparing the base dict where there will be single bate number and the repair order numbers and the page to be None
            bate_dict = {1: {}}
            bate_dict[1][bate_numbers[0]] = repair_orders
            pages_with_issues = []

            # Format data for export
            formatted_data, export_bytes = self.extraction_service.format_data_for_excel_or_csv(
                bate_dict, self.output_format
            )

            # Store results in session state
            st.session_state.extraction_results = {
                "total_pages": 1,  # Text files are treated as single page
                "num_chunks": 1,
                "responses": formatted_data,
                "pages_with_issues": pages_with_issues,
                "export_bytes": export_bytes,
                "export_format": self.output_format,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            st.session_state.extraction_complete = True
            st.session_state.processing_stage = 4

            return formatted_data

        except Exception as e:
            logging.error(f"Error processing text file: {str(e)}", exc_info=True)
            st.error(f"❌ Error processing text file: {str(e)}", icon="❌")
            return None

# ------------------- Main Application ------------------- #
def main():
    # Initialization
    logging.basicConfig(level=logging.INFO)
    st.set_page_config(**AppConfig.PAGE_CONFIG)
    
    UIComponents.inject_custom_css()
    SessionManager.initialize()
    
    # Service initialization
    pdf_service = ServiceManager.init_service(PdfProcessor, "PdfProcessor")
    llm_service = ServiceManager.init_service(LLMService, "LLMService")
    extraction_service = ServiceManager.init_service(DocumentExtractor, "DocumentExtractor")
    
    # Sidebar configuration
    output_format = SectionRenderer.config_sidebar()
    
    # Main UI
    UIComponents.render_header()
    UIComponents.render_step_indicator(st.session_state.processing_stage)
    
    document_uploaded = False
    process_clicked = False
    with st.container():
        left_col, right_col = st.columns([2.4, 1], gap="large")
        with left_col:
            document_uploaded = SectionRenderer.render_upload_section()
            process_clicked = SectionRenderer.render_processing_section()
        with right_col:
            SectionRenderer.render_quick_tips_panel()

    # Processing logic
    if document_uploaded:
        st.session_state.processing_stage = max(st.session_state.processing_stage, 1)
        
        if process_clicked and 'document_bytes' in st.session_state and st.session_state.document_bytes:
            logging.info("User pressed process button. Starting processing pipeline...")
            st.session_state.processing_stage = 2
            
            # Determine document type and process accordingly
            document_type = st.session_state.get('document_type')
            document_bytes = st.session_state.document_bytes
            
            processor = DocumentProcessor(extraction_service, output_format)
            
            # Process based on document type
            if document_type == AppConfig.DOCUMENT_TYPES["PDF"]:
                formatted_data = processor.process_pdf(document_bytes)
            elif document_type == AppConfig.DOCUMENT_TYPES["TEXT"]:
                document_filename = st.session_state.get('document_filename', '')
                formatted_data = processor.process_text(document_bytes, document_filename)
            else:
                st.error("❌ Unknown document type. Please select a valid document type.")
                formatted_data = None
            
            if formatted_data:
                logging.info("Successfully processed document.")
    
    # Results sections
    if st.session_state.extraction_complete:
        with st.container():
            summary_col, download_col = st.columns([2.1, 1], gap="large")
            with summary_col:
                SectionRenderer.render_extraction_summary()
            with download_col:
                SectionRenderer.render_download_section()

        SectionRenderer.render_data_viewer_section()
    
    # Footer
    UIComponents.render_footer()

if __name__ == "__main__":
    main()