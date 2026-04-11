"""
User model for the peer evaluation app.
"""

from sqlalchemy import CheckConstraint
from sqlalchemy.exc import IntegrityError

from .db import db


class User(db.Model):
    """User model with role-based authentication"""

    __tablename__ = "User"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True, index=True)
    student_id = db.Column(db.String(64), nullable=True, index=True)
    hash_pass = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default="student", nullable=False)
    must_change_password = db.Column(db.Boolean, default=False, nullable=False)
    description = db.Column(db.Text, nullable=True)
    profile_picture = db.Column(db.LargeBinary, nullable=True)
    profile_picture_mime_type = db.Column(db.String(128), nullable=True)

    __table_args__ = (
        CheckConstraint("role IN ('student', 'teacher', 'admin')", name="check_valid_role"),
    )

    # relationships
    teaching_courses = db.relationship(
        "Course", back_populates="teacher", foreign_keys="Course.teacherID", lazy="dynamic"
    )
    user_courses = db.relationship(
        "User_Course", back_populates="user", cascade="all, delete-orphan", lazy="dynamic"
    )
    courses = db.relationship(
        "Course",
        secondary="User_Courses",
        back_populates="students",
        lazy="dynamic",
        overlaps="user_courses",
    )
    submissions = db.relationship(
        "Submission", back_populates="student", cascade="all, delete-orphan", lazy="dynamic"
    )
    reviews_made = db.relationship(
        "Review", back_populates="reviewer", foreign_keys="Review.reviewerID", lazy="dynamic"
    )
    reviews_received = db.relationship(
        "Review", back_populates="reviewee", foreign_keys="Review.revieweeID", lazy="dynamic"
    )
    group_memberships = db.relationship(
        "Group_Members", back_populates="user", cascade="all, delete-orphan", lazy="dynamic"
    )

    def __init__(
        self,
        name,
        email,
        hash_pass,
        role="student",
        must_change_password=False,
        student_id=None,
        description=None,
        profile_picture=None,
        profile_picture_mime_type=None,
    ):
        valid_roles = ["student", "teacher", "admin"]
        if role not in valid_roles:
            raise ValueError(f"Invalid role '{role}'. Must be one of: {', '.join(valid_roles)}")
        self.name = name
        self.email = email
        self.hash_pass = hash_pass
        self.role = role
        self.must_change_password = must_change_password
        self.student_id = student_id
        self.description = description
        self.profile_picture = profile_picture
        self.profile_picture_mime_type = profile_picture_mime_type

    def __repr__(self):
        return f"<User id={self.id} email={self.email}>"

    @classmethod
    def get_by_id(cls, user_id):
        return db.session.get(cls, int(user_id))

    @classmethod
    def get_by_email(cls, email):
        """Get user by email"""
        return cls.query.filter_by(email=email).first()

    @classmethod
    def create_user(cls, user):
        """Add a new user to the database"""
        db.session.add(user)
        db.session.commit()
        return user

    def update(self):
        """Update user in the database"""
        db.session.commit()

    def delete(self):
        """Delete user from the database"""
        db.session.delete(self)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise

    def get_delete_blockers(self):
        """Return related-record counts that block deleting this user."""
        return {
            "teaching_courses": self.teaching_courses.count(),
            "enrollments": self.user_courses.count(),
            "submissions": self.submissions.count(),
            "reviews_made": self.reviews_made.count(),
            "reviews_received": self.reviews_received.count(),
            "group_memberships": self.group_memberships.count(),
        }

    def get_delete_associations(self):
        """Return detailed information about all associations that reference this user."""
        associations = {}
        
        # Teaching courses
        teaching = self.teaching_courses.all()
        if teaching:
            associations["teaching_courses"] = {
                "count": len(teaching),
                "items": [{"id": c.id, "name": c.name} for c in teaching]
            }
        
        # Enrollments (student in courses)
        enrollments = self.user_courses.all()
        if enrollments:
            associations["enrollments"] = {
                "count": len(enrollments),
                "items": [{"course_id": uc.courseID, "course_name": uc.course.name} 
                         for uc in enrollments if uc.course]
            }
        
        # Submissions
        submissions = self.submissions.all()
        if submissions:
            associations["submissions"] = {
                "count": len(submissions),
                "items": [{"id": s.id, "assignment_id": s.assignmentID, 
                          "assignment_name": s.assignment.name if s.assignment else "Unknown"}
                         for s in submissions]
            }
        
        # Reviews made
        reviews_made = self.reviews_made.all()
        if reviews_made:
            associations["reviews_made"] = {
                "count": len(reviews_made),
                "items": [{"id": r.id, "assignment_id": r.assignmentID,
                          "reviewee_id": r.revieweeID, "reviewee_name": r.reviewee.name if r.reviewee else "Unknown"}
                         for r in reviews_made]
            }
        
        # Reviews received
        reviews_received = self.reviews_received.all()
        if reviews_received:
            associations["reviews_received"] = {
                "count": len(reviews_received),
                "items": [{"id": r.id, "assignment_id": r.assignmentID,
                          "reviewer_id": r.reviewerID, "reviewer_name": r.reviewer.name if r.reviewer else "Unknown"}
                         for r in reviews_received]
            }
        
        # Group memberships
        group_memberships = self.group_memberships.all()
        if group_memberships:
            associations["group_memberships"] = {
                "count": len(group_memberships),
                "items": [{"group_id": gm.groupID, 
                          "group_name": gm.group.name if gm.group else "Unknown"}
                         for gm in group_memberships]
            }
        
        return associations

    def cascade_delete(self):
        """Delete all associations and then delete the user."""
        try:
            # Delete teaching courses (cascade should handle this via relationship)
            for course in self.teaching_courses.all():
                db.session.delete(course)
            
            # Delete enrollments (user_courses)
            for enrollment in self.user_courses.all():
                db.session.delete(enrollment)
            
            # Delete submissions (cascade should handle via relationship)
            for submission in self.submissions.all():
                db.session.delete(submission)
            
            # Delete reviews made by this user
            for review in self.reviews_made.all():
                db.session.delete(review)
            
            # Delete reviews received by this user
            for review in self.reviews_received.all():
                db.session.delete(review)
            
            # Delete group memberships (cascade should handle via relationship)
            for membership in self.group_memberships.all():
                db.session.delete(membership)
            
            # Finally delete the user
            db.session.delete(self)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e

    def is_teacher_user(self):
        """Check if the user is a teacher (backward compatibility)"""
        return self.role == "teacher"

    def is_teacher(self):
        """Check if the user is a teacher"""
        return self.role == "teacher"

    def is_admin(self):
        """Check if the user is an admin"""
        return self.role == "admin"

    def is_student(self):
        """Check if the user is a student"""
        return self.role == "student"

    def has_role(self, *roles):
        """Check if the user has any of the specified roles"""
        return self.role in roles
