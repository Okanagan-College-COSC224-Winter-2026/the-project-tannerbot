import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import Button from "../components/Button";
import StudentImportButton from "../components/StudentImportButton";
import TabNavigation from "../components/TabNavigation";
import { listReviewsForClass } from "../util/api";
import { isTeacher } from "../util/login";

export default function ClassReviews() {
  const { id } = useParams();
  const navigate = useNavigate();

  const classId = Number(id);
  const [reviews, setReviews] = useState<ReviewAssignment[]>([]);
  const [selectedCompletedReview, setSelectedCompletedReview] = useState<ReviewAssignment | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>("");
  const [studentSearch, setStudentSearch] = useState<string>("");

  const displayReviewer = (review: ReviewAssignment): string => {
    if (review.review_type === "group") {
      return review.reviewer_group_name || "Ungrouped";
    }
    return review.reviewer?.name || `Student ${review.reviewer?.id ?? ""}`;
  };

  const displayReviewee = (review: ReviewAssignment): string => {
    if (review.review_type === "group") {
      return review.reviewee_group_name || "Ungrouped";
    }
    return review.reviewee?.name || `Student ${review.reviewee?.id ?? ""}`;
  };

  const reviewMatchesStudentSearch = (review: ReviewAssignment, searchTerm: string): boolean => {
    const normalizedSearch = searchTerm.trim().toLowerCase();
    if (!normalizedSearch) {
      return true;
    }

    const reviewerName = review.reviewer?.name?.toLowerCase() || "";
    const revieweeName = review.reviewee?.name?.toLowerCase() || "";

    return reviewerName.includes(normalizedSearch) || revieweeName.includes(normalizedSearch);
  };

  const reviewsByAssignment = useMemo(() => {
    const filteredReviews = reviews.filter((review) =>
      reviewMatchesStudentSearch(review, studentSearch),
    );

    const grouped = new Map<number, ReviewAssignment[]>();
    for (const review of filteredReviews) {
      const assignmentId = Number(review.assignmentID);
      const existing = grouped.get(assignmentId) || [];
      existing.push(review);
      grouped.set(assignmentId, existing);
    }
    return Array.from(grouped.entries()).sort((a, b) => a[0] - b[0]);
  }, [reviews, studentSearch]);

  useEffect(() => {
    if (!Number.isFinite(classId) || classId <= 0) {
      setError("Invalid class ID");
      return;
    }

    (async () => {
      try {
        setLoading(true);
        setError("");
        setSelectedCompletedReview(null);
        const payload = await listReviewsForClass(classId);
        setReviews(Array.isArray(payload) ? payload : []);
      } catch (err) {
        const message = err instanceof Error ? err.message : "Failed to load class reviews";
        setError(message);
        setReviews([]);
      } finally {
        setLoading(false);
      }
    })();
  }, [classId]);

  return (
    <div className="ClassHomePage container-fluid py-4 px-3 px-md-4">
      <div className="ClassHeader card border-0 shadow-sm mb-3 p-3 p-md-4">
        <div className="ClassHeaderLeft">
          <h2 className="h3 fw-bold mb-0">Class Reviews</h2>
        </div>

        <div className="ClassHeaderRight">
          {isTeacher() ? <StudentImportButton classId={id} /> : null}
          <Button type="secondary" onClick={() => navigate(`/classes/${classId}/home`)}>
            Back to Class
          </Button>
        </div>
      </div>

      <TabNavigation
        tabs={[
          {
            label: "Home",
            path: `/classes/${id}/home`,
          },
          {
            label: "Members",
            path: `/classes/${id}/members`,
          },
          {
            label: "Reviews",
            path: `/classes/${id}/reviews`,
          },
        ]}
      />

      <div className="card border-0 shadow-sm p-3 p-md-4 mt-3">
        <label htmlFor="student-review-search" className="form-label fw-semibold mb-2">
          Search Reviews By Student Name
        </label>
        <input
          id="student-review-search"
          type="text"
          className="form-control"
          placeholder="Enter student name"
          value={studentSearch}
          onChange={(event) => setStudentSearch(event.target.value)}
        />
      </div>

      {error ? (
        <div className="card border-0 shadow-sm p-3 p-md-4 mt-3" role="alert">
          <p className="mb-0">{error}</p>
        </div>
      ) : loading ? (
        <div className="card border-0 shadow-sm p-3 p-md-4 mt-3" role="status">
          <p className="mb-0">Loading class reviews...</p>
        </div>
      ) : reviewsByAssignment.length === 0 ? (
        <div className="card border-0 shadow-sm p-3 p-md-4 mt-3">
          <p className="mb-0">No reviews found for this class yet.</p>
        </div>
      ) : (
        <div className="d-grid gap-3 mt-3">
          {reviewsByAssignment.map(([assignmentId, assignmentReviews]) => (
            <div key={assignmentId} className="card border-0 shadow-sm p-3 p-md-4">
              <h3 className="h5 mb-2">
                Assignment {assignmentId}: {assignmentReviews[0]?.assignment?.name || "Untitled"}
              </h3>
              <p className="text-muted small mb-3">Total reviews: {assignmentReviews.length}</p>

              <div className="table-responsive">
                <table className="table align-middle mb-0">
                  <thead>
                    <tr>
                      <th>Type</th>
                      <th>Reviewer</th>
                      <th>Reviewee</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {assignmentReviews.map((review) => {
                      const isComplete = Boolean(review.is_complete);
                      return (
                      <tr
                        key={review.id}
                        role={isComplete ? "button" : undefined}
                        tabIndex={isComplete ? 0 : undefined}
                        className={isComplete ? "cursor-pointer" : undefined}
                        style={isComplete ? { cursor: "pointer" } : undefined}
                        onClick={isComplete ? () => setSelectedCompletedReview(review) : undefined}
                        onKeyDown={
                          isComplete
                            ? (event) => {
                                if (event.key === "Enter" || event.key === " ") {
                                  event.preventDefault();
                                  setSelectedCompletedReview(review);
                                }
                              }
                            : undefined
                        }
                        title={isComplete ? "View completed review" : undefined}
                      >
                        <td>{review.review_type === "group" ? "Group" : "Peer"}</td>
                        <td>{displayReviewer(review)}</td>
                        <td>{displayReviewee(review)}</td>
                        <td>
                          {isComplete ? (
                            <span className="badge text-bg-success">Complete</span>
                          ) : (
                            <span className="badge text-bg-secondary">Pending</span>
                          )}
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
      )}

      {selectedCompletedReview && (
        <div className="card border-0 shadow-sm p-3 p-md-4 mt-3">
          <div className="d-flex justify-content-between align-items-center mb-3">
            <h3 className="h5 mb-0">Completed Review Details</h3>
            <Button type="secondary" onClick={() => setSelectedCompletedReview(null)}>
              Close
            </Button>
          </div>

          <div className="row g-3 mb-3">
            <div className="col-12 col-md-4">
              <div className="text-muted small">Assignment</div>
              <div className="fw-semibold">
                {selectedCompletedReview.assignment?.name || `Assignment ${selectedCompletedReview.assignmentID}`}
              </div>
            </div>
            <div className="col-12 col-md-4">
              <div className="text-muted small">Reviewer</div>
              <div className="fw-semibold">{displayReviewer(selectedCompletedReview)}</div>
            </div>
            <div className="col-12 col-md-4">
              <div className="text-muted small">Reviewee</div>
              <div className="fw-semibold">{displayReviewee(selectedCompletedReview)}</div>
            </div>
          </div>

          {!selectedCompletedReview.criteria || selectedCompletedReview.criteria.length === 0 ? (
            <p className="mb-0 text-muted">No criterion responses available for this review.</p>
          ) : (
            <div className="d-grid gap-3">
              {selectedCompletedReview.criteria.map((criterion) => {
                const criterionRow = criterion.criterion_row;
                const hasScore = criterionRow?.hasScore ?? true;
                return (
                  <div key={criterion.id} className="border rounded-3 p-3">
                    <div className="fw-semibold mb-2">{criterionRow?.question || "Criterion"}</div>
                    {hasScore ? (
                      <div className="mb-2">
                        Score: {criterion.grade ?? "Not provided"}
                        {criterionRow?.scoreMax !== undefined ? ` / ${criterionRow.scoreMax}` : ""}
                      </div>
                    ) : null}
                    <div className="mb-0">
                      Comments: {criterion.comments && criterion.comments.trim() ? criterion.comments : "No comment"}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
