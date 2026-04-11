import { useCallback, useEffect, useMemo, useState } from 'react';

import { assignReview, getAssignmentGrouping, listSeparatedReviewsForAssignment } from '../util/api';

import './ReviewAssigner.css';

interface Props {
  assignmentId: number;
  students: User[];
  onAssigned?: (message: string) => void;
}

export default function ReviewAssigner({ assignmentId, students, onAssigned }: Props) {
  const [reviewerId, setReviewerId] = useState<number | ''>('');
  const [revieweeId, setRevieweeId] = useState<number | ''>('');
  const [reviewerGroupId, setReviewerGroupId] = useState<number | ''>('');
  const [revieweeGroupId, setRevieweeGroupId] = useState<number | ''>('');
  const [assignmentMode, setAssignmentMode] = useState<'solo' | 'group'>('solo');
  const [groupReviewType, setGroupReviewType] = useState<'group' | 'peer'>('group');
  const [groups, setGroups] = useState<AssignmentGroupingGroup[]>([]);
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

  const groupsById = useMemo(() => {
    const map = new Map<number, AssignmentGroupingGroup>();
    groups.forEach((group) => {
      map.set(group.id, group);
    });
    return map;
  }, [groups]);

  const groupOptions = useMemo(
    () =>
      groups
        .slice()
        .sort((a, b) => a.name.localeCompare(b.name)),
    [groups],
  );

  const studentGroupNameByUserId = useMemo(() => {
    const map = new Map<number, string>();
    groups.forEach((group) => {
      group.members.forEach((member) => {
        map.set(member.userID, group.name);
      });
    });
    return map;
  }, [groups]);

  const canAssignGroupToGroup = groupOptions.length >= 2;
  const canAssignIntraGroupPeer = groupOptions.length >= 1;
  const canAssignSelectedGroupMode =
    groupReviewType === 'group' ? canAssignGroupToGroup : canAssignIntraGroupPeer;

  const groupedReviewAssignments = useMemo(() => {
    const grouped = new Map<
      string,
      { reviewerLabel: string; reviewTypeLabel: 'GROUP' | 'PEER'; reviewees: string[] }
    >();

    reviews.forEach((review) => {
      const reviewerName =
        review.reviewer?.name
        || studentNameById.get(Number(review.reviewer?.id))
        || `Student ${review.reviewer?.id ?? ''}`;
      const revieweeName =
        review.reviewee?.name
        || studentNameById.get(Number(review.reviewee?.id))
        || `Student ${review.reviewee?.id ?? ''}`;
      const reviewerGroupLabel = studentGroupNameByUserId.get(Number(review.reviewer?.id)) || 'Ungrouped';
      const revieweeGroupLabel = studentGroupNameByUserId.get(Number(review.reviewee?.id)) || 'Ungrouped';

      const isGroupToGroup = assignmentMode === 'group' && review.review_type === 'group';
      const reviewerLabel = isGroupToGroup ? reviewerGroupLabel : reviewerName;
      const revieweeLabel = isGroupToGroup ? revieweeGroupLabel : revieweeName;
      const reviewTypeLabel: 'GROUP' | 'PEER' = isGroupToGroup ? 'GROUP' : 'PEER';

      const key = `${reviewTypeLabel}:${reviewerLabel}`;
      if (!grouped.has(key)) {
        grouped.set(key, {
          reviewerLabel,
          reviewTypeLabel,
          reviewees: [],
        });
      }

      grouped.get(key)?.reviewees.push(revieweeLabel);
    });

    return Array.from(grouped.values()).sort((left, right) =>
      left.reviewerLabel.localeCompare(right.reviewerLabel, undefined, { sensitivity: 'base' }),
    );
  }, [assignmentMode, reviews, studentGroupNameByUserId, studentNameById]);

  const loadGrouping = useCallback(async () => {
    try {
      const payload: AssignmentGroupingResponse = await getAssignmentGrouping(assignmentId);
      setAssignmentMode(payload.assignment.assignment_mode === 'group' ? 'group' : 'solo');
      setGroups(Array.isArray(payload.groups) ? payload.groups : []);
    } catch {
      // Fall back to solo behavior when grouping metadata cannot be loaded.
      setAssignmentMode('solo');
      setGroups([]);
    }
  }, [assignmentId]);

  const loadReviews = useCallback(async () => {
    try {
      setError('');
      const payload: SeparatedReviewAssignments = await listSeparatedReviewsForAssignment(assignmentId);
      const flattenedReviews: ReviewAssignment[] = [
        ...(Array.isArray(payload.group_reviews) ? payload.group_reviews : []),
        ...(Array.isArray(payload.peer_reviews) ? payload.peer_reviews : []),
      ];
      setReviews(flattenedReviews);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load review assignments';
      setError(message);
      setReviews([]);
    }
  }, [assignmentId]);

  useEffect(() => {
    loadGrouping();
    loadReviews();
  }, [loadGrouping, loadReviews]);

  const handleAssign = async () => {
    try {
      setIsSubmitting(true);
      setError('');

      if (assignmentMode === 'group') {
        if (reviewerGroupId === '') {
          setError('Select a reviewer group.');
          return;
        }

        if (groupReviewType === 'group') {
          if (revieweeGroupId === '') {
            setError('Select a reviewee group.');
            return;
          }

          if (reviewerGroupId === revieweeGroupId) {
            setError('Reviewer and reviewee must be different groups.');
            return;
          }

          await assignReview(assignmentId, {
            reviewType: 'group',
            reviewerGroupID: Number(reviewerGroupId),
            revieweeGroupID: Number(revieweeGroupId),
          });
          onAssigned?.('Group-to-group review assignments created successfully.');
        } else {
          await assignReview(assignmentId, {
            reviewType: 'peer',
            reviewerGroupID: Number(reviewerGroupId),
          });
          onAssigned?.('Intra-group peer review assignments created successfully.');
        }
      } else {
        if (reviewerId === '' || revieweeId === '') {
          setError('Select both reviewer and reviewee.');
          return;
        }

        if (reviewerId === revieweeId) {
          setError('Reviewer and reviewee must be different students.');
          return;
        }

        await assignReview(assignmentId, {
          reviewerID: Number(reviewerId),
          revieweeID: Number(revieweeId),
        });
        onAssigned?.('Peer review assignment created successfully.');
      }

      await loadReviews();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to assign review';
      setError(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="ReviewAssigner">

      {assignmentMode === 'group' ? (
        <>
          {groupReviewType === 'group' && !canAssignGroupToGroup ? (
            <p className="ReviewAssignerHint mb-2">
              At least two groups are required for group-to-group review assignment.
            </p>
          ) : null}

          {groupReviewType === 'peer' && !canAssignIntraGroupPeer ? (
            <p className="ReviewAssignerHint mb-2">
              Create at least one group to assign intra-group peer reviews.
            </p>
          ) : null}

          <div className="ReviewAssignerTopGrid mb-2">
            <div className="ReviewAssignerPanel">
              <label className="form-label">Review Type</label>
              <select
                className="form-select"
                value={groupReviewType}
                onChange={(event) => setGroupReviewType(event.target.value === 'peer' ? 'peer' : 'group')}
              >
                <option value="group">Group Review (review another group)</option>
                <option value="peer">Peer Review (review your own group members)</option>
              </select>
            </div>

            <div className="ReviewAssignerPanel">
              <label className="form-label">Reviewer Group</label>
              <select
                className="form-select"
                value={reviewerGroupId}
                onChange={(event) => setReviewerGroupId(event.target.value ? Number(event.target.value) : '')}
                disabled={!canAssignIntraGroupPeer}
              >
                <option value="">Select group</option>
                {groupOptions.map((group) => (
                  <option key={group.id} value={group.id}>
                    {group.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="ReviewAssignerPanel">
              <label className="form-label">Reviewee Group</label>
              {groupReviewType === 'group' ? (
                <select
                  className="form-select"
                  value={revieweeGroupId}
                  onChange={(event) => setRevieweeGroupId(event.target.value ? Number(event.target.value) : '')}
                  disabled={!canAssignGroupToGroup}
                >
                  <option value="">Select group</option>
                  {groupOptions.map((group) => (
                    <option key={group.id} value={group.id}>
                      {group.name}
                    </option>
                  ))}
                </select>
              ) : (
                <p className="mb-0 small text-muted">
                  Peer review mode assigns each member of the selected reviewer group to review every other member of the same group.
                </p>
              )}
            </div>
          </div>

          {groupOptions.length > 0 ? (
            <div className="ReviewAssignerGroupPreview mt-2">
              {groupOptions.map((group) => (
                <div key={group.id}>
                  <span className="fw-semibold">{group.name}:</span>{' '}
                  {(groupsById.get(group.id)?.members || []).map((member) => member.name).join(', ') || 'No members'}
                </div>
              ))}
            </div>
          ) : null}

          <div className="ReviewAssignerActionRow mt-2">
            <button
              type="button"
              className="btn btn-primary"
              onClick={handleAssign}
              disabled={isSubmitting || !canAssignSelectedGroupMode}
            >
              {isSubmitting ? 'Assigning...' : groupReviewType === 'group' ? 'Assign Group Reviews' : 'Assign Peer Reviews'}
            </button>
          </div>

          {error ? <p className="ReviewAssignerError mt-2 mb-0">{error}</p> : null}
        </>
      ) : studentOptions.length < 2 ? (
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
        {groupedReviewAssignments.length === 0 ? (
          <p className="ReviewAssignerHint mb-0">No review assignments yet.</p>
        ) : (
          <div className="ReviewAssignerAccordion">
            {groupedReviewAssignments.map((groupedAssignment) => (
              <details className="ReviewAssignerAccordionItem" key={`${groupedAssignment.reviewTypeLabel}:${groupedAssignment.reviewerLabel}`}>
                <summary className="ReviewAssignerAccordionSummary">
                  <span className="ReviewAssignerAccordionHeading">
                    <span className="badge text-bg-light text-uppercase">{groupedAssignment.reviewTypeLabel}</span>
                    <span className="fw-semibold">{groupedAssignment.reviewerLabel}</span>
                    <span>reviews</span>
                  </span>
                  <span className="text-muted small">{groupedAssignment.reviewees.length}</span>
                </summary>
                <ul className="ReviewAssignerAccordionList mb-0">
                  {groupedAssignment.reviewees.map((revieweeLabel, index) => (
                    <li key={`${groupedAssignment.reviewerLabel}-${revieweeLabel}-${index}`}>
                      <span className="fw-semibold">{revieweeLabel}</span>
                    </li>
                  ))}
                </ul>
              </details>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
