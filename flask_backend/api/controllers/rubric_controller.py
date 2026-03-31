from flask import Blueprint, jsonify, request # type: ignore
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..models import (
    Assignment,
    Course,
    CriteriaDescription,
    CriteriaDescriptionSchema,
    Rubric,
    RubricSchema,
    User_Course,
    User,
)
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


def _can_manage_assignment(assignment):
    user = User.get_by_email(get_jwt_identity())
    if not user:
        return False

    course = Course.get_by_id(assignment.courseID)
    if not course:
        return False

    return user.is_admin() or course.teacherID == user.id


def _can_view_assignment(assignment):
    user = User.get_by_email(get_jwt_identity())
    if not user:
        return False

    course = Course.get_by_id(assignment.courseID)
    if not course:
        return False

    return (
        user.is_admin()
        or course.teacherID == user.id
        or User_Course.get(user.id, course.id) is not None
    )


def _validate_assignment_scope_for_rubric(assignment_id, rubric):
    if rubric.assignmentID != int(assignment_id):
        return jsonify({"msg": "Rubric does not belong to the specified assignment"}), 400
    return None


def _validate_assignment_scope_for_criteria(assignment_id, criteria):
    rubric = Rubric.get_by_id(criteria.rubricID)
    if not rubric or rubric.assignmentID != int(assignment_id):
        return None, (jsonify({"msg": "Criteria not found for this assignment"}), 404)
    return rubric, None


@bp.route("/rubric/assignment/<int:assignment_id>", methods=["GET"])
@jwt_required()
def get_rubric_by_assignment(assignment_id):
    """Get the rubric for a given assignment ID"""
    assignment = Assignment.get_by_id(assignment_id)
    if not assignment:
        return jsonify({"msg": "Assignment not found"}), 404
    if not _can_view_assignment(assignment):
        return jsonify({"msg": "Insufficient permissions"}), 403

    rubric_type = request.args.get("rubricType") or request.args.get("rubric_type")
    normalized_rubric_type = Rubric.normalize_rubric_type(rubric_type)
    if rubric_type is not None and normalized_rubric_type is None:
        return jsonify({"msg": "rubricType must be 'peer' or 'group'"}), 400

    rubric = Rubric.get_for_assignment(assignment_id, normalized_rubric_type)
    if not rubric:
        return jsonify({"msg": "No rubric found for this assignment"}), 404

    rubric_data = RubricSchema().dump(rubric)
    rubric_data["criteria_descriptions"] = CriteriaDescriptionSchema(many=True).dump(
        rubric.criteria_descriptions.all()
    )
    return jsonify(rubric_data), 200


@bp.route("/rubric/assignment/<int:assignment_id>/separated", methods=["GET"])
@jwt_required()
def get_rubrics_by_assignment_separated(assignment_id):
    """Get peer and group rubrics separately for an assignment."""
    assignment = Assignment.get_by_id(assignment_id)
    if not assignment:
        return jsonify({"msg": "Assignment not found"}), 404
    if not _can_view_assignment(assignment):
        return jsonify({"msg": "Insufficient permissions"}), 403

    peer_rubric = Rubric.get_for_assignment(assignment_id, "peer")
    group_rubric = Rubric.get_for_assignment(assignment_id, "group")

    def _serialize_or_none(rubric):
        if not rubric:
            return None
        rubric_data = RubricSchema().dump(rubric)
        rubric_data["criteria_descriptions"] = CriteriaDescriptionSchema(many=True).dump(
            rubric.criteria_descriptions.all()
        )
        return rubric_data

    return jsonify({
        "peer_rubric": _serialize_or_none(peer_rubric),
        "group_rubric": _serialize_or_none(group_rubric),
    }), 200


@bp.route("/criteria", methods=["GET"])
@jwt_required()
def get_criteria():
    """Get all criteria descriptions for a rubric"""
    rubric_id = request.args.get("rubricID")
    if not rubric_id:
        return jsonify({"msg": "rubricID query parameter is required"}), 400

    try:
        rubric_id = int(rubric_id)
    except (TypeError, ValueError):
        return jsonify({"msg": "rubricID must be an integer"}), 400

    rubric = Rubric.get_by_id(rubric_id)
    if not rubric:
        return jsonify({"msg": "Rubric not found"}), 404

    assignment = Assignment.get_by_id(rubric.assignmentID)
    if not assignment:
        return jsonify({"msg": "Assignment not found"}), 404
    if not _can_view_assignment(assignment):
        return jsonify({"msg": "Insufficient permissions"}), 403

    criteria = rubric.criteria_descriptions.all()
    return jsonify(CriteriaDescriptionSchema(many=True).dump(criteria)), 200


