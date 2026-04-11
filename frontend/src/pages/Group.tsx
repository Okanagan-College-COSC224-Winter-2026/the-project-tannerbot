import { useEffect, useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";

import Button from "../components/Button";
import TabNavigation from "../components/TabNavigation";
import {
  autoAssignAssignmentGroups,
  createAssignmentGroup,
  deleteAssignmentGroup,
  getAssignmentGrouping,
  setAssignmentGroupMembers,
  updateAssignmentMode,
} from "../util/api";
import { isAdmin, isTeacher } from "../util/login";

import "./Group.css";

export default function Group() {
  const { id } = useParams();
  const location = useLocation();
  const navigate = useNavigate();

  const canManageAssignment = isTeacher() || isAdmin();
  const stateClassId = (location.state as { classId?: string | number } | null)?.classId;
  const searchClassId = new URLSearchParams(location.search).get("classId");
  const classId = stateClassId ?? searchClassId;
  const classQuery = classId ? `?classId=${classId}` : "";
  const assignmentId = Number(id);

  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [assignmentMode, setAssignmentMode] = useState<"solo" | "group">("solo");
  const [groups, setGroups] = useState<AssignmentGroupingGroup[]>([]);
  const [students, setStudents] = useState<AssignmentGroupingStudent[]>([]);
  const [newGroupName, setNewGroupName] = useState("");
  const [selectedGroupId, setSelectedGroupId] = useState<number | null>(null);
  const [studentAssignments, setStudentAssignments] = useState<Record<number, number | null>>({});

  const loadGrouping = async () => {
    if (!Number.isFinite(assignmentId)) {
      setError("Invalid assignment id.");
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setError("");
    try {
      const payload: AssignmentGroupingResponse = await getAssignmentGrouping(assignmentId);
      const mode = payload.assignment.assignment_mode === "group" ? "group" : "solo";
      setAssignmentMode(mode);
      setGroups(payload.groups);
      setStudents(payload.students);

      setSelectedGroupId((current) => {
        if (payload.groups.length === 0) {
          return null;
        }

        if (current && payload.groups.some((group) => group.id === current)) {
          return current;
        }

        return payload.groups[0].id;
      });

      const membershipMap: Record<number, number | null> = {};
      payload.students.forEach((student) => {
        membershipMap[student.id] = student.groupID ?? null;
      });
      setStudentAssignments(membershipMap);
    } catch (loadError: unknown) {
      console.error("Failed to load grouping data", loadError);
      setError(loadError instanceof Error ? loadError.message : "Failed to load group management data.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (!canManageAssignment) {
      setIsLoading(false);
      return;
    }
    loadGrouping();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [assignmentId, canManageAssignment]);

  const saveAssignmentMode = async () => {
    setIsSaving(true);
    setError("");
    setSuccess("");
    try {
      await updateAssignmentMode(assignmentId, assignmentMode);
      await loadGrouping();
      setSuccess("Assignment mode updated.");
    } catch (saveError: unknown) {
      console.error("Failed to save assignment mode", saveError);
      setError(saveError instanceof Error ? saveError.message : "Failed to save assignment mode.");
    } finally {
      setIsSaving(false);
    }
  };

  const handleCreateGroup = async () => {
    if (!newGroupName.trim()) {
      setError("Enter a group name before creating.");
      return;
    }

    setIsSaving(true);
    setError("");
    setSuccess("");
    try {
      await createAssignmentGroup(assignmentId, newGroupName.trim());
      setNewGroupName("");
      await loadGrouping();
      setSuccess("Group created.");
    } catch (createError: unknown) {
      console.error("Failed to create group", createError);
      setError(createError instanceof Error ? createError.message : "Failed to create group.");
    } finally {
      setIsSaving(false);
    }
  };

  const handleDeleteGroup = async (groupId: number) => {
    setIsSaving(true);
    setError("");
    setSuccess("");
    try {
      await deleteAssignmentGroup(assignmentId, groupId);
      await loadGrouping();
      setSuccess("Group deleted.");
    } catch (deleteError: unknown) {
      console.error("Failed to delete group", deleteError);
      setError(deleteError instanceof Error ? deleteError.message : "Failed to delete group.");
    } finally {
      setIsSaving(false);
    }
  };

  const handleSavePlacements = async () => {
    setIsSaving(true);
    setError("");
    setSuccess("");

    try {
      const membersByGroupId: Record<number, number[]> = {};
      groups.forEach((group) => {
        membersByGroupId[group.id] = [];
      });

      students.forEach((student) => {
        const groupId = studentAssignments[student.id];
        if (groupId && membersByGroupId[groupId]) {
          membersByGroupId[groupId].push(student.id);
        }
      });

      for (const group of groups) {
        await setAssignmentGroupMembers(assignmentId, group.id, membersByGroupId[group.id] || []);
      }

      await loadGrouping();
      setSuccess("Student group assignments saved.");
    } catch (placementError: unknown) {
      console.error("Failed to save group placements", placementError);
      setError(
        placementError instanceof Error
          ? placementError.message
          : "Failed to save student group assignments.",
      );
    } finally {
      setIsSaving(false);
    }
  };

  const handleAutoAssignPlacements = async () => {
    setIsSaving(true);
    setError("");
    setSuccess("");

    try {
      await autoAssignAssignmentGroups(assignmentId);
      await loadGrouping();
      setSuccess("Students were auto-assigned to groups.");
    } catch (autoAssignError: unknown) {
      console.error("Failed to auto-assign group placements", autoAssignError);
      setError(
        autoAssignError instanceof Error
          ? autoAssignError.message
          : "Failed to auto-assign student group assignments.",
      );
    } finally {
      setIsSaving(false);
    }
  };

  const assignmentTypeSection = (
    <div className="GroupSection">
      <label htmlFor="assignment-mode" className="GroupSectionLabel">
        Assignment Type
      </label>
      <div className="GroupRow">
        <select
          id="assignment-mode"
          value={assignmentMode}
          onChange={(event) => setAssignmentMode(event.target.value as "solo" | "group")}
          disabled={isSaving}
        >
          <option value="solo">Solo</option>
          <option value="group">Group</option>
        </select>
        <Button onClick={saveAssignmentMode} disabled={isSaving}>
          Save Type
        </Button>
      </div>
    </div>
  );

  return (
    <div className="AssignmentPage container-fluid py-4 px-3 px-md-4">
      <div className="AssignmentHeader card border-0 shadow-sm mb-3 p-3 p-md-4">
        <h2 className="h3 fw-bold text-primary mb-0">Assignment {id}</h2>
        {canManageAssignment ? (
          <Button
            type="secondary"
            onClick={() => navigate(classId ? `/classes/${classId}/home` : "/home")}
          >
            Return to Class
          </Button>
        ) : null}
      </div>

      <TabNavigation
        tabs={[
          {
            label: "Group",
            path: `/assignments/${id}/group${classQuery}`,
          },
          ...(canManageAssignment
            ? [
                {
                  label: "Criteria",
                  path: `/assignment/${id}/criteria${classQuery}`,
                },
                {
                  label: "Reviews",
                  path: `/assignments/${id}/reviews${classQuery}`,
                },
                {
                  label: "Progress",
                  path: `/assignments/${id}/progress${classQuery}`,
                },
              ]
            : []),
        ]}
      />

      <div className="card border-0 shadow-sm p-3 p-md-4 mt-3 GroupPageCard">
        {!canManageAssignment ? (
          <p className="mb-0 text-muted">Only teachers can manage assignment grouping.</p>
        ) : isLoading ? (
          <p className="mb-0 text-muted">Loading group settings...</p>
        ) : (
          <div className="GroupManagementPanel">
            {error ? <p className="GroupError">{error}</p> : null}
            {success ? <p className="GroupSuccess">{success}</p> : null}

            {assignmentMode === "group" ? (
              <div className="GroupModeLayout">
                <div className="GroupModeTopRow">
                  {assignmentTypeSection}
                  <div className="GroupSection">
                    <label htmlFor="new-group-name" className="GroupSectionLabel">
                      Create Group
                    </label>
                    <div className="GroupRow">
                      <input
                        id="new-group-name"
                        type="text"
                        value={newGroupName}
                        onChange={(event) => setNewGroupName(event.target.value)}
                        placeholder="Enter group name"
                        disabled={isSaving}
                      />
                      <Button onClick={handleCreateGroup} disabled={isSaving || !newGroupName.trim()}>
                        Add Group
                      </Button>
                    </div>
                  </div>

                  <div className="GroupSection">
                    <h4 className="GroupSectionLabel">Existing Groups</h4>
                    {groups.length === 0 ? (
                      <p className="text-muted mb-0">No groups created yet.</p>
                    ) : (
                      <div className="GroupList">
                        <div className="GroupCard">
                          <div className="GroupRow">
                            <select
                              id="existing-group-select"
                              value={selectedGroupId ?? ""}
                              onChange={(event) =>
                                setSelectedGroupId(event.target.value ? Number(event.target.value) : null)
                              }
                              disabled={isSaving}
                            >
                              {groups.map((group) => (
                                <option key={group.id} value={group.id}>
                                  {group.name}
                                </option>
                              ))}
                            </select>
                            <Button
                              type="secondary"
                              onClick={() => selectedGroupId && handleDeleteGroup(selectedGroupId)}
                              disabled={isSaving || !selectedGroupId}
                            >
                              Delete
                            </Button>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                <div className="GroupModeBottom">
                  <div className="GroupSection">
                    <h4 className="GroupSectionLabel">Assign Students To Groups</h4>
                    {students.length === 0 ? (
                      <p className="text-muted mb-0">No enrolled students found in this class.</p>
                    ) : (
                      <div className="GroupStudentsTable">
                        <div className="GroupStudentsHeader">
                          <span>Student</span>
                          <span>Group</span>
                        </div>
                        {students.map((student) => (
                          <div key={student.id} className="GroupStudentsRow">
                            <span>{student.name}</span>
                            <select
                              value={studentAssignments[student.id] ?? ""}
                              onChange={(event) => {
                                const value = event.target.value;
                                setStudentAssignments((prev) => ({
                                  ...prev,
                                  [student.id]: value ? Number(value) : null,
                                }));
                              }}
                              disabled={isSaving}
                            >
                              <option value="">Unassigned</option>
                              {groups.map((group) => (
                                <option key={group.id} value={group.id}>
                                  {group.name}
                                </option>
                              ))}
                            </select>
                          </div>
                        ))}
                      </div>
                    )}
                    <div className="GroupActionsRow">
                      <Button
                        type="secondary"
                        onClick={handleAutoAssignPlacements}
                        disabled={isSaving || groups.length === 0 || students.length === 0}
                      >
                        Auto-Assign
                      </Button>
                      <Button onClick={handleSavePlacements} disabled={isSaving || groups.length === 0}>
                        Save Student Placements
                      </Button>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <>
                {assignmentTypeSection}
                <p className="mb-0 text-muted">
                  Assignment is set to solo mode. Switch to group mode to create groups and assign students.
                </p>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
