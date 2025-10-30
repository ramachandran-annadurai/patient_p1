"""
Doctors Module Services - FUNCTION-BASED MVC
EXTRACTED FROM app_simple.py lines 9610-9850
Business logic for doctor profile management

NO CHANGES TO LOGIC - Exact extraction, converted to function-based

Architecture:
- Function-based services (each endpoint = one function)
- Database imported globally (db singleton pattern)
- Original logic preserved exactly
"""

from flask import jsonify
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from app.core.database import db


def get_doctor_profile_service(doctor_id: str) -> Tuple[Dict[str, Any], int]:
    """
    Get doctor profile details from doctor_v2 collection - EXACT from line 9610
    
    Args:
        doctor_id: Doctor identifier
    
    Returns:
        Tuple of (response_dict with doctor profile, http_status_code)
    """
    try:
        print(f"[*] Getting doctor profile for doctor {doctor_id}")
        
        # Create sample doctor profile if collection is empty or doesn't exist
        sample_doctor = {
            "doctor_id": doctor_id,
            "name": "Dr. John Smith",
            "specialty": "General Medicine",
            "email": "john.smith@hospital.com",
            "phone": "+1-555-0123",
            "location": "Main Hospital",
            "experience": 10,
            "rating": 4.8,
            "bio": "Experienced general practitioner with expertise in preventive care",
            "education": "MD from Medical School",
            "certifications": ["Board Certified Physician"],
            "languages": ["English"],
            "availability": "Monday-Friday 9AM-5PM",
            "profile_image": "https://example.com/doctor.jpg",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # Try to get from doctor_v2 collection if it exists
        if hasattr(db, 'doctor_v2_collection') and db.doctor_v2_collection is not None:
            try:
                # Try different field names
                doctor = db.doctor_v2_collection.find_one({"doctor_id": doctor_id})
                if not doctor:
                    doctor = db.doctor_v2_collection.find_one({"_id": doctor_id})
                if not doctor:
                    doctor = db.doctor_v2_collection.find_one({"id": doctor_id})
                
                if doctor:
                    # Convert ObjectId to string
                    if '_id' in doctor:
                        doctor['_id'] = str(doctor['_id'])
                    # Convert datetime objects
                    for key, value in doctor.items():
                        if isinstance(value, datetime):
                            doctor[key] = value.isoformat()
                    
                    print(f"[OK] Found doctor profile in database for doctor {doctor_id}")
                    return jsonify({
                        "success": True,
                        "doctor_profile": doctor,
                        "message": "Doctor profile retrieved successfully from doctor_v2 collection"
                    }), 200
            except Exception as e:
                print(f"[WARN] Error accessing doctor_v2 collection: {str(e)}")
        
        # Return sample profile if no database data found
        print(f"[*] Returning sample doctor profile for doctor {doctor_id}")
        return jsonify({
            "success": True,
            "doctor_profile": sample_doctor,
            "message": "Sample doctor profile (database not available or empty)"
        }), 200
        
    except Exception as e:
        print(f"[ERROR] Error retrieving doctor profile: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Failed to retrieve doctor profile: {str(e)}"
        }), 500


def get_doctor_profile_by_id_service(doctor_id: str) -> Tuple[Dict[str, Any], int]:
    """
    Get specific doctor profile by doctor_id - EXACT from line 9683
    
    Args:
        doctor_id: Doctor identifier
    
    Returns:
        Tuple of (response_dict with doctor profile, http_status_code)
    """
    try:
        print(f"[*] Getting doctor profile for doctor_id: {doctor_id}")
        
        # Create sample doctor profile
        sample_doctor = {
            "doctor_id": doctor_id,
            "name": f"Dr. {doctor_id}",
            "specialty": "General Medicine",
            "email": f"{doctor_id.lower()}@hospital.com",
            "phone": "+1-555-0123",
            "location": "Main Hospital",
            "experience": 8,
            "rating": 4.5,
            "bio": f"Experienced doctor with ID {doctor_id}",
            "education": "MD from Medical School",
            "certifications": ["Board Certified Physician"],
            "languages": ["English"],
            "availability": "Monday-Friday 9AM-5PM",
            "profile_image": "https://example.com/doctor.jpg",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # Try to get from doctor_v2 collection if it exists
        if hasattr(db, 'doctor_v2_collection') and db.doctor_v2_collection is not None:
            try:
                # Try different field names
                doctor = db.doctor_v2_collection.find_one({"doctor_id": doctor_id})
                if not doctor:
                    doctor = db.doctor_v2_collection.find_one({"_id": doctor_id})
                if not doctor:
                    doctor = db.doctor_v2_collection.find_one({"id": doctor_id})
                
                if doctor:
                    # Convert ObjectId to string
                    if '_id' in doctor:
                        doctor['_id'] = str(doctor['_id'])
                    # Convert datetime objects
                    for key, value in doctor.items():
                        if isinstance(value, datetime):
                            doctor[key] = value.isoformat()
                    
                    print(f"[OK] Found doctor profile in database for doctor_id: {doctor_id}")
                    return jsonify({
                        "success": True,
                        "doctor_profile": doctor,
                        "message": f"Doctor profile for {doctor_id} retrieved successfully from doctor_v2 collection"
                    }), 200
            except Exception as e:
                print(f"[WARN] Error accessing doctor_v2 collection: {str(e)}")
        
        # Return sample profile if no database data found
        print(f"[*] Returning sample doctor profile for doctor_id: {doctor_id}")
        return jsonify({
            "success": True,
            "doctor_profile": sample_doctor,
            "message": f"Sample doctor profile for {doctor_id} (database not available or empty)"
        }), 200
        
    except Exception as e:
        print(f"[ERROR] Error retrieving doctor profile: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Failed to retrieve doctor profile: {str(e)}"
        }), 500


