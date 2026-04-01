import { type ChangeEvent, useRef, useState } from "react";
import {
  downloadMyAssignmentSubmission,
  getMyAssignmentSubmission,
  uploadAssignmentSubmission,
} from "../util/api";
import "./ManageAssignment.css";

interface Props {
  assignmentId: number;
}

export default function StudentSubmissionManager({ assignmentId }: Props) {
  const [isOpen, setIsOpen] = useState(false);
  const [submissionMessage, setSubmissionMessage] = useState("");
  const [submissionError, setSubmissionError] = useState("");
  const [submissionLoading, setSubmissionLoading] = useState(false);
  const [submissionSaving, setSubmissionSaving] = useState(false);
  const [submissionStatus, setSubmissionStatus] = useState<AssignmentSubmissionStatus>({
    has_submitted: false,
    submission: null,
  });
  const [pendingSubmissionFile, setPendingSubmissionFile] = useState<File | null>(null);
  const submissionFileInputRef = useRef<HTMLInputElement | null>(null);

  const loadSubmissionStatus = async () => {
    if (!Number.isFinite(assignmentId) || assignmentId <= 0) {
      return;
    }

    setSubmissionLoading(true);
    setSubmissionError("");

    try {
      const payload = (await getMyAssignmentSubmission(assignmentId)) as AssignmentSubmissionStatus;
      setSubmissionStatus(payload);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to load submission status.";
      setSubmissionError(message);
      setSubmissionStatus({ has_submitted: false, submission: null });
    } finally {
      setSubmissionLoading(false);
    }
  };

  const openModal = async () => {
    setIsOpen(true);
    setSubmissionError("");
    setSubmissionMessage("");
    setPendingSubmissionFile(null);
    if (submissionFileInputRef.current) {
      submissionFileInputRef.current.value = "";
    }
    await loadSubmissionStatus();
  };

  const closeModal = () => {
    setIsOpen(false);
    setSubmissionError("");
    setSubmissionMessage("");
    setPendingSubmissionFile(null);
    if (submissionFileInputRef.current) {
      submissionFileInputRef.current.value = "";
    }
  };

  const handleChooseFile = () => {
    submissionFileInputRef.current?.click();
  };

  const handleFileSelected = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0] ?? null;
    setPendingSubmissionFile(file);
    setSubmissionError("");
    setSubmissionMessage("");
  };

  const handleSaveSubmission = async () => {
    if (!pendingSubmissionFile) {
      setSubmissionMessage("No changes to save.");
      return;
    }

    try {
      setSubmissionSaving(true);
      setSubmissionError("");
      setSubmissionMessage("");

      const payload = (await uploadAssignmentSubmission(
        assignmentId,
        pendingSubmissionFile,
      )) as AssignmentSubmissionStatus;

      setSubmissionStatus(payload);
      setPendingSubmissionFile(null);
      if (submissionFileInputRef.current) {
        submissionFileInputRef.current.value = "";
      }
      setSubmissionMessage("Submission uploaded successfully.");
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to upload submission.";
      setSubmissionError(message);
    } finally {
      setSubmissionSaving(false);
    }
  };

  const handleDownloadSubmission = async () => {
    if (!submissionStatus.submission?.original_name) {
      return;
    }

    try {
      setSubmissionError("");
      await downloadMyAssignmentSubmission(assignmentId, submissionStatus.submission.original_name);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to download submission.";
      setSubmissionError(message);
    }
  };

  return (
    <>
      <button type="button" className="ManageAssignmentButton" onClick={openModal}>
        Submit File
      </button>

      {isOpen && (
        <div className="AttachmentModalOverlay" role="dialog" aria-modal="true" aria-label="Submit assignment file">
          <div className="AttachmentModal">
            <div className="AttachmentModalHeader">
              <h3>Assignment Submission</h3>
              <button
                type="button"
                className="AttachmentModalClose"
                onClick={closeModal}
                aria-label="Close assignment submission modal"
              >
                x
              </button>
            </div>

            <div className="AttachmentModalBody">
              {submissionLoading ? (
                <p className="AttachmentStatus">Loading submission status...</p>
              ) : (
                <>
                  <div className="AttachmentSectionHeaderRow">
                    <button type="button" className="AttachmentAddButton" onClick={handleChooseFile}>
                      + Add File
                    </button>
                    <input
                      ref={submissionFileInputRef}
                      type="file"
                      onChange={handleFileSelected}
                      className="AttachmentHiddenInput"
                    />
                  </div>

                  {!pendingSubmissionFile ? (
                    <p className="AttachmentStatus">No file selected.</p>
                  ) : (
                    <ul className="PendingFileList">
                      <li className="PendingFileListItem">
                        <span>{pendingSubmissionFile.name}</span>
                      </li>
                    </ul>
                  )}

                  {submissionStatus.has_submitted && submissionStatus.submission ? (
                    <ul className="AttachmentList">
                      <li className="AttachmentListItem">
                        <button type="button" className="AttachmentFileName" onClick={handleDownloadSubmission}>
                          {submissionStatus.submission.original_name}
                        </button>
                      </li>
                    </ul>
                  ) : null}

                  {submissionError && <p className="AttachmentError">{submissionError}</p>}
                  {submissionMessage && <p className="AttachmentStatus">{submissionMessage}</p>}
                </>
              )}
            </div>

            <div className="AttachmentModalFooter">
              <button type="button" className="AttachmentFooterButton secondary" onClick={closeModal}>
                Close
              </button>
              <button
                type="button"
                className="AttachmentFooterButton primary"
                onClick={handleSaveSubmission}
                disabled={submissionSaving || submissionLoading}
              >
                {submissionSaving ? "Saving..." : "Save"}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
