import { useState } from "react";
import "./DeleteUserModal.css";

interface Association {
  count: number;
  items: Array<Record<string, unknown>>;
}

interface DeleteUserModalProps {
  isOpen: boolean;
  userName: string;
  associations: Record<string, Association>;
  onClose: () => void;
  onConfirm: () => Promise<void>;
}

export default function DeleteUserModal({
  isOpen,
  userName,
  associations,
  onClose,
  onConfirm,
}: DeleteUserModalProps) {
  const [deleteInProgress, setDeleteInProgress] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [confirmed, setConfirmed] = useState(false);

  const handleClose = () => {
    if (deleteInProgress) {
      return;
    }
    setConfirmed(false);
    setDeleteError(null);
    onClose();
  };

  const handleDelete = async () => {
    setDeleteInProgress(true);
    setDeleteError(null);
    try {
      await onConfirm();
      handleClose();
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to delete user";
      setDeleteError(message);
    } finally {
      setDeleteInProgress(false);
    }
  };

  if (!isOpen) {
    return null;
  }

  const totalAssociations = Object.values(associations).reduce((sum, assoc) => sum + assoc.count, 0);
  const associationLabel = totalAssociations === 1 ? "item" : "items";

  return (
    <div className="DeleteUserModalOverlay" onClick={handleClose}>
      <div className="DeleteUserModal" onClick={(event) => event.stopPropagation()}>
        <div className="DeleteUserModalHeader">
          <h2>Delete User?</h2>
          <button
            className="DeleteUserModalClose"
            onClick={handleClose}
            aria-label="Close delete dialog"
            disabled={deleteInProgress}
          >
            ×
          </button>
        </div>

        <div className="DeleteUserModalContent">
          <p className="DeleteUserModalText">
            This will permanently delete <strong>{userName}</strong> and all associated records ({totalAssociations} {associationLabel}):
          </p>

          <div className="DeleteUserAssociationsList">
            {Object.entries(associations).map(([key, assoc]) => (
              <div key={key} className="AssociationCategory">
                <h3 className="AssociationTitle">
                  {formatAssociationKey(key)} ({assoc.count})
                </h3>
                <ul className="AssociationItems">
                  {assoc.items.slice(0, 5).map((item, idx) => (
                    <li key={idx}>{formatAssociationItem(item)}</li>
                  ))}
                  {assoc.items.length > 5 && (
                    <li className="MoreItems">... and {assoc.items.length - 5} more</li>
                  )}
                </ul>
              </div>
            ))}
          </div>

          {deleteError ? <p className="DeleteUserError">{deleteError}</p> : null}

          <div className="DeleteUserWarningBox">
            <label className="DeleteUserCheckbox">
              <input
                type="checkbox"
                checked={confirmed}
                onChange={(event) => setConfirmed(event.target.checked)}
                disabled={deleteInProgress}
              />
              <span>I understand this action cannot be undone</span>
            </label>
          </div>
        </div>

        <div className="DeleteUserModalActions">
          <button
            className="DeleteUserCancelButton"
            onClick={handleClose}
            disabled={deleteInProgress}
          >
            Cancel
          </button>
          <button
            className="DeleteUserConfirmButton"
            onClick={handleDelete}
            disabled={deleteInProgress || !confirmed}
          >
            Delete User and All Records
          </button>
        </div>
      </div>
    </div>
  );
}

function formatAssociationKey(key: string): string {
  return key
    .replace(/_/g, " ")
    .split(" ")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

function formatAssociationItem(item: Record<string, unknown>): string {
  if (item.name) return `${item.name}`;
  if (item.course_name) return `Course: ${item.course_name}`;
  if (item.assignment_name) return `Assignment: ${item.assignment_name}`;
  if (item.reviewee_name) return `Review of: ${item.reviewee_name}`;
  if (item.reviewer_name) return `Review from: ${item.reviewer_name}`;
  if (item.group_name) return `Group: ${item.group_name}`;
  return JSON.stringify(item);
}
