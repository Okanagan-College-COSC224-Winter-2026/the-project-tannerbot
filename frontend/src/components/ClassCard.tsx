import './ClassCard.css'
import CourseGradeBadge from './CourseGradeBadge'

interface Props {
  image: string
  name: string
  subtitle: string
  gradeLabel?: string
  gradeUnavailable?: boolean
  onclick?: () => void
  canDelete?: boolean
  onDelete?: () => void
}

export default function ClassCard(props: Props) {
  return (
    <div className="ClassCard" onClick={props.onclick}>
      {props.canDelete && props.onDelete ? (
        <button
          className="ClassCardDeleteButton"
          onClick={(event) => {
            event.stopPropagation()
            props.onDelete?.()
          }}
          aria-label={`Delete class ${props.name}`}
          title="Delete class"
        >
          Delete
        </button>
      ) : null}
      {props.gradeLabel ? (
        <CourseGradeBadge label={props.gradeLabel} unavailable={props.gradeUnavailable} />
      ) : null}
      <img src={props.image} alt={props.name} />
      <div className="ClassInfo">
        <h2>{props.name}</h2>
        <p>{props.subtitle}</p>
      </div>
    </div>
  )
}