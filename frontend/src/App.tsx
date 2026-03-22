import { BrowserRouter, Route, Routes, useLocation } from "react-router-dom";
import Home from "./pages/Home";
import ProtectedRoute from "./components/ProtectedRoute";
import Sidebar from "./components/Sidebar";
import AdminPage from "./pages/AdminPage";
import "./App.css";
import Profile from "./pages/Profile";
import CreateClass from "./pages/CreateClass";
import LoginPage from "./pages/LoginPage";
import ClassHome from "./pages/ClassHome";
import ClassMembers from "./pages/ClassMembers";
import Assignment from "./pages/Assignment";
import Group from "./pages/Group";
import AssignmentProgress from "./pages/AssignmentProgress";
import AssignmentReviews from "./pages/AssignmentReviews";
import RegisterPage from "./pages/RegisterPage";
import ChangePassword from "./pages/ChangePassword";
import CreateTeacher from "./pages/CreateTeacher";
import CriteriaCreation from "./pages/CriteriaCreation";
import CourseSearch from "./pages/CourseSearch";

function AppContent() {
  const location = useLocation();
  const noSidebarPaths = ["/", "/login", "/register", "/change-password"];

  return (
    <div className="App">
      {!noSidebarPaths.includes(location.pathname) && <Sidebar />}
      <div className="inner">
        <Routes>
          <Route path="/" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/change-password" element={<ChangePassword />} />

          <Route path="/home" element={
            <ProtectedRoute allowedRoles={['teacher', 'student', 'admin']}>
              <Home />
            </ProtectedRoute>
          } />

          <Route path="/admin/create-teacher" element={
            <ProtectedRoute>
              <CreateTeacher />
            </ProtectedRoute>
          } />

          <Route path="/classes/create" element={
            <ProtectedRoute>
              <CreateClass />
            </ProtectedRoute>
          } />

          <Route path="/courses/search" element={
            <ProtectedRoute>
              <CourseSearch />
            </ProtectedRoute>
          } />

          <Route path="/profile" element={
            <ProtectedRoute>
              <Profile />
            </ProtectedRoute>
          } />

          <Route path="/profile/:id" element={
            <ProtectedRoute>
              <Profile />
            </ProtectedRoute>
          } />

          <Route path="/classes/:id/home" element={
            <ProtectedRoute>
              <ClassHome />
            </ProtectedRoute>
          } />

          <Route path="/classes/:id/members" element={
            <ProtectedRoute>
              <ClassMembers />
            </ProtectedRoute>
          } />

          <Route path="/assignments/:id" element={
            <ProtectedRoute>
              <Assignment />
            </ProtectedRoute>
          } />

          <Route path="/assignments/:id/group" element={
            <ProtectedRoute allowedRoles={["teacher", "admin"]}>
              <Group />
            </ProtectedRoute>
          } />

          <Route path="/assignments/:id/reviews" element={
            <ProtectedRoute allowedRoles={["teacher", "admin"]}>
              <AssignmentReviews />
            </ProtectedRoute>
          } />

          <Route path="/assignments/:id/progress" element={
            <ProtectedRoute allowedRoles={["teacher", "admin"]}>
              <AssignmentProgress />
            </ProtectedRoute>
          } />
          <Route
            path="/admin"
              element={
               <ProtectedRoute allowedRoles={["admin"]}>
                  <AdminPage />
                </ProtectedRoute>
            }
          />
          <Route path="/assignment/:id/criteria" element={
            <ProtectedRoute allowedRoles={["teacher", "admin"]}>
              <CriteriaCreation />
            </ProtectedRoute>
          } />
        </Routes>
      </div>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  );
}

export default App;