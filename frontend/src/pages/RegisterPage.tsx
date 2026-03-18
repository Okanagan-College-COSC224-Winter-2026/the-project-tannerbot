import { useState } from 'react';
import './RegisterPage.css';
import StatusMessage from '../components/StatusMessage';
import { tryRegister } from '../util/api';
import { useNavigate } from 'react-router-dom';

export default function RegisterPage() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const navigate = useNavigate();
  const [error, setError] = useState('');

  
  const attemptRegister = async () => {
    // Check for empty fields first
    if (!name || !email || !password || !confirmPassword) {
      setError('Incomplete data');
      return;
    }

    // Passwords match check
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    // Email format check
    const emailRegex = /^[\w.-]+@[\w.-]+\.\w+$/;
    if (!emailRegex.test(email)) {
      setError('Invalid email format');
      return;
    }

    // Password strength check
    const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*(),.?":{}|<>]).{8,}$/;
    if (!passwordRegex.test(password)) {
      setError(
        'Password must be at least 8 characters, include one uppercase, one lowercase, one number, and one special character'
      );
      return;
    }

    // Clear any previous errors before trying
    setError('');

    try {
      await tryRegister(name, email, password);
      navigate('/');
    } catch {
      setError('Registration failed. Please try again.');
    }
  };

  return (
    <div className="RegisterPage d-flex align-items-center justify-content-center min-vh-100 py-5">
      <div className="container">
        <div className="row justify-content-center">
          <div className="col-12 col-sm-10 col-md-8 col-lg-6 col-xl-5">
            <div className="card border-0 shadow-sm RegisterCard">
              <div className="card-body p-4 p-md-5">
                <h1 className="h3 fw-bold mb-1">Create Account</h1>

                {error && <StatusMessage message={error} type="error" className="RegisterError mb-3" />}

                <form
                  onSubmit={(event) => {
                    event.preventDefault();
                    void attemptRegister();
                  }}
                >
                  <div className="mb-3">
                    <label htmlFor="register-name" className="form-label fw-semibold">Name</label>
                    <input
                      id="register-name"
                      type="text"
                      className="form-control form-control-lg"
                      placeholder="Your full name"
                      value={name}
                      onChange={(event) => setName(event.target.value)}
                      autoComplete="name"
                      required
                    />
                  </div>

                  <div className="mb-3">
                    <label htmlFor="register-email" className="form-label fw-semibold">Email</label>
                    <input
                      id="register-email"
                      type="email"
                      className="form-control form-control-lg"
                      placeholder="name@school.edu"
                      value={email}
                      onChange={(event) => setEmail(event.target.value)}
                      autoComplete="email"
                      required
                    />
                  </div>

                  <div className="mb-3">
                    <label htmlFor="register-password" className="form-label fw-semibold">Password</label>
                    <input
                      id="register-password"
                      type="password"
                      className="form-control form-control-lg"
                      placeholder="Create a strong password"
                      value={password}
                      onChange={(event) => setPassword(event.target.value)}
                      autoComplete="new-password"
                      required
                    />
                  </div>

                  <div className="mb-3">
                    <label htmlFor="register-confirm-password" className="form-label fw-semibold">Confirm Password</label>
                    <input
                      id="register-confirm-password"
                      type="password"
                      className="form-control form-control-lg"
                      placeholder="Confirm your password"
                      value={confirmPassword}
                      onChange={(event) => setConfirmPassword(event.target.value)}
                      autoComplete="new-password"
                      required
                    />
                  </div>

                  <div className="d-grid gap-2 mt-4">
                    <button type="submit" className="btn btn-primary btn-lg">Register</button>
                    <button
                      type="button"
                      className="btn btn-outline-secondary"
                      onClick={() => navigate('/')}
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