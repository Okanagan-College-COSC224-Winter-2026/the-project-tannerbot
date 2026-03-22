import { useEffect, useMemo, useState } from "react";

import { listMyReviewsForAssignment, markReview } from "../util/api";
import { formatDateTime } from "../util/dateUtils";

import "./StudentAssignedReviews.css";

type DraftValues = Record<number, { grade?: number; comments?: string }>;

const isReviewComplete = (review: ReviewAssignment): boolean => {
  if (typeof review.is_complete === "boolean") {
    return review.is_complete;
  }

  const criteria = review.criteria ?? [];
  if (criteria.length === 0) {
    return false;
  }

  return criteria.every((criterion) => {
    const hasScore = criterion.criterion_row?.hasScore ?? true;
    if (hasScore) {
      return criterion.grade !== null && criterion.grade !== undefined;
    }
    return Boolean(criterion.comments && criterion.comments.trim().length > 0);
  });
};

const getReviewWindowMessage = (review: ReviewAssignment): string | null => {
  if (review.review_window_open !== false) {
    return null;
  }

  const startDate = review.assignment?.start_date;
  const dueDate = review.assignment?.due_date;
  const now = Date.now();

  if (startDate) {
    const startTime = new Date(startDate).getTime();
    if (!Number.isNaN(startTime) && now < startTime) {
      return "Review period has not opened yet for this assignment.";
    }
  }

  if (dueDate) {
    const dueTime = new Date(dueDate).getTime();
    if (!Number.isNaN(dueTime) && now > dueTime) {
      return "Review period has ended for this assignment. You can view details but cannot submit feedback.";
    }
  }

  return "Review period is currently closed for this assignment.";
};

interface Props {
  assignmentId: number;
}

