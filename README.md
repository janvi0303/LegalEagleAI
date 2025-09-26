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
- **Clients:** Password: `*Cli123`
- **Lawyers:** Password: `*Law1234`

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
