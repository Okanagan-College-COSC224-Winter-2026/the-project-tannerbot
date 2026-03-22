import { useEffect, useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";

import Button from "../components/Button";
import ReviewAssigner from "../components/ReviewAssigner";
import TabNavigation from "../components/TabNavigation";
import { getAssignmentProgress } from "../util/api";
import { isAdmin, isTeacher } from "../util/login";

export default function AssignmentReviews() {
  const { id } = useParams();
  const location = useLocation();
  const navigate = useNavigate();

  const assignmentId = Number(id);
  const canManageAssignment = isTeacher() || isAdmin();

  const [students, setStudents] = useState<User[]>([]);
  const [classId, setClassId] = useState<string | number | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!canManageAssignment || !Number.isFinite(assignmentId) || assignmentId <= 0) {
      return;
    }

    (async () => {
      try {
        setLoading(true);
        setError("");

        const payload = (await getAssignmentProgress(assignmentId)) as AssignmentProgressResponse;
        const mappedStudents: User[] = (payload.students || []).map((student) => ({
          id: student.id,
          name: student.name,
          email: student.email,
          role: "student",
          student_id: student.student_id ?? null,
        }));

        setStudents(mappedStudents);
        setClassId(payload.assignment.courseID);
      } catch (err) {
        const message = err instanceof Error ? err.message : "Failed to load assignment reviews";
        setError(message);
        setStudents([]);
      } finally {
        setLoading(false);
      }
    })();
  }, [assignmentId, canManageAssignment]);

  const stateClassId = (location.state as { classId?: string | number } | null)?.classId;
  const searchClassId = new URLSearchParams(location.search).get("classId");
  const resolvedClassId = stateClassId ?? searchClassId ?? classId;
  const classQuery = resolvedClassId ? `?classId=${resolvedClassId}` : "";

  return (
    <div className="AssignmentPage container-fluid py-4 px-3 px-md-4">
      <div className="AssignmentHeader card border-0 shadow-sm mb-3 p-3 p-md-4">
        <h2 className="h3 fw-bold mb-0">Assignment {assignmentId}</h2>
        {canManageAssignment ? (
          <Button
            type="secondary"
            onClick={() => navigate(resolvedClassId ? `/classes/${resolvedClassId}/home` : "/home")}
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
          <p className="mb-0">Only instructors can manage review assignments.</p>
        </div>
      ) : error ? (
        <div className="card border-0 shadow-sm p-3 p-md-4 mt-3" role="alert">
          <p className="mb-0">{error}</p>
        </div>
      ) : loading ? (
        <div className="card border-0 shadow-sm p-3 p-md-4 mt-3" role="status">
          <p className="mb-0">Loading review assignment tools...</p>
        </div>
      ) : (
        <div className="card border-0 shadow-sm p-3 p-md-4 mt-3">
          <ReviewAssigner assignmentId={assignmentId} students={students} />
        </div>
      )}
    </div>
  );
}
