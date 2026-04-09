import streamlit as st
import csv
import io
import re
from fpdf import FPDF

st.set_page_config(page_title="INO Games Test Cases QA Tracker", layout="wide")
st.title("🎰 INO Games Test Cases QA Tracker")
st.markdown('<a href="#bottom-of-page" class="scroll-btn" target="_self">⏬</a>', unsafe_allow_html=True)

# --- CUSTOM CSS ---
st.markdown("""
    <style>
            
    .stApp {
        background-color: #1E1E1E;
    }
            
    div[data-testid="stFormSubmitButton"] {
        position: fixed;
        bottom: 20px;
        right: 30px;
        width: fit-content;
        z-index: 9999; 
        opacity: 0.9;
    }
    
    div[data-testid="column"]:nth-child(1) div[data-testid="stDownloadButton"] {
        position: fixed;
        bottom: 40px;
        right: 500px; 
        width: fit-content;
        z-index: 9999; 
    }

    div[data-testid="column"]:nth-child(2) div[data-testid="stDownloadButton"] {
        position: fixed;
        bottom: 40px;
        right: 150px;
        width: fit-content;
        z-index: 9999; 
    }
            
    //div[data-testid="stDownloadButton"] {
        position: fixed;
        bottom: 20px;
        right: 210px;
        width: fit-content;
        z-index: 9999; 
        opacity: 0.9;
        
    }

    div[data-testid="stFormSubmitButton"] button, 
    div[data-testid="stDownloadButton"] button {
        width: auto; 
        box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.5);
        border-radius: 30px;
        padding: 10px 24px;
        font-weight: bold;
        opacity: 0.9;
    }
            
    h3 {
        font-size: 24px !important;
        font-weight: 700;
        margin-bottom: -10px;
    }
            
    a.scroll-btn {
    position: fixed;
    width: fit-content;
    bottom: 21px; 
    right: 210px;
    z-index: 9999;
    background-color: #262730;
    color: #FAFAFA !important;
    border: 2px solid rgba(250, 250, 250, 0.2);
    box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.5);
    border-radius: 30px;
    padding: 8px 24px;
    font-weight: 600;
    text-decoration: none; 
    font-family: "Source Sans Pro", sans-serif;
    opacity: 0.9;       
    }
            
    a.scroll-btn:hover {
        border-color: #FF4B4B;
        color: #FF4B4B !important;
    }
      
    </style>
""", unsafe_allow_html=True)
# ---------------------------------------

uploaded_file = st.file_uploader("📂 Test case CSV aqui", type=['csv'])


