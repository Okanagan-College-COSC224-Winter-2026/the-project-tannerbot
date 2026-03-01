import AssignmentCard from "../components/AssignmentCard";
import Button from "../components/Button";
import "./ClassHome.css";
import { useParams } from "react-router-dom";
import { useState, useEffect } from "react";
import { listAssignments, listClasses, createAssignment } from "../util/api";
import TabNavigation from "../components/TabNavigation";
import { importCSV } from "../util/csv";
import Textbox from "../components/Textbox";
import StatusMessage from "../components/StatusMessage";
import { isTeacher } from "../util/login";

export default function ClassHome() {
  const { id } = useParams();
  const idNew = Number(id)
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [newAssignmentName, setNewAssignmentName] = useState("");
  const [className, setClassName] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState('');
  const [statusType, setStatusType] = useState<'error' | 'success'>('error');

  useEffect(() => { 
    if (!id) return;

    (async () => {
      const resp = await listAssignments(String(id));
      const classes = await listClasses();
      const currentClass = classes.find((c: { id: number }) => c.id === Number(id));
      setAssignments(resp);
      setClassName(currentClass?.name || null);
    })();
  }, [id]);
    
    const tryCreateAssingment = async () => {
      try {
        setStatusMessage('');
        const response = await createAssignment(idNew, newAssignmentName);
        const createdAssignment = response?.assignment;

        if (!createdAssignment?.id) {
          throw new Error('Failed to create assignment');
        }

        setAssignments((prev) => [...prev, createdAssignment]);
        setNewAssignmentName("");
        setStatusType('success');
        setStatusMessage('Assignment created successfully!');
      } catch (error) {
        console.error('Error creating assignment:', error);
        setStatusType('error');
        setStatusMessage('Error creating assignment.');
      }
    };
    
    return (
      <>
        <div className="ClassHeader">
          <div className="ClassHeaderLeft">
            <h2>{className}</h2>
          </div>

        <div className="ClassHeaderRight">
          {isTeacher() ? (
            <Button onClick={() => importCSV(id as string)}>
              Add Students via CSV
            </Button>
          ) : null}
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
        ]}
      />

      <StatusMessage message={statusMessage} type={statusType} />

      <div className="Class">
        <div className="Assignments"> 
          {assignments.length === 0 ? (
            <p>No assignments yet.</p>
          ) : (
            <ul className="Assignment">
              {assignments.map((assignment) => (
                <li key={assignment.id}>
                  <AssignmentCard id={assignment.id}>
                    <div>
                      <div style={{ fontWeight: 600 }}>{assignment.name}</div>
                      <div style={{ fontSize: "0.9rem", opacity: 0.8 }}>
                        Due: {assignment.due_date ? new Date(assignment.due_date).toLocaleDateString() : "Not set"}
                      </div>
                    </div>
                  </AssignmentCard>
                </li>
            ))}
          </ul>
          )}
        </div>

        {isTeacher() ? (
          <div className="AssInputChunk">
            <span>New Assignment Name:</span>
            <Textbox
              placeholder="New Assignment..."
              onInput={setNewAssignmentName}
              className="AssignmentInput"
            />
            <Button
              onClick={() =>
                tryCreateAssingment()
              }
            >
              Add
            </Button>
          </div>
        ) : null}
      </div>
    </>
  );
}
