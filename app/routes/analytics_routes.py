from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required

from app.services.ml_service import *
from app.utils.helpers import clean_response

analytics_bp = Blueprint("analytics", __name__)

@analytics_bp.route("/overview")
@jwt_required()
def overview():
    try:
        return jsonify(clean_response(get_overview_stats())), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@analytics_bp.route("/dashboard-summary")
@jwt_required()
def dashboard_summary():
    try:
        return jsonify(clean_response(get_dashboard_summary())), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@analytics_bp.route("/booking-trends")
@jwt_required()
def booking_trends():
    try:
        return jsonify(clean_response(get_booking_trends())), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@analytics_bp.route("/clusters")
@jwt_required()
def clusters():
    try:
        return jsonify(clean_response(get_clusters())), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@analytics_bp.route("/top-destinations")
@jwt_required()
def top_destinations():
    try:
        return jsonify(clean_response(get_top_destinations())), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@analytics_bp.route("/revenue-analysis")
@jwt_required()
def revenue_analysis():
    try:
        return jsonify(clean_response(get_revenue_analysis())), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@analytics_bp.route("/customer-demographics")
@jwt_required()
def customer_demographics():
    try:
        return jsonify(clean_response(get_customer_demographics())), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@analytics_bp.route("/demand-forecast")
@jwt_required()
def demand_forecast():
    try:
        return jsonify(clean_response(get_demand_forecast())), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@analytics_bp.route("/model-evaluation")
@jwt_required()
def model_evaluation():
    try:
        return jsonify(clean_response(get_model_evaluation())), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

