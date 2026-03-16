import { BASE_URL, maybeHandleExpire } from "./api";
import { CourseSearchResponse } from "../types/courseSearch";

export async function searchCourses(query: string): Promise<CourseSearchResponse> {
  const trimmed = query.trim();
  if (!trimmed) {
    return {
      query: "",
      count: 0,
      results: [],
      msg: "Enter a course name or code to search.",
    };
  }

  const response = await fetch(`${BASE_URL}/course/search?q=${encodeURIComponent(trimmed)}`, {
    method: "GET",
    credentials: "include",
  });

  maybeHandleExpire(response);

  if (!response.ok) {
    let message = `Response status: ${response.status}`;
    try {
      const errorBody = await response.json();
      if (errorBody?.msg) {
        message = errorBody.msg;
      }
    } catch {
      // Keep default message when body is not valid JSON.
    }
    throw new Error(message);
  }

  return response.json();
}
