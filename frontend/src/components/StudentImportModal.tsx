import { useMemo, useState } from "react";
import { createPortal } from "react-dom";
import Button from "./Button";
import { StudentEnrollmentPreviewRow } from "../util/api";
import "./StudentImportModal.css";

type FilterMode = "all" | "new" | "existing" | "already-enrolled";

type StudentImportRow = StudentEnrollmentPreviewRow & {
  password: string;
};

interface StudentImportModalProps {
  isOpen: boolean;
  onClose: () => void;
  rows: StudentImportRow[];
  defaultPassword: string;
  onDefaultPasswordChange: (password: string) => void;
  onApplyDefaultPassword: () => void;
  onRowPasswordChange: (email: string, password: string) => void;
  onConfirm: () => void;
  isSubmitting: boolean;
  errorMessage?: string;
}

export default function StudentImportModal({
  isOpen,
  onClose,
  rows,
  defaultPassword,
  onDefaultPasswordChange,
  onApplyDefaultPassword,
  onRowPasswordChange,
  onConfirm,
  isSubmitting,
  errorMessage,
}: StudentImportModalProps) {
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<FilterMode>("all");

  const stats = useMemo(() => {
    const total = rows.length;
    const newAccounts = rows.filter((row) => !row.account_exists).length;
    const existingAccounts = rows.filter((row) => row.account_exists).length;
    const alreadyEnrolled = rows.filter((row) => row.already_enrolled).length;
    return { total, newAccounts, existingAccounts, alreadyEnrolled };
  }, [rows]);

  const filteredRows = useMemo(() => {
    const loweredSearch = search.trim().toLowerCase();
    return rows.filter((row) => {
      const matchesSearch =
        loweredSearch.length === 0 ||
        row.name.toLowerCase().includes(loweredSearch) ||
        row.email.toLowerCase().includes(loweredSearch);

      if (!matchesSearch) {
        return false;
      }

      if (filter === "new") {
        return !row.account_exists;
      }
      if (filter === "existing") {
        return row.account_exists;
      }
      if (filter === "already-enrolled") {
        return row.already_enrolled;
      }
      return true;
    });
  }, [rows, search, filter]);

  if (!isOpen) {
    return null;
  }

  const modalContent = (
    <div className="student-import-overlay" onClick={onClose}>
      <div className="student-import-modal" onClick={(event) => event.stopPropagation()}>
        <div className="student-import-header">
          <div>
            <h2>Review Students Before Adding</h2>
            <p className="student-import-subtitle">
              {stats.total} students found | {stats.newAccounts} new accounts | {stats.existingAccounts} existing accounts
            </p>
          </div>
          <button className="student-import-close" onClick={onClose} aria-label="Close student import modal">
            x
          </button>
        </div>

        <div className="student-import-toolbar">
          <input
            type="text"
            className="student-import-search"
            placeholder="Search by name or email"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />

          <div className="student-import-filters">
            <button
              className={`student-import-filter ${filter === "all" ? "active" : ""}`}
              onClick={() => setFilter("all")}
              type="button"
            >
              All
            </button>
            <button
              className={`student-import-filter ${filter === "new" ? "active" : ""}`}
              onClick={() => setFilter("new")}
              type="button"
            >
              New
            </button>
            <button
              className={`student-import-filter ${filter === "existing" ? "active" : ""}`}
              onClick={() => setFilter("existing")}
              type="button"
            >
              Existing
            </button>
            <button
              className={`student-import-filter ${filter === "already-enrolled" ? "active" : ""}`}
              onClick={() => setFilter("already-enrolled")}
              type="button"
            >
              Already Enrolled
            </button>
          </div>

          <div className="student-import-default-password">
            <label htmlFor="default-import-password">Default password for new accounts</label>
            <div className="student-import-default-password-row">
              <input
                id="default-import-password"
                type="text"
                value={defaultPassword}
                onChange={(event) => onDefaultPasswordChange(event.target.value)}
                placeholder="password123"
              />
              <Button onClick={onApplyDefaultPassword} type="secondary">Apply to all new</Button>
            </div>
          </div>
        </div>

        <div className="student-import-table-wrapper">
          <table className="student-import-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Email</th>
                <th>Account</th>
                <th>Status</th>
                <th>Password</th>
              </tr>
            </thead>
            <tbody>
              {filteredRows.length === 0 ? (
                <tr>
                  <td colSpan={5} className="student-import-empty-row">No students match this filter.</td>
                </tr>
              ) : (
                filteredRows.map((row) => (
                  <tr key={row.email}>
                    <td>{row.name}</td>
                    <td>{row.email}</td>
                    <td>
                      <span className={`student-import-badge ${row.account_exists ? "existing" : "new"}`}>
                        {row.account_exists ? "Existing" : "New"}
                      </span>
                    </td>
                    <td>
                      {row.already_enrolled ? (
                        <span className="student-import-badge enrolled">Already Enrolled</span>
                      ) : (
                        <span className="student-import-badge ready">Ready to Add</span>
                      )}
                    </td>
                    <td>
                      {row.account_exists ? (
                        <span className="student-import-na">N/A</span>
                      ) : (
                        <input
                          type="text"
                          value={row.password}
                          onChange={(event) => onRowPasswordChange(row.email, event.target.value)}
                          className="student-import-row-password"
                        />
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        <div className="student-import-footer">
          <p className="student-import-summary">
            To create: {stats.newAccounts} | Existing: {stats.existingAccounts} | Already enrolled: {stats.alreadyEnrolled}
          </p>
          {errorMessage ? <p className="student-import-error">{errorMessage}</p> : null}
          <div className="student-import-actions">
            <Button onClick={onClose} type="secondary">Cancel</Button>
            <Button onClick={onConfirm} disabled={isSubmitting || rows.length === 0}>
              {isSubmitting ? "Adding..." : "Confirm and Add Students"}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );

  return createPortal(modalContent, document.body);
}
