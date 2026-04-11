from collections import defaultdict
from sqlalchemy import or_

from ..models import Review, Submission
from ..models.group_members_model import Group_Members


def _extract_original_name(stored_name):
    normalized = (stored_name or "").replace("\\", "/").split("/")[-1]
    if "__" in normalized:
        _, original_name = normalized.split("__", 1)
        return original_name
    return normalized


def build_assignment_progress_payload(assignment):
    """Build per-student submission and review completion status for one assignment."""
    course = assignment.course
    students = sorted(list(course.students), key=lambda s: s.id)
    student_ids = [student.id for student in students]

    submissions = []
    reviews = []
    memberships = []
    if student_ids:
        submissions = (
            Submission.query.filter(
                Submission.assignmentID == assignment.id,
                Submission.studentID.in_(student_ids),
            )
            .all()
        )
        reviews = (
            Review.query.filter(
                Review.assignmentID == assignment.id,
                Review.reviewerID.in_(student_ids),
            )
            .all()
        )
        memberships = (
            Group_Members.query.filter(Group_Members.userID.in_(student_ids))
            .filter(
                or_(
                    Group_Members.assignmentID == assignment.id,
                    (Group_Members.assignmentID.is_(None))
                    & Group_Members.group.has(assignmentID=assignment.id),
                )
            )
            .all()
        )

    submission_by_student_id = {submission.studentID: submission for submission in submissions}
    group_by_student_id = {}
    for membership in sorted(memberships, key=lambda membership: (membership.userID, membership.groupID)):
        if membership.userID not in group_by_student_id:
            group_by_student_id[membership.userID] = {
                "id": membership.groupID,
                "name": membership.group.name if membership.group else None,
            }

    reviews_by_reviewer = defaultdict(list)
    for review in reviews:
        reviews_by_reviewer[review.reviewerID].append(review)

    students_payload = []
    for student in students:
        assigned_reviews = reviews_by_reviewer.get(student.id, [])
        total_reviews = len(assigned_reviews)
        completed_reviews = sum(1 for review in assigned_reviews if review.completion_status())
        assigned_peer_reviews = [review for review in assigned_reviews if review.review_type != "group"]
        total_peer_reviews = len(assigned_peer_reviews)
        completed_peer_reviews = sum(
            1 for review in assigned_peer_reviews if review.completion_status()
        )

        students_payload.append(
            {
                "id": student.id,
                "student_id": student.student_id,
                "name": student.name,
                "email": student.email,
                "group": group_by_student_id.get(student.id),
                "has_submitted": student.id in submission_by_student_id,
                "submission": (
                    {
                        "id": submission_by_student_id[student.id].id,
                        "original_name": _extract_original_name(
                            submission_by_student_id[student.id].path
                        ),
                        "download_url": (
                            f"/assignment/{assignment.id}/submission/{student.id}/download"
                        ),
                    }
                    if student.id in submission_by_student_id
                    else None
                ),
                "review_status": {
                    "has_reviewed": completed_reviews > 0,
                    "completed_assigned_reviews": completed_reviews,
                    "total_assigned_reviews": total_reviews,
                    "pending_assigned_reviews": max(total_reviews - completed_reviews, 0),
                    "is_complete": total_reviews > 0 and completed_reviews == total_reviews,
                },
                "peer_review_status": {
                    "has_reviewed": completed_peer_reviews > 0,
                    "completed_assigned_reviews": completed_peer_reviews,
                    "total_assigned_reviews": total_peer_reviews,
                    "pending_assigned_reviews": max(
                        total_peer_reviews - completed_peer_reviews,
                        0,
                    ),
                    "is_complete": (
                        total_peer_reviews > 0
                        and completed_peer_reviews == total_peer_reviews
                    ),
                },
            }
        )

    return {
        "assignment": {
            "id": assignment.id,
            "name": assignment.name,
            "courseID": assignment.courseID,
            "assignment_mode": assignment.assignment_mode,
        },
        "students": students_payload,
    }
