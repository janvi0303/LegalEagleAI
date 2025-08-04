from flask import Blueprint, request, jsonify, session
from firebase_admin import db

case_tracking_bp = Blueprint('case_tracking', __name__)

# Utility to sanitize Firebase keys
def sanitize_email(email):
    return email.replace('.', ',')

def sanitize_barcouncil_id(bcid):
    return bcid.replace('/', '_')

# Utility to fetch lawyer profile by name
def get_lawyer_profile_by_name(name):
    try:
        all_profiles = db.reference("lawyers_profile/lawyer_profile").get() or {}
        for bcid, profile in all_profiles.items():
            if profile.get("name", "").lower() == name.lower():
                return profile
        return {}
    except Exception as e:
        return {"error": str(e)}

# Route to update case status
@case_tracking_bp.route('/case/update_status', methods=['POST'])
def update_case_status():
    if not session.get("admin_logged_in"):
        return jsonify({"error": "Unauthorized"}), 403

    data = request.json
    client_email = data.get("client_email")
    appointment_id = data.get("appointment_id")
    new_status = data.get("status")

    if not client_email or not appointment_id or not new_status:
        return jsonify({"error": "Missing data"}), 400

    try:
        sanitized_email = sanitize_email(client_email)
        booking_ref = db.reference(f'bookings/{sanitized_email}')
        appointments = booking_ref.get() or {}

        for appt_key, appt in appointments.items():
            if appt.get("id") == appointment_id:
                # Update status in Firebase
                booking_ref.child(appt_key).update({"status": new_status})
                # Add client email for context in the response
                appt["status"] = new_status
                appt["client_email"] = client_email
                return jsonify({
                    "message": "Case status updated successfully",
                    "case": appt
                })

        return jsonify({"error": "Appointment not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Route to get all cases for a lawyer (by bar council ID)
@case_tracking_bp.route('/case/lawyer_cases/<bar_council_id>', methods=['GET'])
def get_lawyer_cases(bar_council_id):
    if not session.get("admin_logged_in") and not session.get("lawyer_logged_in"):
        return jsonify({"error": "Unauthorized"}), 403

    try:
        # Get lawyer name from profile
        sanitized_bcid = sanitize_barcouncil_id(bar_council_id)
        profile_ref = db.reference(f'lawyers_profile/lawyer_profile/{sanitized_bcid}')
        lawyer_profile = profile_ref.get()

        if not lawyer_profile:
            return jsonify({"error": "Lawyer profile not found"}), 404

        lawyer_name = lawyer_profile.get("name", "")
        all_bookings = db.reference('bookings').get() or {}

        matched_cases = []
        for raw_email, appointments in all_bookings.items():
            for appt in appointments.values():
                if appt.get("lawyer_name") == lawyer_name:
                    matched_cases.append({
                        **appt,
                        "client_email": raw_email.replace(',', '.'),
                        "lawyer_profile": lawyer_profile
                    })

        return jsonify({"cases": matched_cases})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Route to get all cases for a client (by email)
@case_tracking_bp.route('/case/client_cases/<client_email>', methods=['GET'])
def get_client_cases(client_email):
    if (not session.get("admin_logged_in") and
        not session.get("client_logged_in") and
        session.get("client_email") != client_email):
        return jsonify({"error": "Unauthorized"}), 403

    try:
        sanitized_email = sanitize_email(client_email)
        appointments = db.reference(f'bookings/{sanitized_email}').get() or {}

        case_list = []
        for appt in appointments.values():
            lawyer_name = appt.get("lawyer_name", "")
            lawyer_profile = get_lawyer_profile_by_name(lawyer_name)
            case_list.append({
                **appt,
                "client_email": client_email,
                "lawyer_profile": lawyer_profile
            })

        return jsonify({"cases": case_list})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
