"""
Appointments Module Services - FUNCTION-BASED MVC
EXTRACTED FROM app_simple.py lines 8727-9604
Business logic for patient and doctor appointment management

NO CHANGES TO LOGIC - Exact extraction, converted to function-based
"""

from flask import jsonify
from datetime import datetime
from bson import ObjectId
from app.core.database import db


# PATIENT APPOINTMENT SERVICES

def get_patient_appointments_service(patient_id, date=None, status=None, consultation_type=None, appointment_type=None):
    """Get all appointments for the authenticated patient - EXACT from line 8727"""
    try:
        if db.patients_collection is None:
            return jsonify({"error": "Database not connected"}), 500
        
        print(f"[*] Getting appointments for patient {patient_id} - date: {date}, status: {status}, type: {consultation_type}, appointment_type: {appointment_type}")
        
        # Get patient document
        patient = db.patients_collection.find_one({"patient_id": patient_id})
        if not patient:
            return jsonify({"error": "Patient not found"}), 404
        
        appointments = patient.get('appointments', [])
        print(f"[*] Found {len(appointments)} total appointments for patient {patient_id}")
        
        # Filter appointments based on query parameters
        filtered_appointments = []
        for appointment in appointments:
            # Filter by date if provided
            if date and appointment.get('appointment_date') != date:
                continue
            
            # Filter by status if provided
            if status is not None and appointment.get('appointment_status') != status:
                continue
            
            # Filter by consultation type if provided (Follow-up, Consultation, etc.)
            if consultation_type and appointment.get('type') != consultation_type:
                continue
            
            # Filter by appointment type (Video Call, In-person) if provided
            if appointment_type and appointment.get('appointment_type') != appointment_type:
                continue
            
            # Add patient info to appointment
            appointment_data = appointment.copy()
            appointment_data['patient_id'] = patient_id
            appointment_data['patient_name'] = f"{patient.get('first_name', '')} {patient.get('last_name', '')}".strip() or patient.get('username', 'Unknown')
            
            filtered_appointments.append(appointment_data)
        
        # Sort by appointment date
        filtered_appointments.sort(key=lambda x: x.get('appointment_date', ''))
        
        print(f"[OK] Found {len(filtered_appointments)} appointments for patient {patient_id}")
        
        return jsonify({
            "appointments": filtered_appointments,
            "total_count": len(filtered_appointments),
            "patient_id": patient_id,
            "message": "Appointments retrieved successfully"
        }), 200
        
    except Exception as e:
        print(f"[ERROR] Error retrieving patient appointments: {str(e)}")
        return jsonify({"error": f"Failed to retrieve appointments: {str(e)}"}), 500


def create_patient_appointment_service(data, patient_id):
    """Create a new appointment request - EXACT from line 8795"""
    try:
        if db.patients_collection is None:
            return jsonify({"error": "Database not connected"}), 500
        
        print(f"[*] Patient {patient_id} creating appointment request - data: {data}")
        
        # Validate required fields - NOW INCLUDES BOTH type AND appointment_type
        required_fields = ['appointment_date', 'appointment_time', 'type', 'appointment_type']
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"{field} is required"}), 400
        
        # Get patient document
        patient = db.patients_collection.find_one({"patient_id": patient_id})
        if not patient:
            return jsonify({"error": "Patient not found"}), 404
        
        print(f"[OK] Patient found: {patient.get('first_name', '')} {patient.get('last_name', '')}")
        
        # Generate unique appointment ID
        appointment_id = str(ObjectId())
        
        # Create appointment object with SEPARATE type and appointment_type
        appointment = {
            "appointment_id": appointment_id,
            "appointment_date": data["appointment_date"],
            "appointment_time": data["appointment_time"],
            "type": data["type"],  # Consultation type: "Follow-up", "Consultation", "Check-up", "Emergency"
            "appointment_type": data["appointment_type"],  # Mode: "Video Call", "In-person"
            "appointment_status": "pending",  # Patient requests start as pending
            "notes": data.get("notes", ""),
            "patient_notes": data.get("patient_notes", ""),
            "doctor_id": data.get("doctor_id", ""),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "status": "active",
            "requested_by": "patient"
        }
        
        print(f"[*] Saving appointment request to patient {patient_id}: {appointment}")
        
        # Add appointment to patient's appointments array
        result = db.patients_collection.update_one(
            {"patient_id": patient_id},
            {"$push": {"appointments": appointment}}
        )
        
        if result.modified_count > 0:
            print(f"[OK] Appointment request saved successfully!")
            return jsonify({
                "appointment_id": appointment_id,
                "message": "Appointment request created successfully",
                "status": "pending",
                "type": data["type"],
                "appointment_type": data["appointment_type"]
            }), 201
        else:
            return jsonify({"error": "Failed to save appointment request"}), 500
        
    except Exception as e:
        print(f"[ERROR] Error creating patient appointment: {str(e)}")
        return jsonify({"error": f"Failed to create appointment: {str(e)}"}), 500


