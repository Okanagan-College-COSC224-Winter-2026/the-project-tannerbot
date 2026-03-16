from flask import Blueprint, jsonify, request # type: ignore

from ..models import CriteriaDescription, Rubric, CriteriaDescriptionSchema, RubricSchema
from .auth_controller import jwt_teacher_required

bp = Blueprint("rubric", __name__)
MAX_ASSIGNMENT_SCORE = 100


def _safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_bool(value, default=True):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "on"}:
            return True
        if normalized in {"false", "0", "no", "off"}:
            return False
    if value is None:
        return default
    return bool(value)


def _rubric_scored_total(rubric, exclude_criteria_id=None):
    total = 0
    for row in rubric.criteria_descriptions.all():
        if exclude_criteria_id is not None and row.id == exclude_criteria_id:
            continue
        if row.hasScore:
            total += max(0, _safe_int(row.scoreMax, 0))
    return total


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
    question = str(data.get("question", "")).strip()
    score_max = _safe_int(data.get("scoreMax", 0), 0)
    has_score = _safe_bool(data.get("hasScore", True), True)

    if not rubric_id:
        return jsonify({"msg": "rubricID is required"}), 400

    if not question:
        return jsonify({"msg": "question is required"}), 400

    rubric = Rubric.get_by_id(rubric_id)
    if not rubric:
        return jsonify({"msg": "Rubric not found"}), 404

    score_max = max(0, min(score_max, MAX_ASSIGNMENT_SCORE))
    if has_score and score_max == 0:
        return jsonify({"msg": "scoreMax must be greater than 0 when hasScore is true"}), 400

    proposed_score = score_max if has_score else 0
    current_total = _rubric_scored_total(rubric)
    if current_total + proposed_score > MAX_ASSIGNMENT_SCORE:
        return (
            jsonify({"msg": "Total rubric score cannot exceed 100"}),
            400,
        )

    criteria = CriteriaDescription(
        rubricID=rubric_id,
        question=question,
        scoreMax=score_max,
        hasScore=has_score,
    )
    CriteriaDescription.create_criteria_description(criteria)

    return jsonify(CriteriaDescriptionSchema().dump(criteria)), 201


@bp.route("/criteria/<int:criteria_id>", methods=["PATCH"])
@jwt_teacher_required
def edit_criteria(criteria_id):
    """Edit an existing criteria description"""
    criteria = CriteriaDescription.get_by_id(criteria_id)
    if not criteria:
        return jsonify({"msg": "Criteria not found"}), 404

    data = request.get_json() or {}

    if "question" in data:
        criteria.question = str(data.get("question", "")).strip()
        if not criteria.question:
            return jsonify({"msg": "question is required"}), 400

    if "hasScore" in data:
        criteria.hasScore = _safe_bool(data.get("hasScore"), criteria.hasScore)

    if "scoreMax" in data:
        criteria.scoreMax = _safe_int(data.get("scoreMax", 0), 0)

    criteria.scoreMax = max(0, min(_safe_int(criteria.scoreMax, 0), MAX_ASSIGNMENT_SCORE))
    if criteria.hasScore and criteria.scoreMax == 0:
        return jsonify({"msg": "scoreMax must be greater than 0 when hasScore is true"}), 400

    rubric = Rubric.get_by_id(criteria.rubricID)
    if rubric:
        proposed_score = criteria.scoreMax if criteria.hasScore else 0
        current_total = _rubric_scored_total(rubric, exclude_criteria_id=criteria.id)
        if current_total + proposed_score > MAX_ASSIGNMENT_SCORE:
            return (
                jsonify({"msg": "Total rubric score cannot exceed 100"}),
                400,
            )

    if not criteria.hasScore:
        criteria.scoreMax = 0

    criteria.update()
    return jsonify(CriteriaDescriptionSchema().dump(criteria)), 200


@bp.route("/criteria/<int:criteria_id>", methods=["DELETE"])
@jwt_teacher_required
def delete_criteria(criteria_id):
    """Delete a criteria description"""
    criteria = CriteriaDescription.get_by_id(criteria_id)
    if not criteria:
        return jsonify({"msg": "Criteria not found"}), 404

    criteria.delete()
    return jsonify({"msg": "Criteria deleted"}), 200


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
