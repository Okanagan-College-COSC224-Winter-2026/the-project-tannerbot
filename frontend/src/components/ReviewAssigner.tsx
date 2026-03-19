import { useEffect, useMemo, useState } from 'react';

import { assignReview, listReviewsForAssignment } from '../util/api';

import './ReviewAssigner.css';

interface Props {
  assignmentId: number;
  students: User[];
  onAssigned?: (message: string) => void;
}

export default function ReviewAssigner({ assignmentId, students, onAssigned }: Props) {
  const [reviewerId, setReviewerId] = useState<number | ''>('');
  const [revieweeId, setRevieweeId] = useState<number | ''>('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [reviews, setReviews] = useState<ReviewAssignment[]>([]);

  const studentOptions = useMemo(
    () =>
      students
        .filter((student) => student.role === 'student')
        .sort((a, b) => a.name.localeCompare(b.name)),
    [students],
  );

  const studentNameById = useMemo(() => {
    const map = new Map<number, string>();
    studentOptions.forEach((student) => {
      map.set(Number(student.id), student.name);
    });
    return map;
  }, [studentOptions]);

  const loadReviews = async () => {
    try {
      setError('');
      const payload = await listReviewsForAssignment(assignmentId);
      setReviews(Array.isArray(payload) ? payload : []);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load review assignments';
      setError(message);
      setReviews([]);
    }
  };

  useEffect(() => {
    loadReviews();
  }, [assignmentId]);

  const handleAssign = async () => {
    if (reviewerId === '' || revieweeId === '') {
      setError('Select both reviewer and reviewee.');
      return;
    }

    if (reviewerId === revieweeId) {
      setError('Reviewer and reviewee must be different students.');
      return;
    }

    try {
      setIsSubmitting(true);
      setError('');
      await assignReview(assignmentId, Number(reviewerId), Number(revieweeId));
      onAssigned?.('Peer review assignment created successfully.');
      await loadReviews();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to assign review';
      setError(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="ReviewAssigner mt-3">
      <h4 className="ReviewAssignerTitle">Assign Peer Review</h4>

      {studentOptions.length < 2 ? (
        <p className="ReviewAssignerHint mb-2">At least two enrolled students are required.</p>
      ) : (
        <>
          <div className="ReviewAssignerForm row g-2 align-items-end">
            <div className="col-12 col-md-5">
              <label className="form-label">Reviewer</label>
              <select
                className="form-select"
                value={reviewerId}
                onChange={(event) => setReviewerId(event.target.value ? Number(event.target.value) : '')}
              >
                <option value="">Select student</option>
                {studentOptions.map((student) => (
                  <option key={student.id} value={student.id}>
                    {student.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="col-12 col-md-5">
              <label className="form-label">Reviewee</label>
              <select
                className="form-select"
                value={revieweeId}
                onChange={(event) => setRevieweeId(event.target.value ? Number(event.target.value) : '')}
              >
                <option value="">Select student</option>
                {studentOptions.map((student) => (
                  <option key={student.id} value={student.id}>
                    {student.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="col-12 col-md-2">
              <button
                type="button"
                className="btn btn-primary w-100"
                onClick={handleAssign}
                disabled={isSubmitting}
              >
                {isSubmitting ? 'Assigning...' : 'Assign'}
              </button>
            </div>
          </div>

          {error ? <p className="ReviewAssignerError mt-2 mb-0">{error}</p> : null}
        </>
      )}

      <div className="ReviewAssignerList mt-3">
        <h5 className="mb-2">Current Review Assignments</h5>
        {reviews.length === 0 ? (
          <p className="ReviewAssignerHint mb-0">No review assignments yet.</p>
        ) : (
          <ul className="mb-0">
            {reviews.map((review) => {
              const reviewerName = review.reviewer?.name || studentNameById.get(Number(review.reviewer?.id)) || `Student ${review.reviewer?.id ?? ''}`;
              const revieweeName = review.reviewee?.name || studentNameById.get(Number(review.reviewee?.id)) || `Student ${review.reviewee?.id ?? ''}`;

              return (
                <li key={review.id}>
                  <span className="fw-semibold">{reviewerName}</span> reviews{' '}
                  <span className="fw-semibold">{revieweeName}</span>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </div>
  );
}
