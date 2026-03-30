import { removeToken } from "./login";

export const BASE_URL = 'http://localhost:5000'

// export const getProfile = async (id: string) => {
//   // TODO
// }


export const maybeHandleExpire = (response: Response) => {
  if (response.status === 401) {
    // Remove the token
    removeToken();

    setTimeout(() => {
    window.location.href = '/loginpage';
    }, 5000);
  }
}

export const tryLogin = async (email: string, password: string) => {
  try {
    const response = await fetch(`${BASE_URL}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ email: email, password: password }),
      credentials: 'include'  // Include cookies in request/response
    });
    
    if (!response.ok) { 
      // Throw if login fails for any reason
      throw new Error(`Response status: ${response.status}`);
    }

    const json = await response.json();
    
    // Store user info (but not token - that's in httponly cookie now)
    localStorage.setItem('user', JSON.stringify(json));
    //console.log("Logged in:", json);

    return json;
  } catch (error) {
    // Login is wrong
    console.error(error);
    // window.location.href = '/';
  }

  return false
}

export const tryRegister = async (name: string, email: string, password: string) => {
  try {
    const response = await fetch(`${BASE_URL}/auth/register`, {
      method: 'POST',
      body: JSON.stringify({
        name,
        email,
        password
      }),
      headers: {
        'Content-Type': 'application/json'
      },
    });
    if (!response.ok) {
      throw new Error(`Response status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error(error);
  }
}

export const createClass = async (name: string) => {
  const response = await fetch(`${BASE_URL}/class/create_class`, {
    method: 'POST',
    body: JSON.stringify({
      name,
    }),
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include'  // Include cookies (JWT token)
  })

  maybeHandleExpire(response);

  if (!response.ok) {
    throw new Error(`Response status: ${response.status}`);
  }
  return response
}

export const listClasses = async () => {
  // TODO get session info and whatnot
  const resp = await fetch(`${BASE_URL}/class/classes`, {
    method: 'GET',
    credentials: 'include'  // Include cookies (JWT token)
  })

  maybeHandleExpire(resp);

  if (!resp.ok) {
    throw new Error(`Response status: ${resp.status}`);
  }

  return await resp.json()
}

export const deleteClass = async (classId: number) => {
  const response = await fetch(`${BASE_URL}/class/${classId}`, {
    method: 'DELETE',
    credentials: 'include',
  });

  maybeHandleExpire(response);

  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    throw new Error(errorData?.msg || `Response status: ${response.status}`);
  }

  return await response.json();
}

export type StudentEnrollmentPreviewRow = {
  id: string
  name: string
  email: string
  account_exists: boolean
  already_enrolled: boolean
}

export type StudentEnrollmentPreview = {
  students: StudentEnrollmentPreviewRow[]
  total_count: number
  new_accounts_count: number
  existing_accounts_count: number
  already_enrolled_count: number
}

export const previewStudentsForCourseImport = async (
  courseID: number,
  students: string,
): Promise<StudentEnrollmentPreview> => {
  const response = await fetch(`${BASE_URL}/class/enroll_students_preview`, {
    method: 'POST',
    body: JSON.stringify({
      students,
      class_id: courseID,
    }),
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include'
  })

  maybeHandleExpire(response);

  if (!response.ok) {
    let errorMessage = `Response status: ${response.status}`;
    try {
      const errorBody = await response.json();
      if (errorBody?.msg) {
        errorMessage = errorBody.msg;
        if (Array.isArray(errorBody.errors) && errorBody.errors.length > 0) {
          errorMessage += ` (${errorBody.errors.join('; ')})`;
        }
      }
    } catch {
      // keep default errorMessage when response body is not JSON
    }
    throw new Error(errorMessage);
  }

  const json = await response.json();
  return json;
}

