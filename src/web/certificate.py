import os
import streamlit as st
from datetime import datetime
import json
import base64
from io import BytesIO

from src.core.k8s_certificate import (
    generate_certificate,
    validate_certificate,
    read_input_file,
    CERT_DB_FILE
)

st.set_page_config(
    page_title="Kubernetes Certificate Generator",
    page_icon="🎓",
    layout="wide"
)

st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #326DE6;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.8rem;
        color: #326DE6;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .error-message {
        background-color: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .certificate-details {
        background-color: #e9ecef;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["Generate Certificate", "Validate Certificate"])

def show_pdf(file_path):
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')

    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)


def create_input_file(data):
    with open("temp_input.txt", "w") as f:
        for key, value in data.items():
            if value:
                f.write(f"{key}: {value}\n")
    return "temp_input.txt"


def display_certificate_details(cert_data, include_verification=False):
    st.markdown('<div class="sub-header">Certificate Details</div>', unsafe_allow_html=True)
    st.markdown('<div class="certificate-details">', unsafe_allow_html=True)
    
    if include_verification:
        st.markdown(f"**Certificate ID:** {cert_data['id']}")
        st.markdown(f"**Verification Code:** {cert_data['verification_code']}")
    else:
        st.markdown(f"**Certificate ID:** {cert_data['id']}")
    
    st.markdown(f"**Student:** {cert_data['student_name']}")
    st.markdown(f"**Course:** {cert_data['course_name']}")
    st.markdown(f"**Issue Date:** {cert_data['issue_date']}")
    
    st.markdown('</div>', unsafe_allow_html=True)


with tab1:
    st.markdown('<div class="main-header">Generate Kubernetes Certificate</div>', unsafe_allow_html=True)

    st.markdown("Fill out the form below to generate a certificate.")
    
    certificate_generated = False
    output_path = None
    output_filename = None

    with st.form("certificate_form"):
        col1, col2 = st.columns(2)

        with col1:
            student = st.text_input("Student Name", help="Enter the full name of the student")
            course = st.text_input("Course Name", help="Enter the name of the course completed")
            hours = st.number_input("Hours Completed", min_value=1, value=40, help="Enter the number of hours completed")

        with col2:
            teacher = st.text_input("Teacher Name", help="Enter the name of the primary instructor")
            co_teacher = st.text_input("Co-Teacher Name (Optional)", help="Enter the name of a co-instructor (if applicable)")
            date = st.date_input("Certificate Date", help="Select the date for the certificate")

        output_filename = st.text_input("Output Filename", "certificate.pdf", help="Name of the output PDF file")

        submitted = st.form_submit_button("Generate Certificate")

        if submitted:
            if not student or not course or not teacher:
                st.markdown('<div class="error-message">Please fill out all required fields: Student Name, Course Name, and Teacher Name.</div>', unsafe_allow_html=True)
            else:
                form_data = {
                    "student": student,
                    "course": course,
                    "hours": str(hours),
                    "teacher": teacher,
                    "date": date.strftime("%Y-%m-%d")
                }

                if co_teacher:
                    form_data["co-teacher"] = co_teacher

                input_file = create_input_file(form_data)

                try:
                    output_path, cert_id, verification_code = generate_certificate(form_data, output_filename)
                    certificate_generated = True

                    st.markdown('<div class="success-message">Certificate generated successfully!</div>', unsafe_allow_html=True)

                    display_certificate_details({
                        'id': cert_id,
                        'verification_code': verification_code,
                        'student_name': student,
                        'course_name': course,
                        'issue_date': date.strftime("%Y-%m-%d")
                    }, include_verification=True)
                    
                    st.markdown(f"**Output File:** {output_path}", unsafe_allow_html=True)

                    st.markdown('<div class="sub-header">Certificate Preview</div>', unsafe_allow_html=True)
                    show_pdf(output_path)

                except Exception as e:
                    st.markdown(f'<div class="error-message">Error generating certificate: {str(e)}</div>', unsafe_allow_html=True)

                if os.path.exists(input_file):
                    os.remove(input_file)
    
    if certificate_generated and output_path and os.path.exists(output_path):
        with open(output_path, "rb") as file:
            st.download_button(
                label="Download Certificate",
                data=file,
                file_name=output_filename,
                mime="application/pdf"
            )

with tab2:
    st.markdown('<div class="main-header">Validate Certificate</div>', unsafe_allow_html=True)

    st.markdown("Enter the certificate ID and verification code to validate a certificate.")

    col1, col2 = st.columns(2)

    with col1:
        cert_id = st.text_input("Certificate ID", help="Enter the certificate ID (e.g., K8S-202503-ABCDEF-1234)")

    with col2:
        verification_code = st.text_input("Verification Code", help="Enter the verification code (optional)")

    if st.button("Validate Certificate"):
        if not cert_id:
            st.markdown('<div class="error-message">Please enter a Certificate ID.</div>', unsafe_allow_html=True)
        else:
            if not os.path.exists(CERT_DB_FILE):
                st.markdown('<div class="error-message">Certificate database not found. No certificates have been generated yet.</div>', unsafe_allow_html=True)
            else:
                is_valid, cert_data = validate_certificate(cert_id, verification_code)

                if is_valid:
                    st.markdown('<div class="success-message">Certificate is valid! ✅</div>', unsafe_allow_html=True)
                    display_certificate_details(cert_data)
                else:
                    if cert_data:
                        st.markdown('<div class="error-message">Invalid verification code for this certificate ID.</div>', unsafe_allow_html=True)
                    else:
                        st.markdown('<div class="error-message">Certificate not found. This ID does not exist in our database.</div>', unsafe_allow_html=True)

    if st.checkbox("Show All Certificates in Database", help="For demonstration purposes only"):
        if os.path.exists(CERT_DB_FILE):
            with open(CERT_DB_FILE, 'r') as f:
                try:
                    all_certs = json.load(f)
                    if all_certs:
                        st.markdown('<div class="sub-header">All Certificates</div>', unsafe_allow_html=True)

                        for cert_id, cert_info in all_certs.items():
                            st.markdown('<div class="certificate-details">', unsafe_allow_html=True)
                            st.markdown(f"**ID:** {cert_id}")
                            st.markdown(f"**Verification Code:** {cert_info['verification_code']}")
                            st.markdown(f"**Student:** {cert_info['student_name']}")
                            st.markdown(f"**Course:** {cert_info['course_name']}")
                            st.markdown(f"**Date:** {cert_info['issue_date']}")
                            st.markdown('</div>', unsafe_allow_html=True)
                    else:
                        st.info("No certificates in the database yet.")
                except json.JSONDecodeError:
                    st.error("Error reading certificate database.")
        else:
            st.info("No certificate database found. Generate a certificate first.")


st.markdown("---")
st.markdown("Kubernetes Certificate Generator | Created with Streamlit")