if uploaded_file is not None:

    csv_text = uploaded_file.getvalue().decode('utf-8').splitlines()
    reader = csv.DictReader(csv_text)
    headers = reader.fieldnames
    data = []
    for row in reader:
        # Grab the topic, convert to string, and strip away any accidental spaces
        topic_val = str(row.get('Topic', '')).strip()
        
        # Only add the row if the topic actually has text in it AND isn't "none"
        if topic_val == "" or topic_val.lower() == "none":
            row['Topic'] = "General"
        else:
            row['Topic'] = topic_val

        data.append(row)

    with st.form("qa_test_form"):
        updated_data = []

        for index, row in enumerate(data):

            test_id = row.get('Title')
            severity = row.get('Severity')
            run_info = row.get('Run')
            st.markdown(f"### <span style='font-size: 25px; color: #b48ff0;'>{run_info}</span> | {test_id} `[{severity}]`", 
    unsafe_allow_html=True)


            
            test_topic = str(row.get('Topic', 'General')).strip()
            
            
            with st.expander(f"🔍 {test_topic}"):
  
                raw_steps = str(row.get('Step by Step', 'No steps listed.'))
                raw_expected = str(row.get('Expected Result', 'No expected result listed.'))
                

                def format_text(text):
                    text = re.sub(r'([\.!?])([A-Z])', r'\1\n\n\2', text)
                    text = re.sub(r'([a-z])([A-Z][a-z])', r'\1\n\n\2', text)
                    text = re.sub(r'([A-Z])([A-Z][a-z])', r'\1\n\n\2', text)
                    text = re.sub(r'\s*(\d+[\.\)\-]|-\s)', r'\n\n\1', text)
                    text = re.sub(r'\n{3,}', r'\n\n', text)
                    return text.strip()

                steps = format_text(raw_steps)
                expected = format_text(raw_expected)

                st.markdown("**Step by Step:**")
                st.info(steps) 
                
                st.markdown("**Expected Result:**")
                st.success(expected)


            col1, col2 = st.columns([1, 2])

            with col1:
                status_options = ["Incomplete", "Pass", "Failed"]
                current_status = row.get('Status', 'Incomplete')
                default_idx = status_options.index(current_status) if current_status in status_options else 0
                
                new_status = st.radio(
                    "Status", 
                    options=status_options, 
                    key=f"status_{index}", 
                    index=default_idx,
                    horizontal=True
                )

            with col2:
                new_comment = st.text_area(
                    "Commentary", 
                    value=str(row.get('Comments', '')), 
                    key=f"comment_{index}",
                    height=100
                )

            st.divider()

            updated_row = row.copy()
            updated_row['Status'] = new_status
            updated_row['Comments'] = new_comment
            updated_data.append(updated_row)

        submitted = st.form_submit_button("💾 Save Test Run", type="primary")

        if submitted:
            # 1. Define the 'Clean' order for Google Sheets
            clean_header_order = ['Run', 'Title', 'Topic', 'Severity', 'Status', 'Step by Step', 'Expected Result', 'Comments']
            
            clean_output_data = []
            
            # --- NEW: Counters for the Report ---
            total_tests = len(updated_data)
            passed = 0
            failed = 0
            incomplete = 0
            # ------------------------------------

            for row in updated_data:
                # --- NEW: Tally up the statuses ---
                current_status = row.get('Status', 'Incomplete')
                if "Pass" in current_status:
                    passed += 1
                elif "Failed" in current_status:
                    failed += 1
                else:
                    incomplete += 1
                # ----------------------------------

                clean_row = {}
                for header in clean_header_order:
                    val = row.get(header, "")
                    if header in ['Step by Step', 'Expected Result']:
                        val = format_text(str(val))
                    clean_row[header] = val
                clean_output_data.append(clean_row)

            # 2. Save to memory
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=clean_header_order)
            writer.writeheader()
            writer.writerows(clean_output_data)
            
            st.session_state['download_ready'] = output.getvalue()
            
            # --- NEW: Display the Mini-Report ---
            st.divider() # Draws a nice line to separate the report
            st.markdown("### 📊 Run Completion Report")
            
            # Calculate Percentage
            completed = passed + failed
            completion_pct = (completed / total_tests) * 100 if total_tests > 0 else 0
            
            # Create 4 columns for a neat dashboard row
            r_col1, r_col2, r_col3, r_col4 = st.columns(4)
            r_col1.metric("Total Completion", f"{completion_pct:.1f}%")
            r_col2.metric("🟢 Passed", passed)
            r_col3.metric("🔴 Failed", failed)
            r_col4.metric("🟡 Incomplete", incomplete)
            # ------------------------------------
            
        # --- NEW: GENERATE THE PDF REPORT ---
            # 1. Setup the PDF document
            pdf = FPDF()
            pdf.add_page()
            
            # 2. Add the Title and Overall Stats
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 10, f"QA Run Report - {completion_pct:.1f}% Complete", ln=True, align="C")
            pdf.ln(5) # Add a small blank line
            
            pdf.set_font("Arial", '', 12)
            pdf.cell(0, 8, f"Passed: {passed} | Failed: {failed} | Incomplete: {incomplete}", ln=True, align="C")
            pdf.ln(10)
            
            # 3. Create the Table Headers
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(145, 10, "Test Title", border=1)
            pdf.cell(45, 10, "Status", border=1, ln=True, align="C")

            def rank_status(row):
                status_text = str(row.get('Status', ''))    
                if "Failed" in status_text:
                    return 1
                elif "Incomplete" in status_text:
                    return 2
                elif "Pass" in status_text:
                    return 3
                else:
                    return 4
                
            sorted_pdf_data = sorted(updated_data, key=rank_status)
                        
            # 4. Loop through the data and add rows
            pdf.set_font("Arial", '', 11)
            for row in sorted_pdf_data:
                # Get the raw text
                raw_title = str(row.get('Title', 'Untitled'))
                raw_status = str(row.get('Status', 'Incomplete'))
                raw_comment = str(row.get('Comments', '')).strip()
                
                # PDF fonts crash if they see Emojis, so we strip out our colored dots!
                clean_status = raw_status.replace("🟡 ", "").replace("🟢 ", "").replace("🔴 ", "")
                
                # If a title is super long, chop it off so it doesn't break the PDF table box
                clean_title = (raw_title[:75] + '...') if len(raw_title) > 75 else raw_title
                
                # Add the row to the PDF
                pdf.set_font("Arial", 'B', 11)
                pdf.cell(145, 10, clean_title, border=1)

                if "Failed" in clean_status:
                    pdf.set_fill_color(255, 200, 200)  
                elif "Pass" in clean_status:
                    pdf.set_fill_color(200, 255, 200)  
                else:
                    pdf.set_fill_color(255, 250, 200)  

                pdf.cell(45, 10, clean_status, border=1, ln=True, align="C", fill=True)

                if raw_comment:
                    pdf.set_font("Arial", 'I', 10)
                    safe_comment = raw_comment.encode('latin-1', 'ignore').decode('latin-1')
                    pdf.set_fill_color(224, 224, 224)
                    pdf.multi_cell(190, 8, f"{safe_comment}", border=1, align="L", fill=True)
            
            # 5. Convert the PDF to a downloadable format
            # Using try/except because different versions of fpdf output differently
            try:
                pdf_bytes = bytes(pdf.output()) 
            except:
                pdf_bytes = pdf.output(dest="S").encode("latin-1")
            
            st.session_state['pdf_ready'] = pdf_bytes
            # ------------------------------------

            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=clean_header_order)
            writer.writeheader()
            writer.writerows(clean_output_data)
            
            st.session_state['download_ready'] = output.getvalue()
            st.success("✅ Cleaned export ready! Download below.")

    if 'download_ready' in st.session_state and 'pdf_ready' in st.session_state:
    

        btn_col1, btn_col2, spacer = st.columns([1.8, 4.6, 7])
    
        with btn_col1:
            st.download_button(
                label="📥 Download CSV",
                data=st.session_state['download_ready'],
                file_name="Updated_Test_Cases.csv",
                mime="text/csv"
            )
        
        with btn_col2:
            st.download_button(
                label="📄 PDF Report",
                data=st.session_state['pdf_ready'],
                file_name="QA_Run_Report.pdf",
                mime="application/pdf"
            )
else:
    st.info("👆 Please drag and drop your exported CSV file into the box above to get started.")

st.markdown('<div id="bottom-of-page"></div>', unsafe_allow_html=True)