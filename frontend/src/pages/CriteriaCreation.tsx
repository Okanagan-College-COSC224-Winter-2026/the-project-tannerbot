import { useParams, useLocation, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import RubricCreator from "../components/RubricCreator";
import Button from "../components/Button";
import { getRubricByAssignment } from "../util/api";
import "./CriteriaCreation.css";

interface CriteriaDescription {
  id: number;
  rubricID: number;
  question: string;
  scoreMax: number;
  hasScore: boolean;
}

interface RubricData {
  id: number;
  assignmentID: number;
  canComment: boolean;
  criteria_descriptions: CriteriaDescription[];
}

export default function CriteriaCreation() {
  const { id } = useParams();
  const location = useLocation();
  const navigate = useNavigate();

  const classId = location.state?.classId;
  const assignmentName = location.state?.assignmentName;

  const [rubric, setRubric] = useState<RubricData | null>(null);

  const fetchRubric = async () => {
    if (!id) return;
    const data = await getRubricByAssignment(Number(id));
    setRubric(data);
  };

  useEffect(() => {
    fetchRubric();
  }, [id]);

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
        {rubric && rubric.criteria_descriptions.length > 0 && (
          <div className="ExistingCriteria">
            <h3>Existing Criteria</h3>
            <table className="ExistingCriteriaTable">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Question</th>
                  <th>Max Score</th>
                </tr>
              </thead>
              <tbody>
                {rubric.criteria_descriptions.map((c, i) => (
                  <tr key={c.id}>
                    <td>{i + 1}</td>
                    <td>{c.question}</td>
                    <td>{c.hasScore ? c.scoreMax : "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {rubric.canComment && (
              <p className="ExistingCriteriaNote">Reviewers can leave a comment.</p>
            )}
          </div>
        )}

        <RubricCreator id={Number(id)} onRubricCreated={fetchRubric} />
      </div>
    </div>
  );
}
