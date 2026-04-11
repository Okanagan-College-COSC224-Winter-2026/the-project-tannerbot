from collections import defaultdict

from ..models import Assignment, Course, Review, Submission


def build_class_progress_payload(course: Course):
    """Build per-student and per-assignment progress payload for an instructor view."""
    students = sorted(list(course.students), key=lambda s: s.id)
    assignments = sorted(Assignment.get_by_class_id(course.id), key=lambda a: a.id)

    student_ids = [student.id for student in students]
    assignment_ids = [assignment.id for assignment in assignments]

    submissions = []
    reviews = []
    if student_ids and assignment_ids:
        submissions = (
            Submission.query.filter(
                Submission.assignmentID.in_(assignment_ids),
                Submission.studentID.in_(student_ids),
            )
            .all()
        )
        reviews = (
            Review.query.filter(
                Review.assignmentID.in_(assignment_ids),
                Review.reviewerID.in_(student_ids),
            )
            .all()
        )

    submitted_pairs = {(submission.assignmentID, submission.studentID) for submission in submissions}
    reviews_by_reviewer = defaultdict(list)
    for review in reviews:
        reviews_by_reviewer[review.reviewerID].append(review)

    students_payload = []
    total_assignments = len(assignments)
    for student in students:
        submitted_assignments = sum(
            1 for assignment in assignments if (assignment.id, student.id) in submitted_pairs
        )

        assigned_reviews = reviews_by_reviewer.get(student.id, [])
        total_reviews = len(assigned_reviews)
        completed_reviews = sum(1 for review in assigned_reviews if review.completion_status())

        students_payload.append(
            {
                "id": student.id,
                "student_id": student.student_id,
                "name": student.name,
                "email": student.email,
                "submission_status": {
                    "submitted_assignments": submitted_assignments,
                    "total_assignments": total_assignments,
                    "pending_assignments": max(total_assignments - submitted_assignments, 0),
                    "is_complete": total_assignments > 0
                    and submitted_assignments == total_assignments,
                },
                "review_completion_status": {
                    "completed_reviews": completed_reviews,
                    "total_reviews": total_reviews,
                    "pending_reviews": max(total_reviews - completed_reviews, 0),
                    "is_complete": total_reviews > 0 and completed_reviews == total_reviews,
                },
            }
        )

    assignments_payload = []
    total_students = len(students)
    for assignment in assignments:
        submitted_students = sum(
            1 for student in students if (assignment.id, student.id) in submitted_pairs
        )

        assignments_payload.append(
            {
                "id": assignment.id,
                "name": assignment.name,
                "submission_status": {
                    "submitted_students": submitted_students,
                    "total_students": total_students,
                    "missing_students": max(total_students - submitted_students, 0),
                    "is_complete": total_students > 0 and submitted_students == total_students,
                },
            }
        )

    return {
        "class": {
            "id": course.id,
            "name": course.name,
        },
        "students": students_payload,
        "assignments": assignments_payload,
    }
