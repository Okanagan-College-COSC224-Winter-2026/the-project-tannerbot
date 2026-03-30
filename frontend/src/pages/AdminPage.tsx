import { useEffect, useState } from "react";
import { listUsers, deleteUser } from "../util/api";
import "./AdminPage.css";
export default function AdminPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [statusMessage, setStatusMessage] = useState<string>("");
  const [statusType, setStatusType] = useState<"error" | "success">("error");
  const currentUser = JSON.parse(localStorage.getItem("user") || "null");

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
    <h1>Admin Panel</h1>

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
              <td>{u.role}</td>
              <td>
                <button
                  className="AdminDeleteBtn"
                  disabled={currentUser?.id === u.id}
                  onClick={() => handleDelete(u.id)}
                >
                  Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  </div>
)
}