def get_patient_appointment_service(appointment_id, patient_id):
    """Get specific appointment details - EXACT from line 8865"""
    try:
        if db.patients_collection is None:
            return jsonify({"error": "Database not connected"}), 500
        
        print(f"[*] Getting appointment {appointment_id} for patient {patient_id}")
        
        # Get patient document
        patient = db.patients_collection.find_one({"patient_id": patient_id})
        if not patient:
            return jsonify({"error": "Patient not found"}), 404
        
        # Find the specific appointment
        appointments = patient.get('appointments', [])
        appointment = None
        for apt in appointments:
            if apt.get('appointment_id') == appointment_id:
                appointment = apt
                break
        
        if not appointment:
            return jsonify({"error": "Appointment not found"}), 404
        
        # Add patient info to appointment
        appointment_data = appointment.copy()
        appointment_data['patient_id'] = patient_id
        appointment_data['patient_name'] = f"{patient.get('first_name', '')} {patient.get('last_name', '')}".strip() or patient.get('username', 'Unknown')
        
        print(f"[OK] Found appointment: {appointment_data}")
        
        return jsonify({
            "appointment": appointment_data,
            "message": "Appointment retrieved successfully"
        }), 200
        
    except Exception as e:
        print(f"[ERROR] Error retrieving patient appointment: {str(e)}")
        return jsonify({"error": f"Failed to retrieve appointment: {str(e)}"}), 500


def update_patient_appointment_service(appointment_id, data, patient_id):
    """Update appointment details - ONLY for pending appointments - EXACT from line 8909"""
    try:
        if db.patients_collection is None:
            return jsonify({"error": "Database not connected"}), 500
        
        print(f"[*] Patient {patient_id} updating appointment {appointment_id} with data: {data}")
        
        # Get patient document
        patient = db.patients_collection.find_one({"patient_id": patient_id})
        if not patient:
            return jsonify({"error": "Patient not found"}), 404
        
        # Find the appointment
        appointments = patient.get('appointments', [])
        appointment_index = None
        current_appointment = None
        
        for idx, appt in enumerate(appointments):
            if appt.get('appointment_id') == appointment_id:
                appointment_index = idx
                current_appointment = appt
                break
        
        if appointment_index is None:
            return jsonify({"error": "Appointment not found"}), 404
        
        # [WARN] CRITICAL BUSINESS RULE: Cannot update approved appointments
        if current_appointment.get('appointment_status') == 'approved':
            return jsonify({
                "error": "Cannot update approved appointments",
                "message": "This appointment has been approved by the doctor. Please cancel this appointment and create a new one if you need to make changes.",
                "action_required": "cancel_and_recreate",
                "current_status": "approved"
            }), 403  # 403 Forbidden
        
        # Prepare update data - patients can only update certain fields
        update_fields = {}
        allowed_fields = ['appointment_date', 'appointment_time', 'type', 'appointment_type', 'patient_notes', 'notes']
        
        for field in allowed_fields:
            if field in data:
                update_fields[f"appointments.{appointment_index}.{field}"] = data[field]
        
        if not update_fields:
            return jsonify({"error": "No valid fields to update"}), 400
        
        # Add updated_at timestamp
        update_fields[f"appointments.{appointment_index}.updated_at"] = datetime.now().isoformat()
        
        print(f"[*] Updating appointment fields: {update_fields}")
        
        # Update appointment in database
        result = db.patients_collection.update_one(
            {"patient_id": patient_id},
            {"$set": update_fields}
        )
        
        if result.modified_count > 0:
            print(f"[OK] Appointment {appointment_id} updated successfully!")
            
            # Get updated appointment
            updated_patient = db.patients_collection.find_one({"patient_id": patient_id})
            updated_appointment = updated_patient['appointments'][appointment_index]
            
            return jsonify({
                "message": "Appointment updated successfully",
                "appointment": updated_appointment,
                "appointment_id": appointment_id
            }), 200
        else:
            return jsonify({"error": "No changes made to appointment"}), 400
        
    except Exception as e:
        print(f"[ERROR] Error updating patient appointment: {str(e)}")
        return jsonify({"error": f"Failed to update appointment: {str(e)}"}), 500


