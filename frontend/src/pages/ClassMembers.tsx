import { useParams, useNavigate } from "react-router-dom";
import TabNavigation from "../components/TabNavigation";
import { useEffect, useState } from "react";
import { listCourseMembers, listClasses } from "../util/api";
import { getProfilePictureSrc } from "../util/profile";
import StudentImportButton from "../components/StudentImportButton";

import './ClassMembers.css'
import { isTeacher } from "../util/login";

export default function ClassMembers() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [members, setMembers] = useState<User[]>([])
  const [className, setClassName] = useState<string | null>(null);
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [reloadKey, setReloadKey] = useState(0)

  useEffect(() => {
    ;(async () => {
      if (!id) {
        setMembers([])
        setClassName(null)
        return
      }
      try {
        setLoading(true)
        setError('')
        const members = await listCourseMembers(id as string)
        const classes = await listClasses();
        const currentClass = classes.find((c: { id: number }) => c.id === Number(id));
        setMembers(members)
        setClassName(currentClass?.name || null);
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to load class members'
        setError(message)
        setMembers([])
      } finally {
        setLoading(false)
      }
    })()
  }, [id, reloadKey])

  return (
    <div className="ClassMembersPage container-fluid py-4 px-3 px-md-4">
      <div className="ClassHeader card border-0 shadow-sm mb-3 p-3 p-md-4">
        <div className="ClassHeaderLeft">
          <h2 className="h3 fw-bold mb-0">{className || "Class"}</h2>
        </div>

        <div className="ClassHeaderRight">
          {isTeacher() ? (
            <StudentImportButton
              classId={id}
              onImported={() => setReloadKey((currentValue) => currentValue + 1)}
            />
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

      <div className="ClassMemberList card border-0 shadow-sm p-3 p-md-4 mt-3">
        {error ? (
          <div className="EmptyMembersState" role="alert">
            <p className="mb-0">{error}</p>
          </div>
        ) : loading ? (
          <div className="EmptyMembersState" role="status">
            <p className="mb-0">Loading class members...</p>
          </div>
        ) : members.length === 0 ? (
          <div className="EmptyMembersState" role="status">
            <p className="mb-0">No class members found.</p>
          </div>
        ) : (
          members.map((member) => {
            const identifier = member.student_id || member.email;
            const picSrc = getProfilePictureSrc(member.profile_picture_url);
            const isInstructor = member.is_instructor === true;
            const profileId = Number(member.id);
            return (
              <div
                key={member.id}
                className={`Member ${isInstructor ? 'MemberInstructorRow' : ''}`}
                onClick={() => {
                  if (Number.isFinite(profileId) && profileId > 0) {
                    navigate(`/profile/${profileId}`)
                  }
                }}
              >
                <div className="MemberAvatar">
                  {picSrc
                    ? <img src={picSrc} alt={member.name} className="MemberAvatarImg" />
                    : <span className="MemberAvatarFallback">{member.name.charAt(0).toUpperCase()}</span>
                  }
                </div>
                <div className="MemberInfo">
                  <span className={`MemberName ${isInstructor ? 'MemberNameInstructor' : ''}`}>{member.name}</span>
                  {isInstructor ? <span className="MemberRoleBadge">Instructor</span> : null}
                  <span className="MemberIdentifier">{identifier}</span>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
