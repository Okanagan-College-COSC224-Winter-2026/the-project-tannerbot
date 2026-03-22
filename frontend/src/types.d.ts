interface Course {
  id: number;
  teacherID: number;
  name: string;
}

interface User {
  id: number;
  student_id?: string | null;
  name: string;
  email: string;
  role: 'student' | 'teacher' | 'admin';
  is_instructor?: boolean;
  profile_picture_url?: string | null;
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
  description?: string;
  rubric?: string;
  due_date?: string;
  start_date?: string;
  attachments?: AssignmentAttachment[];
}

interface ReviewParticipant {
  id: number;
  name: string;
  email?: string;
}

interface ReviewCriterionRow {
  id: number;
  question: string;
  scoreMax: number;
  hasScore: boolean;
}

interface ReviewCriterion {
  id: number;
  criterionRowID: number;
  grade?: number | null;
  comments?: string | null;
  criterion_row?: ReviewCriterionRow;
}

interface ReviewAssignment {
  id: number;
  assignmentID: number;
  reviewer?: ReviewParticipant;
  reviewee?: ReviewParticipant;
  criteria?: ReviewCriterion[];
  assignment?: Assignment;
  review_window_open?: boolean;
  is_complete?: boolean;
}

interface CourseWithAssignments extends Course {
  assignments?: Assignment[];
  assignmentCount?: number;
}