def cancel_patient_appointment_service(appointment_id, patient_id):
    """Cancel/delete appointment - EXACT from line 8996"""
    try:
        if db.patients_collection is None:
            return jsonify({"error": "Database not connected"}), 500
        
        print(f"[*] Patient {patient_id} cancelling appointment {appointment_id}")
        
        # Remove appointment from patient's appointments array
        result = db.patients_collection.update_one(
            {"patient_id": patient_id},
            {"$pull": {"appointments": {"appointment_id": appointment_id}}}
        )
        
        if result.modified_count > 0:
            print(f"[OK] Appointment {appointment_id} cancelled successfully!")
            return jsonify({
                "message": "Appointment cancelled successfully",
                "appointment_id": appointment_id
            }), 200
        else:
            return jsonify({"error": "Appointment not found or already cancelled"}), 404
        
    except Exception as e:
        print(f"[ERROR] Error cancelling patient appointment: {str(e)}")
        return jsonify({"error": f"Failed to cancel appointment: {str(e)}"}), 500


def get_upcoming_appointments_service(patient_id):
    """Get upcoming appointments - EXACT from line 9027"""
    try:
        if db.patients_collection is None:
            return jsonify({"error": "Database not connected"}), 500
        
        print(f"[*] Getting upcoming appointments for patient {patient_id}")
        
        # Get patient document
        patient = db.patients_collection.find_one({"patient_id": patient_id})
        if not patient:
            return jsonify({"error": "Patient not found"}), 404
        
        appointments = patient.get('appointments', [])
        today = datetime.now().date()
        
        # Filter upcoming appointments (future dates and active status)
        upcoming_appointments = []
        for appointment in appointments:
            appointment_date_str = appointment.get('appointment_date', '')
            appointment_status = appointment.get('appointment_status', '')
            
            if appointment_status in ['scheduled', 'confirmed', 'pending']:
                try:
                    appointment_date = datetime.strptime(appointment_date_str, '%Y-%m-%d').date()
                    if appointment_date >= today:
                        appointment_data = appointment.copy()
                        appointment_data['patient_id'] = patient_id
                        appointment_data['patient_name'] = f"{patient.get('first_name', '')} {patient.get('last_name', '')}".strip() or patient.get('username', 'Unknown')
                        upcoming_appointments.append(appointment_data)
                except ValueError:
                    # Skip appointments with invalid date format
                    continue
        
        # Sort by appointment date
        upcoming_appointments.sort(key=lambda x: x.get('appointment_date', ''))
        
        print(f"[OK] Found {len(upcoming_appointments)} upcoming appointments for patient {patient_id}")
        
        return jsonify({
            "upcoming_appointments": upcoming_appointments,
            "total_count": len(upcoming_appointments),
            "patient_id": patient_id,
            "message": "Upcoming appointments retrieved successfully"
        }), 200
        
    except Exception as e:
        print(f"[ERROR] Error retrieving upcoming appointments: {str(e)}")
        return jsonify({"error": f"Failed to retrieve upcoming appointments: {str(e)}"}), 500


