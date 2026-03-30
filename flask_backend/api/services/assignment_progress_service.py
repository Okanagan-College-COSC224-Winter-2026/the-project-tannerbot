from collections import defaultdict

from ..models import Review, Submission


def build_assignment_progress_payload(assignment):
    """Build per-student submission and review completion status for one assignment."""
    course = assignment.course
    students = sorted(list(course.students), key=lambda s: s.id)
    student_ids = [student.id for student in students]

    submissions = []
    reviews = []
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

    submitted_student_ids = {submission.studentID for submission in submissions}
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
                "has_submitted": student.id in submitted_student_ids,
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
        },
        "students": students_payload,
    }
