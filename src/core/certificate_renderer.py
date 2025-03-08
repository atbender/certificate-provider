import os
import io
import json
import hashlib
import base64
from datetime import datetime

from reportlab.lib.pagesizes import landscape, letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Image
from PIL import Image as PILImage

CERT_DB_FILE = os.environ.get("CERT_DB_PATH", "data/certificates_db.json")


def create_kubernetes_logo(size=300):
    logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "assets/kubernetes_logo.svg.png")

    if not os.path.exists(logo_path):
        return None

    try:
        img = PILImage.open(logo_path)
        img = img.resize((size, size), PILImage.Resampling.LANCZOS)
        processed_img = io.BytesIO()
        img.save(processed_img, format='PNG')
        processed_img.seek(0)
        return processed_img
    except Exception:
        return None


def read_input_file(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Input file not found: {file_path}")

    data = {}

    with open(file_path, 'r') as file:
        for line in file:
            if ':' in line:
                key, value = line.split(':', 1)
                data[key.strip().lower()] = value.strip()

    return data


def format_date(date_str=None):
    if date_str:
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            return date_obj.strftime("%d %B, %Y")
        except ValueError:
            return date_str
    else:
        return datetime.now().strftime("%d %B, %Y")


def parse_date(date_str):
    try:
        return datetime.strptime(date_str, "%d %B, %Y")
    except ValueError:
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            return datetime.now()


def generate_secure_certificate_id(student_name, course_name, date):
    if isinstance(date, str):
        date_obj = parse_date(date)
    else:
        date_obj = date

    date_part = date_obj.strftime("%Y%m")

    student_hash = hashlib.md5(student_name.encode('utf-8')).hexdigest()[:6].upper()

    course_hash = hashlib.md5(course_name.encode('utf-8')).hexdigest()[:4].upper()

    cert_id = f"KC-{date_part}-{student_hash}-{course_hash}"

    return cert_id


def generate_verification_code(cert_id, student_name, course_name):
    combined = f"{cert_id}:{student_name}:{course_name}"

    hash_obj = hashlib.sha256(combined.encode('utf-8'))

    verification_code = base64.b64encode(hash_obj.digest()).decode('utf-8')[:12]

    verification_code = ''.join(c for c in verification_code if c.isalnum())

    return verification_code.upper()


def save_certificate_data(cert_id, verification_code, student_name, course_name, issue_date, instructor, instructor_title, co_instructor, co_instructor_title, organization, place, certification_type, hours):
    cert_data = {
        "id": cert_id,
        "verification_code": verification_code,
        "student_name": student_name,
        "course_name": course_name,
        "issue_date": issue_date,
        "timestamp": datetime.now().isoformat(),
        "instructor": instructor,
        "instructor_title": instructor_title,
        "co_instructor": co_instructor,
        "co_instructor_title": co_instructor_title,
        "organization": organization,
        "place": place,
        "certification_type": certification_type,
        "hours": hours
    }

    db = CertificateDB()
    db.save_certificate(cert_data)

    return cert_data


class CertificateDB:
    def __init__(self, db_file=CERT_DB_FILE):
        self.db_file = db_file

    def _load_db(self):
        if not os.path.exists(self.db_file):
            return {}
        try:
            with open(self.db_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}

    def _save_db(self, data):
        with open(self.db_file, 'w') as f:
            json.dump(data, f, indent=2)

    def get_certificate(self, cert_id):
        all_certs = self._load_db()
        return all_certs.get(cert_id)

    def save_certificate(self, cert_data):
        all_certs = self._load_db()
        all_certs[cert_data['id']] = cert_data
        self._save_db(all_certs)


def validate_certificate(cert_id, verification_code=None):
    db = CertificateDB()
    cert_data = db.get_certificate(cert_id)

    if not cert_data:
        return False, None

    if verification_code and cert_data["verification_code"] != verification_code:
        return False, cert_data

    return True, cert_data


def generate_certificate(student_name, course_name, issue_date, instructor, instructor_title, co_instructor, co_instructor_title, organization, place, certification_type, hours, output_path):
    K8S_BLUE = (50/255, 109/255, 230/255)

    input_data = {
        'student': student_name,
        'course': course_name,
        'teacher': instructor,
        'co-teacher': co_instructor,
        'date': issue_date,
        'certification_type': certification_type,
        'instructor_title': instructor_title,
        'co_instructor_title': co_instructor_title,
        'organization': organization,
        'hours': hours,
        'place': place
    }

    main_font = 'Helvetica'
    main_font_bold = 'Helvetica-Bold'
    secondary_font = 'Helvetica'
    signature_font = 'DancingScript-Regular'

    font_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'assets/DancingScript-Regular.ttf')
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont('DancingScript-Regular', font_path))

    page_width, page_height = landscape(letter)
    c = canvas.Canvas(output_path, pagesize=(page_width, page_height))
    c.setAuthor("TestCraft")
    c.setTitle("Kubernetes Certification")
    c.setSubject("Certificate of Completion")

    c.setFillColorRGB(1, 1, 1)
    c.rect(0, 0, page_width, page_height, fill=1)

    c.setFillColorRGB(*K8S_BLUE)
    c.rect(0, page_height - 45, page_width, 45, fill=1)

    c.setFont(main_font_bold, 24)
    c.setFillColorRGB(1, 1, 1)
    c.drawString(30, page_height - 30, input_data['organization'])

    c.setFont(main_font, 20)
    cert_text = input_data['certification_type']
    cert_width = c.stringWidth(cert_text, main_font, 20)
    c.drawString(page_width - cert_width - 30, page_height - 30, cert_text)

    c.setFillColorRGB(*K8S_BLUE)
    c.rect(0, 0, page_width, 25, fill=1)

    c.setFont(main_font_bold, 42)
    c.setFillColorRGB(*K8S_BLUE)
    title = "Certificate of Completion"
    title_width = c.stringWidth(title, main_font_bold, 42)
    c.drawString((page_width - title_width) / 2, page_height - 130, title)

    c.setStrokeColorRGB(*K8S_BLUE)
    c.setLineWidth(1)
    line_width = 350
    c.line((page_width - line_width) / 2, page_height - 145,
           (page_width + line_width) / 2, page_height - 145)

    c.setFont(secondary_font, 16)
    c.setFillColorRGB(0.2, 0.2, 0.2)
    certifies_text = "This certificate is awarded to"
    certifies_width = c.stringWidth(certifies_text, secondary_font, 16)
    c.drawString((page_width - certifies_width) / 2, page_height - 195, certifies_text)

    student_name = input_data.get('student', '')
    c.setFont(signature_font, 42)
    c.setFillColorRGB(0, 0, 0)
    name_width = c.stringWidth(student_name, signature_font, 42)
    c.drawString((page_width - name_width) / 2, page_height - 260, student_name)

    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(1)
    student_line_width = 450
    c.line((page_width - student_line_width) / 2, page_height - 275,
           (page_width + student_line_width) / 2, page_height - 275)

    c.setFont(secondary_font, 16)
    c.setFillColorRGB(0.2, 0.2, 0.2)
    completion_text = "For successfully completing the course:"
    completion_width = c.stringWidth(completion_text, secondary_font, 16)
    c.drawString((page_width - completion_width) / 2, page_height - 310, completion_text)

    course_name = input_data.get('course', '')
    hours = input_data.get('hours', '')
    c.setFont(main_font_bold, 36)
    c.setFillColorRGB(*K8S_BLUE)
    course_width = c.stringWidth(course_name, main_font_bold, 36)
    c.drawString((page_width - course_width) / 2, page_height - 365, course_name)

    formatted_date = format_date(input_data.get('date', None))
    c.setFont(secondary_font, 16)
    c.setFillColorRGB(0.2, 0.2, 0.2)
    place = input_data.get('place', '')
    date_text = f"Amounting to a total of {hours} hours. Given on {formatted_date} at {place}."
    date_width = c.stringWidth(date_text, secondary_font, 16)
    c.drawString((page_width - date_width) / 2, page_height - 415, date_text)

    signature_y = 100
    signature_line_width = 200
    teacher_name = input_data.get('teacher', '')

    if input_data.get('co-teacher'):
        teacher_x = page_width/3
    else:
        teacher_x = page_width/2

    c.setFont(signature_font, 22)
    c.setFillColorRGB(0, 0, 0)
    teacher_sig_width = c.stringWidth(teacher_name, signature_font, 22)
    c.drawString(teacher_x - teacher_sig_width/2, signature_y+3, teacher_name)

    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(1)
    c.line(teacher_x - signature_line_width/2, signature_y-10,
           teacher_x + signature_line_width/2, signature_y-10)

    c.setFont(secondary_font, 12)
    c.setFillColorRGB(0.2, 0.2, 0.2)
    c.drawString(teacher_x - signature_line_width/2, signature_y - 30, teacher_name)

    c.setFont(secondary_font, 10)
    instructor_title = input_data.get('instructor_title', '')
    c.drawString(teacher_x - signature_line_width/2, signature_y - 45, instructor_title)

    if input_data.get('co-teacher'):
        co_teacher_x = 2 * page_width/3
        co_teacher_name = input_data.get('co-teacher', '')

        c.setFont(signature_font, 22)
        c.setFillColorRGB(0, 0, 0)
        co_teacher_sig_width = c.stringWidth(co_teacher_name, signature_font, 22)
        c.drawString(co_teacher_x - co_teacher_sig_width/2, signature_y+3, co_teacher_name)

        c.setStrokeColorRGB(0, 0, 0)
        c.setLineWidth(1)
        c.line(co_teacher_x - signature_line_width/2, signature_y-10,
               co_teacher_x + signature_line_width/2, signature_y-10)

        c.setFont(secondary_font, 12)
        c.setFillColorRGB(0.2, 0.2, 0.2)
        c.drawString(co_teacher_x - signature_line_width/2, signature_y - 30, co_teacher_name)

        c.setFont(secondary_font, 10)
        co_instructor_title = input_data.get('co_instructor_title', '')
        c.drawString(co_teacher_x - signature_line_width/2, signature_y - 45, co_instructor_title)

    cert_id = generate_secure_certificate_id(student_name, course_name, formatted_date)
    verification_code = generate_verification_code(cert_id, student_name, course_name)

    c.setFont(secondary_font, 10)
    c.setFillColorRGB(1, 1, 1)
    c.drawString(30, 10, f"Powered by {input_data['organization']}")

    c.setFont(secondary_font, 10)
    verification_text = f"Certificate ID: {cert_id} | Verification Code: {verification_code}"
    verification_width = c.stringWidth(verification_text, secondary_font, 10)
    c.drawString(page_width - verification_width - 30, 10, verification_text)

    logo_size = 800
    k8s_logo = create_kubernetes_logo(logo_size)
    if k8s_logo:
        img = Image(k8s_logo, width=logo_size * 0.75, height=logo_size * 0.75)
        c.saveState()
        c.translate(page_width * 1.03, 260)
        c.setFillAlpha(0.10)
        c.setStrokeAlpha(0.10)
        img.drawOn(c, -logo_size/2, -logo_size/2)
        c.restoreState()

    c.save()

    print(f"Certificate saved as {output_path}")
    print(f"Certificate ID: {cert_id}")
    print(f"Verification Code: {verification_code}")

    return output_path
