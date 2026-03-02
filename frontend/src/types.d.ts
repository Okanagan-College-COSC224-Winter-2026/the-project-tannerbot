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

interface Assignment {
  id: number;
  name: string;
  courseID: number;
  rubric?: string;
  start_date?: string;
  due_date?: string;
  time_until_due?: {
    days: number;
    hours: number;
    minutes: number;
    expired: boolean;
  };
}

interface CourseWithAssignments extends Course {
  assignments?: Assignment[];
  assignmentCount?: number;
}