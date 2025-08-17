import os
import re
import nltk
import pandas as pd
from firebase_admin import db
from flask import Flask, render_template, request, jsonify, g, session, redirect, url_for, flash
from flask_session import Session
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader
import docx
from datetime import datetime, timedelta
import psycopg2
from psycopg2 import sql
from flask_mailman import Mail
from flask_mailman.message import EmailMessage
import google.generativeai as genai
from admin import admin_bp, init_mail, db
from check_env import init_mail, send_email 
from case_tracking import case_tracking_bp
from dotenv import load_dotenv
from firebase_admin import db
from sklearn.metrics.pairwise import cosine_similarity
import cohere
from tenacity import retry, stop_after_attempt, wait_exponential

load_dotenv()
app = Flask(__name__)
app.secret_key = "supersecretkey"
init_mail(app) 

# ✅ Configure Flask Sessions
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SESSION_TYPE'] = 'filesystem'  # Can also use 'redis' or 'memcached' for better persistence
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
Session(app)  # ✅ Initialize Session

# Download NLTK resources
nltk.download('punkt')
nltk.download('stopwords')

# ✅ Register Blueprints
app.register_blueprint(admin_bp)

# ✅ Register Blueprints
app.register_blueprint(case_tracking_bp)

@app.route('/admin_dashboard')
def admin_dashboard():
    if not session.get("admin_logged_in"):
        return render_template('admin_dashboard.html', admin_logged_in=False)
    return render_template('admin_dashboard.html', admin_logged_in=True)

# ✅ Check Admin Session Before Loading Dashboard
@app.route('/admin_check', methods=['GET'])
def admin_check():
    return jsonify({"logged_in": session.get("admin_logged_in", False)})

# In your main Flask app file (app.py or similar)
@app.route('/client')
def client():
    return render_template('client.html')

@app.route('/client/appointments')
def client_appointment_detail():
    return render_template('client_appointment_detail.html', **g.firebase_config)

@app.route('/lawyer/appointments')
def lawyer_appointment_detail():
    return render_template('lawyer_appointment_detail.html', **g.firebase_config)

@app.route('/api/get_appointments')
def get_appointments():
    user_type = request.args.get('type')  # 'client' or 'lawyer'
    email = request.args.get('email')     # client email or lawyer email

    if not user_type or not email:
        return jsonify({'error': 'Missing parameters'}), 400

    try:
        ref = db.reference('bookings')
        all_bookings = ref.get() or {}

        if user_type == 'client':
            sanitized_email = email.replace('.', ',')
            client_appointments = all_bookings.get(sanitized_email, {})
            return jsonify({'appointments': list(client_appointments.values())})

        elif user_type == 'lawyer':
            lawyer_appointments = []
            for client_email, appointments in all_bookings.items():
                for appointment_id, appointment in appointments.items():
                    if appointment.get('lawyer_name') == email:
                        lawyer_appointments.append(appointment)
            return jsonify({'appointments': lawyer_appointments})

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
def sanitize_email(email):
    return email.replace('.', ',')

def fetch_firebase_appointments_by_email(email):
    sanitized_email = sanitize_email(email)
    ref = db.reference(f'bookings/{sanitized_email}')
    return ref.get() or {}

def fetch_firebase_appointments_by_lawyer_id(barcouncil_id):
    root = db.reference('bookings')
    all_data = root.get()
    results = []
    if all_data:
        for client_email, bookings in all_data.items():
            for _, appointment in bookings.items():
                if appointment.get("Bar_Council_ID") == barcouncil_id:
                    results.append(appointment)
    return results

