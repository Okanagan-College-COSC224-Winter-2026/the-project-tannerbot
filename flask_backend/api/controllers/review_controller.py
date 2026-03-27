from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..models import CriterionSchema, Review, ReviewSchema
from .auth_controller import jwt_teacher_required

bp = Blueprint("review", __name__, url_prefix="/review")

review_schema = ReviewSchema()
review_list_schema = ReviewSchema(many=True)
criterion_schema = CriterionSchema(many=True)


def _dump_review_with_markable_criteria(review):
    payload = review_schema.dump(review)
    # Keep FK id fields available even when schema omits include_fk.
    payload["assignmentID"] = review.assignmentID
    payload["reviewerID"] = review.reviewerID
    payload["revieweeID"] = review.revieweeID
    criteria_rows = review.criteria.order_by("id").all()
    criteria_payload = criterion_schema.dump(criteria_rows)
    for entry, row in zip(criteria_payload, criteria_rows):
        entry["criterion_row"] = {
            "id": row.criterion_row.id,
            "question": row.criterion_row.question,
            "scoreMax": row.criterion_row.scoreMax,
            "hasScore": row.criterion_row.hasScore,
        }
    payload["criteria"] = criteria_payload
    payload["review_window_open"] = review.is_review_window_open()
    payload["is_complete"] = review.completion_status()
    return payload


def _dump_received_review_anonymized(review):
    payload = _dump_review_with_markable_criteria(review)
    payload["reviewer"] = {"id": 0, "name": "Anonymous"}
    payload["reviewer_anonymous"] = True
    return payload


@bp.route("/assign", methods=["POST"])
@jwt_teacher_required
def assign_review():
    """Assign peer reviews for an assignment.

    Solo assignments expect reviewerID/revieweeID.
    Group assignments support reviewerGroupID/revieweeGroupID and expand to
    per-student reviews across both groups.
    """
    data = request.get_json(silent=True) or {}

    assignment_id = data.get("assignmentID") or data.get("assignment_id")
    reviewer_id = data.get("reviewerID") or data.get("reviewer_id")
    reviewee_id = data.get("revieweeID") or data.get("reviewee_id")
    reviewer_group_id = data.get("reviewerGroupID") or data.get("reviewer_group_id")
    reviewee_group_id = data.get("revieweeGroupID") or data.get("reviewee_group_id")
    review_type = data.get("reviewType") or data.get("review_type")

    assignment_result, error = Review.assign_review_for_teacher(
        assignment_id=assignment_id,
        reviewer_id=reviewer_id,
        reviewee_id=reviewee_id,
        reviewer_group_id=reviewer_group_id,
        reviewee_group_id=reviewee_group_id,
        review_type=review_type,
        teacher_email=get_jwt_identity(),
    )
    if error:
        body = {"msg": error["msg"]}
        if "review" in error:
            body["review"] = _dump_review_with_markable_criteria(error["review"])
        return jsonify(body), error["status"]

    mode = assignment_result.get("mode", "solo")
    if mode == "group":
        created_reviews = assignment_result.get("created_reviews", [])
        assigned_review_type = assignment_result.get("review_type", "group")
        message = "Group reviews assigned" if assigned_review_type == "group" else "Peer reviews assigned"
        return (
            jsonify(
                {
                    "msg": message,
                    "review_type": assigned_review_type,
                    "created_count": len(created_reviews),
                    "reviews": [
                        _dump_review_with_markable_criteria(review)
                        for review in created_reviews
                    ],
                }
            ),
            201,
        )

    review = assignment_result.get("review")
    return jsonify({"msg": "Review assigned", "review": _dump_review_with_markable_criteria(review)}), 201


@bp.route("/assignment/<int:assignment_id>", methods=["GET"])
@jwt_teacher_required
def list_reviews_for_assignment(assignment_id):
    """List all review assignments for a given assignment."""
    reviews, error = Review.list_for_assignment_for_teacher(
        assignment_id=assignment_id,
        teacher_email=get_jwt_identity(),
    )
    if error:
        return jsonify({"msg": error["msg"]}), error["status"]

    return jsonify(review_list_schema.dump(reviews)), 200


