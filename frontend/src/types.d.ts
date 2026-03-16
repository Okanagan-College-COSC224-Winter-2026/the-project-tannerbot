interface Course {
  id: number;
  teacherID: number;
  name: string;
}

interface User {
  id: number;
  name: string;
  email: string;
  role: 'student' | 'teacher' | 'admin';
}

interface StudentGroups {
  groupID: number;
  userID: number;
  assignmentID: number;
}

interface CourseGroup{
  id: number;
  name: string;
  assignmentID: number;
}

interface GroupTable {
  [key: number]: GroupTableValue[];
}

interface GroupTableValue{
  groupID: number;
  userID: number;
  assignmentID: number;
}

interface Criterion {
  rubricID: number;
  question: string;
  scoreMax: number;
  hasScore: boolean;
}

interface AssignmentAttachment {
  stored_name: string;
  original_name: string;
  download_url: string;
}

interface Assignment {
  id: number;
  name: string;
  courseID: number;
  rubric?: string;
  due_date?: string;
  start_date?: string;
  attachments?: AssignmentAttachment[];
}

interface CourseWithAssignments extends Course {
  assignments?: Assignment[];
  assignmentCount?: number;
}