"""
Trimester Module

This module provides pregnancy week and trimester tracking functionality,
with RAG integration for personalized patient experiences.
"""

from flask import Blueprint

# Create the blueprint
trimester_bp = Blueprint('trimester', __name__)

# Import routes after blueprint is created to avoid circular imports
from . import routes

__all__ = ['trimester_bp']

