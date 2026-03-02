import AssignmentCard from "../components/AssignmentCard";
import Button from "../components/Button";
import "./ClassHome.css";
import { useParams } from "react-router-dom";
import { useState, useEffect } from "react";
import { listAssignments, listClasses, createAssignment, editAssignment, deleteAssignment } from "../util/api";
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
  const [newAssignmentStartDate, setNewAssignmentStartDate] = useState("");
  const [newAssignmentDueDate, setNewAssignmentDueDate] = useState("");
  const [className, setClassName] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState('');
  const [statusType, setStatusType] = useState<'error' | 'success'>('error');
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editName, setEditName] = useState("");
  const [editStartDate, setEditStartDate] = useState("");
  const [editDueDate, setEditDueDate] = useState("");

  useEffect(() => {
    (async () => {
      const resp = await listAssignments(String(id));
      const classes = await listClasses();
      const currentClass = classes.find((c: { id: number }) => c.id === Number(id));
      setAssignments(resp);
      setClassName(currentClass?.name || null);
    })();
  }, []);
    
    const tryCreateAssingment = async () => {
      try {
        setStatusMessage('');
        if (!newAssignmentName || !newAssignmentStartDate || !newAssignmentDueDate) {
          setStatusType('error');
          setStatusMessage('Start date, due date, and name are required.');
          return;
        }
        const response = await createAssignment(idNew, newAssignmentName, newAssignmentStartDate, newAssignmentDueDate);
        const createdAssignment = response?.assignment;

        if (!createdAssignment?.id) {
          throw new Error('Failed to create assignment');
        }

        setAssignments((prev) => [...prev, createdAssignment]);
        setNewAssignmentName("");
        setNewAssignmentStartDate("");
        setNewAssignmentDueDate("");
        setStatusType('success');
        setStatusMessage('Assignment created successfully!');
      } catch (error) {
        console.error('Error creating assignment:', error);
        setStatusType('error');
        setStatusMessage('Error creating assignment.');
      }
    };

    const toLocalInputValue = (value?: string) => {
      if (!value) {
        return "";
      }
      const date = new Date(value);
      const offset = date.getTimezoneOffset();
      const localDate = new Date(date.getTime() - offset * 60 * 1000);
      return localDate.toISOString().slice(0, 16);
    };

    const formatDateTime = (value?: string) => {
      if (!value) {
        return "Not set";
      }
      const date = new Date(value);
      if (Number.isNaN(date.getTime())) {
        return "Invalid date";
      }
      return date.toLocaleString();
    };

    const getTimeUntilDue = (dueDate?: string) => {
      if (!dueDate) {
        return "No due date";
      }
      const due = new Date(dueDate);
      const diffMs = due.getTime() - Date.now();
      if (Number.isNaN(due.getTime())) {
        return "Invalid due date";
      }
      if (diffMs <= 0) {
        return "Past due";
      }
      const totalMinutes = Math.floor(diffMs / 60000);
      const days = Math.floor(totalMinutes / (24 * 60));
      const hours = Math.floor((totalMinutes % (24 * 60)) / 60);
      const minutes = totalMinutes % 60;
      return `${days}d ${hours}h ${minutes}m remaining`;
    };

    const isPastDue = (assignment: Assignment) => {
      if (!assignment.due_date) {
        return false;
      }
      const due = new Date(assignment.due_date);
      return !Number.isNaN(due.getTime()) && due.getTime() <= Date.now();
    };

    const startEdit = (assignment: Assignment) => {
      setEditingId(assignment.id);
      setEditName(assignment.name || "");
      setEditStartDate(toLocalInputValue(assignment.start_date));
      setEditDueDate(toLocalInputValue(assignment.due_date));
    };

    const cancelEdit = () => {
      setEditingId(null);
      setEditName("");
      setEditStartDate("");
      setEditDueDate("");
    };

    const saveEdit = async (assignmentId: number) => {
      try {
        setStatusMessage('');
        const response = await editAssignment(assignmentId, {
          name: editName,
          start_date: editStartDate,
          due_date: editDueDate,
        });
        const updated = response?.assignment;
        if (!updated?.id) {
          throw new Error('Failed to update assignment');
        }
        setAssignments((prev) => prev.map((item) => (item.id === assignmentId ? updated : item)));
        cancelEdit();
        setStatusType('success');
        setStatusMessage('Assignment updated successfully!');
      } catch (error) {
        console.error('Error updating assignment:', error);
        setStatusType('error');
        setStatusMessage('Error updating assignment.');
      }
    };

    const handleDelete = async (assignmentId: number) => {
      try {
        setStatusMessage('');
        await deleteAssignment(assignmentId);
        setAssignments((prev) => prev.filter((item) => item.id !== assignmentId));
        setStatusType('success');
        setStatusMessage('Assignment deleted successfully!');
      } catch (error) {
        console.error('Error deleting assignment:', error);
        setStatusType('error');
        setStatusMessage('Error deleting assignment.');
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
          <ul className="Assignment">
            {assignments.map((assignment) => {
              const pastDue = isPastDue(assignment);
              return (
                <li key={assignment.id}>
                  <div className="AssignmentRow">
                    <AssignmentCard id={assignment.id}>
                      <div className="AssignmentCardContent">
                        <div className="AssignmentTitle">{assignment.name}</div>
                        <div className="AssignmentMeta">
                          <span>Start: {formatDateTime(assignment.start_date)}</span>
                          <span>Due: {formatDateTime(assignment.due_date)}</span>
                          <span>{getTimeUntilDue(assignment.due_date)}</span>
                        </div>
                      </div>
                    </AssignmentCard>

                    {isTeacher() && !pastDue ? (
                      <div className="AssignmentActions">
                        <Button onClick={() => startEdit(assignment)}>
                          Edit
                        </Button>
                        <Button type="secondary" onClick={() => handleDelete(assignment.id)}>
                          Delete
                        </Button>
                      </div>
                    ) : null}
                  </div>

                  {editingId === assignment.id ? (
                    <div className="AssignmentEditForm">
                      <label>
                        Name
                        <input
                          type="text"
                          value={editName}
                          onChange={(event) => setEditName(event.target.value)}
                        />
                      </label>
                      <label>
                        Start Date
                        <input
                          type="datetime-local"
                          value={editStartDate}
                          onChange={(event) => setEditStartDate(event.target.value)}
                        />
                      </label>
                      <label>
                        Due Date
                        <input
                          type="datetime-local"
                          value={editDueDate}
                          onChange={(event) => setEditDueDate(event.target.value)}
                        />
                      </label>
                      <div className="AssignmentEditActions">
                        <Button onClick={() => saveEdit(assignment.id)}>Save</Button>
                        <Button type="secondary" onClick={cancelEdit}>
                          Cancel
                        </Button>
                      </div>
                    </div>
                  ) : null}
                </li>
              );
            })}
          </ul>
        </div>

        {isTeacher() ? (
          <div className="AssInputChunk">
            <span>New Assignment Name:</span>
            <Textbox
              placeholder="New Assignment..."
              onInput={setNewAssignmentName}
              className="AssignmentInput"
            />
            <div className="AssignmentInputRow">
              <span>Start Date:</span>
              <input
                className="AssignmentInput"
                type="datetime-local"
                value={newAssignmentStartDate}
                onChange={(event) => setNewAssignmentStartDate(event.target.value)}
              />
            </div>
            <div className="AssignmentInputRow">
              <span>Due Date:</span>
              <input
                className="AssignmentInput"
                type="datetime-local"
                value={newAssignmentDueDate}
                onChange={(event) => setNewAssignmentDueDate(event.target.value)}
              />
            </div>
            <div className="AssignmentCountdown">
              {getTimeUntilDue(newAssignmentDueDate)}
            </div>
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
