import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import StatusMessage from '../components/StatusMessage';
import { changePassword } from '../util/api';
import './ChangePassword.css';

export default function ChangePassword() {
  const navigate = useNavigate();
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const handleChangePassword = async () => {
    try {
      setError('');
      setSuccess(false);

      if (!currentPassword || !newPassword || !confirmPassword) {
        setError('All fields are required');
        return;
      }

      if (newPassword !== confirmPassword) {
        setError('New passwords do not match');
        return;
      }

      if (newPassword.length < 6) {
        setError('New password must be at least 6 characters');
        return;
      }

      await changePassword(currentPassword, newPassword);
      setSuccess(true);
      
      // Redirect to home after 2 seconds
      setTimeout(() => {
        navigate('/home');
      }, 2000);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message || 'Failed to change password');
      } else {
        setError('Failed to change password');
      }
    }
  };

  return (
    <div className="ChangePasswordPage d-flex align-items-center justify-content-center min-vh-100 py-5">
      <div className="container">
        <div className="row justify-content-center">
          <div className="col-12 col-sm-10 col-md-8 col-lg-6 col-xl-5">
            <div className="card border-0 shadow-sm ChangePasswordCard">
              <div className="card-body p-4 p-md-5">
                <h1 className="h3 fw-bold mb-1">Change password</h1>
                <p className="text-secondary mb-4">
                  You must change your temporary password before continuing.
                </p>

                {error && <StatusMessage message={error} type="error" className="mb-3" />}
                {success && (
                  <StatusMessage
                    message="Password changed successfully! Redirecting..."
                    type="success"
                    className="mb-3"
                  />
                )}

                <form
                  onSubmit={(event) => {
                    event.preventDefault();
                    void handleChangePassword();
                  }}
                >
                  <div className="mb-3">
                    <label htmlFor="current-password" className="form-label fw-semibold">Current Password</label>
                    <input
                      id="current-password"
                      type="password"
                      className="form-control form-control-lg"
                      placeholder="Current password"
                      value={currentPassword}
                      onChange={(event) => setCurrentPassword(event.target.value)}
                      autoComplete="current-password"
                      required
                    />
                  </div>

                  <div className="mb-3">
                    <label htmlFor="new-password" className="form-label fw-semibold">New Password</label>
                    <input
                      id="new-password"
                      type="password"
                      className="form-control form-control-lg"
                      placeholder="New password"
                      value={newPassword}
                      onChange={(event) => setNewPassword(event.target.value)}
                      autoComplete="new-password"
                      required
                    />
                  </div>

                  <div className="mb-3">
                    <label htmlFor="confirm-new-password" className="form-label fw-semibold">Confirm New Password</label>
                    <input
                      id="confirm-new-password"
                      type="password"
                      className="form-control form-control-lg"
                      placeholder="Confirm new password"
                      value={confirmPassword}
                      onChange={(event) => setConfirmPassword(event.target.value)}
                      autoComplete="new-password"
                      required
                    />
                  </div>

                  <div className="d-grid gap-2 mt-4">
                    <button type="submit" className="btn btn-primary btn-lg" disabled={success}>
                      Change Password
                    </button>
                    <button
                      type="button"
                      className="btn btn-outline-secondary"
                      onClick={() => navigate('/')}
                      disabled={success}
                    >
                      Back to Login
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