export const importStudentsForCourse = async (
  courseID: number,
  students: string,
  options?: {
    defaultPassword?: string
    studentPasswords?: Record<string, string>
  },
) => {
  const response = await fetch(`${BASE_URL}/class/enroll_students`, {
    method: 'POST',
    body: JSON.stringify({
      students,
      class_id: courseID,
      default_password: options?.defaultPassword,
      student_passwords: options?.studentPasswords,
    }),
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include'
  })

  maybeHandleExpire(response);

  if (!response.ok) {
    let errorMessage = `Response status: ${response.status}`;
    try {
      const errorBody = await response.json();
      if (errorBody?.msg) {
        errorMessage = errorBody.msg;
        if (Array.isArray(errorBody.errors) && errorBody.errors.length > 0) {
          errorMessage += ` (${errorBody.errors.join('; ')})`;
        }
      }
    } catch {
      // keep default errorMessage when response body is not JSON
    }
    throw new Error(errorMessage);
  }

  const json = await response.json();
  return json;
}

export const listAssignments = async (classId: string) => {
  const resp = await fetch(`${BASE_URL}/assignment/`+classId, {
    method: 'GET',
    headers: {
       'Content-Type': 'application/json',
    },
    credentials: 'include',
  })
  
  maybeHandleExpire(resp);

  if (!resp.ok) {
    throw new Error(`Response status: ${resp.status}`);
  }

  return await resp.json()
}

export const getAssignmentProgress = async (assignmentId: number) => {
  const resp = await fetch(`${BASE_URL}/assignment/${assignmentId}/progress`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  })

  maybeHandleExpire(resp)

  if (!resp.ok) {
    throw new Error(`Response status: ${resp.status}`)
  }

  return await resp.json()
}

export const listStuGroup = async (assignmentId : number, studentId : number) => {
  const resp = await fetch(`${BASE_URL}/list_stu_groups/`+ assignmentId + "/" + studentId, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
   },
    credentials: 'include',
  })

  maybeHandleExpire(resp);


  if (!resp.ok) {
    throw new Error(`Response status: ${resp.status}`);
  }

  return await resp.json()
} 

export const listGroups = async (assignmentId : number) => {
  const resp = await fetch(`${BASE_URL}/list_all_groups/` + assignmentId, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
   },
    credentials: 'include',
  })
  maybeHandleExpire(resp);


  if (!resp.ok) {
    throw new Error(`Response status: ${resp.status}`);
  }
  
  return await resp.json()
} 

export const listUnassignedGroups = async (assignmentId : number) => {
  const resp = await fetch(`${BASE_URL}/list_ua_groups/` + assignmentId, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
   },
    credentials: 'include',
  })

  maybeHandleExpire(resp);

  return await resp.json()
}

export const listCourseMembers = async (classId: string) => {
  const resp = await fetch(`${BASE_URL}/class/members`, {
    method: 'POST',
    body: JSON.stringify({
      id: classId,
    }),
    headers: {
       'Content-Type': 'application/json',
    },
    credentials: 'include',
  })
  
  maybeHandleExpire(resp);

  if (!resp.ok) {
    throw new Error(`Response status: ${resp.status}`);
  }

  type RawCourseMember = {
    id?: number | string
    userID?: number | string
    user_id?: number | string
    name?: string
    email?: string
    role?: string
    student_id?: string | null
    studentID?: string | null
    is_instructor?: unknown
    isInstructor?: unknown
    profile_picture_url?: string | null
    profilePictureUrl?: string | null
    [key: string]: unknown
  }

  const payload: unknown = await resp.json()
  if (!Array.isArray(payload)) {
    throw new Error('Invalid class members response payload')
  }

  const normalizeInstructorFlag = (value: unknown): boolean => {
    if (value === true || value === 1 || value === '1') {
      return true
    }
    if (typeof value === 'string') {
      return value.toLowerCase() === 'true'
    }
    return false
  }

  return (payload as RawCourseMember[]).map((member) => {
    const normalizedId = Number(member.id ?? member.userID ?? member.user_id)
    const normalizedRole: 'student' | 'teacher' | 'admin' =
      member.role === 'student' || member.role === 'teacher' || member.role === 'admin'
        ? member.role
        : normalizeInstructorFlag(member.is_instructor ?? member.isInstructor)
          ? 'teacher'
          : 'student'

    return {
      id: Number.isFinite(normalizedId) ? normalizedId : 0,
      name: typeof member.name === 'string' ? member.name : '',
      email: typeof member.email === 'string' ? member.email : '',
      role: normalizedRole,
      student_id: member.student_id ?? member.studentID ?? null,
      is_instructor: normalizeInstructorFlag(member.is_instructor ?? member.isInstructor),
      profile_picture_url: member.profile_picture_url ?? member.profilePictureUrl ?? null,
    }
  })
} 




