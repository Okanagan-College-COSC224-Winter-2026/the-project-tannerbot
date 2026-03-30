"""Tests for review assignment and marking endpoints."""

import json
from datetime import datetime, timedelta, timezone

from werkzeug.security import generate_password_hash

from api.models.assignment_model import Assignment
from api.models.course_group_model import CourseGroup
from api.models.course_model import Course
from api.models.criteria_description_model import CriteriaDescription
from api.models.criterion_model import Criterion
from api.models.group_members_model import Group_Members
from api.models.review_model import Review
from api.models.rubric_model import Rubric
from api.models.user_model import User


def _login(client, email, password):
    return client.post(
        "/auth/login",
        data=json.dumps({"email": email, "password": password}),
        headers={"Content-Type": "application/json"},
    )


def _seed_course_with_assignment_and_rubric(db):
    teacher = User(
        name="Teacher",
        email="teacher@example.com",
        hash_pass=generate_password_hash("Password1!"),
        role="teacher",
    )
    reviewer = User(
        name="Reviewer",
        email="reviewer@example.com",
        hash_pass=generate_password_hash("Password1!"),
        role="student",
    )
    reviewee = User(
        name="Reviewee",
        email="reviewee@example.com",
        hash_pass=generate_password_hash("Password1!"),
        role="student",
    )
    other_student = User(
        name="Other Student",
        email="other@example.com",
        hash_pass=generate_password_hash("Password1!"),
        role="student",
    )

    db.session.add_all([teacher, reviewer, reviewee, other_student])
    db.session.commit()

    course = Course(teacherID=teacher.id, name="Comp Sci 101")
    db.session.add(course)
    db.session.commit()

    assignment = Assignment(courseID=course.id, name="Peer Review 1", rubric_text="")
    db.session.add(assignment)
    db.session.commit()

    rubric = Rubric(assignmentID=assignment.id, canComment=True)
    db.session.add(rubric)
    db.session.commit()

    c1 = CriteriaDescription(
        rubricID=rubric.id,
        question="Quality of explanation",
        scoreMax=5,
        hasScore=True,
    )
    c2 = CriteriaDescription(
        rubricID=rubric.id,
        question="Actionable feedback",
        scoreMax=3,
        hasScore=True,
    )
    db.session.add_all([c1, c2])
    db.session.commit()

    return {
        "teacher": teacher,
        "reviewer": reviewer,
        "reviewee": reviewee,
        "other_student": other_student,
        "course": course,
        "assignment": assignment,
        "rubric": rubric,
        "criteria": [c1, c2],
    }


def _add_group_rubric_with_matching_criteria(db, seeded):
    group_rubric = Rubric(
        assignmentID=seeded["assignment"].id,
        canComment=True,
        rubric_type="group",
    )
    db.session.add(group_rubric)
    db.session.commit()

    for criterion in seeded["criteria"]:
        db.session.add(
            CriteriaDescription(
                rubricID=group_rubric.id,
                question=criterion.question,
                scoreMax=criterion.scoreMax,
                hasScore=criterion.hasScore,
            )
        )
    db.session.commit()


def test_assign_review_creates_markable_criteria(test_client, db, enroll_user_in_course):
    seeded = _seed_course_with_assignment_and_rubric(db)

    enroll_user_in_course(seeded["reviewer"].id, seeded["course"].id)
    enroll_user_in_course(seeded["reviewee"].id, seeded["course"].id)

    login_resp = _login(test_client, seeded["teacher"].email, "Password1!")
    assert login_resp.status_code == 200

    assign_resp = test_client.post(
        "/review/assign",
        data=json.dumps(
            {
                "assignmentID": seeded["assignment"].id,
                "reviewerID": seeded["reviewer"].id,
                "revieweeID": seeded["reviewee"].id,
            }
        ),
        headers={"Content-Type": "application/json"},
    )

    assert assign_resp.status_code == 201
    payload = assign_resp.get_json()
    assert payload["msg"] == "Review assigned"
    assert "criteria" in payload["review"]
    assert len(payload["review"]["criteria"]) == 2

    first = payload["review"]["criteria"][0]
    assert first["grade"] is None
    assert "criterion_row" in first
    assert "question" in first["criterion_row"]


