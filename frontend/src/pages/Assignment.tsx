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

      {canManageAssignment ? (
        <div className="card border-0 shadow-sm p-3 p-md-4 mt-3 AssignmentHomePanel">
          <h3 className="h5 fw-semibold mb-2">Assignment Overview</h3>
          <p className="text-muted mb-3">
            Use this page as the instructor landing area for assignment setup and monitoring.
          </p>

          <div className="AssignmentHomeActions">
            <button type="button" onClick={() => (window.location.href = `/assignment/${id}/criteria`)}>
              Edit Criteria
            </button>
            <button type="button" onClick={() => (window.location.href = `/assignments/${id}/reviews`)}>
              Manage Reviews
            </button>
            <button type="button" onClick={() => (window.location.href = `/assignments/${id}/progress`)}>
              View Progress
            </button>
          </div>
        </div>
      ) : (
        <StudentAssignedReviews assignmentId={assignmentId} />
      )}
    </div>
  );
}
