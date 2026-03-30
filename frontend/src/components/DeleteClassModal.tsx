import { useEffect, useState } from "react";
import "./DeleteClassModal.css";

interface DeleteClassModalProps {
  isOpen: boolean;
  className: string;
  onClose: () => void;
  onConfirm: () => Promise<void>;
}

export default function DeleteClassModal({
  isOpen,
  className,
  onClose,
  onConfirm,
}: DeleteClassModalProps) {
  const [typedClassName, setTypedClassName] = useState("");
  const [deleteInProgress, setDeleteInProgress] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const isExactClassNameMatch = typedClassName.trim() === className.trim();

  useEffect(() => {
    if (!isOpen) {
      setTypedClassName("");
      setDeleteError(null);
      setDeleteInProgress(false);
    }
  }, [isOpen]);

  const handleClose = () => {
    if (deleteInProgress) {
      return;
    }
    onClose();
  };

  const handleDelete = async () => {
    if (!isExactClassNameMatch || deleteInProgress) {
      return;
    }

    setDeleteInProgress(true);
    setDeleteError(null);
    try {
      await onConfirm();
      onClose();
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to delete class";
      setDeleteError(message);
    } finally {
      setDeleteInProgress(false);
    }
  };

  if (!isOpen) {
    return null;
  }

  return (
    <div className="DeleteClassModalOverlay" onClick={handleClose}>
      <div className="DeleteClassModal" onClick={(event) => event.stopPropagation()}>
        <div className="DeleteClassModalHeader">
          <h2>Are you sure you wish to delete?</h2>
          <button
            className="DeleteClassModalClose"
            onClick={handleClose}
            aria-label="Close delete dialog"
            disabled={deleteInProgress}
          >
            x
          </button>
        </div>

        <p className="DeleteClassModalText">
          This will permanently delete <strong>{className}</strong> and all related data.
        </p>

        <div className="DeleteClassNameConfirm">
          <label htmlFor="delete-class-name-input">
            Type <strong>{className}</strong> to confirm deletion
          </label>
          <input
            id="delete-class-name-input"
            type="text"
            value={typedClassName}
            onChange={(event) => setTypedClassName(event.target.value)}
            placeholder="Enter class name exactly"
            autoComplete="off"
            disabled={deleteInProgress}
          />
        </div>

        {deleteError ? <p className="DeleteClassError">{deleteError}</p> : null}

        <div className="DeleteClassModalActions">
          <button className="DeleteClassCancelButton" onClick={handleClose} disabled={deleteInProgress}>
            Cancel
          </button>
          <button
            className="DeleteClassConfirmButton"
            onClick={handleDelete}
            disabled={!isExactClassNameMatch || deleteInProgress}
          >
            {deleteInProgress ? "Deleting..." : "Delete"}
          </button>
        </div>
      </div>
    </div>
  );
}