def get_all_doctors_service(specialty: Optional[str] = None, location: Optional[str] = None, 
                    limit: int = 50, offset: int = 0) -> Tuple[Dict[str, Any], int]:
    """
    Get all doctors from doctor_v2 collection - EXACT from line 9753
    
    Args:
        specialty: Optional filter by doctor specialty
        location: Optional filter by location
        limit: Maximum number of results to return (default: 50)
        offset: Number of results to skip for pagination (default: 0)
    
    Returns:
        Tuple of (response_dict with doctors list, http_status_code)
    """
    try:
        print(f"[*] Getting all doctors from doctor_v2 collection")
        
        # Create sample doctors list
        sample_doctors = [
            {
                "doctor_id": "DOC001",
                "name": "Dr. Sarah Johnson",
                "specialty": "Cardiology",
                "email": "sarah.johnson@hospital.com",
                "phone": "+1-555-0123",
                "location": "New York Medical Center",
                "experience": 8,
                "rating": 4.9,
                "bio": "Experienced cardiologist specializing in interventional procedures",
                "created_at": datetime.now().isoformat()
            },
            {
                "doctor_id": "DOC002", 
                "name": "Dr. Michael Chen",
                "specialty": "Neurology",
                "email": "michael.chen@hospital.com",
                "phone": "+1-555-0456",
                "location": "Los Angeles Medical Center",
                "experience": 12,
                "rating": 4.7,
                "bio": "Board-certified neurologist with expertise in movement disorders",
                "created_at": datetime.now().isoformat()
            },
            {
                "doctor_id": "DOC003",
                "name": "Dr. Emily Davis",
                "specialty": "Pediatrics",
                "email": "emily.davis@hospital.com",
                "phone": "+1-555-0789",
                "location": "Chicago Children's Hospital",
                "experience": 6,
                "rating": 4.8,
                "bio": "Pediatrician with focus on childhood development and preventive care",
                "created_at": datetime.now().isoformat()
            }
        ]
        
        # Try to get from doctor_v2 collection if it exists
        if hasattr(db, 'doctor_v2_collection') and db.doctor_v2_collection is not None:
            try:
                # Build query
                query = {}
                if specialty:
                    query['specialty'] = specialty
                if location:
                    query['location'] = {'$regex': location, '$options': 'i'}
                
                # Get doctors from database
                doctors = list(db.doctor_v2_collection.find(query).skip(offset).limit(limit))
                
                if doctors:
                    # Convert ObjectId to string
                    for doctor in doctors:
                        if '_id' in doctor:
                            doctor['_id'] = str(doctor['_id'])
                        # Convert datetime objects
                        for key, value in doctor.items():
                            if isinstance(value, datetime):
                                doctor[key] = value.isoformat()
                    
                    print(f"[OK] Found {len(doctors)} doctors in database")
                    return jsonify({
                        "success": True,
                        "doctors": doctors,
                        "count": len(doctors),
                        "message": f"Retrieved {len(doctors)} doctors from doctor_v2 collection",
                        "filters_applied": {
                            "specialty": specialty,
                            "location": location,
                            "limit": limit,
                            "offset": offset
                        }
                    }), 200
            except Exception as e:
                print(f"[WARN] Error accessing doctor_v2 collection: {str(e)}")
        
        # Apply filters to sample data if provided
        filtered_doctors = sample_doctors
        if specialty:
            filtered_doctors = [d for d in filtered_doctors if d['specialty'].lower() == specialty.lower()]
        if location:
            filtered_doctors = [d for d in filtered_doctors if location.lower() in d['location'].lower()]
        
        # Return sample doctors if no database data found
        print(f"[*] Returning sample doctors list")
        return jsonify({
            "success": True,
            "doctors": filtered_doctors,
            "count": len(filtered_doctors),
            "message": "Sample doctors list (database not available or empty)",
            "filters_applied": {
                "specialty": specialty,
                "location": location,
                "limit": limit,
                "offset": offset
            }
        }), 200
        
    except Exception as e:
        print(f"[ERROR] Error retrieving doctors: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Failed to retrieve doctors: {str(e)}"
        }), 500
