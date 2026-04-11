import { useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";

import Button from "../components/Button";
import TabNavigation from "../components/TabNavigation";
import { downloadStudentAssignmentSubmission, getAssignmentProgress } from "../util/api";
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

  const handleDownloadSubmission = async (student: AssignmentProgressStudent) => {
    if (!student.submission?.original_name) {
      return;
    }

    try {
      setError("");
      await downloadStudentAssignmentSubmission(
        assignmentId,
        student.id,
        student.submission.original_name,
      );
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to download submission";
      setError(message);
    }
  };

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

  const sortedStudents = useMemo(() => {
    if (!progress) {
      return [] as AssignmentProgressStudent[];
    }

    const students = [...progress.students];
    if (progress.assignment.assignment_mode !== "group") {
      return students;
    }

    return students.sort((left, right) => {
      const leftGroupName = left.group?.name?.trim() || "";
      const rightGroupName = right.group?.name?.trim() || "";

      if (leftGroupName && rightGroupName) {
        const byGroupName = leftGroupName.localeCompare(rightGroupName, undefined, {
          sensitivity: "base",
        });
        if (byGroupName !== 0) {
          return byGroupName;
        }
      } else if (leftGroupName || rightGroupName) {
        return leftGroupName ? -1 : 1;
      }

      return left.name.localeCompare(right.name, undefined, { sensitivity: "base" });
    });
  }, [progress]);

  const groupedStudentSections = useMemo(() => {
    if (!progress) {
      return [] as Array<{ label: string; students: AssignmentProgressStudent[] }>;
    }

    if (progress.assignment.assignment_mode !== "group") {
      return [{ label: "Students", students: sortedStudents }];
    }

    const sections = new Map<string, AssignmentProgressStudent[]>();
    for (const student of sortedStudents) {
      const label = student.group?.name?.trim() || "Ungrouped";
      const current = sections.get(label);
      if (current) {
        current.push(student);
      } else {
        sections.set(label, [student]);
      }
    }

    return Array.from(sections.entries()).map(([label, students]) => ({ label, students }));
  }, [progress, sortedStudents]);

  return (
    <div className="AssignmentPage container-fluid py-4 px-3 px-md-4">
      <div className="AssignmentHeader card border-0 shadow-sm mb-3 p-3 p-md-4">
        <h2 className="h3 fw-bold text-primary mb-0">Assignment {assignmentId}</h2>
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
        <>
          <div className="AssignmentProgressGroups">
            {groupedStudentSections.map((section, sectionIndex) => (
              <div className="card border-0 shadow-sm p-3 p-md-4 mt-3" key={`${section.label}-${sectionIndex}`}>
                {progress.assignment.assignment_mode === "group" ? (
                  <h4 className="h5 fw-semibold mb-3">Group: {section.label}</h4>
                ) : null}
                <div className="table-responsive AssignmentProgressTableWrap">
                  <table className="table align-middle AssignmentProgressTable mb-0">
                    <thead>
                      <tr>
                        <th>Student</th>
                        <th>Submission</th>
                        <th>Download</th>
                        <th>Peer Reviews Completed</th>
                        <th>Peer Review Completion</th>
                      </tr>
                    </thead>
                    <tbody>
                      {section.students.map((student) => {
                        const reviewStatus = student.peer_review_status || student.review_status;

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
                              {student.has_submitted && student.submission?.original_name ? (
                                <button
                                  type="button"
                                  className="btn btn-primary rounded-circle AssignmentProgressDownloadButton"
                                  onClick={() => handleDownloadSubmission(student)}
                                  title="Download submission"
                                  aria-label={`Download submission for ${student.name}`}
                                >
                                  <i className="bi bi-check-lg" aria-hidden="true" />
                                </button>
                              ) : (
                                <button
                                  type="button"
                                  className="btn btn-secondary rounded-circle AssignmentProgressDownloadButton"
                                  disabled
                                  title="No file available"
                                  aria-label={`No file available for ${student.name}`}
                                >
                                  <i className="bi bi-x-lg" aria-hidden="true" />
                                </button>
                              )}
                            </td>
                            <td>
                              <span className={`badge ${reviewStatus.has_reviewed ? "text-bg-success" : "text-bg-secondary"}`}>
                                {reviewStatus.has_reviewed ? "Completed" : "Not completed"}
                              </span>
                            </td>
                            <td>
                              <div className="AssignmentProgressCompletionStat">
                                <span>
                                  {reviewStatus.completed_assigned_reviews}/{reviewStatus.total_assigned_reviews}
                                </span>
                                <span className="text-muted small">
                                  ({reviewStatus.pending_assigned_reviews} pending)
                                </span>
                              </div>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
