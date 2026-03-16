import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
// This component checks if the user is authenticated by making a request to the backend.
import { hasRole } from "../util/login";

const BASE_URL = "http://localhost:5000";

interface ProtectedRouteProps {
    children: React.ReactNode;
    allowedRoles?: string[];
}

export default function ProtectedRoute({ children, allowedRoles }: ProtectedRouteProps) {
    const navigate = useNavigate();
    const [isAllowed, setIsAllowed] = useState<boolean | null>(null);

    useEffect(() => {
        ;(async () => {
            try {
                const response = await fetch(`${BASE_URL}/user`, {
                    method: "GET",
                    credentials: "include",
                });
                if (!response.ok) {
                    setIsAllowed(false);
                    navigate("/");
                    return;
                }

                if (allowedRoles && allowedRoles.length > 0) {
                    const roleMatch = hasRole(...allowedRoles);
                    if (!roleMatch) {
                        setIsAllowed(false);
                        navigate("/home");
                        return;
                    }
                }

                setIsAllowed(true);
            } catch (error) {
                console.error("Error checking authentication:", error);
                setIsAllowed(false);
                navigate("/");
            }
        })();
    }, [navigate]);

    return isAllowed ? <>{children}</> : null;
}