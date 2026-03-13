import { useParams, useLocation, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import RubricCreator from "../components/RubricCreator";
import Button from "../components/Button";
import { deleteCriteria, getRubricByAssignment, updateCriteria } from "../util/api";
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
  const [editingCriteriaId, setEditingCriteriaId] = useState<number | null>(null);
  const [editQuestion, setEditQuestion] = useState("");
  const [editScoreMax, setEditScoreMax] = useState(0);
  const [editHasScore, setEditHasScore] = useState(true);
  const [actionMessage, setActionMessage] = useState("");
  const existingScoredTotal = (rubric?.criteria_descriptions || []).reduce(
    (sum, row) => sum + (row.hasScore ? Math.max(0, row.scoreMax) : 0),
    0
  );

  const fetchRubric = async () => {
    if (!id) return;
    const data = await getRubricByAssignment(Number(id));
    setRubric(data);
  };

  useEffect(() => {
    fetchRubric();
  }, [id]);

  const beginEdit = (criteria: CriteriaDescription) => {
    setEditingCriteriaId(criteria.id);
    setEditQuestion(criteria.question || "");
    setEditHasScore(criteria.hasScore);
    setEditScoreMax(criteria.hasScore ? criteria.scoreMax : 0);
    setActionMessage("");
  };

  const cancelEdit = () => {
    setEditingCriteriaId(null);
    setActionMessage("");
  };

  const saveEdit = async () => {
    if (!editingCriteriaId) return;
    try {
      await updateCriteria(
        editingCriteriaId,
        editQuestion.trim(),
        editHasScore ? Math.max(0, Math.min(100, editScoreMax)) : 0,
        editHasScore
      );
      setEditingCriteriaId(null);
      setActionMessage("Criterion updated.");
      await fetchRubric();
    } catch (error) {
      console.error("Error updating criterion:", error);
      setActionMessage("Failed to update criterion.");
    }
  };

  const removeCriteria = async (criteriaId: number) => {
    if (!window.confirm("Delete this criterion?")) return;
    try {
      await deleteCriteria(criteriaId);
      setActionMessage("Criterion deleted.");
      if (editingCriteriaId === criteriaId) {
        setEditingCriteriaId(null);
      }
      await fetchRubric();
    } catch (error) {
      console.error("Error deleting criterion:", error);
      setActionMessage("Failed to delete criterion.");
    }
  };

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
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {rubric.criteria_descriptions.map((c, i) => (
                  <tr key={c.id}>
                    <td>{i + 1}</td>
                    <td>
                      {editingCriteriaId === c.id ? (
                        <input
                          className="CriteriaEditInput"
                          value={editQuestion}
                          onChange={(e) => setEditQuestion(e.target.value)}
                        />
                      ) : (
                        c.question
                      )}
                    </td>
                    <td>
                      {editingCriteriaId === c.id ? (
                        <div className="CriteriaEditScoreWrap">
                          <label className="CriteriaEditCheckbox">
                            <input
                              type="checkbox"
                              checked={editHasScore}
                              onChange={(e) => setEditHasScore(e.target.checked)}
                            />
                            Has score
                          </label>
                          {editHasScore ? (
                            <input
                              className="CriteriaEditInput CriteriaEditNumber"
                              type="number"
                              min={0}
                              max={100}
                              value={editScoreMax}
                              onChange={(e) =>
                                setEditScoreMax(Math.max(0, Math.min(100, Number(e.target.value))))
                              }
                            />
                          ) : (
                            <span>—</span>
                          )}
                        </div>
                      ) : c.hasScore ? (
                        c.scoreMax
                      ) : (
                        "—"
                      )}
                    </td>
                    <td>
                      <div className="CriteriaRowActions">
                        {editingCriteriaId === c.id ? (
                          <>
                            <button className="CriteriaActionButton save" onClick={saveEdit}>Save</button>
                            <button className="CriteriaActionButton cancel" onClick={cancelEdit}>Cancel</button>
                          </>
                        ) : (
                          <>
                            <button className="CriteriaActionButton edit" onClick={() => beginEdit(c)}>Edit</button>
                            <button className="CriteriaActionButton delete" onClick={() => removeCriteria(c.id)}>Delete</button>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {actionMessage && <p className="ExistingCriteriaNote">{actionMessage}</p>}
            {rubric.canComment && (
              <p className="ExistingCriteriaNote">Reviewers can leave a comment.</p>
            )}
          </div>
        )}

        <RubricCreator
          id={Number(id)}
          onRubricCreated={fetchRubric}
          existingScoredTotal={existingScoredTotal}
        />
      </div>
    </div>
  );
}
