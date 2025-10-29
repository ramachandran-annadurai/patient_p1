"""
Doctors Module Routes
Handles doctor profile management
EXTRACTED FROM app_simple.py lines 9610-9850
"""

from flask import Blueprint, request
from app.core.auth import token_required
from .services import (
    get_doctor_profile_service,
    get_doctor_profile_by_id_service,
    get_all_doctors_service
)

doctors_bp = Blueprint('doctors', __name__)


@doctors_bp.route('/doctor/profile', methods=['GET'])
@token_required
def get_doctor_profile():
    """Get doctor profile details from doctor_v2 collection"""
    doctor_id = request.user_data['patient_id']
    return get_doctor_profile_service(doctor_id)


@doctors_bp.route('/doctor/profile/<doctor_id>', methods=['GET'])
@token_required
def get_doctor_profile_by_id(doctor_id):
    """Get specific doctor profile by doctor_id from doctor_v2 collection"""
    return get_doctor_profile_by_id_service(doctor_id)


@doctors_bp.route('/doctors', methods=['GET'])
@token_required
def get_all_doctors():
    """Get all doctors from doctor_v2 collection"""
    specialty = request.args.get('specialty')
    location = request.args.get('location')
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    return get_all_doctors_service(specialty, location, limit, offset)
