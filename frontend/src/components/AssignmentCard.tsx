import './AssignmentCard.css'
import { useEffect, useRef } from 'react';
import { Tooltip } from 'bootstrap';
import { useNavigate } from 'react-router-dom';
import { calculateTimeUntilDue, formatDateTime, isPastDue } from '../util/dateUtils';
import { isTeacher } from '../util/login';
import { downloadAssignmentAttachment } from '../util/api';

interface Props {
  onClick?: () => void
  children?: React.ReactNode
  id: number | string
  assignment?: Assignment
  classId?: number | string
  onEdit?: () => void
  onDelete?: () => void
}

export default function AssignmentCard(props: Props) {
  const navigate = useNavigate();
  const cardRef = useRef<HTMLDivElement | null>(null);

  const timeUntilDue = props.assignment?.due_date 
    ? calculateTimeUntilDue(props.assignment.due_date)
    : null;

  const pastDue = isPastDue(props.assignment?.due_date);
  const canModify = !pastDue;

  useEffect(() => {
    if (!cardRef.current) {
      return;
    }

    const tooltipTriggers = Array.from(
      cardRef.current.querySelectorAll('[data-bs-toggle="tooltip"]')
    ) as HTMLElement[];

    const tooltips = tooltipTriggers.map((element) =>
      new Tooltip(element, {
        trigger: 'hover focus',
      })
    );

    return () => {
      tooltips.forEach((tooltip) => tooltip.dispose());
    };
  }, [canModify, pastDue, props.onEdit, props.onDelete]);

  const handleCardClick = () => {
    const classQuery = props.classId ? `?classId=${props.classId}` : '';
    if (isTeacher()) {
      navigate(`/assignment/${props.id}/criteria${classQuery}`, {
        state: {
          classId: props.classId,
          assignmentName: props.assignment?.name ?? props.children,
        },
      });
    } else {
      navigate(`/assignments/${props.id}${classQuery}`);
    }
  };

  const handleEdit = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (props.onEdit) {
      props.onEdit();
    }
  };

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (props.onDelete && window.confirm('Are you sure you want to delete this assignment?')) {
      props.onDelete();
    }
  };

  const handleAttachmentClick = async (
    e: React.MouseEvent,
    downloadUrl: string,
    fileName: string,
  ) => {
    e.stopPropagation();
    try {
      await downloadAssignmentAttachment(downloadUrl, fileName);
    } catch (error) {
      console.error('Error downloading assignment attachment:', error);
    }
  };

  return (
    <div className='A_Card' onClick={handleCardClick} ref={cardRef}>
      <div className='A_Card_icon'>
        <img src="/icons/document.svg" alt="document" />
      </div>
      
      <div className='A_Card_content'>
        <div className='A_Card_title'>{props.children}</div>
        
        {props.assignment && (
          <div className='A_Card_details'>
            {props.assignment.start_date && (
              <div className='A_Card_date'>
                <span className='date-label'>Starts:</span> {formatDateTime(props.assignment.start_date)}
              </div>
            )}
            {props.assignment.due_date && (
              <div className='A_Card_date'>
                <span className='date-label'>Due:</span> {formatDateTime(props.assignment.due_date)}
                {timeUntilDue && (
                  <span className={`time-remaining ${timeUntilDue.isPast ? 'past-due' : ''}`}>
                    ({timeUntilDue.formatted})
                  </span>
                )}
              </div>
            )}
            {props.assignment.attachments && props.assignment.attachments.length > 0 && (
              <div className='A_Card_attachments'>
                <span className='date-label'>Attachments:</span>
                <div className='A_Card_attachment_list'>
                  {props.assignment.attachments.map((attachment) => (
                    <button
                      key={attachment.stored_name}
                      type='button'
                      className='A_Card_attachment_link'
                      onClick={(e) =>
                        handleAttachmentClick(e, attachment.download_url, attachment.original_name)
                      }
                    >
                      {attachment.original_name}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {(props.onEdit || props.onDelete) && (
        <div className='A_Card_actions'>
          {props.onEdit && canModify && (
            <button 
              className='action-button edit-button' 
              onClick={handleEdit}
              title="Edit assignment"
              data-bs-toggle="tooltip"
              data-bs-placement="top"
              data-bs-title="Edit assignment"
              aria-label="Edit assignment"
            >
              <i className="bi bi-pencil-square" aria-hidden="true" />
            </button>
          )}
          {props.onDelete && canModify && (
            <button 
              className='action-button delete-button' 
              onClick={handleDelete}
              title="Delete assignment"
              data-bs-toggle="tooltip"
              data-bs-placement="top"
              data-bs-title="Delete assignment"
              aria-label="Delete assignment"
            >
              <i className="bi bi-trash" aria-hidden="true" />
            </button>
          )}
          {pastDue && (props.onEdit || props.onDelete) && (
            <span
              className='locked-indicator'
              title="Cannot modify past due assignments"
              data-bs-toggle="tooltip"
              data-bs-placement="top"
              data-bs-title="Cannot modify past due assignments"
              aria-label="Cannot modify past due assignments"
            >
              <i className="bi bi-lock-fill" aria-hidden="true" />
            </span>
          )}
        </div>
      )}
    </div>
  );
}