export default function StudentAssignedReviews({ assignmentId }: Props) {
  const [reviews, setReviews] = useState<ReviewAssignment[]>([]);
  const [selectedReviewId, setSelectedReviewId] = useState<number | null>(null);
  const [draft, setDraft] = useState<DraftValues>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const selectedReview = useMemo(
    () => reviews.find((review) => review.id === selectedReviewId) ?? null,
    [reviews, selectedReviewId],
  );

  const selectedReviewWindowMessage = selectedReview ? getReviewWindowMessage(selectedReview) : null;

  const loadAssignedReviews = async () => {
    if (!Number.isFinite(assignmentId) || assignmentId <= 0) {
      setError("Invalid assignment ID.");
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError("");
      setSuccess("");
      const payload = await listMyReviewsForAssignment(assignmentId);
      const assignedReviews: ReviewAssignment[] = Array.isArray(payload) ? payload : [];
      setReviews(assignedReviews);

      const firstReview = assignedReviews[0] ?? null;
      setSelectedReviewId(firstReview?.id ?? null);
      if (firstReview?.criteria) {
        const initialDraft: DraftValues = {};
        firstReview.criteria.forEach((criterion) => {
          initialDraft[criterion.id] = {
            grade: criterion.grade ?? undefined,
            comments: criterion.comments ?? "",
          };
        });
        setDraft(initialDraft);
      } else {
        setDraft({});
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to load assigned reviews";
      setError(message);
      setReviews([]);
      setSelectedReviewId(null);
      setDraft({});
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAssignedReviews();
  }, [assignmentId]);

  const handleReviewChange = (reviewId: number) => {
    setSelectedReviewId(reviewId);
    const review = reviews.find((item) => item.id === reviewId);
    const nextDraft: DraftValues = {};
    review?.criteria?.forEach((criterion) => {
      nextDraft[criterion.id] = {
        grade: criterion.grade ?? undefined,
        comments: criterion.comments ?? "",
      };
    });
    setDraft(nextDraft);
    setError("");
    setSuccess("");
  };

  const handleScoreChange = (criterionId: number, raw: string) => {
    setDraft((prev) => ({
      ...prev,
      [criterionId]: {
        ...prev[criterionId],
        grade: raw === "" ? undefined : Number(raw),
      },
    }));
  };

  const handleCommentsChange = (criterionId: number, comments: string) => {
    setDraft((prev) => ({
      ...prev,
      [criterionId]: {
        ...prev[criterionId],
        comments,
      },
    }));
  };

  const handleSubmit = async () => {
    if (!selectedReview) {
      setError("Select a review to submit.");
      return;
    }

    if (selectedReview.review_window_open === false) {
      setError(getReviewWindowMessage(selectedReview) ?? "Review period is closed.");
      return;
    }

    const invalidScore = (selectedReview.criteria ?? []).find((criterion) => {
      const hasScore = criterion.criterion_row?.hasScore ?? true;
      if (!hasScore) {
        return false;
      }

      const value = draft[criterion.id]?.grade;
      if (value === undefined || value === null || Number.isNaN(Number(value))) {
        return true;
      }

      const max = criterion.criterion_row?.scoreMax ?? 0;
      return Number(value) < 0 || Number(value) > max;
    });

    if (invalidScore) {
      const max = invalidScore.criterion_row?.scoreMax ?? 0;
      setError(
        `Please enter a valid score from 0 to ${max} for: ${invalidScore.criterion_row?.question ?? "criterion"}`,
      );
      return;
    }

    const missingComment = (selectedReview.criteria ?? []).find((criterion) => {
      const hasScore = criterion.criterion_row?.hasScore ?? true;
      if (hasScore) {
        return false;
      }

      const comments = draft[criterion.id]?.comments ?? "";
      return comments.trim().length === 0;
    });

    if (missingComment) {
      setError(`Please provide comments for: ${missingComment.criterion_row?.question ?? "criterion"}`);
      return;
    }

    const criteriaUpdates = (selectedReview.criteria ?? []).map((criterion) => ({
      criterionID: criterion.id,
      grade: criterion.criterion_row?.hasScore === false ? undefined : draft[criterion.id]?.grade,
      comments: draft[criterion.id]?.comments ?? "",
    }));

    try {
      setSaving(true);
      setError("");
      setSuccess("");
      const payload = await markReview(selectedReview.id, criteriaUpdates);
      const updatedReview: ReviewAssignment = payload.review;

      setReviews((prev) =>
        prev.map((review) => (review.id === updatedReview.id ? updatedReview : review)),
      );
      setSuccess("Review submitted successfully and marked complete.");
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to submit review";
      setError(message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="card border-0 shadow-sm p-3 p-md-4 mt-3">
      <h3 className="h5 mb-3">Your Assigned Peer Reviews</h3>

      {!loading ? <p className="mb-3 text-muted">Assigned reviews: {reviews.length}</p> : null}

      {loading ? <p className="mb-0">Loading assigned reviews...</p> : null}

      {!loading && reviews.length === 0 ? (
        <p className="mb-0">You have no assigned reviews for this assignment yet.</p>
      ) : null}

      {!loading && reviews.length > 0 ? (
        <>
          <div className="mb-3">
            <label className="form-label">Choose Review To Grade</label>
            <select
              className="form-select"
              value={selectedReviewId ?? ""}
              onChange={(event) => handleReviewChange(Number(event.target.value))}
            >
              {reviews.map((review) => (
                <option key={review.id} value={review.id}>
                  {review.reviewee?.name ?? `student ${review.reviewee?.id}`} ({isReviewComplete(review) ? "Complete" : "Pending"})
                </option>
              ))}
            </select>
          </div>

          {selectedReview ? (
            <div className="ReviewCriterionCard mb-3 p-3">
              <div className="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-2">
                <h4 className="h6 mb-0">
                  Reviewing: {selectedReview.reviewee?.name ?? `student ${selectedReview.reviewee?.id}`}
                </h4>
                <span className={`badge ${isReviewComplete(selectedReview) ? "text-bg-success" : "text-bg-secondary"}`}>
                  {isReviewComplete(selectedReview) ? "Complete" : "Pending"}
                </span>
              </div>

              {selectedReview.assignment?.description ? (
                <p className="mb-2">{selectedReview.assignment.description}</p>
              ) : null}

              <div className="small text-muted">
                {selectedReview.assignment?.start_date ? (
                  <p className="mb-1">Review opens: {formatDateTime(selectedReview.assignment.start_date)}</p>
                ) : null}
                {selectedReview.assignment?.due_date ? (
                  <p className="mb-0">Review closes: {formatDateTime(selectedReview.assignment.due_date)}</p>
                ) : null}
              </div>
            </div>
          ) : null}

          {selectedReviewWindowMessage ? <p className="text-warning mt-2">{selectedReviewWindowMessage}</p> : null}

          {selectedReview?.criteria?.map((criterion) => {
            const criterionRow = criterion.criterion_row;
            const scoreMax = criterionRow?.scoreMax ?? 0;
            const hasScore = criterionRow?.hasScore ?? true;

            return (
              <div key={criterion.id} className="ReviewCriterionCard mb-3 p-3">
                <div className="d-flex justify-content-between align-items-start gap-3 mb-2">
                  <h4 className="h6 mb-0">{criterionRow?.question ?? "Criterion"}</h4>
                  {hasScore ? <span className="badge text-bg-light">Max {scoreMax}</span> : null}
                </div>

                {hasScore ? (
                  <div className="mb-2">
                    <label className="form-label">Score</label>
                    <input
                      className="form-control"
                      type="number"
                      min={0}
                      max={scoreMax}
                      value={draft[criterion.id]?.grade ?? ""}
                      onChange={(event) => handleScoreChange(criterion.id, event.target.value)}
                    />
                  </div>
                ) : null}

                <div>
                  <label className="form-label">Comments</label>
                  <textarea
                    className="form-control"
                    rows={3}
                    value={draft[criterion.id]?.comments ?? ""}
                    onChange={(event) => handleCommentsChange(criterion.id, event.target.value)}
                    placeholder="Write your feedback"
                  />
                </div>
              </div>
            );
          })}

          <button
            className="btn btn-primary"
            onClick={handleSubmit}
            disabled={saving || selectedReview?.review_window_open === false}
          >
            {saving ? "Submitting..." : "Submit Review"}
          </button>
        </>
      ) : null}

      {error ? <p className="text-danger mt-3 mb-0">{error}</p> : null}
      {success ? <p className="text-success mt-3 mb-0">{success}</p> : null}
    </div>
  );
}
