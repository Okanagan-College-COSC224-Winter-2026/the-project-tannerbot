import { useState, useEffect } from "react";
import Button from "./Button";
import "./AssignmentModal.css";

interface AssignmentModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (name: string, description: string, dueDate: string, startDate: string, attachments: File[]) => void;
  assignment?: Assignment;
  mode: "create" | "edit";
}

export default function AssignmentModal({ isOpen, onClose, onSave, assignment, mode }: AssignmentModalProps) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [startDate, setStartDate] = useState("");
  const [validationError, setValidationError] = useState("");

  useEffect(() => {
    if (assignment && mode === "edit") {
      setName(assignment.name || "");
      setDescription(assignment.description || "");
      setDueDate(assignment.due_date ? assignment.due_date.slice(0, 16) : "");
      setStartDate(assignment.start_date ? assignment.start_date.slice(0, 16) : "");
    } else {
      setName("");
      setDescription("");
      setDueDate("");
      setStartDate("");
    }
    setValidationError("");
  }, [assignment, mode, isOpen]);
//checks if the start date is after the due date and shows an error message if it is
  const validateDates = () => {
    setValidationError("");
    
    if (startDate && dueDate && startDate > dueDate) {
      setValidationError("Start date cannot be after the due date");
      return false;
    }
    return true;
  };

  const handleSave = () => {
    if (!validateDates()) {
      return; //returns early if validation fails, preventing the save action from proceeding
    }
    onSave(name, description, dueDate, startDate, attachments); //sends assignment data and optional attachments to be persisted
    onClose(); //closes the window after saving the data to the database
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
            <label htmlFor="assignment-description">Description</label>
            <textarea
              id="assignment-description"
              placeholder="Enter assignment description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="text-input"
              rows={4}
            />
          </div>

          <div className="form-group">
            <label htmlFor="start-date">Start Date</label>
            <input
              type="datetime-local"
              id="start-date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              max={dueDate}
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

          {validationError && (
            <div className="validation-error" style={{ color: "red", marginTop: "10px" }}>
              {validationError}
            </div>
          )}
        </div>
        
        <div className="modal-footer">
          <Button onClick={onClose} type="secondary">Cancel</Button>
          <Button onClick={handleSave} disabled={!name || !!validationError}>
            {mode === "create" ? "Create" : "Save"}
          </Button>
        </div>
      </div>
    </div>
  );
}
