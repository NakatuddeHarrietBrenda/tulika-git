from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from app.services.ml_service import *
from app.utils.helpers import clean_response

recommendation_bp = Blueprint("recommendation", __name__)

@recommendation_bp.route("/recommend", methods=["POST"])
@jwt_required()
def recommend():
    try:
        data     = request.get_json()
        budget   = float(data.get("budget", 0))
        category = data.get("category", "").strip()
        return jsonify(clean_response(run_recommend(budget, category))), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@recommendation_bp.route("/predict-sentiment", methods=["POST"])
@jwt_required()
def predict_sentiment():
    try:
        data = request.get_json()
        text = data.get("text")
        return jsonify(clean_response(run_predict_sentiment(text))), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

