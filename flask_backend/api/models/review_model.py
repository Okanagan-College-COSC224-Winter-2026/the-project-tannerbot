"""Review model for the peer evaluation app."""

from datetime import datetime, timezone

from sqlalchemy.orm import joinedload

from .db import db
from .assignment_model import Assignment
from .criterion_model import Criterion
from .criteria_description_model import CriteriaDescription
from .course_group_model import CourseGroup
from .course_model import Course
from .group_members_model import Group_Members
from .rubric_model import Rubric
from .user_course_model import User_Course
from .user_model import User


class Review(db.Model):
    """Review model representing peer evaluations"""

    __tablename__ = "Review"

    id = db.Column(db.Integer, primary_key=True)
    assignmentID = db.Column(db.Integer, db.ForeignKey("Assignment.id"), nullable=False, index=True)
    reviewerID = db.Column(db.Integer, db.ForeignKey("User.id"), nullable=False, index=True)
    revieweeID = db.Column(db.Integer, db.ForeignKey("User.id"), nullable=False, index=True)
    review_type = db.Column(db.String(16), nullable=False, default="peer", index=True)

    # relationships - using lazy='joined' for commonly accessed foreign entities
    assignment = db.relationship("Assignment", back_populates="reviews", lazy="joined")
    reviewer = db.relationship(
        "User", foreign_keys=[reviewerID], back_populates="reviews_made", lazy="joined"
    )
    reviewee = db.relationship(
        "User", foreign_keys=[revieweeID], back_populates="reviews_received", lazy="joined"
    )
    criteria = db.relationship(
        "Criterion", back_populates="review", cascade="all, delete-orphan", lazy="dynamic"
    )

    def __init__(self, assignmentID, reviewerID, revieweeID, review_type="peer"):
        self.assignmentID = assignmentID
        self.reviewerID = reviewerID
        self.revieweeID = revieweeID
        self.review_type = review_type

    def __repr__(self):
        return f"<Review id={self.id} assignmentID={self.assignmentID}>"

    @staticmethod
    def _ensure_timezone_aware(dt):
        if dt is None:
            return None
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)

    @staticmethod
    def _current_utc_time():
        return datetime.now(timezone.utc)

    @staticmethod
    def _normalize_group_review_type(review_type):
        if review_type is None:
            return "group"
        if not isinstance(review_type, str):
            return None
        normalized = review_type.strip().lower()
        if normalized in {"group", "peer"}:
            return normalized
        return None

    @classmethod
    def _resolve_rubric_for_assignment(cls, assignment, review_type):
        if assignment.assignment_mode == "group":
            target_rubric_type = review_type or "peer"
        else:
            target_rubric_type = "peer"

        rubric = Rubric.get_for_assignment(assignment.id, target_rubric_type)
        if not rubric:
            return None, {
                "msg": f"Cannot assign review because assignment has no {target_rubric_type} rubric",
                "status": 400,
            }

        return rubric, None

    def is_review_window_open(self):
        """Return True when assignment start/due bounds allow review submission."""
        assignment = self.assignment
        if assignment is None:
            return False

        now = self._current_utc_time()
        start = self._ensure_timezone_aware(assignment.start_date)
        due = self._ensure_timezone_aware(assignment.due_date)

        if start and now < start:
            return False
        if due and now > due:
            return False
        return True

    def completion_status(self):
        """Return True when all rubric criteria have required feedback."""
        criteria_rows = self.criteria.order_by("id").all()
        if not criteria_rows:
            return False

        for criterion in criteria_rows:
            criterion_row = criterion.criterion_row
            has_score = True if criterion_row is None else bool(criterion_row.hasScore)

            if has_score and criterion.grade is None:
                return False

            if not has_score and not (criterion.comments and str(criterion.comments).strip()):
                return False

        return True

    @classmethod
    def get_by_id(cls, review_id):
        """Get review by ID (relationships are eagerly loaded via lazy='joined')"""
        return db.session.get(cls, int(review_id))

    @classmethod
    def get_by_id_with_relations(cls, review_id):
        """Get review by ID with all relationships explicitly loaded.
        Use this when you need to ensure assignment's course is also loaded."""
        return (
            cls.query.options(joinedload(cls.assignment).joinedload("course"))
            .filter_by(id=int(review_id))
            .first()
        )

    @classmethod
    def get_all_with_relations(cls):
        """Get all reviews with relationships loaded.
        Assignment relationships (reviewer, reviewee, assignment) are
        automatically loaded via lazy='joined'."""
        return cls.query.options(joinedload(cls.assignment).joinedload("course")).all()

    @classmethod
    def assign_review_for_teacher(
        cls,
        assignment_id,
        reviewer_id,
        reviewee_id,
        teacher_email,
        reviewer_group_id=None,
        reviewee_group_id=None,
        review_type=None,
    ):
        """Assign a review for an assignment after validating teacher access and enrollment.

        Returns:
            ({"mode": "solo", "review": review}, None) on success
            ({"mode": "group", "created_reviews": [review, ...]}, None) on success
            (None, {"msg": str, "status": int}) on failure
        """
        if not assignment_id:
            return None, {"msg": "assignmentID is required", "status": 400}

        try:
            assignment_id = int(assignment_id)
        except (TypeError, ValueError):
            return None, {"msg": "assignmentID must be an integer", "status": 400}

        assignment = Assignment.get_by_id(assignment_id)
        if not assignment:
            return None, {"msg": "Assignment not found", "status": 404}

        course = Course.get_by_id(assignment.courseID)
        if not course:
            return None, {"msg": "Course not found", "status": 404}

        current_user = User.get_by_email(teacher_email)
        if not current_user:
            return None, {"msg": "User not found", "status": 404}

        if course.teacherID != current_user.id and not current_user.is_admin():
            return None, {"msg": "Unauthorized: You are not the teacher of this class", "status": 403}

        normalized_review_type = None
        if assignment.assignment_mode == "group":
            normalized_review_type = cls._normalize_group_review_type(review_type)
            if normalized_review_type is None:
                return None, {
                    "msg": "reviewType must be 'group' or 'peer' for group assignments",
                    "status": 400,
                }

        rubric, rubric_error = cls._resolve_rubric_for_assignment(
            assignment=assignment,
            review_type=normalized_review_type,
        )
        if rubric_error:
            return None, rubric_error

        criteria_rows = rubric.criteria_descriptions.order_by(CriteriaDescription.id.asc()).all()
        if not criteria_rows:
            return None, {
                "msg": "Cannot assign review because rubric has no criteria",
                "status": 400,
            }

        if assignment.assignment_mode == "group":
            return cls._assign_group_to_group_reviews(
                assignment=assignment,
                course=course,
                reviewer_id=reviewer_id,
                reviewee_id=reviewee_id,
                reviewer_group_id=reviewer_group_id,
                reviewee_group_id=reviewee_group_id,
                criteria_rows=criteria_rows,
                review_type=normalized_review_type,
            )

        if not reviewer_id or not reviewee_id:
            return None, {
                "msg": "reviewerID and revieweeID are required for solo assignments",
                "status": 400,
            }

        try:
            reviewer_id = int(reviewer_id)
            reviewee_id = int(reviewee_id)
        except (TypeError, ValueError):
            return None, {"msg": "reviewerID and revieweeID must be integers", "status": 400}

        if reviewer_id == reviewee_id:
            return None, {"msg": "Reviewer and reviewee must be different users", "status": 400}

        reviewer = User.get_by_id(reviewer_id)
        reviewee = User.get_by_id(reviewee_id)
        if not reviewer or not reviewee:
            return None, {"msg": "Reviewer or reviewee user not found", "status": 404}

        if not reviewer.is_student() or not reviewee.is_student():
            return None, {"msg": "Reviewer and reviewee must be students", "status": 400}

        if not User_Course.get(reviewer_id, course.id) or not User_Course.get(reviewee_id, course.id):
            return None, {"msg": "Reviewer and reviewee must be enrolled in the class", "status": 400}

        existing = cls.query.filter_by(
            assignmentID=assignment_id,
            reviewerID=reviewer_id,
            revieweeID=reviewee_id,
        ).first()
        if existing:
            return None, {"msg": "This review assignment already exists", "status": 409, "review": existing}

        review = cls(
            assignmentID=assignment_id,
            reviewerID=reviewer_id,
            revieweeID=reviewee_id,
            review_type="peer",
        )
        db.session.add(review)
        db.session.flush()

        criteria = [Criterion(reviewID=review.id, criterionRowID=row.id) for row in criteria_rows]
        db.session.add_all(criteria)
        db.session.commit()

        return {"mode": "solo", "review": review}, None

    @classmethod
    def _assign_group_to_group_reviews(
        cls,
        assignment,
        course,
        reviewer_id,
        reviewee_id,
        reviewer_group_id,
        reviewee_group_id,
        criteria_rows,
        review_type,
    ):
        assignment_id = assignment.id

        def _membership_group_id_for_user(raw_user_id):
            try:
                user_id = int(raw_user_id)
            except (TypeError, ValueError):
                return None, {"msg": "reviewerID/revieweeID must be integers", "status": 400}

            membership = Group_Members.get_for_assignment_and_user(assignment_id, user_id)
            if not membership:
                return None, {
                    "msg": "Both students must be assigned to groups for this assignment",
                    "status": 400,
                }
            return membership.groupID, None

        if reviewer_group_id is None:
            if reviewer_id is None:
                return None, {
                    "msg": "reviewerGroupID is required for group assignments",
                    "status": 400,
                }
            reviewer_group_id, error = _membership_group_id_for_user(reviewer_id)
            if error:
                return None, error

        if review_type == "group":
            if reviewee_group_id is None:
                if reviewee_id is None:
                    return None, {
                        "msg": "revieweeGroupID is required for group-to-group reviews",
                        "status": 400,
                    }
                reviewee_group_id, error = _membership_group_id_for_user(reviewee_id)
                if error:
                    return None, error

            try:
                reviewer_group_id = int(reviewer_group_id)
                reviewee_group_id = int(reviewee_group_id)
            except (TypeError, ValueError):
                return None, {
                    "msg": "reviewerGroupID and revieweeGroupID must be integers",
                    "status": 400,
                }

            if reviewer_group_id == reviewee_group_id:
                return None, {
                    "msg": "Reviewer and reviewee groups must be different",
                    "status": 400,
                }
        else:
            try:
                reviewer_group_id = int(reviewer_group_id)
            except (TypeError, ValueError):
                return None, {
                    "msg": "reviewerGroupID must be an integer",
                    "status": 400,
                }

            if reviewee_group_id is not None:
                try:
                    reviewee_group_id = int(reviewee_group_id)
                except (TypeError, ValueError):
                    return None, {
                        "msg": "revieweeGroupID must be an integer",
                        "status": 400,
                    }

                if reviewer_group_id != reviewee_group_id:
                    return None, {
                        "msg": "Peer reviews must target members of the same group",
                        "status": 400,
                    }

            reviewee_group_id = reviewer_group_id

        reviewer_group = CourseGroup.get_by_id(reviewer_group_id)
        reviewee_group = CourseGroup.get_by_id(reviewee_group_id)
        if not reviewer_group or not reviewee_group:
            return None, {"msg": "Reviewer or reviewee group not found", "status": 404}

        if reviewer_group.assignmentID != assignment_id or reviewee_group.assignmentID != assignment_id:
            return None, {
                "msg": "Groups must belong to the selected assignment",
                "status": 400,
            }

        reviewer_memberships = Group_Members.query.filter_by(
            assignmentID=assignment_id,
            groupID=reviewer_group_id,
        ).all()
        reviewee_memberships = Group_Members.query.filter_by(
            assignmentID=assignment_id,
            groupID=reviewee_group_id,
        ).all()

        reviewer_student_ids = sorted({membership.userID for membership in reviewer_memberships})
        reviewee_student_ids = sorted({membership.userID for membership in reviewee_memberships})

        if not reviewer_student_ids or not reviewee_student_ids:
            return None, {
                "msg": "Both groups must have at least one student",
                "status": 400,
            }

        if any(not User_Course.get(student_id, course.id) for student_id in reviewer_student_ids + reviewee_student_ids):
            return None, {
                "msg": "All group members must be enrolled in the class",
                "status": 400,
            }

        existing_pairs = {
            (review.reviewerID, review.revieweeID)
            for review in cls.query.filter_by(assignmentID=assignment_id).all()
        }

        created_reviews = []
        if review_type == "peer":
            reviewee_student_ids = reviewer_student_ids

        for reviewer_student_id in reviewer_student_ids:
            for reviewee_student_id in reviewee_student_ids:
                if reviewer_student_id == reviewee_student_id:
                    continue
                if (reviewer_student_id, reviewee_student_id) in existing_pairs:
                    continue

                review = cls(
                    assignmentID=assignment_id,
                    reviewerID=reviewer_student_id,
                    revieweeID=reviewee_student_id,
                    review_type=review_type,
                )
                db.session.add(review)
                db.session.flush()

                criteria = [
                    Criterion(reviewID=review.id, criterionRowID=row.id)
                    for row in criteria_rows
                ]
                db.session.add_all(criteria)

                created_reviews.append(review)
                existing_pairs.add((reviewer_student_id, reviewee_student_id))

        if not created_reviews:
            return None, {
                "msg": "All requested group assignment reviews already exist",
                "status": 409,
            }

        db.session.commit()
        return {
            "mode": "group",
            "review_type": review_type,
            "created_reviews": created_reviews,
        }, None

    @classmethod
    def mark_review_for_user(cls, review_id, actor_email, criteria_updates):
        """Apply grades/comments to criterion rows for a review.

        Reviewer can mark their own review. Course teacher and admins can also update.

        Returns:
            (review, None) on success
            (None, {"msg": str, "status": int}) on failure
        """
        review = cls.get_by_id(review_id)
        if not review:
            return None, {"msg": "Review not found", "status": 404}

        actor = User.get_by_email(actor_email)
        if not actor:
            return None, {"msg": "User not found", "status": 404}

        assignment = Assignment.get_by_id(review.assignmentID)
        if not assignment:
            return None, {"msg": "Assignment not found", "status": 404}

        course = Course.get_by_id(assignment.courseID)
        if not course:
            return None, {"msg": "Course not found", "status": 404}

        can_mark = actor.id == review.reviewerID or actor.is_admin() or actor.id == course.teacherID
        if not can_mark:
            return None, {"msg": "Insufficient permissions", "status": 403}

        if not review.is_review_window_open():
            return None, {
                "msg": "Review period has ended or is not yet open for this assignment",
                "status": 403,
            }

        if not isinstance(criteria_updates, list) or not criteria_updates:
            return None, {
                "msg": "criteria must be a non-empty list of criterion updates",
                "status": 400,
            }

        for update in criteria_updates:
            criterion_id = update.get("criterionID") or update.get("criterion_id")
            if not criterion_id:
                return None, {"msg": "criterionID is required for each criterion update", "status": 400}

            try:
                criterion_id = int(criterion_id)
            except (TypeError, ValueError):
                return None, {"msg": "criterionID must be an integer", "status": 400}

            criterion = Criterion.query.filter_by(id=criterion_id, reviewID=review.id).first()
            if not criterion:
                return None, {
                    "msg": f"Criterion {criterion_id} not found for this review",
                    "status": 404,
                }

            criterion_row = criterion.criterion_row

            if "grade" in update:
                raw_grade = update.get("grade")
                if raw_grade is None:
                    criterion.grade = None
                else:
                    try:
                        grade = int(raw_grade)
                    except (TypeError, ValueError):
                        return None, {"msg": "grade must be an integer or null", "status": 400}

                    if criterion_row and criterion_row.hasScore:
                        max_score = int(criterion_row.scoreMax or 0)
                        if grade < 0 or grade > max_score:
                            return None, {
                                "msg": f"grade for criterion {criterion_id} must be between 0 and {max_score}",
                                "status": 400,
                            }
                    elif criterion_row and not criterion_row.hasScore:
                        return None, {
                            "msg": f"criterion {criterion_id} does not allow numeric scoring",
                            "status": 400,
                        }

                    criterion.grade = grade

            if "comments" in update:
                comments = update.get("comments")
                criterion.comments = None if comments is None else str(comments).strip()

        db.session.commit()
        return review, None

    @classmethod
    def list_for_assignment_for_teacher(cls, assignment_id, teacher_email):
        """List reviews for an assignment after validating teacher access.

        Returns:
            (reviews, None) on success
            (None, {"msg": str, "status": int}) on failure
        """
        assignment = Assignment.get_by_id(assignment_id)
        if not assignment:
            return None, {"msg": "Assignment not found", "status": 404}

        course = Course.get_by_id(assignment.courseID)
        if not course:
            return None, {"msg": "Course not found", "status": 404}

        current_user = User.get_by_email(teacher_email)
        if not current_user:
            return None, {"msg": "User not found", "status": 404}

        if course.teacherID != current_user.id and not current_user.is_admin():
            return None, {"msg": "Unauthorized: You are not the teacher of this class", "status": 403}

        reviews = cls.query.filter_by(assignmentID=assignment_id).all()
        return reviews, None

    @classmethod
    def list_for_assignment_for_teacher_separated(cls, assignment_id, teacher_email):
        """List assignment reviews split into peer and group review buckets for teachers."""
        reviews, error = cls.list_for_assignment_for_teacher(
            assignment_id=assignment_id,
            teacher_email=teacher_email,
        )
        if error:
            return None, error

        separated = {
            "peer_reviews": [review for review in reviews if review.review_type != "group"],
            "group_reviews": [review for review in reviews if review.review_type == "group"],
        }
        return separated, None

    @classmethod
    def list_for_assignment_for_reviewer(cls, assignment_id, reviewer_email, review_type=None):
        """List reviews assigned to the current reviewer for a given assignment.

        Returns:
            (reviews, None) on success
            (None, {"msg": str, "status": int}) on failure
        """
        assignment = Assignment.get_by_id(assignment_id)
        if not assignment:
            return None, {"msg": "Assignment not found", "status": 404}

        reviewer = User.get_by_email(reviewer_email)
        if not reviewer:
            return None, {"msg": "User not found", "status": 404}

        query = cls.query.filter_by(assignmentID=assignment_id, reviewerID=reviewer.id)
        if review_type:
            query = query.filter_by(review_type=review_type)

        reviews = query.order_by(cls.id.asc()).all()
        return reviews, None

    @classmethod
    def list_for_assignment_for_reviewer_separated(cls, assignment_id, reviewer_email):
        """List assigned reviews split into peer and group review buckets."""
        reviews, error = cls.list_for_assignment_for_reviewer(
            assignment_id=assignment_id,
            reviewer_email=reviewer_email,
        )
        if error:
            return None, error

        separated = {
            "peer_reviews": [review for review in reviews if review.review_type != "group"],
            "group_reviews": [review for review in reviews if review.review_type == "group"],
        }
        return separated, None

    @classmethod
    def create_review(cls, review):
        """Add a new review to the database"""
        db.session.add(review)
        db.session.commit()
        return review

    def update(self):
        """Update review in the database"""
        db.session.commit()

    def delete(self):
        """Delete review from the database"""
        db.session.delete(self)
        db.session.commit()
