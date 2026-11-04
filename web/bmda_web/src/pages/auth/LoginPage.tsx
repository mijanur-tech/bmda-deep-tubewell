import { useState } from "react";
import type { FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { getCurrentUser, loginUser } from "../../api/auth.api";
import { removeAccessToken, saveAccessToken } from "../../auth/session";
import "./LoginPage.css";
import bmdaLogo from "../../assets/bmda-official-logo.png";

function LoginPage() {
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage("");
    setLoading(true);

    removeAccessToken();

    try {
      const loginResponse = await loginUser({ username, password });

      // Verify user identity and role before storing the token.
      const currentUser = await getCurrentUser(loginResponse.access_token);

      let destination: string;

      if (currentUser.role === "admin") {
        destination = "/admin/dashboard";
      } else if (currentUser.role === "assistant_engineer") {
        destination = "/ae/dashboard";
      } else if (currentUser.role === "supervisor") {
        destination = "/supervisor/dashboard";
      } else {
        setMessage("এই user role Web Application-এর জন্য অনুমোদিত নয়.");
        return;
      }

      saveAccessToken(loginResponse.access_token);
      navigate(destination, { replace: true });
    } catch (error) {
      removeAccessToken();

      if (error instanceof Error) {
        setMessage(error.message);
      } else {
        setMessage("Login failed.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="bmda-login-page">
      <div className="bmda-login-shell">
        <section className="bmda-login-intro" aria-label="BMDA system information">
          <div className="bmda-login-brand">
            <img className="bmda-login-mark bmda-login-logo" src={bmdaLogo} alt="BMDA official logo" />
            <div>
              <p className="bmda-login-brand-title">Barind Multipurpose Development Authority</p>
              <p className="bmda-login-brand-subtitle">Deep Tubewell Management System</p>
            </div>
          </div>
          <div className="bmda-login-intro-content">
            <span className="bmda-login-eyebrow">OFFICIAL MANAGEMENT PORTAL</span>
            <h1>Smarter management for every deep tubewell.</h1>
            <p>Secure access to operational records, field activities and management reports.</p>
            <div className="bmda-login-intro-note">
              <span className="bmda-login-note-dot" aria-hidden="true" />
              Authorized BMDA personnel only
            </div>
          </div>
          <p className="bmda-login-intro-footer">BMDA • Deep Tubewell Management</p>
        </section>

        <section className="bmda-login-form-panel" aria-label="Sign in">
          <div className="bmda-login-form-inner">
            <div className="bmda-login-mobile-brand">BMDA <span>Management Portal</span></div>
            <span className="bmda-login-form-eyebrow">WELCOME BACK</span>
            <h2>Sign in to your account</h2>
            <p className="bmda-login-form-description">Enter your authorized credentials to continue.</p>

            <form className="bmda-login-form" onSubmit={handleSubmit}>
              <div className="bmda-login-field">
                <label htmlFor="username">Username</label>
                <input
                  id="username"
                  name="username"
                  type="text"
                  autoComplete="username"
                  placeholder="Enter your username"
                  value={username}
                  onChange={(event) => setUsername(event.target.value)}
                  disabled={loading}
                  required
                />
              </div>
              <div className="bmda-login-field">
                <label htmlFor="password">Password</label>
                <div className="bmda-login-password-wrap">
                  <input
                    id="password"
                    name="password"
                    type={showPassword ? "text" : "password"}
                    autoComplete="current-password"
                    placeholder="Enter your password"
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    disabled={loading}
                    required
                  />
                  <button
                    type="button"
                    className="bmda-login-password-toggle"
                    onClick={() => setShowPassword((visible) => !visible)}
                    aria-label={showPassword ? "Hide password" : "Show password"}
                    aria-pressed={showPassword}
                  >
                    {showPassword ? "Hide" : "Show"}
                  </button>
                </div>
              </div>

              {message && <p className="bmda-login-error" role="alert">{message}</p>}

              <button className="bmda-login-submit" type="submit" disabled={loading}>
                {loading ? "Signing in..." : "Sign in"}
                {!loading && <span aria-hidden="true">→</span>}
              </button>
            </form>
            <p className="bmda-login-help">For account assistance, contact your BMDA administrator.</p>
          </div>
          <p className="bmda-login-form-footer">Secure organizational access</p>
        </section>
      </div>
    </main>
  );
}

export default LoginPage;
