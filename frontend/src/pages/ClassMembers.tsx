import { useParams } from "react-router-dom";
import TabNavigation from "../components/TabNavigation";
import { useEffect, useState } from "react";
import Button from "../components/Button";
import { importCSV } from "../util/csv";
import { listCourseMembers, listClasses } from "../util/api";

import './ClassMembers.css'
import { isTeacher } from "../util/login";

export default function ClassMembers() {
  const { id } = useParams()
  const [members, setMembers] = useState<User[]>([])
  const [className, setClassName] = useState<string | null>(null);

  useEffect(() => {
    ;(async () => {
      const members = await listCourseMembers(id as string)
      const classes = await listClasses();
      const currentClass = classes.find((c: { id: number }) => c.id === Number(id));
      setMembers(members)
      setClassName(currentClass?.name || null);
    })()
  }, [])  

  return (
    <div className="ClassMembersPage container-fluid py-4 px-3 px-md-4">
      <div className="ClassHeader card border-0 shadow-sm mb-3 p-3 p-md-4">
        <div className="ClassHeaderLeft">
          <h2 className="h3 fw-bold mb-0">{className || "Class"}</h2>
        </div>

        <div className="ClassHeaderRight">
          {isTeacher() ? (
            <Button onClick={() => importCSV(id as string)}>Add Students via CSV</Button>
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
        {members.length === 0 ? (
          <div className="EmptyMembersState" role="status">
            <p className="mb-0">No class members found.</p>
          </div>
        ) : (
          members.map((member) => {
            const identifier = member.student_id || member.email;
            return (
              <div key={member.id} className="Member">
                <span className="MemberName">{member.name}</span>
                <span className="MemberIdentifier">{identifier}</span>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
