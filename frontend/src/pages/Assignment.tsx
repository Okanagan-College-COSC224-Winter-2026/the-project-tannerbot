import { useEffect } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";

import Button from "../components/Button";
import TabNavigation from "../components/TabNavigation";
import StudentAssignedReviews from "../components/StudentAssignedReviews";
import { isAdmin, isTeacher } from "../util/login";

import "./Assignment.css";

export default function Assignment() {
  const { id } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const assignmentId = Number(id);
  const canManageAssignment = isTeacher() || isAdmin();
  const stateClassId = (location.state as { classId?: string | number } | null)?.classId;
  const searchClassId = new URLSearchParams(location.search).get("classId");
  const classId = stateClassId ?? searchClassId;
  const classQuery = classId ? `?classId=${classId}` : "";

  useEffect(() => {
    if (!canManageAssignment || !id) {
      return;
    }

    navigate(`/assignment/${id}/criteria${classQuery}`, { replace: true });
  }, [canManageAssignment, id, classQuery, navigate]);

  return (
    <div className="AssignmentPage container-fluid py-4 px-3 px-md-4">
      <div className="AssignmentHeader card border-0 shadow-sm mb-3 p-3 p-md-4">
        <h2 className="h3 fw-bold mb-0">Assignment {assignmentId}</h2>
        {classId ? (
          <Button
            type="secondary"
            onClick={() => navigate(`/classes/${classId}/home`)}
          >
            Back to Class
          </Button>
        ) : null}
      </div>

      <TabNavigation
        tabs={[
          ...(canManageAssignment
            ? [
                {
                  label: "Group",
                  path: `/assignments/${id}/group${classQuery}`,
                },
                {
                  label: "Criteria",
                  path: `/assignment/${id}/criteria${classQuery}`,
                },
                {
                  label: "Reviews",
                  path: `/assignments/${id}/reviews${classQuery}`,
                },
                {
                  label: "Progress",
                  path: `/assignments/${id}/progress${classQuery}`,
                },
              ]
            : []),
        ]}
      />

      {!canManageAssignment ? (
        <StudentAssignedReviews assignmentId={assignmentId} />
      ) : null}
    </div>
  );
}
