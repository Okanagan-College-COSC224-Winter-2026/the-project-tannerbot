import AssignmentCard from "../components/AssignmentCard";
import Button from "../components/Button";
import AssignmentModal from "../components/AssignmentModal";
import "./ClassHome.css";
import { useParams } from "react-router-dom";
import { useState, useEffect } from "react";
import { listAssignments, listClasses, createAssignment, editAssignment, deleteAssignment } from "../util/api";
import TabNavigation from "../components/TabNavigation";
import { importCSV } from "../util/csv";
import StatusMessage from "../components/StatusMessage";
import { isTeacher } from "../util/login";

export default function ClassHome() {
  const { id } = useParams();
  const idNew = Number(id)
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [className, setClassName] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState('');
  const [statusType, setStatusType] = useState<'error' | 'success'>('error');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingAssignment, setEditingAssignment] = useState<Assignment | undefined>(undefined);
  const [modalMode, setModalMode] = useState<"create" | "edit">("create");

  useEffect(() => { 
    if (!id) return;

    (async () => {
      const resp = await listAssignments(String(id));
      const classes = await listClasses();
      const currentClass = classes.find((c: { id: number }) => c.id === Number(id));
      setAssignments(resp);
      setClassName(currentClass?.name || null);
    })();
  }, [id]);
    
  const handleCreateAssignment = async (name: string, description: string, dueDate: string, startDate: string, attachments: File[]) => {
    try {
      setStatusMessage('');
      const response = await createAssignment(
        idNew,
        name,
        description || undefined,
        dueDate || undefined,
        startDate || undefined,
        attachments
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
    } catch (error: any) {
      console.error('Error creating assignment:', error);
      setStatusType('error');
      const errorMsg = error?.message || 'Error creating assignment.';
      setStatusMessage(errorMsg);
    }
  };

  const handleEditAssignment = async (name: string, description: string, dueDate: string, startDate: string) => {
    if (!editingAssignment) return;
    
    try {
      setStatusMessage('');
      const response = await editAssignment(
        editingAssignment.id, 
        name, 
        description || undefined,
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
    } catch (error: any) {
      console.error('Error updating assignment:', error);
      setStatusType('error');
      // Show the error message from backend, or a default message
      const errorMsg = error.message || 'Error updating assignment.';
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
    } catch (error: any) {
      console.error('Error deleting assignment:', error);
      setStatusType('error');
      setStatusMessage(error.message || 'Error deleting assignment.');
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

  const handleModalSave = (name: string, description: string, dueDate: string, startDate: string, attachments: File[]) => {
    if (modalMode === "create") {
      handleCreateAssignment(name, description, dueDate, startDate, attachments);
    } else {
      handleEditAssignment(name, description, dueDate, startDate);
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
          {assignments.length === 0 ? (
            <p>No assignments yet.</p>
          ) : (
            <ul className="Assignment">
              {assignments.map((assignment) => (
                <li key={assignment.id}>
                  <AssignmentCard 
                    id={assignment.id}
                    assignment={assignment}
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
          <div className="AssInputChunk">
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
    </>
  );
}
