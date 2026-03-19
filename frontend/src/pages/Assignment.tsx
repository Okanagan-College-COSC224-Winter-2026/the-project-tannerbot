import { useParams } from "react-router-dom";

import TabNavigation from "../components/TabNavigation";
import StudentAssignedReviews from "../components/StudentAssignedReviews";
import { isTeacher } from "../util/login";

import "./Assignment.css";

export default function Assignment() {
  const { id } = useParams();
  const assignmentId = Number(id);

  return (
    <div className="AssignmentPage container-fluid py-4 px-3 px-md-4">
      <div className="AssignmentHeader card border-0 shadow-sm mb-3 p-3 p-md-4">
        <h2 className="h3 fw-bold mb-0">Assignment {assignmentId}</h2>
      </div>

      <TabNavigation
        tabs={[
          {
            label: "Home",
            path: `/assignments/${id}`,
          },
          {
            label: "Group",
            path: `/assignments/${id}/group`,
          },
        ]}
      />

      {isTeacher() ? (
        <div className="card border-0 shadow-sm p-3 p-md-4 mt-3">
          <p className="mb-0">Review assignment is managed from class home for teachers.</p>
        </div>
      ) : (
        <StudentAssignedReviews assignmentId={assignmentId} />
      )}
    </div>
  );
}
