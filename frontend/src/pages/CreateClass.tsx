import { useState, type FormEvent } from 'react'
import StatusMessage from '../components/StatusMessage'
import './CreateClass.css'
import { createClass } from '../util/api'

export default function CreateClass() {
  const [name, setName] = useState('')
  const [statusMessage, setStatusMessage] = useState('')
  const [statusType, setStatusType] = useState<'error' | 'success'>('error')

  const attemptCreateClass = async () => {
    if (!name.trim()) {
      setStatusType('error')
      setStatusMessage('Class name is required.')
      return
    }

    try {
      setStatusMessage('')
      const response = await createClass(name.trim())

      if (!response.ok) {
        throw new Error('Failed to create class')
      }

      setStatusType('success')
      setStatusMessage('Class created successfully!')
      setName('')
    } catch (error) {
      console.error('Error creating class:', error)
      setStatusType('error')
      setStatusMessage('Error creating class.')
    }
  }

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    void attemptCreateClass()
  }

  return (
    <div className="CreateClassPage container py-4 py-md-5">
      <div className="row justify-content-center">
        <div className="col-12 col-xl-10">
          <div className="CreateClassPanel card border-0 shadow-sm p-3 p-md-4">
            <div className="CreateClassHeader mb-3 mb-md-4">
              <h1 className="h3 fw-bold mb-1">Create Class</h1>
              <p className="text-secondary mb-0">Set up a class for your students.</p>
            </div>

            {statusMessage ? (
              <StatusMessage
                message={statusMessage}
                type={statusType}
                className="CreateClassStatus mb-3"
              />
            ) : null}

            <form className="CreateClassForm row g-2 g-md-3 align-items-stretch" onSubmit={handleSubmit}>
              <div className="col-12 col-md">
                <label htmlFor="class-name" className="form-label fw-semibold">Class Name</label>
                <input
                  id="class-name"
                  type="text"
                  value={name}
                  onChange={(event) => setName(event.target.value)}
                  maxLength={100}
                  className="form-control form-control-lg"
                  placeholder="Example: COSC 404"
                  autoComplete="off"
                  required
                />
              </div>
              <div className="col-12 col-md-auto d-grid CreateClassSubmitCol">
                <button type="submit" className="btn btn-primary btn-lg">Submit</button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  )
}

