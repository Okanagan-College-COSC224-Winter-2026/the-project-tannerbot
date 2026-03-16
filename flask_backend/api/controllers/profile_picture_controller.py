"""Profile picture endpoints."""

import io

from flask import Blueprint, jsonify, request, send_file
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..models import User, UserSchema

bp = Blueprint("profile_picture", __name__, url_prefix="/user")

ALLOWED_PROFILE_PICTURE_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
}
MAX_PROFILE_PICTURE_SIZE_BYTES = 2 * 1024 * 1024

user_schema = UserSchema()


def _get_authenticated_user():
    email = get_jwt_identity()
    return User.get_by_email(email)


def _can_view_user(requesting_user, requested_user):
    if requesting_user.id == requested_user.id or requesting_user.has_role("teacher", "admin"):
        return True

    requesting_classes = {uc.courseID for uc in requesting_user.user_courses}
    requested_classes = {uc.courseID for uc in requested_user.user_courses}
    return bool(requesting_classes & requested_classes)


def _extract_profile_picture_file():
    for key in ("profile_picture", "file", "image"):
        uploaded_file = request.files.get(key)
        if uploaded_file:
            return uploaded_file

    for key in request.files.keys():
        uploaded_file = request.files.get(key)
        if uploaded_file:
            return uploaded_file

    return None


@bp.route("/profile-picture", methods=["POST"])
@jwt_required()
def update_current_user_profile_picture():
    """Upload or replace the current user's profile picture."""
    user = _get_authenticated_user()
    if not user:
        return jsonify({"msg": "User not found"}), 404

    uploaded_file = _extract_profile_picture_file()
    if not uploaded_file or not uploaded_file.filename:
        return jsonify({"msg": "No profile picture uploaded"}), 400

    mime_type = uploaded_file.mimetype or ""
    if mime_type not in ALLOWED_PROFILE_PICTURE_MIME_TYPES:
        return jsonify({"msg": "Profile picture must be a PNG, JPEG, GIF, or WebP image"}), 400

    content = uploaded_file.read()
    if not content:
        return jsonify({"msg": "Uploaded profile picture is empty"}), 400
    if len(content) > MAX_PROFILE_PICTURE_SIZE_BYTES:
        return jsonify({"msg": "Profile picture must be 2 MB or smaller"}), 400

    user.profile_picture = content
    user.profile_picture_mime_type = mime_type
    user.update()

    return jsonify(user_schema.dump(user)), 200


@bp.route("/profile-picture", methods=["DELETE"])
@jwt_required()
def delete_current_user_profile_picture():
    """Remove the current user's profile picture."""
    user = _get_authenticated_user()
    if not user:
        return jsonify({"msg": "User not found"}), 404

    user.profile_picture = None
    user.profile_picture_mime_type = None
    user.update()

    return jsonify(user_schema.dump(user)), 200


@bp.route("/<int:user_id>/profile-picture", methods=["GET"])
@jwt_required()
def get_user_profile_picture(user_id):
    """Return a user's profile picture when the requester can view that user."""
    current_user = _get_authenticated_user()
    if not current_user:
        return jsonify({"msg": "User not found"}), 404

    user = User.get_by_id(user_id)
    if not user:
        return jsonify({"msg": "User not found"}), 404

    if not _can_view_user(current_user, user):
        return jsonify({"msg": "Insufficient permissions"}), 403

    if not user.profile_picture or not user.profile_picture_mime_type:
        return jsonify({"msg": "Profile picture not found"}), 404

    return send_file(
        io.BytesIO(user.profile_picture),
        mimetype=user.profile_picture_mime_type,
        as_attachment=False,
        download_name=f"user-{user.id}-profile-picture",
        max_age=0,
    )