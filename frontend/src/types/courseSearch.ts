export interface CourseSearchResult {
  id: number;
  name: string;
  code: string;
  teacher_id: number;
  teacher_name: string | null;
  enrollment_count: number;
}

export interface CourseSearchResponse {
  query: string;
  count: number;
  results: CourseSearchResult[];
  msg: string | null;
}