def test_assign_review_fails_when_assignment_has_no_rubric(test_client, db, enroll_user_in_course):
    teacher = User(
        name="Teacher",
        email="teacher@example.com",
        hash_pass=generate_password_hash("Password1!"),
        role="teacher",
    )
    reviewer = User(
        name="Reviewer",
        email="reviewer@example.com",
        hash_pass=generate_password_hash("Password1!"),
        role="student",
    )
    reviewee = User(
        name="Reviewee",
        email="reviewee@example.com",
        hash_pass=generate_password_hash("Password1!"),
        role="student",
    )
    db.session.add_all([teacher, reviewer, reviewee])
    db.session.commit()

    course = Course(teacherID=teacher.id, name="Comp Sci 101")
    db.session.add(course)
    db.session.commit()

    assignment = Assignment(courseID=course.id, name="Peer Review 1", rubric_text="")
    db.session.add(assignment)
    db.session.commit()

    enroll_user_in_course(reviewer.id, course.id)
    enroll_user_in_course(reviewee.id, course.id)

    _login(test_client, teacher.email, "Password1!")

    assign_resp = test_client.post(
        "/review/assign",
        data=json.dumps(
            {
                "assignmentID": assignment.id,
                "reviewerID": reviewer.id,
                "revieweeID": reviewee.id,
            }
        ),
        headers={"Content-Type": "application/json"},
    )

    assert assign_resp.status_code == 400
    assert "no peer rubric" in assign_resp.get_json()["msg"].lower()


