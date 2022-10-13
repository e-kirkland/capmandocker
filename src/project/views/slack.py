from flask import Blueprint, request, jsonify

slack = Blueprint("slack", __name__, url_prefix="/slack")

