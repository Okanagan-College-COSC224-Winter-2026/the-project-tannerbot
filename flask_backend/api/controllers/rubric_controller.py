from flask import Blueprint, jsonify, request

from ..models import CriteriaDescription, Rubric, CriteriaDescriptionSchema, RubricSchema
from .auth_controller import jwt_teacher_required

bp = Blueprint("rubric", __name__)


@bp.route("/rubric/assignment/<int:assignment_id>", methods=["GET"])
def get_rubric_by_assignment(assignment_id):
    """Get the rubric for a given assignment ID"""
    rubric = Rubric.query.filter_by(assignmentID=assignment_id).order_by(Rubric.id.desc()).first()
    if not rubric:
        return jsonify({"msg": "No rubric found for this assignment"}), 404

    rubric_data = RubricSchema().dump(rubric)
    rubric_data["criteria_descriptions"] = CriteriaDescriptionSchema(many=True).dump(
        rubric.criteria_descriptions.all()
    )
    return jsonify(rubric_data), 200


@bp.route("/criteria", methods=["GET"])
def get_criteria():
    """Get all criteria descriptions for a rubric"""
    rubric_id = request.args.get("rubricID")
    if not rubric_id:
        return jsonify({"msg": "rubricID query parameter is required"}), 400

    rubric = Rubric.get_by_id(int(rubric_id))
    if not rubric:
        return jsonify({"msg": "Rubric not found"}), 404

    criteria = rubric.criteria_descriptions.all()
    return jsonify(CriteriaDescriptionSchema(many=True).dump(criteria)), 200


@bp.route("/create_rubric", methods=["POST"])
@jwt_teacher_required
def create_rubric():
    """Create a new rubric for an assignment"""
    data = request.get_json()
    assignment_id = data.get("assignmentID")
    can_comment = data.get("canComment", True)

    if not assignment_id:
        return jsonify({"msg": "assignmentID is required"}), 400

    existing_rubric = Rubric.query.filter_by(assignmentID=assignment_id).order_by(Rubric.id.desc()).first()
    if existing_rubric:
        return jsonify(RubricSchema().dump(existing_rubric)), 200

    rubric = Rubric(assignmentID=assignment_id, canComment=can_comment)
    Rubric.create_rubric(rubric)

    return jsonify(RubricSchema().dump(rubric)), 201


@bp.route("/create_criteria", methods=["POST"])
@jwt_teacher_required
def create_criteria():
    """Create a new criteria description for a rubric"""
    data = request.get_json()
    rubric_id = data.get("rubricID")
    question = data.get("question", "")
    score_max = data.get("scoreMax", 0)
    has_score = data.get("hasScore", True)

    if not rubric_id:
        return jsonify({"msg": "rubricID is required"}), 400

    rubric = Rubric.get_by_id(rubric_id)
    if not rubric:
        return jsonify({"msg": "Rubric not found"}), 404

    criteria = CriteriaDescription(
        rubricID=rubric_id,
        question=question,
        scoreMax=score_max,
        hasScore=has_score,
    )
    CriteriaDescription.create_criteria_description(criteria)

    return jsonify(CriteriaDescriptionSchema().dump(criteria)), 201


@bp.route("/rubric", methods=["GET"])
def get_rubric():
    """Get a rubric and its criteria descriptions by rubric ID"""
    rubric_id = request.args.get("rubricID")
    if not rubric_id:
        return jsonify({"msg": "rubricID query parameter is required"}), 400

    rubric = Rubric.get_by_id(int(rubric_id))
    if not rubric:
        return jsonify({"msg": "Rubric not found"}), 404

    rubric_data = RubricSchema().dump(rubric)
    rubric_data["criteria_descriptions"] = CriteriaDescriptionSchema(many=True).dump(
        rubric.criteria_descriptions.all()
    )

    return jsonify(rubric_data), 200
