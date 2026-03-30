"""
Rubric model for the peer evaluation app.
"""

from .db import db


class Rubric(db.Model):
    """Rubric model representing evaluation criteria"""

    __tablename__ = "Rubric"

    id = db.Column(db.Integer, primary_key=True)
    assignmentID = db.Column(db.Integer, db.ForeignKey("Assignment.id"), nullable=False, index=True)
    canComment = db.Column(db.Boolean, nullable=False, default=True)
    rubric_type = db.Column(db.String(16), nullable=False, default="peer", index=True)

    # relationships
    assignment = db.relationship("Assignment", back_populates="rubrics")
    criteria_descriptions = db.relationship(
        "CriteriaDescription", back_populates="rubric", cascade="all, delete-orphan", lazy="dynamic"
    )

    def __init__(self, assignmentID, canComment=True, rubric_type="peer"):
        self.assignmentID = assignmentID
        self.canComment = canComment
        self.rubric_type = rubric_type

    def __repr__(self):
        return f"<Rubric id={self.id} assignmentID={self.assignmentID}>"

    @staticmethod
    def normalize_rubric_type(raw_value):
        if raw_value is None:
            return "peer"
        if not isinstance(raw_value, str):
            return None

        normalized = raw_value.strip().lower()
        if normalized in {"peer", "group"}:
            return normalized
        return None

    @classmethod
    def get_for_assignment(cls, assignment_id, rubric_type=None):
        query = cls.query.filter_by(assignmentID=int(assignment_id))
        if rubric_type:
            query = query.filter_by(rubric_type=rubric_type)
        return query.order_by(cls.id.desc()).first()

    @classmethod
    def get_by_id(cls, rubric_id):
        """Get rubric by ID"""
        return db.session.get(cls, int(rubric_id))

    @classmethod
    def create_rubric(cls, rubric):
        """Add a new rubric to the database"""
        db.session.add(rubric)
        db.session.commit()
        return rubric

    def update(self):
        """Update rubric in the database"""
        db.session.commit()

    def delete(self):
        """Delete rubric from the database"""
        db.session.delete(self)
        db.session.commit()
