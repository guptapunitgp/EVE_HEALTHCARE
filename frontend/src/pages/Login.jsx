import { useState } from "react";
import { createUserWithEmailAndPassword, sendEmailVerification, sendPasswordResetEmail, signInWithEmailAndPassword, signInWithPopup, updateProfile } from "firebase/auth";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { auth, googleProvider } from "../firebase";
import api from "../lib/api";
import { useAuth } from "../context/useAuth";

function Login() {
  const [mode, setMode] = useState("signin");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const navigate = useNavigate();
  const location = useLocation();
  const { acceptSession } = useAuth();

  const finishSignIn = async (firebaseUser) => {
    const response = await api.post("/auth/firebase", { id_token: await firebaseUser.getIdToken(true) });
    acceptSession(response.data);
    const rolePath = response.data.user.role === "admin" ? "/admin" : response.data.user.role === "staff" ? "/staff" : "/app";
    const requested = location.state?.from;
    navigate(requested?.startsWith("/app") && response.data.user.role === "patient" ? requested : rolePath, { replace: true });
  };

  const handleEmail = async (event) => {
    event.preventDefault(); setBusy(true); setError(""); setNotice("");
    try {
      if (!auth) throw new Error("Firebase is not configured. Add your Firebase web app settings to the frontend environment file.");
      if (mode === "signup") {
        const credential = await createUserWithEmailAndPassword(auth, email, password);
        if (name.trim()) await updateProfile(credential.user, { displayName: name.trim() });
        await sendEmailVerification(credential.user);
        setNotice("Check your inbox to verify your email, then return here to sign in.");
        setMode("signin");
      } else {
        const credential = await signInWithEmailAndPassword(auth, email, password);
        await finishSignIn(credential.user);
      }
    } catch (exception) {
      const messages = {
        "auth/email-already-in-use": "An account with this email already exists.",
        "auth/invalid-credential": "Email or password is incorrect.",
        "auth/weak-password": "Use a password with at least 6 characters.",
        "auth/too-many-requests": "Too many attempts. Wait a moment and try again.",
      };
      setError(messages[exception.code] || exception.response?.data?.detail || exception.message || "Could not sign in. Please try again.");
    } finally { setBusy(false); }
  };

  const handleGoogle = async () => {
    setBusy(true); setError(""); setNotice("");
    try {
      if (!auth || !googleProvider) throw new Error("Firebase is not configured. Add your Firebase web app settings to the frontend environment file.");
      const result = await signInWithPopup(auth, googleProvider);
      await finishSignIn(result.user);
    } catch (exception) {
      setError(exception.response?.data?.detail || exception.message || "Google sign in could not be completed.");
    } finally { setBusy(false); }
  };

  const resetPassword = async () => {
    if (!auth || !email) { setError("Enter your email address first."); return; }
    try { await sendPasswordResetEmail(auth, email); setNotice("Password reset instructions have been sent to your email."); setError(""); }
    catch { setError("Could not send a reset email. Check the address and try again."); }
  };

  return <main className="auth-page">
    <section className="auth-form-panel">
      <Link className="brand" to="/">♡ <b>EVE Healthcare</b></Link>
      <div className="auth-card">
        <p className="eyebrow">{mode === "signup" ? "START YOUR CARE JOURNEY" : "WELCOME BACK"}</p>
        <h1>{mode === "signup" ? "Create your account" : "Your health, in good hands."}</h1>
        <p className="muted">{mode === "signup" ? "Create a secure account to book and manage your tests." : "Sign in to find centres, book tests and manage appointments."}</p>
        <button className="google-button" onClick={handleGoogle} disabled={busy}><span className="google-mark">G</span>Continue with Google</button>
        <div className="auth-divider"><span>or continue with email</span></div>
        <form onSubmit={handleEmail} className="form-stack">
          {mode === "signup" && <label>Full name<input autoComplete="name" value={name} onChange={(e) => setName(e.target.value)} required maxLength={255} placeholder="Your name" /></label>}
          <label>Email address<input type="email" autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} required placeholder="you@example.com" /></label>
          <label>Password<input type="password" autoComplete={mode === "signup" ? "new-password" : "current-password"} value={password} onChange={(e) => setPassword(e.target.value)} required minLength={6} placeholder="At least 6 characters" /></label>
          {mode === "signin" && <button type="button" className="text-button forgot" onClick={resetPassword}>Forgot password?</button>}
          {notice && <div className="notice success" role="status">{notice}</div>}
          {error && <div className="notice error" role="alert">{error}</div>}
          <button className="primary-button full" type="submit" disabled={busy}>{busy ? "Please wait…" : mode === "signup" ? "Create account" : "Sign in"}</button>
        </form>
        <p className="auth-toggle">{mode === "signup" ? "Already have an account?" : "Don't have an account?"} <button className="text-button" onClick={() => { setMode(mode === "signup" ? "signin" : "signup"); setError(""); setNotice(""); }}>{mode === "signup" ? "Sign in" : "Sign up"}</button></p>
        <small className="auth-legal">By continuing, you agree to EVE Healthcare's terms and privacy notice.</small>
      </div>
      <div className="auth-bottom">© 2026 EVE Healthcare <span>Care for your whole journey.</span></div>
    </section>
    <aside className="auth-art"><div className="art-orb orb-a"/><div className="art-orb orb-b"/><div className="art-cross">✚</div><div className="auth-art-copy"><span>THOUGHTFUL CARE, EVERY DAY</span><h2>Your health<br/>journey starts here.</h2><p>Trusted diagnostic centres, secure bookings, and thoughtful support in one place.</p><div className="art-stats"><span>✦ Trusted centres</span><span>♡ Easy booking</span><span>⌖ Care nearby</span></div></div></aside>
  </main>;
}

export default Login;
