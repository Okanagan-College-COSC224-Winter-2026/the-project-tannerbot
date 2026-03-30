import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Button from '../components/Button';
import Textbox from '../components/Textbox';
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

    if (newPassword.length < 8) {
      setError('Password must be at least 8 characters long');
      return;
    }

    if (!/[A-Z]/.test(newPassword)) {
      setError('Password must contain at least one uppercase letter');
      return;
    }

    if (!/[a-z]/.test(newPassword)) {
      setError('Password must contain at least one lowercase letter');
      return;
    }

    if (!/[0-9]/.test(newPassword)) {
      setError('Password must contain at least one number');
      return;
    }

    if (!/[!@#$%^&*(),.?":{}|<>]/.test(newPassword)) {
      setError('Password must contain at least one special character');
      return;
    }

    await changePassword(currentPassword, newPassword);
    setSuccess(true);

    setTimeout(() => {
      navigate('/home');
    }, 2000);

  } catch (err) {
    setError(err instanceof Error ? err.message : 'An error occurred. Please try again.');

    setTimeout(() => {
      setError('');
    }, 10000);
  }
};

  return (
    <div className="LoginPage">
      <div className="LoginBlock">
        <h1>Change Password</h1>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '1rem' }}>
          You must change your temporary password before continuing.
        </p>

        <StatusMessage message={error} type="error" />
        {success && (
          <StatusMessage 
            message="Password changed successfully! Redirecting..." 
            type="success" 
          />
        )}

        <div className="LoginInner">
          <div className="LoginInputs">
            <div className="LoginInputChunk">
              <span>Current Password</span>
              <Textbox
                type='password'
                placeholder='Current password...'
                onInput={setCurrentPassword}
                className='LoginInput'
              />
            </div>

            <div className="LoginInputChunk">
              <span>New Password</span>
              <Textbox
                type='password'
                placeholder='New password...'
                onInput={setNewPassword}
                className='LoginInput'
              />
            </div>

            <div className="LoginInputChunk">
              <span>Confirm New Password</span>
              <Textbox
                type='password'
                placeholder='Confirm new password...'
                onInput={setConfirmPassword}
                className='LoginInput'
              />
            </div>
          </div>
        </div>

        <div>
          <Button
            onClick={handleChangePassword}
            disabled={success}
          >
            Change Password
          </Button>
        </div>
      </div>
    </div>
  );
}
