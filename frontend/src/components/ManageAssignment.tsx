import { ChangeEvent, useRef, useState } from "react";
import {
  addAssignmentAttachments,
  deleteAssignmentAttachment,
  downloadAssignmentAttachment,
  editAssignment,
  listAssignments,
} from "../util/api";
import "./ManageAssignment.css";

interface Props {
  assignmentId?: number;
  classId?: number | string;
}

export default function ManageAssignment({ assignmentId, classId }: Props) {
  const [isOpen, setIsOpen] = useState(false);
  const [attachmentMessage, setAttachmentMessage] = useState("");
  const [attachmentError, setAttachmentError] = useState("");
  const [attachmentsLoading, setAttachmentsLoading] = useState(false);
  const [isSavingAttachments, setIsSavingAttachments] = useState(false);
  const [existingAttachments, setExistingAttachments] = useState<AssignmentAttachment[]>([]);
  const [existingDescription, setExistingDescription] = useState("");
  const [descriptionDraft, setDescriptionDraft] = useState("");
  const [pendingAddedFiles, setPendingAddedFiles] = useState<File[]>([]);
  const [pendingRemovedStoredNames, setPendingRemovedStoredNames] = useState<Set<string>>(new Set());
  const attachmentFileInputRef = useRef<HTMLInputElement | null>(null);

  const loadAttachments = async () => {
    if (!assignmentId) {
      return;
    }

    if (!classId) {
      setExistingAttachments([]);
      setAttachmentError("Unable to load attachments without class context. Return to class and reopen this page.");
      return;
    }

    setAttachmentsLoading(true);
    setAttachmentError("");

    try {
      const assignments = await listAssignments(String(classId));
      const assignment = assignments.find((item: Assignment) => item.id === assignmentId);
      setExistingAttachments(assignment?.attachments || []);
      const assignmentDescription = assignment?.description || "";
      setExistingDescription(assignmentDescription);
      setDescriptionDraft(assignmentDescription);
    } catch (error) {
      console.error("Error loading attachments:", error);
      setAttachmentError("Failed to load attachments.");
      setExistingAttachments([]);
      setExistingDescription("");
      setDescriptionDraft("");
    } finally {
      setAttachmentsLoading(false);
    }
  };

  const openModal = async () => {
    setIsOpen(true);
    setAttachmentMessage("");
    setPendingAddedFiles([]);
    setPendingRemovedStoredNames(new Set());
    await loadAttachments();
  };

  const closeModal = () => {
    setIsOpen(false);
    setAttachmentError("");
    setAttachmentMessage("");
    setPendingAddedFiles([]);
    setPendingRemovedStoredNames(new Set());
    setExistingDescription("");
    setDescriptionDraft("");
  };

  const handleAddFilesClick = () => {
    attachmentFileInputRef.current?.click();
  };

  const handleFilesSelected = (event: ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || []);
    if (files.length === 0) {
      return;
    }

    setPendingAddedFiles((prev) => [...prev, ...files]);
    event.target.value = "";
    setAttachmentMessage("");
  };

  const toggleExistingAttachmentRemoval = (storedName: string) => {
    setPendingRemovedStoredNames((prev) => {
      const next = new Set(prev);
      if (next.has(storedName)) {
        next.delete(storedName);
      } else {
        next.add(storedName);
      }
      return next;
    });
    setAttachmentMessage("");
  };

  const applyAttachmentChanges = async () => {
    if (!assignmentId) {
      return;
    }

    const descriptionChanged = descriptionDraft !== existingDescription;

    if (
      pendingAddedFiles.length === 0
      && pendingRemovedStoredNames.size === 0
      && !descriptionChanged
    ) {
      setAttachmentMessage("No changes to save.");
      return;
    }

    setIsSavingAttachments(true);
    setAttachmentError("");
    setAttachmentMessage("");

    try {
      if (descriptionChanged) {
        await editAssignment(assignmentId, undefined, undefined, undefined, undefined, descriptionDraft);
      }

      if (pendingAddedFiles.length > 0) {
        await addAssignmentAttachments(assignmentId, pendingAddedFiles);
      }

      if (pendingRemovedStoredNames.size > 0) {
        for (const storedName of pendingRemovedStoredNames) {
          await deleteAssignmentAttachment(assignmentId, storedName);
        }
      }

      setPendingAddedFiles([]);
      setPendingRemovedStoredNames(new Set());
      setAttachmentMessage("");
      await loadAttachments();
    } catch (error) {
      console.error("Error updating attachments:", error);
      setAttachmentError("Failed to update assignment details.");
    } finally {
      setIsSavingAttachments(false);
    }
  };

  return (
    <>
      <button
        type="button"
        className="ManageAssignmentButton"
        onClick={openModal}
      >
        Manage
      </button>

      {isOpen && (
        <div className="AttachmentModalOverlay" role="dialog" aria-modal="true" aria-label="Manage assignment">
          <div className="AttachmentModal">
            <div className="AttachmentModalHeader">
              <h3>Manage Assignment</h3>
              <button
                type="button"
                className="AttachmentModalClose"
                onClick={closeModal}
                aria-label="Close manage assignment modal"
              >
                x
              </button>
            </div>

            <div className="AttachmentModalBody">
              {attachmentsLoading ? (
                <p className="AttachmentStatus">Loading attachments...</p>
              ) : (
                <>
                  <div className="AssignmentDescriptionSection">
                    <textarea
                      className="AssignmentDescriptionInput"
                      value={descriptionDraft}
                      onChange={(event) => {
                        setDescriptionDraft(event.target.value);
                        setAttachmentMessage("");
                      }}
                      placeholder="Add assignment description"
                      rows={4}
                    />
                  </div>

                  <div className="AttachmentSectionHeaderRow">
                    <h4>Files To Add</h4>
                    <button
                      type="button"
                      className="AttachmentAddButton"
                      onClick={handleAddFilesClick}
                    >
                      + Add Files
                    </button>
                    <input
                      ref={attachmentFileInputRef}
                      type="file"
                      multiple
                      onChange={handleFilesSelected}
                      className="AttachmentHiddenInput"
                    />
                  </div>

                  {pendingAddedFiles.length === 0 ? (
                    <p className="AttachmentStatus">No new files selected.</p>
                  ) : (
                    <ul className="PendingFileList">
                      {pendingAddedFiles.map((file, index) => (
                        <li key={`${file.name}-${file.size}-${index}`} className="PendingFileListItem">
                          <span>{file.name}</span>
                        </li>
                      ))}
                    </ul>
                  )}

                  <div className="AttachmentPendingSection">
                    {existingAttachments.length === 0 ? null : (
                      <ul className="AttachmentList">
                        {existingAttachments.map((attachment) => {
                          const markedForRemoval = pendingRemovedStoredNames.has(attachment.stored_name);
                          return (
                            <li key={attachment.stored_name} className={`AttachmentListItem ${markedForRemoval ? "marked-for-removal" : ""}`}>
                              <button
                                type="button"
                                className="AttachmentFileName"
                                onClick={() =>
                                  downloadAssignmentAttachment(
                                    attachment.download_url,
                                    attachment.original_name,
                                  )
                                }
                              >
                                {attachment.original_name}
                              </button>
                              <button
                                type="button"
                                className={`AttachmentActionButton ${markedForRemoval ? "undo" : "remove"}`}
                                onClick={() => toggleExistingAttachmentRemoval(attachment.stored_name)}
                              >
                                {markedForRemoval ? "Undo" : "Remove"}
                              </button>
                            </li>
                          );
                        })}
                      </ul>
                    )}
                  </div>

                  {attachmentError && <p className="AttachmentError">{attachmentError}</p>}
                  {attachmentMessage && <p className="AttachmentStatus">{attachmentMessage}</p>}
                </>
              )}
            </div>

            <div className="AttachmentModalFooter">
              <button
                type="button"
                className="AttachmentFooterButton secondary"
                onClick={closeModal}
              >
                Close
              </button>
              <button
                type="button"
                className="AttachmentFooterButton primary"
                onClick={applyAttachmentChanges}
                disabled={isSavingAttachments || attachmentsLoading}
              >
                {isSavingAttachments ? "Saving..." : "Save"}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}