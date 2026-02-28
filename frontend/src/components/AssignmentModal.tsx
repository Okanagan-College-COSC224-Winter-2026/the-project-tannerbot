import { useState, useEffect } from "react";
import Button from "./Button";
import "./AssignmentModal.css";

interface AssignmentModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (name: string, dueDate: string, startDate: string) => void;
  assignment?: Assignment;
  mode: "create" | "edit";
}

export default function AssignmentModal({ isOpen, onClose, onSave, assignment, mode }: AssignmentModalProps) {
  const [name, setName] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [startDate, setStartDate] = useState("");

  useEffect(() => {
    if (assignment && mode === "edit") {
      setName(assignment.name || "");
      setDueDate(assignment.due_date ? assignment.due_date.slice(0, 16) : "");
      setStartDate(assignment.start_date ? assignment.start_date.slice(0, 16) : "");
    } else {
      setName("");
      setDueDate("");
      setStartDate("");
    }
  }, [assignment, mode, isOpen]);

  const handleSave = () => {
    onSave(name, dueDate, startDate);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{mode === "create" ? "Create Assignment" : "Edit Assignment"}</h2>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>
        
        <div className="modal-body">
          <div className="form-group">
            <label htmlFor="assignment-name">Assignment Name*</label>
            <input
              type="text"
              id="assignment-name"
              placeholder="Enter assignment name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="text-input"
            />
          </div>

          <div className="form-group">
            <label htmlFor="start-date">Start Date</label>
            <input
              type="datetime-local"
              id="start-date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="date-input"
            />
          </div>

          <div className="form-group">
            <label htmlFor="due-date">Due Date</label>
            <input
              type="datetime-local"
              id="due-date"
              value={dueDate}
              onChange={(e) => setDueDate(e.target.value)}
              className="date-input"
            />
          </div>
        </div>
        
        <div className="modal-footer">
          <Button onClick={onClose} type="secondary">Cancel</Button>
          <Button onClick={handleSave} disabled={!name}>
            {mode === "create" ? "Create" : "Save"}
          </Button>
        </div>
      </div>
    </div>
  );
}