@bp.route("/create_rubric", methods=["POST"])
@jwt_teacher_required
def create_rubric():
    """Create a new rubric for an assignment"""
    data = request.get_json() or {}
    assignment_id = data.get("assignmentID")
    can_comment = data.get("canComment", True)
    rubric_type = data.get("rubricType") or data.get("rubric_type")

    normalized_rubric_type = Rubric.normalize_rubric_type(rubric_type)
    if normalized_rubric_type is None:
        return jsonify({"msg": "rubricType must be 'peer' or 'group'"}), 400

    if not assignment_id:
        return jsonify({"msg": "assignmentID is required"}), 400

    assignment = Assignment.get_by_id(assignment_id)
    if not assignment:
        return jsonify({"msg": "Assignment not found"}), 404

    if not _can_manage_assignment(assignment):
        return jsonify({"msg": "Unauthorized: You are not the teacher of this class"}), 403

    if assignment.assignment_mode == "solo" and normalized_rubric_type != "peer":
        return jsonify({"msg": "Solo assignments only support peer rubrics"}), 400

    existing_rubric = Rubric.query.filter_by(
        assignmentID=assignment_id,
        rubric_type=normalized_rubric_type,
    ).order_by(Rubric.id.desc()).first()
    if existing_rubric:
        return jsonify(RubricSchema().dump(existing_rubric)), 200

    rubric = Rubric(
        assignmentID=assignment_id,
        canComment=can_comment,
        rubric_type=normalized_rubric_type,
    )
    Rubric.create_rubric(rubric)

    return jsonify(RubricSchema().dump(rubric)), 201


@bp.route("/create_criteria", methods=["POST"])
@jwt_teacher_required
def create_criteria():
    """Create a new criteria description for a rubric"""
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400

    data = request.get_json(silent=True) or {}
    rubric_id = data.get("rubricID")
    question = str(data.get("question", "")).strip()
    score_max = _safe_int(data.get("scoreMax", 0), 0)
    has_score = _safe_bool(data.get("hasScore", True), True)

    if not rubric_id:
        return jsonify({"msg": "rubricID is required"}), 400

    if not question:
        return jsonify({"msg": "question is required"}), 400

    if len(question) > 255:
        return jsonify({"msg": "Question must not exceed 255 characters"}), 400

    rubric = Rubric.get_by_id(rubric_id)
    if not rubric:
        return jsonify({"msg": "Rubric not found"}), 404

    assignment = Assignment.get_by_id(rubric.assignmentID)
    if not assignment:
        return jsonify({"msg": "Assignment not found"}), 404
    if not _can_manage_assignment(assignment):
        return jsonify({"msg": "Unauthorized: You are not the teacher of this class"}), 403

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


@bp.route("/assignment/<int:assignment_id>/criteria", methods=["POST"])
@jwt_teacher_required
def create_criteria_for_assignment(assignment_id):
    """Create a new criteria description scoped to a specific assignment."""
    assignment = Assignment.get_by_id(assignment_id)
    if not assignment:
        return jsonify({"msg": "Assignment not found"}), 404
    if not _can_manage_assignment(assignment):
        return jsonify({"msg": "Unauthorized: You are not the teacher of this class"}), 403

    data = request.get_json() or {}
    rubric_id = data.get("rubricID")
    if not rubric_id:
        return jsonify({"msg": "rubricID is required"}), 400

    rubric = Rubric.get_by_id(rubric_id)
    if not rubric:
        return jsonify({"msg": "Rubric not found"}), 404

    scope_error = _validate_assignment_scope_for_rubric(assignment_id, rubric)
    if scope_error:
        return scope_error

    return create_criteria()