export const listGroupMembers = async (assignmentId : number, groupID: number) => {
  const resp = await fetch(`${BASE_URL}/list_group_members/` + assignmentId + '/' + groupID, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
   },
    credentials: 'include',
  })

  maybeHandleExpire(resp);

  if (!resp.ok) {
    throw new Error(`Response status: ${resp.status}`);
  }
  
  return await resp.json()
} 

export const getUserId = async () => {
  const resp = await fetch(`${BASE_URL}/user_id`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
   },
    credentials: 'include',
  })

  maybeHandleExpire(resp);

  if (!resp.ok) {
    throw new Error(`Response status: ${resp.status}`);
  }
  
  return await resp.json()
} 

export const saveGroups = async (groupID: number, userID: number, assignmentID : number) =>{
  await fetch(`${BASE_URL}/save_groups`, {
    method: 'POST',
    body: JSON.stringify({
      groupID,
      userID,
      assignmentID
    }),
    headers: {
      'Content-Type': 'application/json',
   },
    credentials: 'include',
  })
}

export const getCriteria = async (rubricID: number) => {
  const resp = await fetch(`${BASE_URL}/criteria?rubricID=${rubricID}`, {
    credentials: 'include'
  })

  maybeHandleExpire(resp);

  if (!resp.ok) {
    throw new Error(`Response status: ${resp.status}`);
  }

  return await resp.json()
}

export const createCriteria = async (
  assignmentID: number,
  rubricID: number,
  question: string,
  scoreMax: number,
  canComment: boolean,
  hasScore: boolean = true,
) => {
  const response = await fetch(`${BASE_URL}/assignment/${assignmentID}/criteria`, {
    method: 'POST',
    body: JSON.stringify({
      rubricID, question, scoreMax, canComment, hasScore
    }),
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include'
  })

  maybeHandleExpire(response);

  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(error?.msg || `Response status: ${response.status}`);
  }
}

export const updateCriteria = async (
  assignmentID: number,
  criteriaId: number,
  question: string,
  scoreMax: number,
  hasScore: boolean = true,
) => {
  const response = await fetch(`${BASE_URL}/assignment/${assignmentID}/criteria/${criteriaId}`, {
    method: 'PATCH',
    body: JSON.stringify({
      question,
      scoreMax,
      hasScore,
    }),
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include'
  })

  maybeHandleExpire(response);

  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(error?.msg || `Response status: ${response.status}`);
  }

  return await response.json();
}

export const deleteCriteria = async (assignmentID: number, criteriaId: number) => {
  const response = await fetch(`${BASE_URL}/assignment/${assignmentID}/criteria/${criteriaId}`, {
    method: 'DELETE',
    credentials: 'include'
  })

  maybeHandleExpire(response);

  if (!response.ok) {
    throw new Error(`Response status: ${response.status}`);
  }

  return await response.json();
}

export const createRubric = async (
  assignmentID: number,
  canComment: boolean,
  rubricType: 'peer' | 'group' = 'peer',
): Promise<{ id: number }> => {
  const response = await fetch(`${BASE_URL}/create_rubric`, {
    method: 'POST',
    body: JSON.stringify({
      assignmentID,
      canComment,
      rubricType,
    }),
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include'
  })

  maybeHandleExpire(response);

  if (!response.ok) {
    throw new Error(`Response status: ${response.status}`);
  }

  return await response.json();
}

export const getRubric = async (rubricID: number) => {
  const resp = await fetch(`${BASE_URL}/rubric?rubricID=${rubricID}`, {
      credentials: 'include'
  });

  maybeHandleExpire(resp);

  if (!resp.ok) {
      throw new Error(`Response status: ${resp.status}`);
  }

  return await resp.json();
}

