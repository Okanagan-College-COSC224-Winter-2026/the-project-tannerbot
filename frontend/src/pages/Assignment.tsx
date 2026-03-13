import { useEffect, useState, ChangeEvent } from "react";
import { useParams } from "react-router-dom";
import "./Assignment.css";
import RubricCreator from "../components/RubricCreator";
import RubricDisplay from "../components/RubricDisplay";
import TabNavigation from "../components/TabNavigation";
import AssignmentModal from "../components/AssignmentModal";
import { isTeacher } from "../util/login";

import { 
  listStuGroup,
  getUserId,
  createReview,
  createCriterion,
  getReview,
  getAssignmentDetails,
  editAssignment,
  deleteAssignment,
  deleteRubric
} from "../util/api";

interface SelectedCriterion {
  row: number;
  column: number;
}

export default function Assignment() {
  const { id } = useParams();
  const [stuGroup, setStuGroup] = useState<StudentGroups[]>([]);
  const [revieweeID, setRevieweeID] = useState<number>(0);
  const [stuID, setStuID] = useState<number>(0);
  const [selectedCriteria, setSelectedCriteria] = useState<SelectedCriterion[]>([]);
  const [review, setReview] = useState<number[]>([]);
  const [assignmentDetails, setAssignmentDetails] = useState<any>(null);

  // editing state for modal
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState<"create" | "edit">("edit");
  const [editingAssignment, setEditingAssignment] = useState<any>(null);

  // status messages
  const [statusMessage, setStatusMessage] = useState<string>("");
  const [statusType, setStatusType] = useState<"success" | "error">("success");

  useEffect(() => {
      (async () => {
        const stuID = await getUserId();
        setStuID(stuID);
        const stus = await listStuGroup(Number(id), stuID);
        setStuGroup(stus);
        try {
          const reviewResponse = await getReview(Number(id), stuID, revieweeID);
          const reviewData = await reviewResponse.json();
          setReview(reviewData.grades);
          console.log("Review data:", reviewData);
        } catch (error) {
          console.error('Error fetching review:', error);
        }
      })();
  }, [revieweeID, id, stuID]);

  // fetch assignment details for teachers so they can inspect peer-review settings
  useEffect(() => {
    if (isTeacher() && id) {
      getAssignmentDetails(Number(id))
        .then((data) => {
          setAssignmentDetails(data);
        })
        .catch((err) => console.error('could not fetch details', err));
    }
  }, [id]);

  const openEditModal = () => {
    setEditingAssignment(assignmentDetails);
    setModalMode("edit");
    setIsModalOpen(true);
  };

  const handleModalSave = async (name: string, description: string, dueDate: string, startDate: string, _attachments: File[]) => {
    if (modalMode === "edit" && editingAssignment) {
      try {
        await editAssignment(editingAssignment.id, name, description, dueDate, startDate);
        setStatusMessage("Assignment updated");
        setStatusType("success");
        // refresh details
        const updated = await getAssignmentDetails(Number(id));
        setAssignmentDetails(updated);
      } catch (err: any) {
        setStatusMessage(err.message || "Could not update assignment");
        setStatusType("error");
      }
    }
  };

  const handleDelete = async () => {
    if (!assignmentDetails) return;
    if (!window.confirm("Are you sure you want to delete this assignment?")) return;
    try {
      await deleteAssignment(Number(id));
      // go back to previous page (class home)
      window.history.back();
    } catch (err: any) {
      setStatusMessage(err.message || "Could not delete assignment");
      setStatusType("error");
    }
  };

  const handleDeleteRubric = async (rubricId: number) => {
    if (!window.confirm("Are you sure you want to delete this rubric? This will also delete all its criteria.")) return;
    try {
      await deleteRubric(rubricId);
      setStatusMessage("Rubric deleted successfully");
      setStatusType("success");
      // refresh details
      const updated = await getAssignmentDetails(Number(id));
      setAssignmentDetails(updated);
    } catch (err: any) {
      setStatusMessage(err.message || "Could not delete rubric");
      setStatusType("error");
    }
  };

  const handleCriterionSelect = (row: number, column: number) => {
    // Check if this criterion is already selected
    const existingIndex = selectedCriteria.findIndex(
      criterion => criterion.row === row && criterion.column === column
    );
    
    if (existingIndex >= 0) {
      // If already selected, remove it (toggle off)
      setSelectedCriteria(prev => 
        prev.filter((_, index) => index !== existingIndex)
      );
    } else {
      // Add the new criterion, removing any other selection in the same row
      setSelectedCriteria(prev => {
        // Remove any existing selection for this row
        const filteredCriteria = prev.filter(criterion => criterion.row !== row);
        // Add the new selection
        return [...filteredCriteria, { row, column }];
      });
    }
  };

  function handleRadioChange(event: ChangeEvent<HTMLInputElement>): void {
    const selectedID = Number(event.target.value);
    setRevieweeID(selectedID);
    console.log(`Selected group member ID: ${selectedID}`);
  }

  return (
    <>
      <div className="AssignmentHeader">
        <h2>Assignment {id}</h2>
        {isTeacher() && assignmentDetails && (
          <div className="assignmentActions">
            <button onClick={openEditModal}>Edit</button>
            <button onClick={handleDelete} style={{ marginLeft: '8px' }}>Delete</button>
          </div>
        )}
      </div>
      {statusMessage && (
        <div className={`status ${statusType}`}>{statusMessage}</div>
      )}

      <TabNavigation
        tabs={[
          {
            label: "Home",
            path: `/assignment/${id}`,
          },
          {
            label: "Group",
            path: `/assignment/${id}/group`,
          }
        ]}
      />

      <div className='assignmentRubricDisplay'>
        <RubricDisplay rubricId={Number(id)} onCriterionSelect={handleCriterionSelect} grades={review} />
      </div>

      {isTeacher() && assignmentDetails && (
        <div className="peerReviewSettings">
          <h3>Peer-Review Settings</h3>
          <p><strong>Assignment name:</strong> {assignmentDetails.name}</p>
          {assignmentDetails.description && (
            <p><strong>Description:</strong> {assignmentDetails.description}</p>
          )}
          <p><strong>Rubrics defined:</strong> {assignmentDetails.rubrics?.length || 0}</p>
          <ul>
            {assignmentDetails.rubrics?.map((r: any) => (
              <li key={r.id} style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span>Rubric {r.id} &ndash; canComment: {String(r.canComment)}</span>
                <button 
                  onClick={() => handleDeleteRubric(r.id)}
                  style={{ 
                    background: '#dc3545', 
                    color: 'white', 
                    border: 'none', 
                    padding: '4px 8px', 
                    borderRadius: '4px', 
                    cursor: 'pointer',
                    fontSize: '12px'
                  }}
                >
                  Delete
                </button>
              </li>
            ))}
          </ul>
          <p><strong>Attachments:</strong> {assignmentDetails.attachments?.length || 0}</p>
        </div>
      )}

      {isTeacher() && 
          <div className='assignmentRubric'>
            <RubricCreator id={Number(id)}/>
          </div>
      }

{
      //List group members as radio buttons to select for given review
      !isTeacher() && <div className='groupMembers'>
        <h3>Select a group member to review</h3>
          {stuGroup.map((stus) => {
                return (
                  <>
                  <input type='radio' id={stus.userID.toString()} value={stus.userID} name='groupMembers' onChange={handleRadioChange}></input>
                  <label htmlFor={stus.userID.toString()}>{stus.userID}</label>
                  <br></br>
                  </>
                )
              }
            )
          }
          <button className='submitReview' onClick={async () => {
            console.log("Submitting review with selected criteria:", selectedCriteria);
            try {
              const reviewResponse = await createReview(Number(id), stuID, revieweeID);
              const reviewData = await reviewResponse.json();
              console.log("Review response:", reviewData);
              for (const criterion of selectedCriteria) {
                await createCriterion(reviewData.id, criterion.row, criterion.column, "");
              }
              console.log('Review submitted successfully');
            } catch (error) {
              console.error('Error submitting review:', error);
            }
          }}>Submit Review</button>
      </div>}
      <AssignmentModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSave={handleModalSave}
        assignment={editingAssignment}
        mode={modalMode}
      />    </>
  );
}