def get_appointment_history_service(patient_id, status=None, consultation_type=None, appointment_type=None, date=None):
    """Get appointment history with filtering - EXACT from line 9081"""
    try:
        if db.patients_collection is None:
            return jsonify({"error": "Database not connected"}), 500
        
        print(f"[*] Getting appointment history for patient {patient_id} - status: {status}, type: {consultation_type}, appointment_type: {appointment_type}, date: {date}")
        
        # Get patient document
        patient = db.patients_collection.find_one({"patient_id": patient_id})
        if not patient:
            return jsonify({"error": "Patient not found"}), 404
        
        appointments = patient.get('appointments', [])
        print(f"[*] Found {len(appointments)} total appointments for patient {patient_id}")
        
        # Filter appointments based on query parameters
        filtered_appointments = []
        for appointment in appointments:
            # Filter by status if provided
            if status and appointment.get('appointment_status') != status:
                continue
            
            # Filter by consultation type if provided (Follow-up, Consultation, etc.)
            if consultation_type and appointment.get('type') != consultation_type:
                continue
            
            # Filter by appointment type (Video Call, In-person) if provided
            if appointment_type and appointment.get('appointment_type') != appointment_type:
                continue
            
            # Filter by date if provided
            if date and appointment.get('appointment_date') != date:
                continue
            
            # Add patient info to appointment
            appointment_data = appointment.copy()
            appointment_data['patient_id'] = patient_id
            appointment_data['patient_name'] = f"{patient.get('first_name', '')} {patient.get('last_name', '')}".strip() or patient.get('username', 'Unknown')
            filtered_appointments.append(appointment_data)
        
        # Sort by appointment date (most recent first)
        filtered_appointments.sort(key=lambda x: x.get('appointment_date', ''), reverse=True)
        
        print(f"[OK] Found {len(filtered_appointments)} appointments in filtered history for patient {patient_id}")
        
        return jsonify({
            "appointment_history": filtered_appointments,
            "total_count": len(filtered_appointments),
            "patient_id": patient_id,
            "filters_applied": {
                "status": status,
                "type": consultation_type,
                "appointment_type": appointment_type,
                "date": date
            },
            "message": "Appointment history retrieved successfully"
        }), 200
        
    except Exception as e:
        print(f"[ERROR] Error retrieving appointment history: {str(e)}")
        return jsonify({"error": f"Failed to retrieve appointment history: {str(e)}"}), 500


# DOCTOR APPOINTMENT SERVICES

def get_doctor_appointments_service(date=None, status=None, appointment_type=None, patient_id=None):
    """Get all appointments for doctor management - EXACT from line 9158"""
    try:
        if db.patients_collection is None:
            return jsonify({"error": "Database not connected"}), 500
        
        print(f"[*] Getting appointments for doctor - date: {date}, status: {status}, type: {appointment_type}, patient: {patient_id}")
        
        # Build query filter
        query_filter = {}
        if patient_id:
            query_filter["patient_id"] = patient_id
        
        # Get all patients with appointments
        patients = db.patients_collection.find(query_filter)
        
        all_appointments = []
        for patient in patients:
            appointments = patient.get('appointments', [])
            for appointment in appointments:
                # Filter appointments based on query parameters
                if date and appointment.get('appointment_date') != date:
                    continue
                if status and appointment.get('appointment_status') != status:
                    continue
                if appointment_type and appointment.get('appointment_type') != appointment_type:
                    continue
                
                # Add patient info to appointment
                appointment_data = appointment.copy()
                appointment_data['patient_id'] = patient.get('patient_id')
                appointment_data['patient_name'] = f"{patient.get('first_name', '')} {patient.get('last_name', '')}".strip() or patient.get('username', 'Unknown')
                appointment_data['patient_email'] = patient.get('email', '')
                appointment_data['patient_mobile'] = patient.get('mobile', '')
                
                all_appointments.append(appointment_data)
        
        # Sort by appointment date
        all_appointments.sort(key=lambda x: x.get('appointment_date', ''))
        
        print(f"[OK] Found {len(all_appointments)} appointments for doctor")
        
        return jsonify({
            "appointments": all_appointments,
            "total_count": len(all_appointments),
            "message": "Appointments retrieved successfully"
        }), 200
        
    except Exception as e:
        print(f"[ERROR] Error retrieving doctor appointments: {str(e)}")
        return jsonify({"error": f"Failed to retrieve appointments: {str(e)}"}), 500


