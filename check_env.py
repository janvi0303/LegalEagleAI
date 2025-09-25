import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def init_mail(app):
    """Initialize email configuration"""
    app.config["SENDGRID_API_KEY"] = os.getenv("SENDGRID_API_KEY")
    app.config["SENDGRID_FROM_EMAIL"] = os.getenv("SENDGRID_FROM_EMAIL")
    print(f"Email service configured: {'Yes' if app.config['SENDGRID_API_KEY'] else 'No'}")

def send_email(client_name, client_email, appointment_date, appointment_time, case_details, lawyer_name):
    """Send email using SendGrid API (HTTP version)"""
    try:
        api_key = os.getenv("SENDGRID_API_KEY")
        from_email = os.getenv("SENDGRID_FROM_EMAIL")
        
        if not api_key or not from_email:
            print("Email configuration missing")
            return False

        email_data = {
            "personalizations": [{
                "to": [{"email": client_email}],
                "subject": "Appointment Confirmation - LegalEagle AI"
            }],
            "from": {"email": from_email, "name": "LegalEagle AI"},
            "content": [{
                "type": "text/plain",
                "value": f"""Dear {client_name},

Your appointment has been successfully booked for {appointment_date} at {appointment_time} with {lawyer_name}.

Case Details:
{case_details}

Thank you for choosing our services.

Best regards,
LegalEagle AI Team"""
            }]
        }

        response = requests.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json=email_data,
            timeout=10  # 10 second timeout
        )

        if response.status_code == 202:
            print("Email sent successfully via SendGrid!")
            return True
        else:
            print(f"SendGrid error: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        print(f"Failed to send email: {e}")
        return False
