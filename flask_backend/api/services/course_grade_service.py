from ..models import Assignment, CriteriaDescription, Criterion, Review, db


def calculate_student_course_total_grade(student_id: int, course_id: int):
    """Return student's total grade percentage for a course or None if unavailable."""
    rows = (
        db.session.query(Criterion.grade, CriteriaDescription.scoreMax)
        .join(Review, Review.id == Criterion.reviewID)
        .join(Assignment, Assignment.id == Review.assignmentID)
        .join(CriteriaDescription, CriteriaDescription.id == Criterion.criterionRowID)
        .filter(
            Assignment.courseID == course_id,
            Review.revieweeID == student_id,
            CriteriaDescription.hasScore.is_(True),
            Criterion.grade.isnot(None),
            CriteriaDescription.scoreMax.isnot(None),
            CriteriaDescription.scoreMax > 0,
        )
        .all()
    )

    if not rows:
        return None

    earned_points = sum(int(grade) for grade, _ in rows)
    possible_points = sum(int(score_max) for _, score_max in rows)

    if possible_points <= 0:
        return None

    return round((earned_points / possible_points) * 100, 1)