export const getRubricByAssignment = async (
  assignmentId: number,
  rubricType: 'peer' | 'group' = 'peer',
) => {
  const resp = await fetch(`${BASE_URL}/rubric/assignment/${assignmentId}?rubricType=${rubricType}`, {
    credentials: 'include'
  });

  maybeHandleExpire(resp);

  if (resp.status === 404) {
    return null;
  }

  if (!resp.ok) {
    throw new Error(`Response status: ${resp.status}`);
  }

  return await resp.json();
}


export const createAssignment = async (
  courseID: number,
  name: string,
  dueDate?: string,
  startDate?: string,
  assignmentMode?: 'solo' | 'group',
)=> {
  const response = await fetch(`${BASE_URL}/assignment/create_assignment`, {
    method: 'POST',
    body: JSON.stringify({
      courseID,
      name,
      due_date: dueDate,
      start_date: startDate,
      assignment_mode: assignmentMode,
    }),
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  })
  
  maybeHandleExpire(response);

  if (!response.ok) {
    let errorMsg = `Response status: ${response.status}`;
    try {
      const error = await response.json();
      if (error?.msg) {
        errorMsg = error.msg;
      } else if (error?.error) {
        errorMsg = error.error;
      }
    } catch {
      // Keep status fallback when response body is empty or not JSON.
    }
    throw new Error(errorMsg);
  }

  return await response.json();
}

export const editAssignment = async (
  assignmentID: number,
  name?: string,
  dueDate?: string,
  startDate?: string,
  rubric?: string,
  description?: string,
  assignmentMode?: 'solo' | 'group',
) => {
  const response = await fetch(`${BASE_URL}/assignment/edit_assignment/${assignmentID}`, {
    method: 'PATCH',
    body: JSON.stringify({
      name,
      due_date: dueDate,
      start_date: startDate,
      rubric,
      description,
      assignment_mode: assignmentMode,
    }),
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include'
  })

  maybeHandleExpire(response);

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.msg || `Response status: ${response.status}`);
  }

  return await response.json();
}

export const deleteAssignment = async (assignmentID: number) => {
  const response = await fetch(`${BASE_URL}/assignment/delete_assignment/${assignmentID}`, {
    method: 'DELETE',
    credentials: 'include'
  })

  maybeHandleExpire(response);

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.msg || `Response status: ${response.status}`);
  }

  return await response.json();
}

export const downloadAssignmentAttachment = async (downloadUrl: string, fileName: string) => {
  const response = await fetch(`${BASE_URL}${downloadUrl}`, {
    method: 'GET',
    credentials: 'include',
  });

  maybeHandleExpire(response);

  if (!response.ok) {
    let errorMsg = `Response status: ${response.status}`;
    try {
      const error = await response.json();
      if (error?.msg) {
        errorMsg = error.msg;
      }
    } catch {
      // Keep status fallback when body is not JSON.
    }
    throw new Error(errorMsg);
  }

  const blob = await response.blob();
  const objectUrl = window.URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = objectUrl;
  anchor.download = fileName;
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  window.URL.revokeObjectURL(objectUrl);
}

export const addAssignmentAttachments = async (assignmentID: number, files: File[]) => {
  const formData = new FormData();
  files.forEach((file) => {
    formData.append('attachments', file);
  });

  const response = await fetch(`${BASE_URL}/assignment/${assignmentID}/attachment`, {
    method: 'POST',
    body: formData,
    credentials: 'include',
  });

  maybeHandleExpire(response);

  if (!response.ok) {
    let errorMsg = `Response status: ${response.status}`;
    try {
      const error = await response.json();
      if (error?.msg) {
        errorMsg = error.msg;
      }
    } catch {
      // Keep status fallback when body is not JSON.
    }
    throw new Error(errorMsg);
  }

  return await response.json();
}