def test_reviewer_can_mark_review_criteria(test_client, db, enroll_user_in_course):
    seeded = _seed_course_with_assignment_and_rubric(db)

    enroll_user_in_course(seeded["reviewer"].id, seeded["course"].id)
    enroll_user_in_course(seeded["reviewee"].id, seeded["course"].id)

    _login(test_client, seeded["teacher"].email, "Password1!")
    assign_resp = test_client.post(
        "/review/assign",
        data=json.dumps(
            {
                "assignmentID": seeded["assignment"].id,
                "reviewerID": seeded["reviewer"].id,
                "revieweeID": seeded["reviewee"].id,
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    review_payload = assign_resp.get_json()["review"]
    review_id = review_payload["id"]

    criteria = review_payload["criteria"]
    mark_resp = _login(test_client, seeded["reviewer"].email, "Password1!")
    assert mark_resp.status_code == 200

    update_resp = test_client.patch(
        f"/review/{review_id}/mark",
        data=json.dumps(
            {
                "criteria": [
                    {
                        "criterionID": criteria[0]["id"],
                        "grade": 4,
                        "comments": "Clear and specific.",
                    },
                    {
                        "criterionID": criteria[1]["id"],
                        "grade": 3,
                        "comments": "Strong suggestions.",
                    },
                ]
            }
        ),
        headers={"Content-Type": "application/json"},
    )

    assert update_resp.status_code == 200
    updated_review = update_resp.get_json()["review"]
    updated_criteria = {c["id"]: c for c in updated_review["criteria"]}
    assert updated_criteria[criteria[0]["id"]]["grade"] == 4
    assert updated_criteria[criteria[1]["id"]]["grade"] == 3


def test_non_reviewer_student_cannot_mark_review(test_client, db, enroll_user_in_course):
    seeded = _seed_course_with_assignment_and_rubric(db)

    enroll_user_in_course(seeded["reviewer"].id, seeded["course"].id)
    enroll_user_in_course(seeded["reviewee"].id, seeded["course"].id)
    enroll_user_in_course(seeded["other_student"].id, seeded["course"].id)

    _login(test_client, seeded["teacher"].email, "Password1!")
    assign_resp = test_client.post(
        "/review/assign",
        data=json.dumps(
            {
                "assignmentID": seeded["assignment"].id,
                "reviewerID": seeded["reviewer"].id,
                "revieweeID": seeded["reviewee"].id,
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    review_id = assign_resp.get_json()["review"]["id"]
    criterion_id = assign_resp.get_json()["review"]["criteria"][0]["id"]

    _login(test_client, seeded["other_student"].email, "Password1!")
    forbidden_resp = test_client.patch(
        f"/review/{review_id}/mark",
        data=json.dumps(
            {
                "criteria": [
                    {
                        "criterionID": criterion_id,
                        "grade": 2,
                        "comments": "Should not be allowed.",
                    }
                ]
            }
        ),
        headers={"Content-Type": "application/json"},
    )

    assert forbidden_resp.status_code == 403


def test_mark_review_validates_grade_range(test_client, db, enroll_user_in_course):
    seeded = _seed_course_with_assignment_and_rubric(db)

    enroll_user_in_course(seeded["reviewer"].id, seeded["course"].id)
    enroll_user_in_course(seeded["reviewee"].id, seeded["course"].id)

    _login(test_client, seeded["teacher"].email, "Password1!")
    assign_resp = test_client.post(
        "/review/assign",
        data=json.dumps(
            {
                "assignmentID": seeded["assignment"].id,
                "reviewerID": seeded["reviewer"].id,
                "revieweeID": seeded["reviewee"].id,
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    review_id = assign_resp.get_json()["review"]["id"]
    criterion_id = assign_resp.get_json()["review"]["criteria"][0]["id"]

    _login(test_client, seeded["reviewer"].email, "Password1!")
    bad_grade_resp = test_client.patch(
        f"/review/{review_id}/mark",
        data=json.dumps(
            {
                "criteria": [
                    {
                        "criterionID": criterion_id,
                        "grade": 99,
                        "comments": "Out of range.",
                    }
                ]
            }
        ),
        headers={"Content-Type": "application/json"},
    )

    assert bad_grade_resp.status_code == 400
    assert "between 0 and" in bad_grade_resp.get_json()["msg"]

    review = Review.get_by_id(review_id)
    criterion = review.criteria.filter_by(id=criterion_id).first()
    assert criterion.grade is None


def test_reviewer_cannot_mark_when_review_window_closed(test_client, db, enroll_user_in_course):
    seeded = _seed_course_with_assignment_and_rubric(db)

    enroll_user_in_course(seeded["reviewer"].id, seeded["course"].id)
    enroll_user_in_course(seeded["reviewee"].id, seeded["course"].id)

    seeded["assignment"].due_date = datetime.now(timezone.utc) - timedelta(hours=1)
    db.session.commit()

    _login(test_client, seeded["teacher"].email, "Password1!")
    assign_resp = test_client.post(
        "/review/assign",
        data=json.dumps(
            {
                "assignmentID": seeded["assignment"].id,
                "reviewerID": seeded["reviewer"].id,
                "revieweeID": seeded["reviewee"].id,
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    review_id = assign_resp.get_json()["review"]["id"]
    criterion_id = assign_resp.get_json()["review"]["criteria"][0]["id"]

    _login(test_client, seeded["reviewer"].email, "Password1!")
    blocked_resp = test_client.patch(
        f"/review/{review_id}/mark",
        data=json.dumps(
            {
                "criteria": [
                    {
                        "criterionID": criterion_id,
                        "grade": 2,
                        "comments": "Late submission",
                    }
                ]
            }
        ),
        headers={"Content-Type": "application/json"},
    )

    assert blocked_resp.status_code == 403
    assert "review period" in blocked_resp.get_json()["msg"].lower()


def test_reviewer_can_list_assigned_reviews_for_assignment(test_client, db, enroll_user_in_course):
    seeded = _seed_course_with_assignment_and_rubric(db)

    enroll_user_in_course(seeded["reviewer"].id, seeded["course"].id)
    enroll_user_in_course(seeded["reviewee"].id, seeded["course"].id)

    _login(test_client, seeded["teacher"].email, "Password1!")
    assign_resp = test_client.post(
        "/review/assign",
        data=json.dumps(
            {
                "assignmentID": seeded["assignment"].id,
                "reviewerID": seeded["reviewer"].id,
                "revieweeID": seeded["reviewee"].id,
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    assert assign_resp.status_code == 201

    _login(test_client, seeded["reviewer"].email, "Password1!")
    list_resp = test_client.get(f"/review/my/assignment/{seeded['assignment'].id}")

    assert list_resp.status_code == 200
    payload = list_resp.get_json()
    assert isinstance(payload, list)
    assert len(payload) == 1
    assert payload[0]["reviewee"]["id"] == seeded["reviewee"].id
    assert len(payload[0]["criteria"]) == 2


def test_group_assignment_assigns_reviews_group_to_group(test_client, db, enroll_user_in_course):
    seeded = _seed_course_with_assignment_and_rubric(db)

    student_a = seeded["reviewer"]
    student_b = seeded["other_student"]
    student_c = seeded["reviewee"]

    seeded["assignment"].assignment_mode = "group"
    db.session.commit()
    _add_group_rubric_with_matching_criteria(db, seeded)

    enroll_user_in_course(student_a.id, seeded["course"].id)
    enroll_user_in_course(student_b.id, seeded["course"].id)
    enroll_user_in_course(student_c.id, seeded["course"].id)

    group_one = CourseGroup(name="Team One", assignmentID=seeded["assignment"].id)
    group_two = CourseGroup(name="Team Two", assignmentID=seeded["assignment"].id)
    db.session.add_all([group_one, group_two])
    db.session.commit()

    db.session.add_all(
        [
            Group_Members(userID=student_a.id, groupID=group_one.id, assignmentID=seeded["assignment"].id),
            Group_Members(userID=student_b.id, groupID=group_one.id, assignmentID=seeded["assignment"].id),
            Group_Members(userID=student_c.id, groupID=group_two.id, assignmentID=seeded["assignment"].id),
        ]
    )
    db.session.commit()

    _login(test_client, seeded["teacher"].email, "Password1!")
    assign_resp = test_client.post(
        "/review/assign",
        data=json.dumps(
            {
                "assignmentID": seeded["assignment"].id,
                "reviewerGroupID": group_one.id,
                "revieweeGroupID": group_two.id,
            }
        ),
        headers={"Content-Type": "application/json"},
    )

    assert assign_resp.status_code == 201
    payload = assign_resp.get_json()
    assert payload["msg"] == "Group reviews assigned"
    assert payload["review_type"] == "group"
    assert payload["created_count"] == 1

    created_pairs = {
        (review["reviewer"]["id"], review["reviewee"]["id"])
        for review in payload["reviews"]
    }
    assert created_pairs == {(student_a.id, student_c.id)}


def test_group_assignment_can_assign_peer_reviews_within_group(test_client, db, enroll_user_in_course):
    seeded = _seed_course_with_assignment_and_rubric(db)

    student_a = seeded["reviewer"]
    student_b = seeded["other_student"]
    student_c = seeded["reviewee"]

    seeded["assignment"].assignment_mode = "group"
    db.session.commit()

    enroll_user_in_course(student_a.id, seeded["course"].id)
    enroll_user_in_course(student_b.id, seeded["course"].id)
    enroll_user_in_course(student_c.id, seeded["course"].id)

    group_one = CourseGroup(name="Team One", assignmentID=seeded["assignment"].id)
    db.session.add(group_one)
    db.session.commit()

    db.session.add_all(
        [
            Group_Members(userID=student_a.id, groupID=group_one.id, assignmentID=seeded["assignment"].id),
            Group_Members(userID=student_b.id, groupID=group_one.id, assignmentID=seeded["assignment"].id),
            Group_Members(userID=student_c.id, groupID=group_one.id, assignmentID=seeded["assignment"].id),
        ]
    )
    db.session.commit()

    _login(test_client, seeded["teacher"].email, "Password1!")
    assign_resp = test_client.post(
        "/review/assign",
        data=json.dumps(
            {
                "assignmentID": seeded["assignment"].id,
                "reviewType": "peer",
                "reviewerGroupID": group_one.id,
            }
        ),
        headers={"Content-Type": "application/json"},
    )

    assert assign_resp.status_code == 201
    payload = assign_resp.get_json()
    assert payload["msg"] == "Peer reviews assigned"
    assert payload["review_type"] == "peer"
    assert payload["created_count"] == 6

    created_pairs = {
        (review["reviewer"]["id"], review["reviewee"]["id"], review["review_type"])
        for review in payload["reviews"]
    }
    assert created_pairs == {
        (student_a.id, student_b.id, "peer"),
        (student_a.id, student_c.id, "peer"),
        (student_b.id, student_a.id, "peer"),
        (student_b.id, student_c.id, "peer"),
        (student_c.id, student_a.id, "peer"),
        (student_c.id, student_b.id, "peer"),
    }

    _login(test_client, student_a.email, "Password1!")
    list_resp = test_client.get(f"/review/my/assignment/{seeded['assignment'].id}")
    assert list_resp.status_code == 200
    my_reviews = list_resp.get_json()
    assert len(my_reviews) == 2
    assert all(review["review_type"] == "peer" for review in my_reviews)
    assert {review["reviewee"]["id"] for review in my_reviews} == {student_b.id, student_c.id}


def test_group_assignment_rejects_same_group_review_pair(test_client, db, enroll_user_in_course):
    seeded = _seed_course_with_assignment_and_rubric(db)
    seeded["assignment"].assignment_mode = "group"
    db.session.commit()
    _add_group_rubric_with_matching_criteria(db, seeded)

    enroll_user_in_course(seeded["reviewer"].id, seeded["course"].id)

    group_one = CourseGroup(name="Team One", assignmentID=seeded["assignment"].id)
    db.session.add(group_one)
    db.session.commit()

    db.session.add(
        Group_Members(
            userID=seeded["reviewer"].id,
            groupID=group_one.id,
            assignmentID=seeded["assignment"].id,
        )
    )
    db.session.commit()

    _login(test_client, seeded["teacher"].email, "Password1!")
    assign_resp = test_client.post(
        "/review/assign",
        data=json.dumps(
            {
                "assignmentID": seeded["assignment"].id,
                "reviewerGroupID": group_one.id,
                "revieweeGroupID": group_one.id,
            }
        ),
        headers={"Content-Type": "application/json"},
    )

    assert assign_resp.status_code == 400
    assert "different" in assign_resp.get_json()["msg"].lower()


def test_reviewer_can_list_assigned_reviews_separated_by_type(test_client, db, enroll_user_in_course):
    seeded = _seed_course_with_assignment_and_rubric(db)

    student_a = seeded["reviewer"]
    student_b = seeded["other_student"]
    student_c = seeded["reviewee"]

    seeded["assignment"].assignment_mode = "group"
    db.session.commit()
    _add_group_rubric_with_matching_criteria(db, seeded)

    enroll_user_in_course(student_a.id, seeded["course"].id)
    enroll_user_in_course(student_b.id, seeded["course"].id)
    enroll_user_in_course(student_c.id, seeded["course"].id)

    group_one = CourseGroup(name="Team One", assignmentID=seeded["assignment"].id)
    group_two = CourseGroup(name="Team Two", assignmentID=seeded["assignment"].id)
    db.session.add_all([group_one, group_two])
    db.session.commit()

    db.session.add_all(
        [
            Group_Members(userID=student_a.id, groupID=group_one.id, assignmentID=seeded["assignment"].id),
            Group_Members(userID=student_b.id, groupID=group_one.id, assignmentID=seeded["assignment"].id),
            Group_Members(userID=student_c.id, groupID=group_two.id, assignmentID=seeded["assignment"].id),
        ]
    )
    db.session.commit()

    _login(test_client, seeded["teacher"].email, "Password1!")

    group_assign_resp = test_client.post(
        "/review/assign",
        data=json.dumps(
            {
                "assignmentID": seeded["assignment"].id,
                "reviewType": "group",
                "reviewerGroupID": group_one.id,
                "revieweeGroupID": group_two.id,
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    assert group_assign_resp.status_code == 201

    peer_assign_resp = test_client.post(
        "/review/assign",
        data=json.dumps(
            {
                "assignmentID": seeded["assignment"].id,
                "reviewType": "peer",
                "reviewerGroupID": group_one.id,
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    assert peer_assign_resp.status_code == 201

    _login(test_client, student_a.email, "Password1!")
    list_resp = test_client.get(f"/review/my/assignment/{seeded['assignment'].id}/separated")

    assert list_resp.status_code == 200
    payload = list_resp.get_json()
    assert "group_reviews" in payload
    assert "peer_reviews" in payload
    assert len(payload["group_reviews"]) == 1
    assert len(payload["peer_reviews"]) == 1
    assert payload["group_reviews"][0]["review_type"] == "group"
    assert payload["group_reviews"][0]["reviewer_group_name"] == "Team One"
    assert payload["group_reviews"][0]["reviewee_group_name"] == "Team Two"
    assert payload["peer_reviews"][0]["review_type"] == "peer"


def test_group_review_payload_group_names_resolve_with_legacy_null_assignment_membership(
    test_client,
    db,
    enroll_user_in_course,
):
    seeded = _seed_course_with_assignment_and_rubric(db)

    student_a = seeded["reviewer"]
    student_b = seeded["reviewee"]

    seeded["assignment"].assignment_mode = "group"
    db.session.commit()
    _add_group_rubric_with_matching_criteria(db, seeded)

    enroll_user_in_course(student_a.id, seeded["course"].id)
    enroll_user_in_course(student_b.id, seeded["course"].id)

    reviewer_group = CourseGroup(name="Alpha", assignmentID=seeded["assignment"].id)
    reviewee_group = CourseGroup(name="Beta", assignmentID=seeded["assignment"].id)
    db.session.add_all([reviewer_group, reviewee_group])
    db.session.commit()

    db.session.add_all(
        [
            Group_Members(userID=student_a.id, groupID=reviewer_group.id, assignmentID=seeded["assignment"].id),
            Group_Members(userID=student_b.id, groupID=reviewee_group.id, assignmentID=seeded["assignment"].id),
        ]
    )
    db.session.commit()

    _login(test_client, seeded["teacher"].email, "Password1!")
    assign_resp = test_client.post(
        "/review/assign",
        data=json.dumps(
            {
                "assignmentID": seeded["assignment"].id,
                "reviewType": "group",
                "reviewerGroupID": reviewer_group.id,
                "revieweeGroupID": reviewee_group.id,
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    assert assign_resp.status_code == 201

    # Simulate legacy data where assignmentID is null but group links remain valid.
    Group_Members.query.filter_by(userID=student_b.id, groupID=reviewee_group.id).update(
        {"assignmentID": None}, synchronize_session=False
    )
    db.session.commit()

    _login(test_client, student_a.email, "Password1!")
    list_resp = test_client.get(f"/review/my/assignment/{seeded['assignment'].id}/separated")
    assert list_resp.status_code == 200
    payload = list_resp.get_json()
    assert len(payload["group_reviews"]) == 1
    assert payload["group_reviews"][0]["reviewer_group_name"] == "Alpha"
    assert payload["group_reviews"][0]["reviewee_group_name"] == "Beta"


def test_teacher_can_list_assignment_reviews_separated_by_type(test_client, db, enroll_user_in_course):
    seeded = _seed_course_with_assignment_and_rubric(db)

    student_a = seeded["reviewer"]
    student_b = seeded["other_student"]
    student_c = seeded["reviewee"]

    seeded["assignment"].assignment_mode = "group"
    db.session.commit()
    _add_group_rubric_with_matching_criteria(db, seeded)

    enroll_user_in_course(student_a.id, seeded["course"].id)
    enroll_user_in_course(student_b.id, seeded["course"].id)
    enroll_user_in_course(student_c.id, seeded["course"].id)

    group_one = CourseGroup(name="Team One", assignmentID=seeded["assignment"].id)
    group_two = CourseGroup(name="Team Two", assignmentID=seeded["assignment"].id)
    db.session.add_all([group_one, group_two])
    db.session.commit()

    db.session.add_all(
        [
            Group_Members(userID=student_a.id, groupID=group_one.id, assignmentID=seeded["assignment"].id),
            Group_Members(userID=student_b.id, groupID=group_one.id, assignmentID=seeded["assignment"].id),
            Group_Members(userID=student_c.id, groupID=group_two.id, assignmentID=seeded["assignment"].id),
        ]
    )
    db.session.commit()

    _login(test_client, seeded["teacher"].email, "Password1!")

    group_assign_resp = test_client.post(
        "/review/assign",
        data=json.dumps(
            {
                "assignmentID": seeded["assignment"].id,
                "reviewType": "group",
                "reviewerGroupID": group_one.id,
                "revieweeGroupID": group_two.id,
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    assert group_assign_resp.status_code == 201

    peer_assign_resp = test_client.post(
        "/review/assign",
        data=json.dumps(
            {
                "assignmentID": seeded["assignment"].id,
                "reviewType": "peer",
                "reviewerGroupID": group_one.id,
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    assert peer_assign_resp.status_code == 201

    list_resp = test_client.get(f"/review/assignment/{seeded['assignment'].id}/separated")
    assert list_resp.status_code == 200

    payload = list_resp.get_json()
    assert "group_reviews" in payload
    assert "peer_reviews" in payload
    assert len(payload["group_reviews"]) == 1
    assert len(payload["peer_reviews"]) == 2
    assert all(review["review_type"] == "group" for review in payload["group_reviews"])
    assert all(review["review_type"] == "peer" for review in payload["peer_reviews"])


def test_group_review_any_member_can_mark_until_completed_then_locks(
    test_client,
    db,
    enroll_user_in_course,
):
    seeded = _seed_course_with_assignment_and_rubric(db)

    student_a = seeded["reviewer"]
    student_b = seeded["other_student"]
    student_c = seeded["reviewee"]

    seeded["assignment"].assignment_mode = "group"
    db.session.commit()
    _add_group_rubric_with_matching_criteria(db, seeded)

    enroll_user_in_course(student_a.id, seeded["course"].id)
    enroll_user_in_course(student_b.id, seeded["course"].id)
    enroll_user_in_course(student_c.id, seeded["course"].id)

    group_one = CourseGroup(name="Team One", assignmentID=seeded["assignment"].id)
    group_two = CourseGroup(name="Team Two", assignmentID=seeded["assignment"].id)
    db.session.add_all([group_one, group_two])
    db.session.commit()

    db.session.add_all(
        [
            Group_Members(userID=student_a.id, groupID=group_one.id, assignmentID=seeded["assignment"].id),
            Group_Members(userID=student_b.id, groupID=group_one.id, assignmentID=seeded["assignment"].id),
            Group_Members(userID=student_c.id, groupID=group_two.id, assignmentID=seeded["assignment"].id),
        ]
    )
    db.session.commit()

    _login(test_client, seeded["teacher"].email, "Password1!")
    assign_resp = test_client.post(
        "/review/assign",
        data=json.dumps(
            {
                "assignmentID": seeded["assignment"].id,
                "reviewType": "group",
                "reviewerGroupID": group_one.id,
                "revieweeGroupID": group_two.id,
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    assert assign_resp.status_code == 201
    payload = assign_resp.get_json()
    assert payload["created_count"] == 1

    # student_b is in the reviewer group but is not the canonical reviewer row owner.
    _login(test_client, student_b.email, "Password1!")
    list_resp = test_client.get(f"/review/my/assignment/{seeded['assignment'].id}/separated")
    assert list_resp.status_code == 200
    list_payload = list_resp.get_json()
    assert len(list_payload["group_reviews"]) == 1
    assert list_payload["group_reviews"][0]["can_mark"] is True

    created_review_id = payload["reviews"][0]["id"]
    created_criteria = payload["reviews"][0]["criteria"]
    mark_resp = test_client.patch(
        f"/review/{created_review_id}/mark",
        data=json.dumps(
            {
                "criteria": [
                    {
                        "criterionID": created_criteria[0]["id"],
                        "grade": 4,
                    },
                    {
                        "criterionID": created_criteria[1]["id"],
                        "grade": 3,
                    }
                ]
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    assert mark_resp.status_code == 200

    # Once completed by one group member, it should be locked for other members.
    _login(test_client, student_a.email, "Password1!")
    canonical_list_resp = test_client.get(f"/review/my/assignment/{seeded['assignment'].id}/separated")
    assert canonical_list_resp.status_code == 200
    canonical_payload = canonical_list_resp.get_json()
    assert len(canonical_payload["group_reviews"]) == 1
    assert canonical_payload["group_reviews"][0]["can_mark"] is False
    assert canonical_payload["group_reviews"][0]["is_complete"] is True

    canonical_mark_resp = test_client.patch(
        f"/review/{created_review_id}/mark",
        data=json.dumps(
            {
                "criteria": [
                    {
                        "criterionID": created_criteria[0]["id"],
                        "grade": 3,
                    }
                ]
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    assert canonical_mark_resp.status_code == 403


def test_canonical_group_reviewer_can_view_and_mark_group_review(
    test_client,
    db,
    enroll_user_in_course,
):
    seeded = _seed_course_with_assignment_and_rubric(db)

    student_a = seeded["reviewer"]
    student_c = seeded["reviewee"]

    seeded["assignment"].assignment_mode = "group"
    db.session.commit()
    _add_group_rubric_with_matching_criteria(db, seeded)

    enroll_user_in_course(student_a.id, seeded["course"].id)
    enroll_user_in_course(student_c.id, seeded["course"].id)

    group_one = CourseGroup(name="Team One", assignmentID=seeded["assignment"].id)
    group_two = CourseGroup(name="Team Two", assignmentID=seeded["assignment"].id)
    db.session.add_all([group_one, group_two])
    db.session.commit()

    db.session.add_all(
        [
            Group_Members(userID=student_a.id, groupID=group_one.id, assignmentID=seeded["assignment"].id),
            Group_Members(userID=student_c.id, groupID=group_two.id, assignmentID=seeded["assignment"].id),
        ]
    )
    db.session.commit()

    _login(test_client, seeded["teacher"].email, "Password1!")
    assign_resp = test_client.post(
        "/review/assign",
        data=json.dumps(
            {
                "assignmentID": seeded["assignment"].id,
                "reviewType": "group",
                "reviewerGroupID": group_one.id,
                "revieweeGroupID": group_two.id,
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    assert assign_resp.status_code == 201
    payload = assign_resp.get_json()
    assert payload["created_count"] == 1

    _login(test_client, student_a.email, "Password1!")
    list_resp = test_client.get(f"/review/my/assignment/{seeded['assignment'].id}/separated")
    assert list_resp.status_code == 200
    list_payload = list_resp.get_json()
    assert len(list_payload["group_reviews"]) == 1

    group_review = list_payload["group_reviews"][0]
    criterion_id = group_review["criteria"][0]["id"]
    mark_resp = test_client.patch(
        f"/review/{group_review['id']}/mark",
        data=json.dumps(
            {
                "criteria": [
                    {
                        "criterionID": criterion_id,
                        "grade": 4,
                    }
                ]
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    assert mark_resp.status_code == 200


def test_student_group_members_auto_receive_peer_reviews_for_teammates(
    test_client,
    db,
    enroll_user_in_course,
):
    seeded = _seed_course_with_assignment_and_rubric(db)

    student_a = seeded["reviewer"]
    student_b = seeded["other_student"]

    seeded["assignment"].assignment_mode = "group"
    db.session.commit()

    enroll_user_in_course(student_a.id, seeded["course"].id)
    enroll_user_in_course(student_b.id, seeded["course"].id)

    group_one = CourseGroup(name="Team One", assignmentID=seeded["assignment"].id)
    db.session.add(group_one)
    db.session.commit()

    db.session.add_all(
        [
            Group_Members(userID=student_a.id, groupID=group_one.id, assignmentID=seeded["assignment"].id),
            Group_Members(userID=student_b.id, groupID=group_one.id, assignmentID=seeded["assignment"].id),
        ]
    )

    # Provide both rubric types for group assignments.
    _add_group_rubric_with_matching_criteria(db, seeded)
    db.session.commit()

    # Explicitly create peer reviews for group members (simulates write path via API)
    Review._ensure_group_peer_reviews_for_reviewer(seeded["assignment"], student_a)

    _login(test_client, student_a.email, "Password1!")
    list_resp = test_client.get(f"/review/my/assignment/{seeded['assignment'].id}/separated")

    assert list_resp.status_code == 200
    payload = list_resp.get_json()
    assert len(payload["peer_reviews"]) == 1
    assert payload["peer_reviews"][0]["reviewee"]["id"] == student_b.id
    assert payload["peer_reviews"][0]["review_type"] == "peer"


def test_student_can_view_received_reviews_anonymously_across_peer_and_group(
    test_client,
    db,
    enroll_user_in_course,
):
    seeded = _seed_course_with_assignment_and_rubric(db)

    student_a = seeded["reviewer"]
    student_b = seeded["reviewee"]

    seeded["assignment"].assignment_mode = "group"
    db.session.commit()
    _add_group_rubric_with_matching_criteria(db, seeded)

    enroll_user_in_course(student_a.id, seeded["course"].id)
    enroll_user_in_course(student_b.id, seeded["course"].id)

    reviewer_group = CourseGroup(name="Team One", assignmentID=seeded["assignment"].id)
    reviewee_group = CourseGroup(name="Team Two", assignmentID=seeded["assignment"].id)
    db.session.add_all([reviewer_group, reviewee_group])
    db.session.commit()

    db.session.add_all(
        [
            Group_Members(userID=student_a.id, groupID=reviewer_group.id, assignmentID=seeded["assignment"].id),
            Group_Members(userID=student_b.id, groupID=reviewee_group.id, assignmentID=seeded["assignment"].id),
        ]
    )
    db.session.commit()

    peer_review = Review(
        assignmentID=seeded["assignment"].id,
        reviewerID=student_a.id,
        revieweeID=student_b.id,
        review_type="peer",
    )
    group_review = Review(
        assignmentID=seeded["assignment"].id,
        reviewerID=student_a.id,
        revieweeID=student_b.id,
        review_type="group",
    )
    db.session.add_all([peer_review, group_review])
    db.session.commit()

    peer_criterion_row = seeded["criteria"][0]
    group_criterion_row = CriteriaDescription.query.filter_by(
        question=peer_criterion_row.question,
        rubricID=Rubric.get_for_assignment(seeded["assignment"].id, "group").id,
    ).first()

    db.session.add_all(
        [
            Criterion(
                reviewID=peer_review.id,
                criterionRowID=peer_criterion_row.id,
                grade=4,
                comments="Peer contribution was strong.",
            ),
            Criterion(
                reviewID=group_review.id,
                criterionRowID=group_criterion_row.id,
                grade=5,
                comments="Group delivery was excellent.",
            ),
        ]
    )
    db.session.commit()

    _login(test_client, student_b.email, "Password1!")
    list_resp = test_client.get(
        f"/review/my/received/assignment/{seeded['assignment'].id}/separated"
    )

    assert list_resp.status_code == 200
    payload = list_resp.get_json()
    assert len(payload["peer_reviews"]) == 1
    assert len(payload["group_reviews"]) == 1

    for review in payload["peer_reviews"] + payload["group_reviews"]:
        assert review["reviewer"]["name"] == "Anonymous"
        assert review["reviewer_anonymous"] is True
        assert review["reviewee"]["id"] == student_b.id


def test_received_reviews_endpoint_only_returns_completed_reviews(
    test_client,
    db,
    enroll_user_in_course,
):
    seeded = _seed_course_with_assignment_and_rubric(db)

    enroll_user_in_course(seeded["reviewer"].id, seeded["course"].id)
    enroll_user_in_course(seeded["reviewee"].id, seeded["course"].id)

    complete_review = Review(
        assignmentID=seeded["assignment"].id,
        reviewerID=seeded["reviewer"].id,
        revieweeID=seeded["reviewee"].id,
        review_type="peer",
    )
    incomplete_review = Review(
        assignmentID=seeded["assignment"].id,
        reviewerID=seeded["reviewer"].id,
        revieweeID=seeded["reviewee"].id,
        review_type="peer",
    )
    db.session.add_all([complete_review, incomplete_review])
    db.session.commit()

    criterion_row = seeded["criteria"][0]
    db.session.add_all(
        [
            Criterion(reviewID=complete_review.id, criterionRowID=criterion_row.id, grade=3),
            Criterion(reviewID=incomplete_review.id, criterionRowID=criterion_row.id, grade=None),
        ]
    )
    db.session.commit()

    _login(test_client, seeded["reviewee"].email, "Password1!")
    list_resp = test_client.get(
        f"/review/my/received/assignment/{seeded['assignment'].id}/separated"
    )

    assert list_resp.status_code == 200
    payload = list_resp.get_json()
    assert len(payload["peer_reviews"]) == 1


def test_teacher_can_view_all_reviews_for_a_class(test_client, db, enroll_user_in_course):
    seeded = _seed_course_with_assignment_and_rubric(db)

    student_a = seeded["reviewer"]
    student_b = seeded["reviewee"]

    enroll_user_in_course(student_a.id, seeded["course"].id)
    enroll_user_in_course(student_b.id, seeded["course"].id)

    second_assignment = Assignment(
        courseID=seeded["course"].id,
        name="Peer Review 2",
        rubric_text="",
    )
    db.session.add(second_assignment)
    db.session.commit()

    first_review = Review(
        assignmentID=seeded["assignment"].id,
        reviewerID=student_a.id,
        revieweeID=student_b.id,
        review_type="peer",
    )
    second_review = Review(
        assignmentID=second_assignment.id,
        reviewerID=student_b.id,
        revieweeID=student_a.id,
        review_type="peer",
    )
    db.session.add_all([first_review, second_review])
    db.session.commit()

    _login(test_client, seeded["teacher"].email, "Password1!")
    list_resp = test_client.get(f"/review/class/{seeded['course'].id}")

    assert list_resp.status_code == 200
    payload = list_resp.get_json()
    assert isinstance(payload, list)
    assert len(payload) == 2

    assignment_ids = {review["assignmentID"] for review in payload}
    assert seeded["assignment"].id in assignment_ids
    assert second_assignment.id in assignment_ids


def test_teacher_cannot_view_reviews_for_other_teachers_class(test_client, db):
    seeded = _seed_course_with_assignment_and_rubric(db)

    other_teacher = User(
        name="Other Teacher",
        email="other-teacher@example.com",
        hash_pass=generate_password_hash("Password1!"),
        role="teacher",
    )
    db.session.add(other_teacher)
    db.session.commit()

    _login(test_client, other_teacher.email, "Password1!")
    list_resp = test_client.get(f"/review/class/{seeded['course'].id}")

    assert list_resp.status_code == 403
