import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import StatusMessage from '../components/StatusMessage';
import { createTeacherAccount } from '../util/api';
import './RegisterPage.css';

export default function CreateTeacher() {
  const navigate = useNavigate();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [createdTeacher, setCreatedTeacher] = useState<User | null>(null);

  const handleCreateTeacher = async () => {
    try {
      setError('');
      setSuccess(false);

      if (!name || !email || !password) {
        setError('All fields are required');
        return;
      }

      if (password.length < 6) {
        setError('Temporary password must be at least 6 characters');
        return;
      }

      const result = await createTeacherAccount(name, email, password);
      setCreatedTeacher(result.user);
      setSuccess(true);
      
      // Clear form
      setName('');
      setEmail('');
      setPassword('');
    } 
    catch (err: unknown) {
      const message = err instanceof Error ? err.message : '';
      const isDuplicateEmail = message.toLowerCase().includes('email');
      const isConflict = message.includes('409');

      console.log('Create teacher error:', { message });

      if (isConflict || isDuplicateEmail) {
        setError('Duplicate email address, please use a different email.');
      } else {
        setError('Failed to create teacher account');
      }
    }
  };

  return (
    <div className="RegisterPage d-flex align-items-center justify-content-center min-vh-100 py-5">
      <div className="container">
        <div className="row justify-content-center">
          <div className="col-12 col-sm-10 col-md-8 col-lg-6 col-xl-5">
            <div className="card border-0 shadow-sm RegisterCard">
              <div className="card-body p-4 p-md-5">
                <h1 className="h3 fw-bold mb-1">Create Teacher Account</h1>
                <p className="text-muted mb-3">
                  Create a new teacher account with a temporary password.
                </p>

                {error && <StatusMessage message={error} type="error" className="mb-3" />}

                {success && createdTeacher && (
                  <StatusMessage type="success" className="mb-3">
                    <div>
                      <strong>Teacher account created successfully!</strong>
                      <div className="small mt-2">
                        <div><strong>Name:</strong> {createdTeacher.name}</div>
                        <div><strong>Email:</strong> {createdTeacher.email}</div>
                        <div><strong>Temporary Password:</strong> (provided by you)</div>
                        <div className="mt-2 fst-italic">
                          The teacher will be prompted to change their password on first login.
                        </div>
                      </div>
                    </div>
                  </StatusMessage>
                )}

                <form
                  onSubmit={(event) => {
                    event.preventDefault();
                    void handleCreateTeacher();
                  }}
                >
                  <div className="mb-3">
                    <label htmlFor="create-teacher-name" className="form-label fw-semibold">Teacher Name</label>
                    <input
                      id="create-teacher-name"
                      type="text"
                      className="form-control form-control-lg"
                      placeholder="Full name"
                      value={name}
                      onChange={(event) => setName(event.target.value)}
                      autoComplete="name"
                      required
                    />
                  </div>

                  <div className="mb-3">
                    <label htmlFor="create-teacher-email" className="form-label fw-semibold">Institutional Email</label>
                    <input
                      id="create-teacher-email"
                      type="email"
                      className="form-control form-control-lg"
                      placeholder="teacher@institution.edu"
                      value={email}
                      onChange={(event) => setEmail(event.target.value.toLowerCase())}
                      autoComplete="email"
                      required
                    />
                  </div>

                  <div className="mb-3">
                    <label htmlFor="create-teacher-password" className="form-label fw-semibold">Temporary Password</label>
                    <input
                      id="create-teacher-password"
                      type="password"
                      className="form-control form-control-lg"
                      placeholder="Temporary password"
                      value={password}
                      onChange={(event) => setPassword(event.target.value)}
                      autoComplete="new-password"
                      required
                    />
                  </div>

                  <div className="d-grid gap-2 mt-4">
                    <button type="submit" className="btn btn-primary btn-lg">Create Teacher</button>
                    <button
                      type="button"
                      className="btn btn-outline-secondary"
                      onClick={() => navigate('/home')}
                    >
                      Cancel
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
