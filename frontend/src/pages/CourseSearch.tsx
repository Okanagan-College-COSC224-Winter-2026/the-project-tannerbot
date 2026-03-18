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
    <div className="CourseSearchPage container py-4 py-md-5">
      <div className="row justify-content-center">
        <div className="col-12 col-xl-10">
          <div className="CourseSearchPanel card border-0 shadow-sm p-3 p-md-4">
            <div className="CourseSearchHeader mb-3 mb-md-4">
              <h1 className="h3 fw-bold mb-1">Find Your Course</h1>
              <p className="text-secondary mb-0">Search by course name or code.</p>
            </div>

            <form className="CourseSearchForm row g-2 g-md-3 align-items-stretch" onSubmit={handleSearch}>
              <div className="col-12 col-md">
                <input
                  type="text"
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  placeholder="Example: COSC 404 or Math"
                  aria-label="Search courses"
                  className="form-control form-control-lg"
                />
              </div>
              <div className="col-6 col-md-auto d-grid">
                <button type="submit" className="btn btn-primary btn-lg" disabled={loading}>
                  {loading ? "Searching..." : "Search"}
                </button>
              </div>
              <div className="col-6 col-md-auto d-grid">
                <button type="button" className="btn btn-outline-secondary btn-lg" onClick={handleClear} disabled={loading}>
                  Clear
                </button>
              </div>
            </form>

            <p className="CourseSearchHint mt-3 mb-0 text-secondary">Press Enter to search.</p>

            {queryTooShort ? (
              <div className="CourseSearchStatus Empty mt-3">
                Enter at least {MIN_QUERY_LENGTH} characters to search.
              </div>
            ) : null}

            {errorMessage ? (
              <div className="CourseSearchStatus Error mt-3">{errorMessage}</div>
            ) : null}

            {result ? (
              <div className="CourseSearchResults mt-4">
                {result.count === 0 ? (
                  <div className="CourseSearchStatus Empty">{result.msg || "No courses found."}</div>
                ) : (
                  <>
                    <p className="ResultCount mb-3 text-secondary">{result.count} course(s) found</p>
                    <ul className="row g-3 list-unstyled m-0 p-0">
                      {result.results.map((course: CourseSearchResult) => (
                        <li key={course.id} className="col-12 col-lg-6">
                          <div className="CourseResultCard card border-0 shadow-sm h-100">
                            <div className="card-body">
                              <h2 className="h5 mb-3">
                                <Link className="CourseNameLink" to={`/classes/${course.id}/home`}>
                                  {course.name}
                                </Link>
                              </h2>
                              <p className="mb-2">
                                <strong>Code:</strong> {course.code}
                              </p>
                              <p className="mb-2">
                                <strong>Teacher:</strong> {course.teacher_name || "Unknown"}
                              </p>
                              <p className="mb-0">
                                <strong>Enrollment:</strong> {course.enrollment_count}
                              </p>
                            </div>
                          </div>
                        </li>
                      ))}
                    </ul>
                  </>
                )}
              </div>
            ) : null}
          </div>
        </div>
      </div>
    </div>
  );
}