@bp.route("/class/<int:class_id>", methods=["GET"])
@jwt_teacher_required
def list_reviews_for_class(class_id):
    """List all reviews across all assignments in a class for teachers/admins."""
    reviews, error = Review.list_for_class_for_teacher(
        class_id=class_id,
        teacher_email=get_jwt_identity(),
    )
    if error:
        return jsonify({"msg": error["msg"]}), error["status"]

    payload = [_dump_review_with_markable_criteria(review) for review in reviews]
    return jsonify(payload), 200


@bp.route("/assignment/<int:assignment_id>/separated", methods=["GET"])
@jwt_teacher_required
def list_reviews_for_assignment_separated(assignment_id):
    """List all review assignments for a given assignment split by review type."""
    separated, error = Review.list_for_assignment_for_teacher_separated(
        assignment_id=assignment_id,
        teacher_email=get_jwt_identity(),
    )
    if error:
        return jsonify({"msg": error["msg"]}), error["status"]

    payload = {
        "peer_reviews": [
            _dump_review_with_markable_criteria(review)
            for review in separated["peer_reviews"]
        ],
        "group_reviews": [
            _dump_review_with_markable_criteria(review)
            for review in separated["group_reviews"]
        ],
    }
    return jsonify(payload), 200


@bp.route("/my/assignment/<int:assignment_id>", methods=["GET"])
@jwt_required()
def list_my_reviews_for_assignment(assignment_id):
    """List reviews assigned to the authenticated reviewer for a given assignment."""
    reviews, error = Review.list_for_assignment_for_reviewer(
        assignment_id=assignment_id,
        reviewer_email=get_jwt_identity(),
    )
    if error:
        return jsonify({"msg": error["msg"]}), error["status"]

    payload = [_dump_review_with_markable_criteria(review) for review in reviews]
    return jsonify(payload), 200


@bp.route("/my/assignment/<int:assignment_id>/separated", methods=["GET"])
@jwt_required()
def list_my_reviews_for_assignment_separated(assignment_id):
    """List assigned reviews for an assignment, split by review type."""
    separated, error = Review.list_for_assignment_for_reviewer_separated(
        assignment_id=assignment_id,
        reviewer_email=get_jwt_identity(),
    )
    if error:
        return jsonify({"msg": error["msg"]}), error["status"]

    payload = {
        "peer_reviews": [
            _dump_review_with_markable_criteria(review)
            for review in separated["peer_reviews"]
        ],
        "group_reviews": [
            _dump_review_with_markable_criteria(review)
            for review in separated["group_reviews"]
        ],
    }
    return jsonify(payload), 200


@bp.route("/my/received/assignment/<int:assignment_id>/separated", methods=["GET"])
@jwt_required()
def list_reviews_received_for_assignment_separated(assignment_id):
    """List completed reviews received by the current user, with anonymous reviewer identity."""
    reviews, error = Review.list_for_assignment_for_reviewee(
        assignment_id=assignment_id,
        reviewee_email=get_jwt_identity(),
        completed_only=True,
    )
    if error:
        return jsonify({"msg": error["msg"]}), error["status"]

    payload = {
        "peer_reviews": [
            _dump_received_review_anonymized(review)
            for review in reviews
            if review.review_type != "group"
        ],
        "group_reviews": [
            _dump_received_review_anonymized(review)
            for review in reviews
            if review.review_type == "group"
        ],
    }
    return jsonify(payload), 200


@bp.route("/<int:review_id>/mark", methods=["PATCH"])
@jwt_required()
def mark_review(review_id):
    """Mark a review by submitting grades/comments for its criterion rows."""
    data = request.get_json(silent=True) or {}
    criteria_updates = data.get("criteria")

    review, error = Review.mark_review_for_user(
        review_id=review_id,
        actor_email=get_jwt_identity(),
        criteria_updates=criteria_updates,
    )
    if error:
        return jsonify({"msg": error["msg"]}), error["status"]

    return jsonify({"msg": "Review updated", "review": _dump_review_with_markable_criteria(review)}), 200
