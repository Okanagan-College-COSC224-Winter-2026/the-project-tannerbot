import AssignmentCard from "../components/AssignmentCard";
import Button from "../components/Button";
import AssignmentModal from "../components/AssignmentModal";
import "./ClassHome.css";
import { useNavigate, useParams } from "react-router-dom";
import { useState, useEffect } from "react";
import {
  listAssignments,
  listClasses,
  createAssignment,
  editAssignment,
  deleteAssignment,
} from "../util/api";
import TabNavigation from "../components/TabNavigation";
import StatusMessage from "../components/StatusMessage";
import { isAdmin, isTeacher } from "../util/login";
import StudentImportButton from "../components/StudentImportButton";

export default function ClassHome() {
  const { id } = useParams();
  const navigate = useNavigate();
  const idNew = Number(id)
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [className, setClassName] = useState<string | null>(null);
  const [classNotFound, setClassNotFound] = useState(false);
  const [loadingClass, setLoadingClass] = useState(true);
  const [statusMessage, setStatusMessage] = useState('');
  const [statusType, setStatusType] = useState<'error' | 'success'>('error');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingAssignment, setEditingAssignment] = useState<Assignment | undefined>(undefined);
  const [modalMode, setModalMode] = useState<"create" | "edit">("create");

  useEffect(() => {
    if (!id) {
      setLoadingClass(false);
      return;
    }

    (async () => {
      setLoadingClass(true);
      try {
        const classes = await listClasses();
        const currentClass = classes.find((c: { id: number }) => c.id === Number(id));

        if (!currentClass) {
          setClassNotFound(true);
          setClassName(null);
          setAssignments([]);
          return;
        }

        const resp = await listAssignments(String(id));
        setClassNotFound(false);
        setAssignments(resp);
        setClassName(currentClass.name || null);
      } catch (error) {
        console.error('Error loading class:', error);
        setStatusType('error');
        setStatusMessage('Unable to load class details.');
      } finally {
        setLoadingClass(false);
      }
    })();
  }, [id]);
    
  const handleCreateAssignment = async (name: string, dueDate: string, startDate: string) => {
    try {
      setStatusMessage('');
      const response = await createAssignment(
        idNew,
        name,
        dueDate || undefined,
        startDate || undefined
      );
      const createdAssignment = response?.assignment
        ? {
            ...response.assignment,
            attachments: response.attachments || response.assignment.attachments || [],
          }
        : null;

      if (!createdAssignment?.id) {
        throw new Error('Failed to create assignment');
      }

      setAssignments((prev) => [...prev, createdAssignment]);
      setStatusType('success');
      setStatusMessage('Assignment created successfully!');
    } catch (error: unknown) {
      console.error('Error creating assignment:', error);
      setStatusType('error');
      const errorMsg = error instanceof Error ? error.message : 'Error creating assignment.';
      setStatusMessage(errorMsg);
    }
  };

  const handleEditAssignment = async (name: string, dueDate: string, startDate: string) => {
    if (!editingAssignment) return;
    
    try {
      setStatusMessage('');
      const response = await editAssignment(
        editingAssignment.id, 
        name, 
        dueDate || undefined, 
        startDate || undefined
      );
      const updatedAssignment = response?.assignment;

      if (!updatedAssignment?.id) {
        throw new Error('Failed to update assignment');
      }

      setAssignments((prev) => 
        prev.map(a => a.id === updatedAssignment.id ? updatedAssignment : a)
      );
      setStatusType('success');
      setStatusMessage('Assignment updated successfully!');
      setEditingAssignment(undefined);
    } catch (error: unknown) {
      console.error('Error updating assignment:', error);
      setStatusType('error');
      // Show the error message from backend, or a default message
      const errorMsg = error instanceof Error ? error.message : 'Error updating assignment.';
      setStatusMessage(errorMsg);
    }
  };

  const handleDeleteAssignment = async (assignmentId: number) => {
    try {
      setStatusMessage('');
      await deleteAssignment(assignmentId);
      setAssignments((prev) => prev.filter(a => a.id !== assignmentId));
      setStatusType('success');
      setStatusMessage('Assignment deleted successfully!');
    } catch (error: unknown) {
      console.error('Error deleting assignment:', error);
      setStatusType('error');
      setStatusMessage(error instanceof Error ? error.message : 'Error deleting assignment.');
    }
  };

  const openCreateModal = () => {
    setModalMode("create");
    setEditingAssignment(undefined);
    setIsModalOpen(true);
  };

  const openEditModal = (assignment: Assignment) => {
    setModalMode("edit");
    setEditingAssignment(assignment);
    setIsModalOpen(true);
  };

  const handleModalSave = (name: string, dueDate: string, startDate: string) => {
    if (modalMode === "create") {
      handleCreateAssignment(name, dueDate, startDate);
    } else {
      handleEditAssignment(name, dueDate, startDate);
    }
  };
    
  if (classNotFound) {
    return (
      <div className="ClassHomePage container-fluid py-4 px-3 px-md-4">
        <div className="Class card border-0 shadow-sm p-3 p-md-4">
          <h2 className="h4 fw-bold mb-2">Class not found</h2>
          <p className="mb-3">This class does not exist or you do not have access to it.</p>
          <div>
            <Button onClick={() => navigate('/home')}>Back to Home</Button>
          </div>
        </div>
      </div>
    );
  }

    return (
      <div className="ClassHomePage container-fluid py-4 px-3 px-md-4">
        <div className="ClassHeader card border-0 shadow-sm mb-3 p-3 p-md-4">
          <div className="ClassHeaderLeft">
            <h2 className="h3 fw-bold mb-0 text-primary">{className || "Class"}</h2>
          </div>

          <div className="ClassHeaderRight">
            {isTeacher() ? (
              <StudentImportButton classId={id} />
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
            ...(isTeacher() || isAdmin()
              ? [
                  {
                    label: "Reviews",
                    path: `/classes/${id}/reviews`,
                  },
                ]
              : []),
          ]}
        />

        <div className="mb-3 mt-3">
          <StatusMessage message={statusMessage} type={statusType} />
        </div>

        <div className="Class card border-0 shadow-sm p-3 p-md-4">
          <div className="Assignments">
            {loadingClass ? (
              <div className="EmptyAssignmentsState" role="status">
                <p className="mb-0">Loading class...</p>
              </div>
            ) : assignments.length === 0 ? (
              <div className="EmptyAssignmentsState" role="status">
                <p className="mb-0">No assignments yet.</p>
              </div>
            ) : (
              <ul className="Assignment row g-3">
                {assignments.map((assignment) => (
                  <li key={assignment.id} className="col-12">
                    <AssignmentCard
                      id={assignment.id}
                      assignment={assignment}
                      classId={id}
                      onEdit={isTeacher() ? () => openEditModal(assignment) : undefined}
                      onDelete={isTeacher() ? () => handleDeleteAssignment(assignment.id) : undefined}
                    >
                      {assignment.name}
                    </AssignmentCard>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {isTeacher() ? (
            <div className="AssInputChunk mt-3">
              <Button onClick={openCreateModal}>
                Create New Assignment
              </Button>
            </div>
          ) : null}
        </div>

        <AssignmentModal
          isOpen={isModalOpen}
          onClose={() => setIsModalOpen(false)}
          onSave={handleModalSave}
          assignment={editingAssignment}
          mode={modalMode}
        />
      </div>
    );
}