def create_doctor_appointment_service(data):
    """Create a new appointment by doctor - EXACT from line 9218"""
    try:
        if db.patients_collection is None:
            return jsonify({"error": "Database not connected"}), 500
        
        print(f"[*] Doctor creating appointment - data: {data}")
        
        # Validate required fields
        required_fields = ['patient_id', 'appointment_date', 'appointment_time', 'appointment_type']
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"{field} is required"}), 400
        
        patient_id = data['patient_id']
        
        # Get patient document
        patient = db.patients_collection.find_one({"patient_id": patient_id})
        if not patient:
            return jsonify({"error": "Patient not found"}), 404
        
        print(f"[OK] Patient found: {patient.get('first_name', '')} {patient.get('last_name', '')}")
        
        # Generate unique appointment ID
        appointment_id = str(ObjectId())
        
        # Create appointment object
        appointment = {
            "appointment_id": appointment_id,
            "appointment_date": data["appointment_date"],
            "appointment_time": data["appointment_time"],
            "appointment_type": data["appointment_type"],
            "appointment_status": "scheduled",  # Doctor creates as scheduled
            "notes": data.get("notes", ""),
            "patient_notes": data.get("patient_notes", ""),
            "doctor_id": data.get("doctor_id", "DOC001"),
            "doctor_notes": data.get("doctor_notes", ""),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "status": "active",
            "created_by": "doctor"
        }
        
        print(f"[*] Saving appointment to patient {patient_id}: {appointment}")
        
        # Add appointment to patient's appointments array
        result = db.patients_collection.update_one(
            {"patient_id": patient_id},
            {"$push": {"appointments": appointment}}
        )
        
        if result.modified_count > 0:
            print(f"[OK] Appointment created successfully!")
            return jsonify({
                "appointment_id": appointment_id,
                "message": "Appointment created successfully",
                "status": "scheduled"
            }), 201
        else:
            return jsonify({"error": "Failed to create appointment"}), 500
        
    except Exception as e:
        print(f"[ERROR] Error creating doctor appointment: {str(e)}")
        return jsonify({"error": f"Failed to create appointment: {str(e)}"}), 500


def get_doctor_appointment_service(appointment_id):
    """Get specific appointment details for doctor - EXACT from line 9287"""
    try:
        if db.patients_collection is None:
            return jsonify({"error": "Database not connected"}), 500
        
        print(f"[*] Doctor getting appointment {appointment_id}")
        
        # Find patient with this appointment
        patient = db.patients_collection.find_one({
            "appointments.appointment_id": appointment_id
        })
        if not patient:
            return jsonify({"error": "Appointment not found"}), 404
        
        # Find the specific appointment
        appointments = patient.get('appointments', [])
        appointment = None
        for apt in appointments:
            if apt.get('appointment_id') == appointment_id:
                appointment = apt
                break
        
        if not appointment:
            return jsonify({"error": "Appointment not found"}), 404
        
        # Add patient info to appointment
        appointment_data = appointment.copy()
        appointment_data['patient_id'] = patient.get('patient_id')
        appointment_data['patient_name'] = f"{patient.get('first_name', '')} {patient.get('last_name', '')}".strip() or patient.get('username', 'Unknown')
        appointment_data['patient_email'] = patient.get('email', '')
        appointment_data['patient_mobile'] = patient.get('mobile', '')
        
        print(f"[OK] Found appointment: {appointment_data}")
        
        return jsonify({
            "appointment": appointment_data,
            "message": "Appointment retrieved successfully"
        }), 200
        
    except Exception as e:
        print(f"[ERROR] Error retrieving doctor appointment: {str(e)}")
        return jsonify({"error": f"Failed to retrieve appointment: {str(e)}"}), 500


