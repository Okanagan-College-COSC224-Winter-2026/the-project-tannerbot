"""
cd flask_backend
pytest tests/test_rubric.py -v

Tests for rubric endpoints.

Covers user stories:
- Instructor can add multiple rubric criteria
- Instructor can set scale or score for each criterion
- Instructor can save the rubric and attach it to an assignment
"""

import json
import datetime


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _login(client, email, password):
    client.post(
        "/auth/login",
        data=json.dumps({"email": email, "password": password}),
        headers={"Content-Type": "application/json"},
    )


def _create_class(client, name="Test Course"):
    resp = client.post(
        "/class/create_class",
        data=json.dumps({"name": name}),
        headers={"Content-Type": "application/json"},
    )
    return resp.json["class"]["id"]


def _create_assignment(client, course_id, name="Assignment 1", assignment_mode="solo"):
    due = datetime.datetime(2027, 12, 31, 23, 59, 59).isoformat()
    resp = client.post(
        "/assignment/create_assignment",
        data=json.dumps(
            {
                "courseID": course_id,
                "name": name,
                "rubric": "",
                "due_date": due,
                "assignment_mode": assignment_mode,
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    return resp.json["assignment"]["id"]


def _create_rubric(client, assignment_id, rubric_type="peer"):
    resp = client.post(
        "/create_rubric",
        data=json.dumps({"assignmentID": assignment_id, "rubricType": rubric_type}),
        headers={"Content-Type": "application/json"},
    )
    return resp


def _add_criterion(client, rubric_id, question, score_max, has_score=True):
    return client.post(
        "/create_criteria",
        data=json.dumps({"rubricID": rubric_id, "question": question, "scoreMax": score_max, "hasScore": has_score}),
        headers={"Content-Type": "application/json"},
    )


def _add_criterion_for_assignment(client, assignment_id, rubric_id, question, score_max, has_score=True):
    return client.post(
        f"/assignment/{assignment_id}/criteria",
        data=json.dumps({"rubricID": rubric_id, "question": question, "scoreMax": score_max, "hasScore": has_score}),
        headers={"Content-Type": "application/json"},
    )


# ---------------------------------------------------------------------------
# Tests: instructor saves a rubric and attaches it to an assignment
# ---------------------------------------------------------------------------

class TestCreateRubricAndAttachToAssignment:
    """Instructor can create a rubric and attach it to an assignment."""

    def test_instructor_creates_rubric_for_assignment(self, test_client, make_admin):
        """
        GIVEN an instructor (admin) and an existing assignment
        WHEN POST /create_rubric is called with a valid assignmentID
        THEN a rubric is created and linked to that assignment (201)
        """
        make_admin(email="teacher@example.com", password="pass", name="Teacher")
        _login(test_client, "teacher@example.com", "pass")
        course_id = _create_class(test_client)
        assignment_id = _create_assignment(test_client, course_id)

        resp = _create_rubric(test_client, assignment_id)

        assert resp.status_code == 201
        data = resp.get_json()
        assert "id" in data

    def test_rubric_attached_to_assignment_is_retrievable(self, test_client, make_admin):
        """
        GIVEN a rubric saved for an assignment
        WHEN GET /rubric/assignment/<assignment_id> is called
        THEN the rubric data is returned with the correct assignmentID
        """
        make_admin(email="teacher@example.com", password="pass", name="Teacher")
        _login(test_client, "teacher@example.com", "pass")
        course_id = _create_class(test_client)
        assignment_id = _create_assignment(test_client, course_id)
        _create_rubric(test_client, assignment_id)

        resp = test_client.get(f"/rubric/assignment/{assignment_id}")

        assert resp.status_code == 200
        data = resp.get_json()
        assert "id" in data

    def test_create_rubric_missing_assignment_id(self, test_client, make_admin):
        """
        GIVEN an instructor
        WHEN POST /create_rubric is called without assignmentID
        THEN the API returns 400
        """
        make_admin(email="teacher@example.com", password="pass", name="Teacher")
        _login(test_client, "teacher@example.com", "pass")

        resp = test_client.post(
            "/create_rubric",
            data=json.dumps({}),
            headers={"Content-Type": "application/json"},
        )

        assert resp.status_code == 400
        assert resp.get_json()["msg"] == "assignmentID is required"

    def test_non_instructor_cannot_create_rubric(self, test_client):
        """
        GIVEN a student user (not a teacher or admin)
        WHEN POST /create_rubric is called
        THEN the request is rejected with 403
        """
        test_client.post(
            "/auth/register",
            data=json.dumps({"name": "Student", "email": "student@example.com", "password": "Password1!"}),
            headers={"Content-Type": "application/json"},
        )
        _login(test_client, "student@example.com", "Password1!")

        resp = test_client.post(
            "/create_rubric",
            data=json.dumps({"assignmentID": 999}),
            headers={"Content-Type": "application/json"},
        )

        assert resp.status_code == 403

    def test_get_rubric_for_nonexistent_assignment_returns_404(self, test_client):
        """
        GIVEN no rubric exists for assignment 9999
        WHEN GET /rubric/assignment/9999 is called
        THEN 404 is returned
        """
        resp = test_client.get("/rubric/assignment/9999")
        assert resp.status_code == 404

    def test_group_assignment_supports_separate_peer_and_group_rubrics(self, test_client, make_admin):
        make_admin(email="teacher@example.com", password="pass", name="Teacher")
        _login(test_client, "teacher@example.com", "pass")
        course_id = _create_class(test_client)
        assignment_id = _create_assignment(test_client, course_id, assignment_mode="group")

        peer_resp = _create_rubric(test_client, assignment_id, rubric_type="peer")
        group_resp = _create_rubric(test_client, assignment_id, rubric_type="group")

        assert peer_resp.status_code == 201
        assert group_resp.status_code == 201
        assert peer_resp.get_json()["rubric_type"] == "peer"
        assert group_resp.get_json()["rubric_type"] == "group"
        assert peer_resp.get_json()["id"] != group_resp.get_json()["id"]

    def test_group_assignment_rubrics_can_be_fetched_by_type(self, test_client, make_admin):
        make_admin(email="teacher@example.com", password="pass", name="Teacher")
        _login(test_client, "teacher@example.com", "pass")
        course_id = _create_class(test_client)
        assignment_id = _create_assignment(test_client, course_id, assignment_mode="group")

        peer_rubric = _create_rubric(test_client, assignment_id, rubric_type="peer").get_json()
        group_rubric = _create_rubric(test_client, assignment_id, rubric_type="group").get_json()

        peer_get = test_client.get(f"/rubric/assignment/{assignment_id}?rubricType=peer")
        group_get = test_client.get(f"/rubric/assignment/{assignment_id}?rubricType=group")
        separated_get = test_client.get(f"/rubric/assignment/{assignment_id}/separated")

        assert peer_get.status_code == 200
        assert group_get.status_code == 200
        assert separated_get.status_code == 200
        assert peer_get.get_json()["id"] == peer_rubric["id"]
        assert group_get.get_json()["id"] == group_rubric["id"]
        assert separated_get.get_json()["peer_rubric"]["id"] == peer_rubric["id"]
        assert separated_get.get_json()["group_rubric"]["id"] == group_rubric["id"]

    def test_solo_assignment_rejects_group_rubric_creation(self, test_client, make_admin):
        make_admin(email="teacher@example.com", password="pass", name="Teacher")
        _login(test_client, "teacher@example.com", "pass")
        course_id = _create_class(test_client)
        assignment_id = _create_assignment(test_client, course_id, assignment_mode="solo")

        resp = _create_rubric(test_client, assignment_id, rubric_type="group")
        assert resp.status_code == 400
        assert "Solo assignments" in resp.get_json()["msg"]


# ---------------------------------------------------------------------------
# Tests: instructor adds multiple rubric criteria
# ---------------------------------------------------------------------------

class TestAddMultipleCriteria:
    """Instructor can add multiple criteria to a rubric."""

    def test_instructor_adds_multiple_criteria(self, test_client, make_admin):
        """
        GIVEN an instructor with a rubric
        WHEN multiple POST /create_criteria calls are made
        THEN each criterion is saved and all are retrievable via GET /criteria
        """
        make_admin(email="teacher@example.com", password="pass", name="Teacher")
        _login(test_client, "teacher@example.com", "pass")
        course_id = _create_class(test_client)
        assignment_id = _create_assignment(test_client, course_id)
        rubric_id = _create_rubric(test_client, assignment_id).get_json()["id"]

        r1 = _add_criterion(test_client, rubric_id, "Clarity of argument", 30)
        r2 = _add_criterion(test_client, rubric_id, "Use of evidence", 40)
        r3 = _add_criterion(test_client, rubric_id, "Grammar and style", 30)

        assert r1.status_code == 201
        assert r2.status_code == 201
        assert r3.status_code == 201

        get_resp = test_client.get(f"/criteria?rubricID={rubric_id}")
        assert get_resp.status_code == 200
        criteria_list = get_resp.get_json()
        assert len(criteria_list) == 3
        questions = {c["question"] for c in criteria_list}
        assert "Clarity of argument" in questions
        assert "Use of evidence" in questions
        assert "Grammar and style" in questions

    def test_criteria_are_returned_inside_rubric_response(self, test_client, make_admin):
        """
        GIVEN a rubric with two criteria
        WHEN GET /rubric?rubricID=<id> is called
        THEN the response includes the criteria_descriptions list
        """
        make_admin(email="teacher@example.com", password="pass", name="Teacher")
        _login(test_client, "teacher@example.com", "pass")
        course_id = _create_class(test_client)
        assignment_id = _create_assignment(test_client, course_id)
        rubric_id = _create_rubric(test_client, assignment_id).get_json()["id"]

        _add_criterion(test_client, rubric_id, "Organization", 50)
        _add_criterion(test_client, rubric_id, "Depth of analysis", 50)

        resp = test_client.get(f"/rubric?rubricID={rubric_id}")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "criteria_descriptions" in data
        assert len(data["criteria_descriptions"]) == 2

    def test_add_criterion_to_nonexistent_rubric_returns_404(self, test_client, make_admin):
        """
        GIVEN a teacher
        WHEN POST /create_criteria references a rubric that does not exist
        THEN 404 is returned
        """
        make_admin(email="teacher@example.com", password="pass", name="Teacher")
        _login(test_client, "teacher@example.com", "pass")

        resp = _add_criterion(test_client, 9999, "Some question", 10)
        assert resp.status_code == 404
        assert resp.get_json()["msg"] == "Rubric not found"

    def test_add_criterion_without_rubric_id_returns_400(self, test_client, make_admin):
        """
        GIVEN a teacher
        WHEN POST /create_criteria is called without rubricID
        THEN 400 is returned
        """
        make_admin(email="teacher@example.com", password="pass", name="Teacher")
        _login(test_client, "teacher@example.com", "pass")

        resp = test_client.post(
            "/create_criteria",
            data=json.dumps({"question": "Something", "scoreMax": 10}),
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 400
        assert resp.get_json()["msg"] == "rubricID is required"

    def test_add_criterion_without_question_returns_400(self, test_client, make_admin):
        """
        GIVEN a teacher and valid rubric
        WHEN POST /create_criteria is called with a blank question
        THEN 400 is returned and criterion is not created
        """
        make_admin(email="teacher@example.com", password="pass", name="Teacher")
        _login(test_client, "teacher@example.com", "pass")
        course_id = _create_class(test_client)
        assignment_id = _create_assignment(test_client, course_id)
        rubric_id = _create_rubric(test_client, assignment_id).get_json()["id"]

        resp = _add_criterion(test_client, rubric_id, "   ", 10, has_score=True)

        assert resp.status_code == 400
        assert resp.get_json()["msg"] == "question is required"

    def test_assignment_scoped_create_criteria_rejects_rubric_from_other_assignment(self, test_client, make_admin):
        make_admin(email="teacher@example.com", password="pass", name="Teacher")
        _login(test_client, "teacher@example.com", "pass")

        course_id = _create_class(test_client)
        assignment_one = _create_assignment(test_client, course_id, name="A1", assignment_mode="group")
        assignment_two = _create_assignment(test_client, course_id, name="A2", assignment_mode="group")

        rubric_two = _create_rubric(test_client, assignment_two, rubric_type="group").get_json()["id"]

        resp = _add_criterion_for_assignment(
            test_client,
            assignment_one,
            rubric_two,
            "Should fail",
            10,
            has_score=True,
        )

        assert resp.status_code == 400
        assert "does not belong" in resp.get_json()["msg"].lower()

    def test_assignment_scoped_edit_criteria_rejects_other_assignment_criteria(self, test_client, make_admin):
        make_admin(email="teacher@example.com", password="pass", name="Teacher")
        _login(test_client, "teacher@example.com", "pass")

        course_id = _create_class(test_client)
        assignment_one = _create_assignment(test_client, course_id, name="A1", assignment_mode="group")
        assignment_two = _create_assignment(test_client, course_id, name="A2", assignment_mode="group")

        rubric_two = _create_rubric(test_client, assignment_two, rubric_type="peer").get_json()["id"]
        criteria_two = _add_criterion(test_client, rubric_two, "A2 criterion", 20, has_score=True).get_json()["id"]

        resp = test_client.patch(
            f"/assignment/{assignment_one}/criteria/{criteria_two}",
            data=json.dumps({"question": "Not allowed"}),
            headers={"Content-Type": "application/json"},
        )

        assert resp.status_code == 404
        assert "not found for this assignment" in resp.get_json()["msg"].lower()

    def test_get_criteria_with_non_integer_rubric_id_returns_400(self, test_client):
        """
        GIVEN an invalid rubricID query parameter
        WHEN GET /criteria is called
        THEN the API returns a 400 instead of crashing
        """
        resp = test_client.get("/criteria?rubricID=abc")
        assert resp.status_code == 400
        assert resp.get_json()["msg"] == "rubricID must be an integer"

    def test_get_rubric_with_non_integer_rubric_id_returns_400(self, test_client):
        """
        GIVEN an invalid rubricID query parameter
        WHEN GET /rubric is called
        THEN the API returns a 400 instead of crashing
        """
        resp = test_client.get("/rubric?rubricID=xyz")
        assert resp.status_code == 400
        assert resp.get_json()["msg"] == "rubricID must be an integer"

    def test_create_criteria_without_json_returns_400(self, test_client, make_admin):
        """
        GIVEN a teacher sending a non-JSON request
        WHEN POST /create_criteria is called
        THEN the API returns 400 with a clear message
        """
        make_admin(email="teacher@example.com", password="pass", name="Teacher")
        _login(test_client, "teacher@example.com", "pass")

        resp = test_client.post(
            "/create_criteria",
            data="rubricID=1&question=Q&scoreMax=10",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert resp.status_code == 400
        assert resp.get_json()["msg"] == "Missing JSON in request"


# ---------------------------------------------------------------------------
# Tests: instructor sets scale / score for each criterion
# ---------------------------------------------------------------------------

class TestCriterionScoreAndScale:
    """Instructor can set and update the score/scale for each criterion."""

    def test_criterion_stores_score_max(self, test_client, make_admin):
        """
        GIVEN an instructor adding a scored criterion
        WHEN POST /create_criteria is called with scoreMax and hasScore=True
        THEN the criterion is saved with the provided scoreMax
        """
        make_admin(email="teacher@example.com", password="pass", name="Teacher")
        _login(test_client, "teacher@example.com", "pass")
        course_id = _create_class(test_client)
        assignment_id = _create_assignment(test_client, course_id)
        rubric_id = _create_rubric(test_client, assignment_id).get_json()["id"]

        resp = _add_criterion(test_client, rubric_id, "Thoroughness", 40, has_score=True)

        assert resp.status_code == 201
        data = resp.get_json()
        assert data["scoreMax"] == 40
        assert data["hasScore"] is True

    def test_criterion_without_score_has_zero_score_max(self, test_client, make_admin):
        """
        GIVEN an instructor adding a qualitative (no-score) criterion
        WHEN POST /create_criteria is called with hasScore=False
        THEN scoreMax is stored as 0
        """
        make_admin(email="teacher@example.com", password="pass", name="Teacher")
        _login(test_client, "teacher@example.com", "pass")
        course_id = _create_class(test_client)
        assignment_id = _create_assignment(test_client, course_id)
        rubric_id = _create_rubric(test_client, assignment_id).get_json()["id"]

        resp = _add_criterion(test_client, rubric_id, "Overall impression", 0, has_score=False)

        assert resp.status_code == 201
        data = resp.get_json()
        assert data["hasScore"] is False
        assert data["scoreMax"] == 0

    def test_scored_criterion_with_zero_score_is_rejected(self, test_client, make_admin):
        """
        GIVEN an instructor adding a scored criterion
        WHEN POST /create_criteria has hasScore=True and scoreMax=0
        THEN 400 is returned and the criterion is not created
        """
        make_admin(email="teacher@example.com", password="pass", name="Teacher")
        _login(test_client, "teacher@example.com", "pass")
        course_id = _create_class(test_client)
        assignment_id = _create_assignment(test_client, course_id)
        rubric_id = _create_rubric(test_client, assignment_id).get_json()["id"]

        resp = _add_criterion(test_client, rubric_id, "Scored item", 0, has_score=True)

        assert resp.status_code == 400
        assert "greater than 0" in resp.get_json()["msg"]

    def test_instructor_can_update_criterion_score(self, test_client, make_admin):
        """
        GIVEN an instructor with an existing criterion scored at 20
        WHEN PATCH /criteria/<id> is called with a new scoreMax of 35
        THEN the criterion score is updated to 35
        """
        make_admin(email="teacher@example.com", password="pass", name="Teacher")
        _login(test_client, "teacher@example.com", "pass")
        course_id = _create_class(test_client)
        assignment_id = _create_assignment(test_client, course_id)
        rubric_id = _create_rubric(test_client, assignment_id).get_json()["id"]

        criteria_id = _add_criterion(test_client, rubric_id, "Research quality", 20).get_json()["id"]

        resp = test_client.patch(
            f"/criteria/{criteria_id}",
            data=json.dumps({"scoreMax": 35}),
            headers={"Content-Type": "application/json"},
        )

        assert resp.status_code == 200
        assert resp.get_json()["scoreMax"] == 35

    def test_total_score_cannot_exceed_100(self, test_client, make_admin):
        """
        GIVEN an instructor whose rubric criteria already sum to 90
        WHEN they try to add a criterion worth 20
        THEN the API returns 400 (total would exceed 100)
        """
        make_admin(email="teacher@example.com", password="pass", name="Teacher")
        _login(test_client, "teacher@example.com", "pass")
        course_id = _create_class(test_client)
        assignment_id = _create_assignment(test_client, course_id)
        rubric_id = _create_rubric(test_client, assignment_id).get_json()["id"]

        _add_criterion(test_client, rubric_id, "Part A", 50)
        _add_criterion(test_client, rubric_id, "Part B", 40)

        resp = _add_criterion(test_client, rubric_id, "Part C (too large)", 20)

        assert resp.status_code == 400
        assert "100" in resp.get_json()["msg"]

    def test_score_capped_at_100_per_criterion(self, test_client, make_admin):
        """
        GIVEN an instructor
        WHEN a criterion is submitted with scoreMax > 100
        THEN the stored scoreMax is capped at 100
        """
        make_admin(email="teacher@example.com", password="pass", name="Teacher")
        _login(test_client, "teacher@example.com", "pass")
        course_id = _create_class(test_client)
        assignment_id = _create_assignment(test_client, course_id)
        rubric_id = _create_rubric(test_client, assignment_id).get_json()["id"]

        resp = _add_criterion(test_client, rubric_id, "Impossible criterion", 200)

        assert resp.status_code == 201
        assert resp.get_json()["scoreMax"] == 100

    def test_instructor_can_delete_a_criterion(self, test_client, make_admin):
        """
        GIVEN an instructor with a criterion on a rubric
        WHEN DELETE /criteria/<id> is called
        THEN the criterion is removed and no longer appears in the rubric
        """
        make_admin(email="teacher@example.com", password="pass", name="Teacher")
        _login(test_client, "teacher@example.com", "pass")
        course_id = _create_class(test_client)
        assignment_id = _create_assignment(test_client, course_id)
        rubric_id = _create_rubric(test_client, assignment_id).get_json()["id"]

        criteria_id = _add_criterion(test_client, rubric_id, "To be removed", 25).get_json()["id"]

        del_resp = test_client.delete(f"/criteria/{criteria_id}")
        assert del_resp.status_code == 200
        assert del_resp.get_json()["msg"] == "Criteria deleted"

        criteria_list = test_client.get(f"/criteria?rubricID={rubric_id}").get_json()
        ids = [c["id"] for c in criteria_list]
        assert criteria_id not in ids
