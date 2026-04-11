import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './LoginPage.css';
import StatusMessage from '../components/StatusMessage';
import { tryLogin } from '../util/api';

export default function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const attemptLogin = async () => {
  setError('');

  try {
    const result = await tryLogin(email, password);

    if (result) {
      // Regex: at least 8 chars, one uppercase, one lowercase, one number, one special char
      const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*(),.?":{}|<>]).{8,}$/;

      // If password doesn't meet requirements → force change
      if (!passwordRegex.test(password)) {
        navigate('/change-password');
        return;
      }

      // Otherwise check backend flag
      if (result.must_change_password) {
        navigate('/change-password');
      } else {
        navigate('/home');
      }
    } else {
      setError('Invalid email or password');
    }
  } catch (err) {
    if (err instanceof Error) {
      const normalized = err.message.toLowerCase();
      if (normalized.includes('too many')) {
        setError(err.message);
        return;
      }
      if (normalized.includes('login failed with status')) {
        setError('Unable to log in right now. Please try again shortly.');
        return;
      }
    }
    setError('Invalid email or password');
  }
};

  return (
    <div className="LoginPage d-flex align-items-center justify-content-center min-vh-100 py-5">
      <div className="container">
        <div className="row justify-content-center">
          <div className="col-12 col-sm-10 col-md-8 col-lg-6 col-xl-5">
            <div className="card border-0 shadow-sm LoginCard">
              <div className="card-body p-4 p-md-5">
                <h1 className="h3 fw-bold mb-1">Welcome Back</h1>
                <p className="text-secondary mb-4">Sign in to your account to continue</p>

                {error && <StatusMessage message={error} type="error" className="LoginError mb-3" />}

                <form
                  onSubmit={(event) => {
                    event.preventDefault();
                    void attemptLogin();
                  }}
                >
                  <div className="mb-3">
                    <label htmlFor="login-email" className="form-label fw-semibold">Email</label>
                    <input
                      id="login-email"
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
                    <label htmlFor="login-password" className="form-label fw-semibold">Password</label>
                    <input
                      id="login-password"
                      type="password"
                      className="form-control form-control-lg"
                      placeholder="Enter your password"
                      value={password}
                      onChange={(event) => setPassword(event.target.value)}
                      autoComplete="current-password"
                      required
                    />
                  </div>

                  <div className="d-grid gap-2 mt-4">
                    <button type="submit" className="btn btn-primary btn-lg">Login</button>
                    <button
                      type="button"
                      className="btn btn-outline-secondary"
                      onClick={() => navigate('/register')}
                    >
                      Register
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