export const deleteAssignmentAttachment = async (assignmentID: number, storedName: string) => {
  const response = await fetch(`${BASE_URL}/assignment/${assignmentID}/attachment/${storedName}`, {
    method: 'DELETE',
    credentials: 'include',
  });

  maybeHandleExpire(response);

  if (!response.ok) {
    let errorMsg = `Response status: ${response.status}`;
    try {
      const error = await response.json();
      if (error?.msg) {
        errorMsg = error.msg;
      }
    } catch {
      // Keep status fallback when body is not JSON.
    }
    throw new Error(errorMsg);
  }

  return await response.json();
}

export const deleteGroup = async (groupID: number) => {
  await fetch(`${BASE_URL}/delete_group`, {
    method: 'POST',
    body: JSON.stringify({
      groupID,
    }),
    headers: {
      'Content-Type': 'application/json',
   },
    credentials: 'include',
  })
}

export const createReview = async (assignmentID: number, reviewerID: number, revieweeID: number) => {
  const response = await fetch(`${BASE_URL}/create_review`, {
    method: 'POST',
    body: JSON.stringify({
      assignmentID,
      reviewerID,
      revieweeID,
    }),
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include'
  })

  maybeHandleExpire(response);

  if (!response.ok) {
    throw new Error(`Response status: ${response.status}`);
  }
  return response
}

export const createCriterion = async (reviewID: number, criterionRowID: number, grade: number, comments: string) => {
  const response = await fetch(`${BASE_URL}/create_criterion`, {
    method: 'POST',
    body: JSON.stringify({
      reviewID,
      criterionRowID,
      grade,
      comments,
    }),
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include'
  })

  maybeHandleExpire(response);

  if (!response.ok) {
    throw new Error(`Response status: ${response.status}`);
  }
  return response
}

export const getReview = async (assignmentID: number, reviewerID: number, revieweeID: number) => {
  const resp = await fetch(`${BASE_URL}/review?assignmentID=${assignmentID}&reviewerID=${reviewerID}&revieweeID=${revieweeID}`, {
    credentials: 'include'
  })

  maybeHandleExpire(resp);

  if (!resp.ok) {
    throw new Error(`Response status: ${resp.status}`);
  }

  return resp
}

