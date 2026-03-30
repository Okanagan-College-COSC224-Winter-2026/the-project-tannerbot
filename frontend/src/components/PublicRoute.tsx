import { Navigate } from "react-router-dom";

interface PublicRouteProps {
  children: React.ReactNode;
}

export default function PublicRoute({ children }: PublicRouteProps) {
  const user = JSON.parse(localStorage.getItem("user") || "null");

  // If logged in → block access to login/register pages
  if (user) {
    return <Navigate to="/home" replace />;
  }

  // If NOT logged in → allow access
  return <>{children}</>;
}