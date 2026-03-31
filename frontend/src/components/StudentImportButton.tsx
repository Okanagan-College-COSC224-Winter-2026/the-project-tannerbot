import { ChangeEvent, useRef, useState } from "react";
import Button from "./Button";
import StudentImportModal from "./StudentImportModal";
import {
  importStudentsForCourse,
  previewStudentsForCourseImport,
  StudentEnrollmentPreviewRow,
} from "../util/api";

type StudentImportRow = StudentEnrollmentPreviewRow & {
  password: string;
};

interface StudentImportButtonProps {
  classId?: string;
  onImported?: () => void;
}

const DEFAULT_PASSWORD = "password123";

const toCsvCell = (value: string) => {
  const escaped = value.replace(/"/g, '""');
  return `"${escaped}"`;
};

const rowsToCsv = (rows: StudentEnrollmentPreviewRow[]) => {
  const header = "id,name,email";
  const body = rows
    .map((row) => [toCsvCell(row.id), toCsvCell(row.name), toCsvCell(row.email)].join(","))
    .join("\n");
  return `${header}\n${body}`;
};

export default function StudentImportButton({ classId, onImported }: StudentImportButtonProps) {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [csvText, setCsvText] = useState("");
  const [rows, setRows] = useState<StudentImportRow[]>([]);
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);
  const [isLoadingPreview, setIsLoadingPreview] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [defaultPassword, setDefaultPassword] = useState(DEFAULT_PASSWORD);

  const openPicker = () => {
    if (!classId) {
      return;
    }
    setErrorMessage("");
    fileInputRef.current?.click();
  };

  const handleFileChange = async (event: ChangeEvent<HTMLInputElement>) => {
    if (!classId) {
      return;
    }

    const file = event.target.files?.[0];
    if (!file) {
      return;
    }

    try {
      setIsLoadingPreview(true);
      setErrorMessage("");
      const text = await file.text();
      setCsvText(text);

      const preview = await previewStudentsForCourseImport(Number(classId), text);
      const previewRows = preview.students.map((row) => ({
        ...row,
        password: row.account_exists ? "" : DEFAULT_PASSWORD,
      }));

      setRows(previewRows);
      setDefaultPassword(DEFAULT_PASSWORD);
      setIsPreviewOpen(true);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to parse student file";
      setErrorMessage(message);
      alert(`Error: ${message}`);
    } finally {
      setIsLoadingPreview(false);
      event.target.value = "";
    }
  };

  const applyDefaultPassword = () => {
    const fallback = defaultPassword.trim() || DEFAULT_PASSWORD;
    setDefaultPassword(fallback);
    setRows((currentRows) =>
      currentRows.map((row) =>
        row.account_exists ? row : { ...row, password: fallback }
      )
    );
  };

  const updateRowPassword = (email: string, password: string) => {
    setRows((currentRows) =>
      currentRows.map((row) => (row.email === email ? { ...row, password } : row))
    );
  };

  const confirmImport = async () => {
    if (!classId) {
      return;
    }

    try {
      setIsSubmitting(true);
      setErrorMessage("");

      const fallbackPassword = defaultPassword.trim() || DEFAULT_PASSWORD;
      const studentPasswords = rows.reduce<Record<string, string>>((acc, row) => {
        if (row.account_exists) {
          return acc;
        }
        acc[row.email] = row.password.trim() || fallbackPassword;
        return acc;
      }, {});

      const csvPayload = csvText.trim().length > 0 ? csvText : rowsToCsv(rows);
      const result = await importStudentsForCourse(Number(classId), csvPayload, {
        defaultPassword: fallbackPassword,
        studentPasswords,
      });

      const details: string[] = [];
      if (typeof result?.added_count === "number") {
        details.push(`Added: ${result.added_count}`);
      }
      if (typeof result?.already_enrolled_count === "number") {
        details.push(`Already enrolled: ${result.already_enrolled_count}`);
      }
      if (typeof result?.created_accounts_count === "number") {
        details.push(`New accounts created: ${result.created_accounts_count}`);
      }

      const detailText = details.length > 0 ? `\n${details.join(" | ")}` : "";
      alert((result?.msg || "Students imported successfully") + detailText);

      setIsPreviewOpen(false);
      onImported?.();
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to import students";
      setErrorMessage(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <>
      <input
        ref={fileInputRef}
        type="file"
        accept=".csv,text/csv"
        onChange={handleFileChange}
        style={{ display: "none" }}
      />

      <Button onClick={openPicker} disabled={!classId || isLoadingPreview}>
        {isLoadingPreview ? "Preparing Student List..." : "Add Students via CSV"}
      </Button>

      <StudentImportModal
        isOpen={isPreviewOpen}
        onClose={() => setIsPreviewOpen(false)}
        rows={rows}
        defaultPassword={defaultPassword}
        onDefaultPasswordChange={setDefaultPassword}
        onApplyDefaultPassword={applyDefaultPassword}
        onRowPasswordChange={updateRowPassword}
        onConfirm={confirmImport}
        isSubmitting={isSubmitting}
        errorMessage={errorMessage}
      />
    </>
  );
}
