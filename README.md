# LegalEagleAI-majorproject

**LegalEagle AI** is an AI-powered legal marketplace that connects clients with verified lawyers, streamlining access to legal services. The platform is built with Flask, HTML, CSS, JavaScript, Firebase, and PostgreSQL, and is deployed on Render. It leverages the Cohere API and a re-ranking algorithm for precise semantic matching between clients' legal needs and lawyer expertise.

---

## 🚀 Features

- **Smart Semantic Matching:** Utilizes Cohere API and a custom re-ranking algorithm for accurate lawyer-client pairing based on legal needs.
- **Role-Specific Dashboards:** Centralized management dashboards for clients, lawyers, and admins.
- **Appointment Booking:** Schedule and manage appointments between clients and lawyers.
- **Gamification:** Leaderboards and rewards to incentivize user engagement and platform activity.
- **Real-Time Sync:** Bookings are synced between PostgreSQL and Firebase for reliability and performance.
- **Admin Panel:** Manage users, appointments, and monitor platform activity.
- **Deployed on Render:** Accessible 24/7 at [LegalEagleAI](https://legaleagleai-ut6e.onrender.com).

---

## 🛠️ Tech Stack

- **Backend:** Flask (Python), Flask-Session, Flask-Mailman
- **Frontend:** HTML, CSS, JavaScript
- **Database:** PostgreSQL (primary), Firebase (for real-time sync)
- **AI Integration:** Cohere API for semantic search and re-ranking
- **Other Libraries:** pandas, nltk, transformers, werkzeug, PyPDF2, python-docx, python-dotenv

---

## 🔒 Login Credentials

- **Admin Page**
  - Username: `admin`
  - Password: `admin123`
- **Clients:** Password: `*Cli123` or `123456`
- **Lawyers:** Password: `*Law1234` or `123456`

> **IMPORTANT:**  
> When booking appointments, always use the same name and email as your logged-in client profile.

---

## 🏁 Getting Started

1. **Install dependencies:**
   ```bash
   pip install flask flask-session flask-mailman psycopg2 pandas nltk transformers werkzeug PyPDF2 docx google-generativeai python-dotenv
   ```

2. **Download NLTK data:**
   ```bash
   python -c "import nltk; nltk.download('all');"
   ```

3. **Sync PostgreSQL bookings to Firebase:**
   - Run this in a separate terminal and keep it running:
     ```bash
     python sync_bookings_to_firebase.py
     ```

4. **Start the Flask server:**
   - Add `.env` and other required files (sent via mail/drive) to your project folder.
   - Run your Flask app as per your main application file (e.g., `python app.py`).

5. **View appointments as both client and lawyer:**
   - Open the web app in two different browser windows (one as client, one as lawyer) to see updates in real time.

---

## 🔧 Firebase & API Configuration

Copy the following variables into your `.env` file and update with your actual credentials:

```
# Firebase Configuration
FIREBASE_API_KEY=your_firebase_api_key
FIREBASE_AUTH_DOMAIN=your_project_auth_domain
FIREBASE_PROJECT_ID=your_project_id
FIREBASE_STORAGE_BUCKET=your_storage_bucket
FIREBASE_MESSAGING_SENDER_ID=your_messaging_sender_id
FIREBASE_APP_ID=your_app_id
FIREBASE_DB_URL=your_database_url

# Google API Key
GOOGLE_API_KEY=your_google_api_key

# Cohere API Key
COHERE_API_KEY=your_cohere_api_key

# SendGrid Email Service
SENDGRID_API_KEY=your_sendgrid_api_key
SENDGRID_FROM_EMAIL=your_email@example.com

# SMTP Credentials
MAIL_USERNAME=your_email@example.com
MAIL_PASSWORD=your_email_password

# Firebase Admin SDK
FIREBASE_TYPE=service_account
FIREBASE_PRIVATE_KEY="your_firebase_private_key"
FIREBASE_CLIENT_EMAIL=your_firebase_client_email
FIREBASE_CLIENT_ID=your_firebase_client_id
FIREBASE_AUTH_URI=https://accounts.google.com/o/oauth2/auth
FIREBASE_TOKEN_URI=https://oauth2.googleapis.com/token
FIREBASE_AUTH_PROVIDER_CERT_URL=https://www.googleapis.com/oauth2/v1/certs
FIREBASE_CLIENT_CERT_URL=your_firebase_client_cert_url
```

---

## 🌐 Live Demo

- [LegalEagleAI on Render](https://legaleagleai-ut6e.onrender.com)
- [Demo Link 1](https://bit.ly/LegalEagleAI-j03j03)
- [Demo Link 2](https://bit.ly/legaleagleai-j03)

---

## 📝 Notes

- `.env` and three additional files are required for full functionality. Download these from your email or the project drive and place them in the project root.
- The booking sync script (`sync_bookings_to_firebase.py`) must always be running in the background for data consistency between PostgreSQL and Firebase.

---

## 🤝 Contributing

Pull requests and suggestions are welcome! Please open an issue to discuss your ideas or report bugs.

---

Happy Lawyering with LegalEagle AI! 🦅⚖️

