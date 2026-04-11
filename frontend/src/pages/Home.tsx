import { useEffect, useState } from "react";
import ClassCard from "../components/ClassCard";
import DeleteClassModal from "../components/DeleteClassModal";

import './Home.css'
import { deleteClass, listClasses, listAssignments } from "../util/api";
import { getCurrentUserId, hasRole, isTeacher, isStudent } from "../util/login";

export default function Home() {
  const [courses, setCourses] = useState<CourseWithAssignments[]>([]);
  const [loading, setLoading] = useState(true);
  const [classToDelete, setClassToDelete] = useState<CourseWithAssignments | null>(null);
  const [successToast, setSuccessToast] = useState<string | null>(null);
  const studentView = isStudent();
  const currentUserId = getCurrentUserId();
  const isAdminUser = hasRole("admin");

  useEffect(() => {
    ;(async () => {
      try {
        const coursesResp = await listClasses();
        
        // Fetch assignments for each course
        const coursesWithAssignments = await Promise.all(
          coursesResp.map(async (course: Course) => {
            try {
              const assignments = await listAssignments(String(course.id));
              return {
                ...course,
                assignments: assignments || [],
                assignmentCount: assignments?.length || 0
              };
            } catch (error) {
              console.error(`Error fetching assignments for course ${course.id}:`, error);
              return {
                ...course,
                assignments: [],
                assignmentCount: 0
              };
            }
          })
        );
        
        setCourses(coursesWithAssignments);
      } catch (error) {
        console.error("Error fetching courses:", error);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  useEffect(() => {
    if (!successToast) {
      return;
    }

    const timeoutId = window.setTimeout(() => {
      setSuccessToast(null);
    }, 3000);

    return () => {
      window.clearTimeout(timeoutId);
    };
  }, [successToast]);

  const totalAssignments = courses.reduce( 
    (sum, course) => sum + (course.assignmentCount || 0), 
    0
  );

  const openDeleteModal = (course: CourseWithAssignments) => {
    setClassToDelete(course);
  };

  const closeDeleteModal = () => {
    setClassToDelete(null);
  };

  const handleDeleteClass = async () => {
    if (!classToDelete) {
      return;
    }

    const deletedClassName = classToDelete.name;
    await deleteClass(classToDelete.id);
    setCourses((prev) => prev.filter((course) => course.id !== classToDelete.id));
    setSuccessToast(`Deleted class "${deletedClassName}"`);
  };

  if (loading) {
    return (
      <div className="Home">
        <h1 className="text-primary">{isTeacher() ? "Teacher Dashboard" : "Peer Review Dashboard"}</h1>
        <p>Loading courses...</p>
      </div>
    );
  }

  return (
    <>
    <div className="Home">
      {successToast ? <div className="HomeSuccessToast">{successToast}</div> : null}
      <h1 className="text-primary">{isTeacher() ? "Teacher Dashboard" : "Peer Review Dashboard"}</h1>

        {isTeacher() && (
          <div className="DashboardSummary">
            <div className="DashboardWidget">
              <h3>My Classes</h3>
              <p>{courses.length}</p>
            </div>
            <div className="DashboardWidget">
              <h3>My Assignments</h3>
              <p>{totalAssignments}</p>
            </div>
          </div>
        )}

      <div className="Classes">
        {courses.length > 0 ? (
          courses.map((course) => {
            const assignmentText = `${course.assignmentCount || 0} assignments`;
            const hasTotalGrade =
              typeof course.total_grade === "number" && Number.isFinite(course.total_grade);
            const formattedGrade = hasTotalGrade
              ? `${course.total_grade!.toFixed(1).replace(/\.0$/, "")}%`
              : "Grade unavailable";

            return (
              // Show delete action for admins and for teachers who own the class.
              // Ownership check keeps the control visible even if role metadata drifts.
              (() => {
                const canDeleteCourse =
                  isAdminUser ||
                  (typeof course.teacherID === "number" && currentUserId !== null
                    ? course.teacherID === currentUserId
                    : false);

                return (
              <ClassCard
                key={course.id}
                image="https://crc.losrios.edu//shared/img/social-1200-630/programs/general-science-social.jpg"
                name={course.name}
                subtitle={assignmentText}
                gradeLabel={studentView ? formattedGrade : undefined}
                gradeUnavailable={studentView && !hasTotalGrade}
                canDelete={canDeleteCourse}
                onDelete={() => openDeleteModal(course)}
                onclick={() => {
                  window.location.href = `/classes/${course.id}/home`
                }}
              />
                );
              })()
            )
          })
        ) : (
          <div className="EmptyCoursesState" role="status">
            <h2>No courses yet</h2>
            {isStudent() ? (
              <p>
                You are not registered in any courses yet. Ask your instructor to add you to a course.
              </p>
            ) : isTeacher() ?(
              <p>
                You haven't created any courses yet. Click the "Create Class" button to get started.
              </p>
            ) : (
              <p>No courses are available right now.</p>
            )}
          </div>
        )}

        {isTeacher() && ( 
          <div className="ClassCreateButton" onClick={() => window.location.href = '/classes/create'}>
          <h2>Create Class</h2>
        </div> 
        )}
      </div>
    </div>

    <DeleteClassModal
      isOpen={Boolean(classToDelete)}
      className={classToDelete?.name || ""}
      onClose={closeDeleteModal}
      onConfirm={handleDeleteClass}
    />
    </>
  )
}