interface Course {
  id: number;
  teacherID: number;
  name: string;
  total_grade?: number | null;
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
  assignment_mode?: 'solo' | 'group';
  attachments?: AssignmentAttachment[];
}

interface AssignmentGroupingMember {
  userID: number;
  assignmentID: number;
  groupID: number;
  name: string;
  email: string;
  student_id?: string | null;
}

interface AssignmentGroupingGroup {
  id: number;
  name: string;
  assignmentID: number;
  members: AssignmentGroupingMember[];
}

interface AssignmentGroupingStudent {
  id: number;
  name: string;
  email: string;
  student_id?: string | null;
  groupID?: number | null;
}

interface AssignmentGroupingResponse {
  assignment: Assignment;
  groups: AssignmentGroupingGroup[];
  students: AssignmentGroupingStudent[];
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
  review_type?: 'group' | 'peer';
  reviewer?: ReviewParticipant;
  reviewee?: ReviewParticipant;
  criteria?: ReviewCriterion[];
  assignment?: Assignment;
  review_window_open?: boolean;
  is_complete?: boolean;
}

interface SeparatedReviewAssignments {
  peer_reviews: ReviewAssignment[];
  group_reviews: ReviewAssignment[];
}

interface CourseWithAssignments extends Course {
  assignments?: Assignment[];
  assignmentCount?: number;
}

interface AssignmentStudentReviewStatus {
  has_reviewed: boolean;
  completed_assigned_reviews: number;
  total_assigned_reviews: number;
  pending_assigned_reviews: number;
  is_complete: boolean;
}

interface AssignmentProgressStudent {
  id: number;
  student_id?: string | null;
  name: string;
  email: string;
  has_submitted: boolean;
  review_status: AssignmentStudentReviewStatus;
  peer_review_status?: AssignmentStudentReviewStatus;
}

interface AssignmentProgressResponse {
  assignment: {
    id: number;
    name: string;
    courseID: number;
  };
  students: AssignmentProgressStudent[];
}