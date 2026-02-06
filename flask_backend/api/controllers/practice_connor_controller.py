from flask import Blueprint, jsonify

practice = Blueprint("practice", __name__, url_prefix="/practice")


@practice.route("/test", methods=["GET"])
def get_practice():
    return jsonify({'course': 'cosc 224'}), 200
