"""
GroupMembers model for the peer evaluation app.
"""

from .db import db


class Group_Members(db.Model):
    """Group_Members model representing members of a group"""

    __tablename__ = "Group_Members"

    userID = db.Column(db.Integer, db.ForeignKey("User.id"), primary_key=True)
    groupID = db.Column(db.Integer, db.ForeignKey("CourseGroup.id"), primary_key=True)
    assignmentID = db.Column(db.Integer, db.ForeignKey("Assignment.id"), nullable=True, index=True)

    # relationships
    user = db.relationship("User", back_populates="group_memberships")
    group = db.relationship("CourseGroup", back_populates="members")
    assignment = db.relationship("Assignment", back_populates="group_members")

    def __init__(self, userID, groupID, assignmentID):
        self.userID = userID
        self.groupID = groupID
        self.assignmentID = assignmentID

    def __repr__(self):
        return f"<Group_Members user={self.userID} group={self.groupID}>"

    @classmethod
    def get(cls, userID, groupID):
        """Get group member by userID and groupID"""
        return cls.query.get((int(userID), int(groupID)))

    @classmethod
    def create_group_member(cls, userID, groupID, assignmentID=None):
        """Add a new group member to the database"""
        group_member = cls(
            userID=int(userID),
            groupID=int(groupID),
            assignmentID=(int(assignmentID) if assignmentID is not None else None),
        )
        db.session.add(group_member)
        db.session.commit()
        return group_member

    @classmethod
    def get_for_assignment(cls, assignment_id):
        """Get all group members for an assignment."""
        assignment_id = int(assignment_id)
        return (
            cls.query.filter(
                (cls.assignmentID == assignment_id)
                | ((cls.assignmentID.is_(None)) & cls.group.has(assignmentID=assignment_id))
            )
            .all()
        )

    @classmethod
    def get_for_assignment_and_user(cls, assignment_id, user_id):
        """Get the current group membership for a user on an assignment."""
        assignment_id = int(assignment_id)
        user_id = int(user_id)
        return (
            cls.query.filter_by(userID=user_id)
            .filter(
                (cls.assignmentID == assignment_id)
                | ((cls.assignmentID.is_(None)) & cls.group.has(assignmentID=assignment_id))
            )
            .first()
        )

    def delete(self):
        """Delete group member from the database"""
        db.session.delete(self)
        db.session.commit()