export const getNextGroupID = async(assignmentID: number)=> {
  const response = await fetch(`${BASE_URL}/next_groupid?assignmentID=${assignmentID}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include'
  })

  maybeHandleExpire(response);

  if (!response.ok) {
      throw new Error(`Response status: ${response.status}`);
  }

  return await response.json();
}

export const createGroup = async(assignmentID: number, name: string, id: number) =>{
  const response = await fetch(`${BASE_URL}/create_group`,{
    method:"POST",
    body: JSON.stringify({
      assignmentID, name, id
    }),
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include'
  })
  maybeHandleExpire(response);

  if (!response.ok) {
      throw new Error(`Response status: ${response.status}`);
  }

  return await response.json();
}

export const getAssignmentGrouping = async (assignmentID: number) => {
  const response = await fetch(`${BASE_URL}/assignment/${assignmentID}/grouping`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  });

  maybeHandleExpire(response);

  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(error?.msg || `Response status: ${response.status}`);
  }

  return await response.json();
};

export const updateAssignmentMode = async (
  assignmentID: number,
  assignmentMode: 'solo' | 'group',
) => {
  const response = await fetch(`${BASE_URL}/assignment/${assignmentID}/mode`, {
    method: 'PATCH',
    body: JSON.stringify({ assignment_mode: assignmentMode }),
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  });

  maybeHandleExpire(response);

  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(error?.msg || `Response status: ${response.status}`);
  }

  return await response.json();
};

export const createAssignmentGroup = async (assignmentID: number, name: string) => {
  const response = await fetch(`${BASE_URL}/assignment/${assignmentID}/groups`, {
    method: 'POST',
    body: JSON.stringify({ name }),
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  });

  maybeHandleExpire(response);

  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(error?.msg || `Response status: ${response.status}`);
  }

  return await response.json();
};

export const renameAssignmentGroup = async (
  assignmentID: number,
  groupID: number,
  name: string,
) => {
  const response = await fetch(`${BASE_URL}/assignment/${assignmentID}/groups/${groupID}`, {
    method: 'PATCH',
    body: JSON.stringify({ name }),
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  });

  maybeHandleExpire(response);

  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(error?.msg || `Response status: ${response.status}`);
  }

  return await response.json();
};

export const deleteAssignmentGroup = async (assignmentID: number, groupID: number) => {
  const response = await fetch(`${BASE_URL}/assignment/${assignmentID}/groups/${groupID}`, {
    method: 'DELETE',
    credentials: 'include',
  });

  maybeHandleExpire(response);

  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(error?.msg || `Response status: ${response.status}`);
  }

  return await response.json();
};

export const setAssignmentGroupMembers = async (
  assignmentID: number,
  groupID: number,
  studentIds: number[],
) => {
  const response = await fetch(
    `${BASE_URL}/assignment/${assignmentID}/groups/${groupID}/members`,
    {
      method: 'PUT',
      body: JSON.stringify({ student_ids: studentIds }),
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
    },
  );

  maybeHandleExpire(response);

  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(error?.msg || `Response status: ${response.status}`);
  }

  return await response.json();
};

// Admin - Create Teacher Account
export const createTeacherAccount = async (name: string, email: string, password: string) => {
  const response = await fetch(`${BASE_URL}/admin/users/create`, {
    method: 'POST',
    body: JSON.stringify({ 
      name, 
      email, 
      password,
      role: 'teacher',
      must_change_password: true
    }),
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include'
  });

  maybeHandleExpire(response);

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.msg || `Response status: ${response.status}`);
  }

  return await response.json();
}

// Review - Assign reviewer to peer review
export const assignReview = async (
  assignmentID: number,
  params:
    | { reviewerID: number; revieweeID: number }
    | { reviewType: 'group'; reviewerGroupID: number; revieweeGroupID: number }
    | { reviewType: 'peer'; reviewerGroupID: number },
) => {
  const payload = {
    assignmentID,
    ...params,
  };

  const response = await fetch(`${BASE_URL}/review/assign`, {
    method: 'POST',
    body: JSON.stringify(payload),
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include'
  });

  maybeHandleExpire(response);

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.msg || `Response status: ${response.status}`);
  }

  return await response.json();
}

function isSeparatedReviewAssignments(payload: unknown): payload is SeparatedReviewAssignments {
  return (
    payload !== null &&
    typeof payload === 'object' &&
    !Array.isArray(payload) &&
    'peer_reviews' in payload &&
    'group_reviews' in payload
  );
}

// Review - List reviews for an assignment
export const listReviewsForAssignment = async (assignmentID: number): Promise<SeparatedReviewAssignments> => {
  const response = await fetch(`${BASE_URL}/review/assignment/${assignmentID}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include'
  });

  maybeHandleExpire(response);

  if (response.status === 404) {
    const legacyPayload = await listMyReviewsForAssignment(assignmentID);
    const reviews: ReviewAssignment[] = Array.isArray(legacyPayload) ? legacyPayload : [];
    return {
      peer_reviews: reviews.filter((review) => review.review_type !== 'group'),
      group_reviews: reviews.filter((review) => review.review_type === 'group'),
    };
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    throw new Error(errorData?.msg || `Response status: ${response.status}`);
  }

  const payload = await response.json().catch(() => null);
  if (isSeparatedReviewAssignments(payload)) {
    return payload;
  }
  const reviews: ReviewAssignment[] = Array.isArray(payload) ? payload : [];
  return {
    peer_reviews: reviews.filter((review) => review.review_type !== 'group'),
    group_reviews: reviews.filter((review) => review.review_type === 'group'),
  };
}

export const listMyReceivedSeparatedReviewsForAssignment = async (assignmentID: number) => {
  const response = await fetch(`${BASE_URL}/review/my/received/assignment/${assignmentID}/separated`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include'
  });

  maybeHandleExpire(response);

  if (response.status === 404) {
    return {
      peer_reviews: [],
      group_reviews: [],
    };
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    throw new Error(errorData?.msg || `Response status: ${response.status}`);
  }

  const payload = await response.json().catch(() => null);
  if (payload && typeof payload === 'object') {
    return payload;
  }

  return {
    peer_reviews: [],
    group_reviews: [],
  };
}

