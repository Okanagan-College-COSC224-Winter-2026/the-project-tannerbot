import "./CourseGradeBadge.css";

interface CourseGradeBadgeProps {
  label: string;
  unavailable?: boolean;
}

export default function CourseGradeBadge({ label, unavailable = false }: CourseGradeBadgeProps) {
  return (
    <div className={`CourseGradeBadge ${unavailable ? "Unavailable" : ""}`}>
      <span className="CourseGradeBadgeCaption">Total Grade</span>
      <strong>{label}</strong>
    </div>
  );
}