@bp.route("/criteria/<int:criteria_id>", methods=["PATCH"])
@jwt_teacher_required
def edit_criteria(criteria_id):
    """Edit an existing criteria description"""
    criteria = CriteriaDescription.get_by_id(criteria_id)
    if not criteria:
        return jsonify({"msg": "Criteria not found"}), 404

    rubric = Rubric.get_by_id(criteria.rubricID)
    if not rubric:
        return jsonify({"msg": "Rubric not found"}), 404

    assignment = Assignment.get_by_id(rubric.assignmentID)
    if not assignment:
        return jsonify({"msg": "Assignment not found"}), 404
    if not _can_manage_assignment(assignment):
        return jsonify({"msg": "Unauthorized: You are not the teacher of this class"}), 403

    data = request.get_json() or {}

    if "question" in data:
        criteria.question = str(data.get("question", "")).strip()
        if not criteria.question:
            return jsonify({"msg": "question is required"}), 400
        if len(criteria.question) > 255:
            return jsonify({"msg": "Question must not exceed 255 characters"}), 400

    if "hasScore" in data:
        criteria.hasScore = _safe_bool(data.get("hasScore"), criteria.hasScore)

    if "scoreMax" in data:
        criteria.scoreMax = _safe_int(data.get("scoreMax", 0), 0)

    criteria.scoreMax = max(0, min(_safe_int(criteria.scoreMax, 0), MAX_ASSIGNMENT_SCORE))
    if criteria.hasScore and criteria.scoreMax == 0:
        return jsonify({"msg": "scoreMax must be greater than 0 when hasScore is true"}), 400

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


@bp.route("/assignment/<int:assignment_id>/criteria/<int:criteria_id>", methods=["PATCH"])
@jwt_teacher_required
def edit_criteria_for_assignment(assignment_id, criteria_id):
    """Edit an existing criteria description scoped to a specific assignment."""
    assignment = Assignment.get_by_id(assignment_id)
    if not assignment:
        return jsonify({"msg": "Assignment not found"}), 404
    if not _can_manage_assignment(assignment):
        return jsonify({"msg": "Unauthorized: You are not the teacher of this class"}), 403

    criteria = CriteriaDescription.get_by_id(criteria_id)
    if not criteria:
        return jsonify({"msg": "Criteria not found"}), 404

    _, scope_error = _validate_assignment_scope_for_criteria(assignment_id, criteria)
    if scope_error:
        return scope_error

    return edit_criteria(criteria_id)


@bp.route("/criteria/<int:criteria_id>", methods=["DELETE"])
@jwt_teacher_required
def delete_criteria(criteria_id):
    """Delete a criteria description"""
    criteria = CriteriaDescription.get_by_id(criteria_id)
    if not criteria:
        return jsonify({"msg": "Criteria not found"}), 404

    rubric = Rubric.get_by_id(criteria.rubricID)
    if not rubric:
        return jsonify({"msg": "Rubric not found"}), 404

    assignment = Assignment.get_by_id(rubric.assignmentID)
    if not assignment:
        return jsonify({"msg": "Assignment not found"}), 404
    if not _can_manage_assignment(assignment):
        return jsonify({"msg": "Unauthorized: You are not the teacher of this class"}), 403

    criteria.delete()
    return jsonify({"msg": "Criteria deleted"}), 200


@bp.route("/assignment/<int:assignment_id>/criteria/<int:criteria_id>", methods=["DELETE"])
@jwt_teacher_required
def delete_criteria_for_assignment(assignment_id, criteria_id):
    """Delete a criteria description scoped to a specific assignment."""
    assignment = Assignment.get_by_id(assignment_id)
    if not assignment:
        return jsonify({"msg": "Assignment not found"}), 404
    if not _can_manage_assignment(assignment):
        return jsonify({"msg": "Unauthorized: You are not the teacher of this class"}), 403

    criteria = CriteriaDescription.get_by_id(criteria_id)
    if not criteria:
        return jsonify({"msg": "Criteria not found"}), 404

    _, scope_error = _validate_assignment_scope_for_criteria(assignment_id, criteria)
    if scope_error:
        return scope_error

    return delete_criteria(criteria_id)


@bp.route("/rubric", methods=["GET"])
@jwt_required()
def get_rubric():
    """Get a rubric and its criteria descriptions by rubric ID"""
    rubric_id = request.args.get("rubricID")
    if not rubric_id:
        return jsonify({"msg": "rubricID query parameter is required"}), 400

    try:
        rubric_id = int(rubric_id)
    except (TypeError, ValueError):
        return jsonify({"msg": "rubricID must be an integer"}), 400

    rubric = Rubric.get_by_id(rubric_id)
    if not rubric:
        return jsonify({"msg": "Rubric not found"}), 404

    assignment = Assignment.get_by_id(rubric.assignmentID)
    if not assignment:
        return jsonify({"msg": "Assignment not found"}), 404
    if not _can_view_assignment(assignment):
        return jsonify({"msg": "Insufficient permissions"}), 403

    rubric_data = RubricSchema().dump(rubric)
    rubric_data["criteria_descriptions"] = CriteriaDescriptionSchema(many=True).dump(
        rubric.criteria_descriptions.all()
    )

    return jsonify(rubric_data), 200
