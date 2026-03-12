import { useParams, useLocation, useNavigate } from "react-router-dom";
import RubricCreator from "../components/RubricCreator";
import Button from "../components/Button";
import "./CriteriaCreation.css";

export default function CriteriaCreation() {
  const { id } = useParams();
  const location = useLocation();
  const navigate = useNavigate();

  const classId = location.state?.classId;
  const assignmentName = location.state?.assignmentName;

  const handleBackToClass = () => {
    if (classId) {
      navigate(`/classes/${classId}/home`);
    } else {
      navigate("/home");
    }
  };

  return (
    <div className="CriteriaCreationPage">
      <div className="CriteriaCreationHeader">
        <div className="CriteriaCreationHeaderLeft">
          <h2>Create Criteria</h2>
          {assignmentName && (
            <span className="CriteriaCreationAssignmentName">
              {assignmentName}
            </span>
          )}
        </div>
        <div className="CriteriaCreationHeaderRight">
          <Button onClick={handleBackToClass} type="secondary">
            ← Back to Class
          </Button>
        </div>
      </div>

      <div className="CriteriaCreationBody">
        <RubricCreator id={Number(id)} />
      </div>
    </div>
  );
}