@app.route('/api/request_reschedule', methods=['POST'])
def request_reschedule():
    data = request.json
    appointment_id = data.get('id')
    new_date = data.get('new_date')
    new_time = data.get('new_time')
    requester = data.get('requester')

    if not all([appointment_id, new_date, new_time, requester]):
        return jsonify({"error": "Missing required parameters"}), 400

    try:
        # Validate date format
        datetime.strptime(new_date, "%Y-%m-%d")
        
        bookings_ref = db.reference('bookings')
        all_bookings = bookings_ref.get() or {}
        
        for email_key, appointments in all_bookings.items():
            for key, appointment in appointments.items():
                if appointment.get("id") == appointment_id:
                    updates = {}
                    status_update = "reschedule_requested"
                    
                    if requester == "client":
                        reschedule_status = "pending_lawyer_confirmation"
                    elif requester == "lawyer":
                        reschedule_status = "pending_client_confirmation"
                    else:
                        return jsonify({"error": "Invalid requester type"}), 400

                    updates[f"{email_key}/{key}/reschedule_request"] = {
                        "new_date": new_date,
                        "new_time": new_time,
                        "status": reschedule_status,
                        "requested_at": datetime.now().isoformat()
                    }
                    updates[f"{email_key}/{key}/status"] = status_update
                    
                    # Check for time slot availability
                    if not is_time_slot_available(new_date, new_time, appointment.get('lawyer_name'), appointment_id):
                        return jsonify({"error": "This time slot is already booked"}), 400
                    
                    bookings_ref.update(updates)
                    return jsonify({
                        "message": "Reschedule request submitted",
                        "status": status_update,
                        "reschedule_status": reschedule_status
                    })
        
        return jsonify({"error": "Appointment not found"}), 404
    except ValueError as ve:
        return jsonify({"error": f"Invalid date format: {str(ve)}"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# New helper function for time slot availability
def is_time_slot_available(date, time, lawyer_name, exclude_appointment_id=None):
    try:
        bookings_ref = db.reference('bookings')
        all_bookings = bookings_ref.get() or {}
        
        for email_key, appointments in all_bookings.items():
            for key, appointment in appointments.items():
                # Skip the appointment we're trying to reschedule
                if appointment.get("id") == exclude_appointment_id:
                    continue
                    
                if (appointment.get("lawyer_name") == lawyer_name and 
                    appointment.get("appointment_date") == date and
                    appointment.get("appointment_time") == time):
                    return False
        return True
    except Exception:
        return False

@app.route('/api/confirm_reschedule', methods=['POST'])
def confirm_reschedule():
    data = request.json
    appointment_id = data.get('id')
    approve = data.get('approve', False)
    new_date = data.get('new_date')  # Only needed if approving
    new_time = data.get('new_time')  # Only needed if approving

    if not appointment_id:
        return jsonify({"error": "Missing appointment ID"}), 400

    try:
        bookings_ref = db.reference('bookings')
        all_bookings = bookings_ref.get() or {}
        
        for email_key, appointments in all_bookings.items():
            for key, appointment in appointments.items():
                if appointment.get("id") == appointment_id:
                    updates = {}
                    
                    if approve:
                        if not all([new_date, new_time]):
                            return jsonify({"error": "New date and time required for approval"}), 400
                            
                        # Validate the new time slot is available
                        if not is_time_slot_available(new_date, new_time, appointment.get('lawyer_name'), appointment_id):
                            return jsonify({"error": "This time slot is no longer available"}), 400
                            
                        updates[f"{email_key}/{key}/appointment_date"] = new_date
                        updates[f"{email_key}/{key}/appointment_time"] = new_time
                        updates[f"{email_key}/{key}/status"] = "confirmed"
                    
                    # Clear the reschedule request regardless of approval
                    updates[f"{email_key}/{key}/reschedule_request"] = None
                    
                    bookings_ref.update(updates)
                    return jsonify({
                        "message": "Reschedule request processed",
                        "status": "confirmed" if approve else "original appointment kept"
                    })
        
        return jsonify({"error": "Appointment not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/confirm_delete', methods=['POST'])
def confirm_delete():
    data = request.json
    appointment_id = data.get('id')
    confirm = data.get('confirm', False)

    try:
        bookings_ref = db.reference('bookings')
        all_bookings = bookings_ref.get() or {}
        
        for email_key, appointments in all_bookings.items():
            for key, appointment in appointments.items():
                if appointment.get("id") == appointment_id:
                    if confirm:
                        # Delete the appointment
                        bookings_ref.child(f"{email_key}/{key}").delete()
                        return jsonify({"message": "Appointment deleted."})
                    else:
                        # Just update the status
                        updates = {
                            f"{email_key}/{key}/status": "confirmed",
                            f"{email_key}/{key}/delete_by": None
                        }
                        bookings_ref.update(updates)
                        return jsonify({"message": "Delete request cancelled."})
        
        return jsonify({"error": "Appointment not found."}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/request_delete', methods=['POST'])
def request_delete():
    data = request.json
    appointment_id = data.get('id')
    requester = data.get('requester')

    if not all([appointment_id, requester]):
        return jsonify({"error": "Missing required parameters"}), 400

    try:
        bookings_ref = db.reference('bookings')
        all_bookings = bookings_ref.get() or {}
        
        for email_key, appointments in all_bookings.items():
            for key, appointment in appointments.items():
                if appointment.get("id") == appointment_id:
                    updates = {
                        f"{email_key}/{key}/status": "delete_requested",
                        f"{email_key}/{key}/delete_by": requester,
                        f"{email_key}/{key}/delete_requested_at": datetime.now().isoformat()
                    }
                    
                    bookings_ref.update(updates)
                    return jsonify({
                        "message": "Delete request submitted",
                        "status": "delete_requested"
                    })
        
        return jsonify({"error": "Appointment not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# New endpoint for immediate deletion (used by lawyers)
@app.route('/api/delete_appointment', methods=['POST'])
def delete_appointment():
    data = request.json
    appointment_id = data.get('id')

    if not appointment_id:
        return jsonify({"error": "Missing appointment ID"}), 400

    try:
        bookings_ref = db.reference('bookings')
        all_bookings = bookings_ref.get() or {}
        
        for email_key, appointments in all_bookings.items():
            for key, appointment in appointments.items():
                if appointment.get("id") == appointment_id:
                    bookings_ref.child(f"{email_key}/{key}").delete()
                    return jsonify({
                        "message": "Appointment deleted successfully",
                        "status": "deleted"
                    })
        
        return jsonify({"error": "Appointment not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Load dataset
def fetch_lawyer_profiles():
    ref = db.reference("lawyers_profile/lawyer_profile")  # Use reference, not collection
    lawyers = ref.get()  # Fetch all lawyers' data

    if lawyers:
        return list(lawyers.values())  # Convert dictionary values to a list
    else:
        return []
    
co = cohere.Client(os.getenv('COHERE_API_KEY'))

# Define practice areas
practice_areas = [
  "Criminal Law","Corporate Law","Family Law",
  "Intellectual Property (IP) Law","Real Estate Law","Employment & Labor Law",
  "Banking & Finance Law","Tax Law","Environmental Law","Immigration Law",
  "Cyber Law","Personal Injury Law","Constitutional Law","Human Rights Law"
]

# Initialize stemmer and stopwords
stemmer = PorterStemmer()
stop_words = set(stopwords.words('english'))

def preprocess_query(query):
    """Preprocess the input query by cleaning, tokenizing, and stemming."""
    query = re.sub(r'[^\w\s]', '', query.lower())
    tokens = nltk.word_tokenize(query)
    tokens = [stemmer.stem(word) for word in tokens if word not in stop_words]
    return ' '.join(tokens)


def extract_text_from_file(file):
    """Extract text from a PDF or DOCX file."""
    try:
        if file.filename.endswith('.pdf'):
            reader = PdfReader(file)
            text = ''.join(page.extract_text() or '' for page in reader.pages)
            return text.strip()
        elif file.filename.endswith('.docx'):
            doc = docx.Document(file)
            text = '\n'.join([para.text for para in doc.paragraphs])
            return text.strip()
    except Exception as e:
        print(f"Error extracting text from file: {e}")
    return ''



@app.route('/recommend_lawyers', methods=['GET', 'POST'])
def recommend_lawyers_route():
    lawyer_recommendations = None
    sort_order = None
    location = None

    # Fetch unique locations from Firebase
    lawyers = fetch_lawyer_profiles()
    unique_locations = sorted(set(
        lawyer.get("Location") for lawyer in lawyers if lawyer.get("Location")
    ))

    if request.method == 'POST':
        try:
            # Handle typed query
            user_query = ""
            if 'query' in request.form and request.form['query'].strip():
                user_query = request.form['query'].strip()
            
            # Handle document upload
            if 'upload' in request.files and request.files['upload'].filename:
                file = request.files['upload']
                if file and file.filename.endswith(('.pdf', '.docx')):
                    document_text = extract_text_from_file(file)
                    if document_text:
                        user_query = document_text
                    else:
                        return render_template(
                            'recommend_lawyers.html',
                            recommended_lawyers=None,
                            error_message="Failed to extract text from the uploaded document",
                            unique_locations=unique_locations,
                            selected_location=location,
                            sort_order=sort_order
                        )
            
            # Get the form data
            min_price = request.form.get('min_price')
            max_price = request.form.get('max_price')
            sort_order = request.form.get('sort_order')
            location = request.form.get('location')

            # Proceed only if we have a query
            if user_query:
                lawyer_recommendations = recommend_lawyers(
                    user_query, 
                    min_price, 
                    max_price, 
                    sort_order, 
                    location
                )
            else:
                return render_template(
                    'recommend_lawyers.html',
                    recommended_lawyers=None,
                    error_message="Please provide a query or upload a document",
                    unique_locations=unique_locations,
                    selected_location=location,
                    sort_order=sort_order
                )

        except Exception as e:
            return render_template(
                'recommend_lawyers.html',
                recommended_lawyers=None,
                error_message=f"An error occurred: {str(e)}",
                unique_locations=unique_locations,
                selected_location=location,
                sort_order=sort_order
            )

    return render_template(
        'recommend_lawyers.html',
        recommended_lawyers=lawyer_recommendations,
        error_message=None,
        unique_locations=unique_locations,
        selected_location=location,
        sort_order=sort_order
    )
    
# Configure the API key
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
if not GOOGLE_API_KEY:
    raise ValueError("Please set the GOOGLE_API_KEY environment variable.")
genai.configure(api_key=GOOGLE_API_KEY)
@app.route("/api/generate", methods=["POST"])
def generate():
    try:
        # Get the question from the incoming JSON
        data = request.json
        user_question = data.get("question", "").strip().lower()

        # If the question is empty
        if not user_question:
            return jsonify({"error": "Please provide a valid question."}), 400

        # Check if the user is asking for lawyer recommendations
        # List of keyword phrases that should trigger redirection
        trigger_phrases = [
            "recommend lawyer", "find me a lawyer", "suggest a lawyer",
            "need a lawyer", "best lawyer for", "hire a lawyer", "find a lawyer", 
            "suggest lawyer"
        ]

        # Check if any of the trigger phrases appear **consecutively** in the query
        if any(phrase in user_question for phrase in trigger_phrases):
            if session.get("user_logged_in"):  # Check if user is logged in
                return jsonify({
                    "response": 'I can help you find a lawyer!<a href="/recommend_lawyers.html">Recommend</a>'
                })
            else:
                return jsonify({
                    "response": 'I can help you find a lawyer! <a href="/client_login">Recommend</a>'
                })

        # Set up the chatbot prompt
        summarization_prompt = f"You are a chatbot that gives legal advice only if asked. Otherwise, answer the following question in simple answers and in no more than 70 words: {user_question}"

        # Generate a response using the AI model
        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash-exp",  # Use a valid model name
        )

        chat_session = model.start_chat(history=[])
        response = chat_session.send_message(summarization_prompt)

        # Return the AI-generated response
        return jsonify({"response": response.text})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# Load Firebase config and make it globally available before each request
@app.before_request
def load_firebase_config():
    g.firebase_config = {
        'firebase_api_key': os.getenv('FIREBASE_API_KEY'),
        'firebase_auth_domain': os.getenv('FIREBASE_AUTH_DOMAIN'),
        'firebase_project_id': os.getenv('FIREBASE_PROJECT_ID'),
        'firebase_storage_bucket': os.getenv('FIREBASE_STORAGE_BUCKET'),
        'firebase_messaging_sender_id': os.getenv('FIREBASE_MESSAGING_SENDER_ID'),
        'firebase_app_id': os.getenv('FIREBASE_APP_ID'),
        'firebase_database_url': os.getenv('FIREBASE_DATABASE_URL')
    }
    
@app.route('/')
def index():
    return render_template('index.html')  # The new landing page

@app.route('/client_signup')
def client_signup():
    return render_template('client_signup.html', **g.firebase_config)

@app.route('/client_login')
def client_login():
    return render_template('client_login.html', **g.firebase_config)

@app.route('/afterlogin')
def afterlogin():
    return render_template('afterlogin.html', **g.firebase_config)

@app.route('/lawyer_login.html')
def lawyer_login():
    return render_template('lawyer_login.html', **g.firebase_config)

@app.route('/lawyer_signup.html')
def lawyer_signup():
    return render_template('lawyer_signup.html', **g.firebase_config)

@app.route('/dashboard.html')
def dashboard():
    return render_template('dashboard.html', **g.firebase_config)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def classify_with_cohere(query, candidate_labels):
    """Classify query using Cohere's embedding similarity"""
    try:
        # Get embeddings for query and labels
        query_emb = co.embed(texts=[query], model="embed-english-v3.0", input_type="search_query").embeddings[0]
        label_embs = co.embed(texts=candidate_labels, model="embed-english-v3.0", input_type="classification").embeddings
        
        # Calculate cosine similarities
        similarities = cosine_similarity([query_emb], label_embs)[0]
        
        # Pair labels with scores and sort
        results = sorted(zip(candidate_labels, similarities), key=lambda x: x[1], reverse=True)
        
        return {
            'labels': [r[0] for r in results],
            'scores': [r[1] for r in results]
        }
    except Exception as e:
        print(f"Cohere classification failed: {str(e)}")
        raise

def recommend_lawyers(query, min_price=None, max_price=None, sort_order=None, location=None):
    try:
        # Step 1: Classification with Cohere
        processed_query = preprocess_query(query)
        
        classification = classify_with_cohere(processed_query, practice_areas)
        recommended_area = classification['labels'][0]
        confidence = classification['scores'][0]

        # Skip if confidence is too low
        if confidence < 0.2:
            return []

        # Step 2: Fetch lawyers
        ref = db.reference("lawyers_profile/lawyer_profile")
        all_lawyers = list((ref.get() or {}).values())

        # Step 3: Apply filters
        filtered_lawyers = [
            lawyer for lawyer in all_lawyers
            if (lawyer.get("Practice_area") == recommended_area and
                (not location or location.lower() == lawyer.get("Location", "").lower()) and
                (not min_price or not max_price or 
                 float(min_price) <= float(lawyer.get("Nominal_fees_per_hearing", 0)) <= float(max_price)))
        ]

        if not filtered_lawyers:
            return []

        # Step 4: Get query embedding
        try:
            query_embed = co.embed(texts=[query], model="embed-english-v3.0").embeddings[0]
        except Exception as e:
            print(f"Query embedding failed: {str(e)}")
            return filtered_lawyers[:20]  # Return unfiltered results if embedding fails

        # Step 5: Score lawyers
        max_fee = max([float(l.get("Nominal_fees_per_hearing", 0)) for l in filtered_lawyers] or [1])
        
        for lawyer in filtered_lawyers:
            # Create lawyer description
            lawyer_text = (
                f"{lawyer.get('Lawyer_name', '')} specializing in {lawyer.get('Practice_area', '')} "
                f"in {lawyer.get('Location', '')}. Experience: {lawyer.get('Experience', '')} years. "
                f"Cases won: {lawyer.get('Successful_cases', 0)}/{lawyer.get('Total_cases', 1)}"
            )
            
            try:
                lawyer_embed = co.embed(texts=[lawyer_text], model="embed-english-v3.0").embeddings[0]
                semantic_score = cosine_similarity([query_embed], [lawyer_embed])[0][0]
            except:
                semantic_score = 0.5

            # Calculate other metrics
            price = float(lawyer.get("Nominal_fees_per_hearing", 0))
            success_rate = float(lawyer.get("Successful_cases", 0)) / max(1, float(lawyer.get("Total_cases", 1)))
            
            lawyer["match_metrics"] = {
                "semantic_score": round(semantic_score, 2),
                "success_rate": round(success_rate, 2),
                "price_score": 1 - (price / max_fee) if max_fee > 0 else 0,
                "location_match": location and location.lower() == lawyer.get("Location", "").lower()
            }

        # Step 6: Sort results
        if sort_order == "low_to_high":
            filtered_lawyers.sort(key=lambda x: float(x.get("Nominal_fees_per_hearing", 0)))
        elif sort_order == "high_to_low":
            filtered_lawyers.sort(key=lambda x: -float(x.get("Nominal_fees_per_hearing", 0)))
        else:
            for lawyer in filtered_lawyers:
                metrics = lawyer["match_metrics"]
                lawyer["match_metrics"]["combined_score"] = metrics["semantic_score"] * 0.7 + metrics["success_rate"] * 0.3
            filtered_lawyers.sort(key=lambda x: -x["match_metrics"]["combined_score"])

        return filtered_lawyers[:20]

    except Exception as e:
        print(f"Recommendation error: {str(e)}")
        return []
    
# Database configuration 
@app.route('/booking.html')
def booking():
    lawyer_name = request.args.get('lawyer')  # Get lawyer name from URL parameters
    barcouncil_id = request.args.get('barcouncil_id', '').replace('/', '_')
    return render_template('booking.html', lawyer_name=lawyer_name, barcouncil_id=barcouncil_id)

# Route to handle form submissions (Firebase version)
@app.route('/book_appointment', methods=['POST'])
def book_appointment():
    data = request.json
    appointment_date = data['appointmentDate']
    client_name = data['clientName']
    client_email = data['clientEmail']
    lawyer_name = data['lawyerName']
    appointment_time = data['appointmentTime']
    case_details = data['caseDetails']
    barcouncil_id = data.get('barcouncilid', '')
    
    print(f"[Server] Received Bar Council ID in request: {barcouncil_id}")

    try:
        # Parse date and time to datetime object
        appointment_datetime = datetime.strptime(f"{appointment_date} {appointment_time}", "%Y-%m-%d %H:%M")
        appointment_end_time = appointment_datetime + timedelta(minutes=30)

        # ✅ Check for overlapping appointments in Firebase
        all_bookings = db.reference('bookings').get() or {}
        for user_email, appointments in all_bookings.items():
            for appt in appointments.values():
                if appt.get("lawyer_name") == lawyer_name and appt.get("appointment_date") == appointment_date:
                    appt_time_str = appt.get("appointment_time")
                    try:
                        appt_time = datetime.strptime(f"{appointment_date} {appt_time_str}", "%Y-%m-%d %H:%M")
                        appt_end_time = appt_time + timedelta(minutes=30)
                        if (appointment_datetime < appt_end_time and appointment_end_time > appt_time):
                            return jsonify({"message": f"This time slot is already booked for {lawyer_name}. Please choose another time."}), 400
                    except Exception as e:
                        print(f"Error parsing existing appointment time: {e}")

        # ✅ Save to Firebase
        booking_data = {
            "id": f"{int(datetime.now().timestamp())}",  # Use timestamp as ID
            "appointment_date": appointment_date,
            "client_name": client_name,
            "client_email": client_email,
            "appointment_time": appointment_time,
            "case_details": case_details,
            "lawyer_name": lawyer_name,
            "Bar_Council_ID": barcouncil_id,
            "status": "scheduled"
        }
        sanitized_email = client_email.replace('.', ',')
        db.reference(f'bookings/{sanitized_email}').push().set(booking_data)

        # ✅ Send confirmation email
        email_sent = send_email(client_name, client_email, appointment_date,
                                appointment_time, case_details, lawyer_name)

        if email_sent:
            return jsonify({"success": True, "message": "Appointment booked successfully, and confirmation email sent!"})
        else:
            return jsonify({"success": False, "message": "Appointment booked, but email confirmation failed."}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500
              
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000)) 
    app.run(host="0.0.0.0", port=port)

    