export const listSeparatedReviewsForAssignment = async (assignmentID: number) => {
  const response = await fetch(`${BASE_URL}/review/assignment/${assignmentID}/separated`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include'
  });

  maybeHandleExpire(response);

  if (response.status === 404) {
    return await listReviewsForAssignment(assignmentID);
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    throw new Error(errorData?.msg || `Response status: ${response.status}`);
  }

  const payload = await response.json().catch(() => null);
  if (isSeparatedReviewAssignments(payload)) {
    return payload;
  }

  return await listReviewsForAssignment(assignmentID);
}

export const listMyReviewsForAssignment = async (assignmentID: number) => {
  const response = await fetch(`${BASE_URL}/review/my/assignment/${assignmentID}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include'
  });

  maybeHandleExpire(response);

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.msg || `Response status: ${response.status}`);
  }

  return await response.json();
}

export const listReviewsForClass = async (classID: number) => {
  const response = await fetch(`${BASE_URL}/review/class/${classID}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include'
  });

  maybeHandleExpire(response);

  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    throw new Error(errorData?.msg || `Response status: ${response.status}`);
  }

  return await response.json();
}

export const listMySeparatedReviewsForAssignment = async (assignmentID: number) => {
  const response = await fetch(`${BASE_URL}/review/my/assignment/${assignmentID}/separated`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include'
  });

  maybeHandleExpire(response);

  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    throw new Error(errorData?.msg || `Response status: ${response.status}`);
  }

  return await response.json();
}

// Review - Mark/grade a review
export const markReview = async (reviewID: number, criteria: Array<{criterionID: number, grade?: number, comments?: string}>) => {
  const response = await fetch(`${BASE_URL}/review/${reviewID}/mark`, {
    method: 'PATCH',
    body: JSON.stringify({
      criteria,
    }),
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include'
  });

  maybeHandleExpire(response);

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.msg || `Response status: ${response.status}`);
  }

  return await response.json();
}

// User - Change Password
export const changePassword = async (currentPassword: string, newPassword: string) => {
  const response = await fetch(`${BASE_URL}/user/password`, {
    method: 'PATCH',
    body: JSON.stringify({
      current_password: currentPassword,
      new_password: newPassword
    }),
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include'
  });

  maybeHandleExpire(response);

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.msg || `Response status: ${response.status}`);
  }

  return await response.json();
}

export const listUsers = async () => {
  const response = await fetch(`${BASE_URL}/admin/users`, {
    method: 'GET',
    credentials: 'include',
  });

  maybeHandleExpire(response);

  if (!response.ok) {
    throw new Error(`Response status: ${response.status}`);
  }

  return await response.json();
};

export const updateUser = async (userId: number, name?: string, email?: string) => {
  const response = await fetch(`${BASE_URL}/admin/users/${userId}`, {
    method: 'PUT',
    body: JSON.stringify({ name, email }),
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  });

  maybeHandleExpire(response);

  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    throw new Error(errorData?.msg || `Response status: ${response.status}`);
  }

  return await response.json();
};

export const updateUserRole = async (id: number, role: string) => {
  const response = await fetch(`${BASE_URL}/admin/users/${id}/role`, {
    method: 'PUT',
    body: JSON.stringify({ role }),
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  });

  maybeHandleExpire(response);

  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    throw new Error(errorData?.msg || `Response status: ${response.status}`);
  }

  return await response.json();
};

export const deleteUser = async (userId: number) => {
  const response = await fetch(`${BASE_URL}/admin/users/${userId}`, {
    method: 'DELETE',
    credentials: 'include',
  });

  maybeHandleExpire(response);

  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    if (errorData?.msg && errorData?.blockers && typeof errorData.blockers === 'object') {
      const blockerSummary = Object.entries(errorData.blockers)
        .filter(([, count]) => Number(count) > 0)
        .map(([key, count]) => `${key}: ${count}`)
        .join(', ');
      throw new Error(blockerSummary ? `${errorData.msg}. ${blockerSummary}` : errorData.msg);
    }
    throw new Error(errorData?.msg || `Response status: ${response.status}`);
  }

  return await response.json();
};
