import { useEffect, useState } from "react";
import { listUsers, deleteUser, deleteUserCascade, DeleteUserConflictError } from "../util/api";
import DeleteUserModal from "../components/DeleteUserModal";
import "./AdminPage.css";
export default function AdminPage() {
  type UserAssociations = Record<string, { count: number; items: Array<Record<string, unknown>> }>;

  const [users, setUsers] = useState<User[]>([]);
  const [statusMessage, setStatusMessage] = useState<string>("");
  const [statusType, setStatusType] = useState<"error" | "success">("error");
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleteModalUser, setDeleteModalUser] = useState<User | null>(null);
  const [deleteModalAssociations, setDeleteModalAssociations] = useState<UserAssociations>({});
  const currentUser = JSON.parse(localStorage.getItem("user") || "null");

  const getRoleBadgeClass = (role: string) => {
    const normalizedRole = role.toLowerCase();
    if (normalizedRole === "admin") {
      return "text-bg-success";
    }
    if (normalizedRole === "teacher") {
      return "text-bg-primary";
    }
    return "text-bg-secondary";
  };

  async function handleDelete(userId: number) {
    setStatusMessage("");

    if (currentUser?.id === userId) {
      setStatusType("error");
      setStatusMessage("You cannot delete your own account.");
      return;
    }

    try {
      await deleteUser(userId);

      setUsers((prev) => prev.filter((u) => u.id !== userId));
      setStatusType("success");
      setStatusMessage("User deleted successfully.");
    } catch (err) {
      if (err instanceof DeleteUserConflictError) {
        // Show the modal with associations
        const userToDelete = users.find((u) => u.id === userId);
        if (userToDelete) {
          setDeleteModalUser(userToDelete);
          setDeleteModalAssociations(err.associations);
          setShowDeleteModal(true);
        }
      } else {
        const message = err instanceof Error ? err.message : "Failed to delete user.";
        setStatusType("error");
        setStatusMessage(message);
        console.error("Failed to delete user:", err);
      }
    }
  }

  async function handleConfirmDelete() {
    if (!deleteModalUser) return;

    try {
      await deleteUserCascade(deleteModalUser.id);
      setUsers((prev) => prev.filter((u) => u.id !== deleteModalUser.id));
      setShowDeleteModal(false);
      setDeleteModalUser(null);
      setStatusType("success");
      setStatusMessage(`User ${deleteModalUser.name} has been deleted successfully.`);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to delete user.";
      setStatusType("error");
      setStatusMessage(message);
      console.error("Failed to delete user:", err);
    }
  }

  // load users
  useEffect(() => {
    async function fetchUsers() {
      try {
        const data = await listUsers();
        setUsers(data);
      } catch (err) {
        console.error("Failed to load users:", err);
      }
    }

    fetchUsers();
  }, []);
  return (
  <div className="AdminPage">
    <h1 className="text-primary">Admin Panel</h1>

    {statusMessage ? (
      <div className={`AdminStatusMessage ${statusType === "error" ? "Error" : "Success"}`} role="alert">
        {statusMessage}
      </div>
    ) : null}

    <div className="AdminTableWrapper">
      <table className="AdminTable">
        <thead>
          <tr>
            <th>ID</th>
            <th>Name</th>
            <th>Email</th>
            <th>Role</th>
            <th>Actions</th>
          </tr>
        </thead>

        <tbody>
          {users.map((u) => (
            <tr key={u.id}>
              <td>{u.id}</td>
              <td>{u.name}</td>
              <td>{u.email}</td>
              <td>
                <span className={`badge text-uppercase ${getRoleBadgeClass(u.role)}`}>
                  {u.role}
                </span>
              </td>
              <td>
                <button
                  className="btn btn-primary rounded-circle AdminDeleteCircleButton"
                  disabled={currentUser?.id === u.id}
                  onClick={() => handleDelete(u.id)}
                  aria-label={`Delete user ${u.name}`}
                  title={currentUser?.id === u.id ? "You cannot delete your own account" : "Delete user"}
                >
                  <i className="bi bi-x-lg" aria-hidden="true" />
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>

    <DeleteUserModal
      isOpen={showDeleteModal}
      userName={deleteModalUser?.name || ""}
      associations={deleteModalAssociations}
      onClose={() => {
        setShowDeleteModal(false);
        setDeleteModalUser(null);
      }}
      onConfirm={handleConfirmDelete}
    />
  </div>
)
}