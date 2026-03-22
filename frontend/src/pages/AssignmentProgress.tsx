import { useEffect, useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";

import Button from "../components/Button";
import TabNavigation from "../components/TabNavigation";
import { getAssignmentProgress } from "../util/api";
import { isAdmin, isTeacher } from "../util/login";

import "./AssignmentProgress.css";

export default function AssignmentProgress() {
  const { id } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const assignmentId = Number(id);
  const canManageAssignment = isTeacher() || isAdmin();
  const stateClassId = (location.state as { classId?: string | number } | null)?.classId;
  const searchClassId = new URLSearchParams(location.search).get("classId");
  const classId = stateClassId ?? searchClassId;
  const classQuery = classId ? `?classId=${classId}` : "";

  const [progress, setProgress] = useState<AssignmentProgressResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    ;(async () => {
      if (!Number.isFinite(assignmentId) || assignmentId <= 0) {
        setProgress(null);
        setError("Invalid assignment id");
        return;
      }

      try {
        setLoading(true);
        setError("");
        const response = (await getAssignmentProgress(assignmentId)) as AssignmentProgressResponse;
        setProgress(response);
      } catch (err) {
        const message = err instanceof Error ? err.message : "Failed to load assignment progress";
        setError(message);
        setProgress(null);
      } finally {
        setLoading(false);
      }
    })();
  }, [assignmentId]);

  return (
    <div className="AssignmentPage container-fluid py-4 px-3 px-md-4">
      <div className="AssignmentHeader card border-0 shadow-sm mb-3 p-3 p-md-4">
        <h2 className="h3 fw-bold mb-0">Assignment {assignmentId}</h2>
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
          {
            label: "Criteria",
            path: `/assignment/${id}/criteria${classQuery}`,
          },
          ...(canManageAssignment
            ? [
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
        <div className="card border-0 shadow-sm p-3 p-md-4 mt-3">
          <p className="mb-0">Only instructors can view assignment progress.</p>
        </div>
      ) : error ? (
        <div className="card border-0 shadow-sm p-3 p-md-4 mt-3" role="alert">
          <p className="mb-0">{error}</p>
        </div>
      ) : loading ? (
        <div className="card border-0 shadow-sm p-3 p-md-4 mt-3" role="status">
          <p className="mb-0">Loading assignment progress...</p>
        </div>
      ) : !progress ? (
        <div className="card border-0 shadow-sm p-3 p-md-4 mt-3" role="status">
          <p className="mb-0">No progress data found.</p>
        </div>
      ) : (
        <div className="card border-0 shadow-sm p-3 p-md-4 mt-3">
          <h3 className="h5 fw-semibold mb-3">{progress.assignment.name}</h3>
          <div className="table-responsive AssignmentProgressTableWrap">
            <table className="table align-middle AssignmentProgressTable mb-0">
              <thead>
                <tr>
                  <th>Student</th>
                  <th>Submission</th>
                  <th>Reviews Completed</th>
                  <th>Review Completion</th>
                </tr>
              </thead>
              <tbody>
                {progress.students.map((student) => {
                  const reviewStatus = student.review_status;
                  return (
                    <tr key={student.id}>
                      <td>
                        <div className="fw-semibold AssignmentProgressStudentName">{student.name}</div>
                        <div className="text-muted small AssignmentProgressStudentMeta">
                          {student.student_id || student.email}
                        </div>
                      </td>
                      <td>
                        <span className={`badge ${student.has_submitted ? "text-bg-success" : "text-bg-secondary"}`}>
                          {student.has_submitted ? "Submitted" : "Not submitted"}
                        </span>
                      </td>
                      <td>
                        <span className={`badge ${reviewStatus.has_reviewed ? "text-bg-success" : "text-bg-secondary"}`}>
                          {reviewStatus.has_reviewed ? "Completed" : "Not completed"}
                        </span>
                      </td>
                      <td>
                        <span>
                          {reviewStatus.completed_assigned_reviews}/{reviewStatus.total_assigned_reviews}
                        </span>
                        <span className="text-muted small ms-2">
                          ({reviewStatus.pending_assigned_reviews} pending)
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