def update_doctor_appointment_service(appointment_id, data):
    """Update an existing appointment - EXACT from line 9333"""
    try:
        if db.patients_collection is None:
            return jsonify({"error": "Database not connected"}), 500
        
        print(f"[*] Doctor updating appointment {appointment_id} with data: {data}")
        
        # Find patient with this appointment
        patient = db.patients_collection.find_one({
            "appointments.appointment_id": appointment_id
        })
        if not patient:
            return jsonify({"error": "Appointment not found"}), 404
        
        # Prepare update data - doctors can update all fields
        update_fields = {}
        allowed_fields = [
            'appointment_date', 'appointment_time', 'appointment_type', 
            'appointment_status', 'notes', 'patient_notes', 'doctor_notes', 'doctor_id'
        ]
        
        for field in allowed_fields:
            if field in data:
                update_fields[f"appointments.$.{field}"] = data[field]
        
        if update_fields:
            update_fields["appointments.$.updated_at"] = datetime.now().isoformat()
            
            # Update the specific appointment in the array
            result = db.patients_collection.update_one(
                {"appointments.appointment_id": appointment_id},
                {"$set": update_fields}
            )
            
            if result.modified_count > 0:
                print(f"[OK] Appointment {appointment_id} updated successfully by doctor")
                return jsonify({"message": "Appointment updated successfully"}), 200
            else:
                return jsonify({"message": "No changes made"}), 200
        else:
            return jsonify({"message": "No valid fields to update"}), 400
        
    except Exception as e:
        print(f"[ERROR] Error updating doctor appointment: {str(e)}")
        return jsonify({"error": f"Failed to update appointment: {str(e)}"}), 500


def delete_doctor_appointment_service(appointment_id):
    """Delete an appointment - EXACT from line 9384"""
    try:
        if db.patients_collection is None:
            return jsonify({"error": "Database not connected"}), 500
        
        print(f"[*] Doctor deleting appointment {appointment_id}")
        
        # Find patient with this appointment
        patient = db.patients_collection.find_one({
            "appointments.appointment_id": appointment_id
        })
        if not patient:
            return jsonify({"error": "Appointment not found"}), 404
        
        # Remove the appointment from the array
        result = db.patients_collection.update_one(
            {"appointments.appointment_id": appointment_id},
            {"$pull": {"appointments": {"appointment_id": appointment_id}}}
        )
        
        if result.modified_count > 0:
            print(f"[OK] Appointment {appointment_id} deleted by doctor")
            return jsonify({"message": "Appointment deleted successfully"}), 200
        else:
            return jsonify({"error": "Failed to delete appointment"}), 500
        
    except Exception as e:
        print(f"[ERROR] Error deleting doctor appointment: {str(e)}")
        return jsonify({"error": f"Failed to delete appointment: {str(e)}"}), 500


def approve_appointment_service(appointment_id, data):
    """Approve a pending appointment - EXACT from line 9417"""
    try:
        if db.patients_collection is None:
            return jsonify({"error": "Database not connected"}), 500
        
        doctor_notes = data.get('doctor_notes', '')
        
        print(f"[*] Doctor approving appointment {appointment_id}")
        
        # Find patient with this appointment
        patient = db.patients_collection.find_one({
            "appointments.appointment_id": appointment_id
        })
        if not patient:
            return jsonify({"error": "Appointment not found"}), 404
        
        # Update appointment status to approved
        result = db.patients_collection.update_one(
            {"appointments.appointment_id": appointment_id},
            {
                "$set": {
                    "appointments.$.appointment_status": "confirmed",
                    "appointments.$.updated_at": datetime.now().isoformat(),
                    "appointments.$.approved_by": "doctor",
                    "appointments.$.doctor_notes": doctor_notes
                }
            }
        )
        
        if result.modified_count > 0:
            print(f"[OK] Appointment {appointment_id} approved by doctor")
            return jsonify({"message": "Appointment approved successfully"}), 200
        else:
            return jsonify({"error": "Failed to approve appointment"}), 500
        
    except Exception as e:
        print(f"[ERROR] Error approving appointment: {str(e)}")
        return jsonify({"error": f"Failed to approve appointment: {str(e)}"}), 500


