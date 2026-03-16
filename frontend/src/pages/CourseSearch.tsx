import { useState } from "react";
import { Link } from "react-router-dom";
import { searchCourses } from "../util/courseSearchApi";
import { CourseSearchResponse, CourseSearchResult } from "../types/courseSearch";
import "./CourseSearch.css";

const MIN_QUERY_LENGTH = 2;

export default function CourseSearch() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [result, setResult] = useState<CourseSearchResponse | null>(null);

  const trimmedQuery = query.trim();
  const queryTooShort = trimmedQuery.length > 0 && trimmedQuery.length < MIN_QUERY_LENGTH;

  const handleClear = () => {
    setQuery("");
    setResult(null);
    setErrorMessage("");
  };

  const handleSearch = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setErrorMessage("");

    if (queryTooShort) {
      setResult(null);
      setErrorMessage(`Please enter at least ${MIN_QUERY_LENGTH} characters.`);
      return;
    }

    setLoading(true);

    try {
      const payload = await searchCourses(query);
      setResult(payload);
    } catch (error: any) {
      setResult(null);
      setErrorMessage(error?.message || "Unable to search courses right now.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="CourseSearchPage">
      <div className="CourseSearchHeader">
        <h1>Find Your Course</h1>
        <p>Search by course name or code.</p>
      </div>

      <form className="CourseSearchForm" onSubmit={handleSearch}>
        <input
          type="text"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Example: COSC 404 or Math"
          aria-label="Search courses"
        />
        <button type="submit" disabled={loading}>
          {loading ? "Searching..." : "Search"}
        </button>
        <button type="button" className="ClearButton" onClick={handleClear} disabled={loading}> 
          Clear
        </button>
      </form>

      <p className="CourseSearchHint">Press Enter to search.</p>

      {queryTooShort ? (
        <div className="CourseSearchStatus Empty">
          Enter at least {MIN_QUERY_LENGTH} characters to search.
        </div>
      ) : null}

      {errorMessage ? (
        <div className="CourseSearchStatus Error">{errorMessage}</div>
      ) : null}

      {result ? (
        <div className="CourseSearchResults">
          {result.count === 0 ? (
            <div className="CourseSearchStatus Empty">{result.msg || "No courses found."}</div>
          ) : (
            <>
              <p className="ResultCount">{result.count} course(s) found</p>
              <ul>
                {result.results.map((course: CourseSearchResult) => (
                  <li key={course.id}>
                    <div className="CourseResultCard">
                      <h2>
                        <Link className="CourseNameLink" to={`/classes/${course.id}/home`}>
                          {course.name}
                        </Link>
                      </h2>
                      <p>
                        <strong>Code:</strong> {course.code}
                      </p>
                      <p>
                        <strong>Teacher:</strong> {course.teacher_name || "Unknown"}
                      </p>
                      <p>
                        <strong>Enrollment:</strong> {course.enrollment_count}
                      </p>
                    </div>
                  </li>
                ))}
              </ul>
            </>
          )}
        </div>
      ) : null}
    </div>
  );
}
