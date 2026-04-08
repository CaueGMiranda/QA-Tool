import streamlit as st
import csv
import io
import re

# 1. Setup the page
st.set_page_config(page_title="INO Games Test Cases QA Tracker", layout="wide")
st.title("🎰 INO Games Test Cases QA Tracker")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
            
    .stApp {
        background-color: #1E1E1E;
    }
            
    /* 1. Target the Save button container */
    div[data-testid="stFormSubmitButton"] {
        position: fixed;
        bottom: 20px;
        right: 30px;
        width: fit-content;
        z-index: 9999; 
        opacity: 0.9;
    }
    
    /* 2. Target the Download button container (Shifted to the left!) */
    div[data-testid="stDownloadButton"] {
        position: fixed;
        bottom: 20px;
        right: 210px; /* Pushes it left so it sits exactly beside the Save button */
        width: fit-content;
        z-index: 9999; 
        opacity: 0.9;
        
    }

    /* 3. Apply the same beautiful styling to BOTH buttons */
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
            
    </style>
""", unsafe_allow_html=True)
# ---------------------------------------

uploaded_file = st.file_uploader("📂 Test case CSV aqui", type=['csv'])


if uploaded_file is not None:

    csv_text = uploaded_file.getvalue().decode('utf-8').splitlines()
    reader = csv.DictReader(csv_text)
    headers = reader.fieldnames
    data = list(reader)


    with st.form("qa_test_form"):
        updated_data = []

        for index, row in enumerate(data):

            test_id = row.get('Title')
            severity = row.get('Severity')
            run_info = row.get('Run', 'N/A')
            st.markdown(f"### <span style='font-size: 25px; color: #b48ff0;'>{run_info}</span> | {test_id} `[{severity}]`", 
    unsafe_allow_html=True)


            with st.expander("🔍 View Test Details"):
  
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
            clean_header_order = ['Run', 'Test ID', 'Severity', 'Test Description', 'Status', 'Step by Step', 'Expected Result', 'Comments']
            
            clean_output_data = []
            for row in updated_data:
                clean_row = {}
                for header in clean_header_order:
                    val = row.get(header, "")
                    # Ensure newlines are the standard \n that Google Sheets likes
                    if isinstance(val, str):
                        val = val.replace('\n\n', '\n') 
                    clean_row[header] = val
                clean_output_data.append(clean_row)

            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=clean_header_order)
            writer.writeheader()
            writer.writerows(clean_output_data)
            
            st.session_state['download_ready'] = output.getvalue()
            st.success("✅ Cleaned export ready! Download below.")

    if 'download_ready' in st.session_state:
        st.download_button(
            label="📥 Download Completed Test Run",
            data=st.session_state['download_ready'],
            file_name="completed_test_cases.csv",
            mime="text/csv"
        )
else:
    st.info("👆 Please drag and drop your exported CSV file into the box above to get started.")