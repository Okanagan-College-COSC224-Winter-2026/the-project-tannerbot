"""
Assignment attachment model for database-backed file storage.
"""

from datetime import datetime

from .db import db

# Note: Assignment model is imported here to define the relationship, but it also imports this file for the reverse relationship.
class AssignmentAttachment(db.Model):
    """Attachment metadata and binary content for an assignment."""

    __tablename__ = "AssignmentAttachment"

    id = db.Column(db.Integer, primary_key=True)
    assignmentID = db.Column(db.Integer, db.ForeignKey("Assignment.id"), nullable=False, index=True)
    stored_name = db.Column(db.String(64), nullable=False)
    original_name = db.Column(db.String(255), nullable=False)
    mime_type = db.Column(db.String(255), nullable=True)
    size_bytes = db.Column(db.Integer, nullable=False)
    content = db.Column(db.LargeBinary, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint(
            "assignmentID",
            "stored_name",
            name="uq_assignment_attachment_assignment_stored_name",
        ),
    )

    assignment = db.relationship("Assignment", back_populates="attachments")

    def __init__(self, assignmentID, stored_name, original_name, mime_type, size_bytes, content):
        self.assignmentID = assignmentID
        self.stored_name = stored_name
        self.original_name = original_name
        self.mime_type = mime_type
        self.size_bytes = size_bytes
        self.content = content

    def __repr__(self):
        return (
            f"<AssignmentAttachment id={self.id} assignment={self.assignmentID} "
            f"name={self.original_name}>"
        )

    @classmethod
    def get_for_assignment(cls, assignment_id):
        """Return all attachments for an assignment ordered by creation."""
        return cls.query.filter_by(assignmentID=int(assignment_id)).order_by(cls.id.asc()).all()

    @classmethod
    def get_by_assignment_and_stored_name(cls, assignment_id, stored_name):
        """Return a single attachment for an assignment by its public stored name."""
        return cls.query.filter_by(
            assignmentID=int(assignment_id),
            stored_name=stored_name,
        ).first()

    @classmethod
    def create_attachments(cls, attachments):
        """Persist a batch of attachments in a single transaction."""
        if not attachments:
            return []

        db.session.add_all(attachments)
        db.session.commit()
        return attachments

    def delete(self):
        """Delete a single attachment row."""
        db.session.delete(self)
        db.session.commit()
