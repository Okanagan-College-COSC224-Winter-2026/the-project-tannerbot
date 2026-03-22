import { useLocation, useNavigate, useParams } from "react-router-dom";

import Button from "../components/Button";
import TabNavigation from "../components/TabNavigation";
import { isAdmin, isTeacher } from "../util/login";

import "./Group.css";

export default function Group() {
  const { id } = useParams();
  const location = useLocation();
  const navigate = useNavigate();

  const canManageAssignment = isTeacher() || isAdmin();
  const stateClassId = (location.state as { classId?: string | number } | null)?.classId;
  const searchClassId = new URLSearchParams(location.search).get("classId");
  const classId = stateClassId ?? searchClassId;
  const classQuery = classId ? `?classId=${classId}` : "";

  return (
    <div className="AssignmentPage container-fluid py-4 px-3 px-md-4">
      <div className="AssignmentHeader card border-0 shadow-sm mb-3 p-3 p-md-4">
        <h2 className="h3 fw-bold mb-0">Assignment {id}</h2>
        {canManageAssignment ? (
          <Button
            type="secondary"
            onClick={() => navigate(classId ? `/classes/${classId}/home` : "/home")}
          >
            Return to Class
          </Button>
        ) : null}
      </div>

      <TabNavigation
        tabs={[
          {
            label: "Group",
            path: `/assignments/${id}/group${classQuery}`,
          },
          ...(canManageAssignment
            ? [
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

      <div className="card border-0 shadow-sm p-3 p-md-4 mt-3">
        <h3 className="h5 fw-semibold mb-2">Group Management</h3>
        <p className="mb-0 text-muted">
          Group management controls are temporarily disabled while this area is being updated.
        </p>
      </div>
    </div>
  );
}