def reject_appointment_service(appointment_id, data):
    """Reject a pending appointment - EXACT from line 9460"""
    try:
        if db.patients_collection is None:
            return jsonify({"error": "Database not connected"}), 500
        
        doctor_notes = data.get('doctor_notes', '')
        rejection_reason = data.get('rejection_reason', '')
        
        print(f"[*] Doctor rejecting appointment {appointment_id}")
        
        # Find patient with this appointment
        patient = db.patients_collection.find_one({
            "appointments.appointment_id": appointment_id
        })
        if not patient:
            return jsonify({"error": "Appointment not found"}), 404
        
        # Update appointment status to rejected
        result = db.patients_collection.update_one(
            {"appointments.appointment_id": appointment_id},
            {
                "$set": {
                    "appointments.$.appointment_status": "rejected",
                    "appointments.$.updated_at": datetime.now().isoformat(),
                    "appointments.$.rejected_by": "doctor",
                    "appointments.$.doctor_notes": doctor_notes,
                    "appointments.$.rejection_reason": rejection_reason
                }
            }
        )
        
        if result.modified_count > 0:
            print(f"[OK] Appointment {appointment_id} rejected by doctor")
            return jsonify({"message": "Appointment rejected successfully"}), 200
        else:
            return jsonify({"error": "Failed to reject appointment"}), 500
        
    except Exception as e:
        print(f"[ERROR] Error rejecting appointment: {str(e)}")
        return jsonify({"error": f"Failed to reject appointment: {str(e)}"}), 500


def get_pending_appointments_service():
    """Get all pending appointments for doctor approval - EXACT from line 9505"""
    try:
        if db.patients_collection is None:
            return jsonify({"error": "Database not connected"}), 500
        
        print(f"[*] Getting pending appointments for doctor")
        
        # Get all patients with pending appointments
        patients = db.patients_collection.find({
            "appointments.appointment_status": "pending"
        })
        
        pending_appointments = []
        for patient in patients:
            appointments = patient.get('appointments', [])
            for appointment in appointments:
                if appointment.get('appointment_status') == 'pending':
                    # Add patient info to appointment
                    appointment_data = appointment.copy()
                    appointment_data['patient_id'] = patient.get('patient_id')
                    appointment_data['patient_name'] = f"{patient.get('first_name', '')} {patient.get('last_name', '')}".strip() or patient.get('username', 'Unknown')
                    appointment_data['patient_email'] = patient.get('email', '')
                    appointment_data['patient_mobile'] = patient.get('mobile', '')
                    
                    pending_appointments.append(appointment_data)
        
        # Sort by creation date (oldest first)
        pending_appointments.sort(key=lambda x: x.get('created_at', ''))
        
        print(f"[OK] Found {len(pending_appointments)} pending appointments")
        
        return jsonify({
            "pending_appointments": pending_appointments,
            "total_count": len(pending_appointments),
            "message": "Pending appointments retrieved successfully"
        }), 200
        
    except Exception as e:
        print(f"[ERROR] Error retrieving pending appointments: {str(e)}")
        return jsonify({"error": f"Failed to retrieve pending appointments: {str(e)}"}), 500


def get_appointment_statistics_service():
    """Get appointment statistics for doctor dashboard - EXACT from line 9549"""
    try:
        if db.patients_collection is None:
            return jsonify({"error": "Database not connected"}), 500
        
        print(f"[*] Getting appointment statistics for doctor")
        
        # Get all patients with appointments
        patients = db.patients_collection.find({})
        
        stats = {
            "total_appointments": 0,
            "pending": 0,
            "confirmed": 0,
            "cancelled": 0,
            "completed": 0,
            "rejected": 0,
            "today_appointments": 0,
            "upcoming_appointments": 0
        }
        
        today = datetime.now().date()
        
        for patient in patients:
            appointments = patient.get('appointments', [])
            for appointment in appointments:
                stats["total_appointments"] += 1
                
                status = appointment.get('appointment_status', '')
                if status in stats:
                    stats[status] += 1
                
                # Check if appointment is today
                appointment_date_str = appointment.get('appointment_date', '')
                try:
                    appointment_date = datetime.strptime(appointment_date_str, '%Y-%m-%d').date()
                    if appointment_date == today:
                        stats["today_appointments"] += 1
                    elif appointment_date > today and status in ['scheduled', 'confirmed', 'pending']:
                        stats["upcoming_appointments"] += 1
                except ValueError:
                    continue
        
        print(f"[OK] Appointment statistics calculated: {stats}")
        
        return jsonify({
            "statistics": stats,
            "message": "Appointment statistics retrieved successfully"
        }), 200
        
    except Exception as e:
        print(f"[ERROR] Error retrieving appointment statistics: {str(e)}")
        return jsonify({"error": f"Failed to retrieve appointment statistics: {str(e)}"}), 500
