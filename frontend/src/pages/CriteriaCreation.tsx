import { useParams, useLocation, useNavigate } from "react-router-dom";
import { useCallback, useEffect, useState } from "react";
import RubricCreator from "../components/RubricCreator";
import Button from "../components/Button";
import ManageAssignment from "../components/ManageAssignment";
import TabNavigation from "../components/TabNavigation";
import { deleteCriteria, getAssignmentGrouping, getRubricByAssignment, updateCriteria } from "../util/api";
import { isAdmin, isTeacher } from "../util/login";
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
  rubric_type?: "peer" | "group";
  criteria_descriptions: CriteriaDescription[];
}

export default function CriteriaCreation() {
  const { id } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const canManageAssignment = isTeacher() || isAdmin();

  const stateClassId = (location.state as { classId?: string | number } | null)?.classId;
  const searchClassId = new URLSearchParams(location.search).get("classId");
  const classId = stateClassId ?? searchClassId;
  const classIdForManage = classId ?? undefined;
  const classQuery = classId ? `?classId=${classId}` : "";

  const [rubric, setRubric] = useState<RubricData | null>(null);
  const [assignmentMode, setAssignmentMode] = useState<"solo" | "group">("solo");
  const [rubricType, setRubricType] = useState<"peer" | "group">("peer");
  const [editingCriteriaId, setEditingCriteriaId] = useState<number | null>(null);
  const [editQuestion, setEditQuestion] = useState("");
  const [editScoreMax, setEditScoreMax] = useState(0);
  const [actionMessage, setActionMessage] = useState("");
  const existingScoredTotal = (rubric?.criteria_descriptions || []).reduce(
    (sum, row) => sum + (row.hasScore ? Math.max(0, row.scoreMax) : 0),
    0
  );

  const fetchRubric = useCallback(async () => {
    if (!id) return;
    const data = await getRubricByAssignment(Number(id), rubricType);
    setRubric(data);
  }, [id, rubricType]);

  const fetchAssignmentMode = useCallback(async () => {
    if (!id) return;
    try {
      const groupingPayload: AssignmentGroupingResponse = await getAssignmentGrouping(Number(id));
      const mode = groupingPayload.assignment.assignment_mode === "group" ? "group" : "solo";
      setAssignmentMode(mode);
      if (mode === "solo") {
        setRubricType("peer");
      }
    } catch {
      setAssignmentMode("solo");
      setRubricType("peer");
    }
  }, [id]);

  useEffect(() => {
    fetchAssignmentMode();
  }, [fetchAssignmentMode]);

  useEffect(() => {
    fetchRubric();
  }, [fetchRubric]);

  const beginEdit = (criteria: CriteriaDescription) => {
    setEditingCriteriaId(criteria.id);
    setEditQuestion(criteria.question || "");
    setEditScoreMax(criteria.scoreMax);
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
        Math.max(0, Math.min(100, editScoreMax)),
        true
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
    <div className="AssignmentPage CriteriaCreationPage container-fluid py-4 px-3 px-md-4">
      <div className="AssignmentHeader CriteriaCreationHeader card border-0 shadow-sm mb-3 p-3 p-md-4">
        <div className="CriteriaCreationHeaderLeft">
          <h2 className="h3 fw-bold mb-0">Assignment {id}</h2>
        </div>
        <div className="CriteriaCreationHeaderRight">
          <Button onClick={handleBackToClass} type="secondary">
            Return to Class
          </Button>
          <ManageAssignment
            assignmentId={id ? Number(id) : undefined}
            classId={classIdForManage}
          />
        </div>
      </div>

      <div className="CriteriaNavRow mb-3">
        <div className="CriteriaTabsWrap">
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
        </div>

        {assignmentMode === "group" ? (
          <div className="RubricTypeContainer">
            <select
              id="rubric-type-select"
              className="form-select RubricTypeSelect"
              value={rubricType}
              onChange={(event) => setRubricType(event.target.value === "group" ? "group" : "peer")}
            >
              <option value="peer">Peer Review Rubric</option>
              <option value="group">Group Review Rubric</option>
            </select>
          </div>
        ) : null}
      </div>

      <div className="CriteriaCreationBody">

        {rubric && rubric.criteria_descriptions.length > 0 && (
          <div className="ExistingCriteria">
            <h3>
              Existing {rubricType === "group" ? "Group Review" : "Peer Review"} Criteria
            </h3>
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
                          placeholder="Enter criterion point"
                        />
                      ) : (
                        <div>{c.question}</div>
                      )}
                    </td>
                    <td>
                      {editingCriteriaId === c.id ? (
                        <input
                          className="CriteriaEditInput CriteriaEditNumber"
                          type="number"
                          min={0}
                          max={100}
                          value={editScoreMax === 0 ? "" : editScoreMax}
                          onChange={(e) =>
                            setEditScoreMax(Math.max(0, Math.min(100, Number(e.target.value || 0))))
                          }
                          placeholder="Max Score"
                        />
                      ) : (
                        c.scoreMax
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
          </div>
        )}

        <RubricCreator
          id={Number(id)}
          onRubricCreated={fetchRubric}
          existingScoredTotal={existingScoredTotal}
          rubricType={rubricType}
        />
      </div>
    </div>
  );
}
