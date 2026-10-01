import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import api from "../lib/api";
import { useApi } from "../hooks/useApi";
import { useAuth } from "../context/useAuth";
import { DataTable, PageHeader } from "../components/Layout";

const dateTime = new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" });
const today = new Date();
const minDate = `${today.getFullYear()}-${String(today.getMonth()+1).padStart(2,"0")}-${String(today.getDate()).padStart(2,"0")}`;
const money = (amount) => `₹${Number(amount || 0).toLocaleString("en-IN", { maximumFractionDigits: 2 })}`;
const statusLabel = (status) => status?.replaceAll("_", " ") || "pending";

export function PatientDashboard() {
  const { user } = useAuth();
  const [now] = useState(() => Date.now());
  const { data: bookingPage, items: bookings, loading } = useApi("/bookings?limit=50");
  const { items: payments } = useApi("/payments/");
  const { items: centres } = useApi("/centres?limit=100");
  const { items: tests } = useApi("/tests?limit=100");
  const { items: offers } = useApi("/centre-tests?limit=100");
  const upcoming = bookings.filter((b) => Date.parse(b.appointment_at) > now && ["pending", "confirmed", "payment_failed"].includes(b.status));
  const spent = payments.filter((p) => p.status === "success").reduce((sum, p) => sum + Number(p.amount), 0);
  const catalog = Object.fromEntries(tests.map((test) => [test.id, test]));
  const centreById = Object.fromEntries(centres.map((centre) => [centre.id, centre]));
  const offerById = Object.fromEntries(offers.map((offer) => [offer.id, offer]));
  const rows = upcoming.slice(0, 5).map((booking) => {
    const offer = offerById[booking.centre_test_id];
    return { ...booking, test_name: catalog[offer?.test_id]?.name || "Diagnostic test", centre_name: centreById[offer?.centre_id]?.name || "Diagnostic centre" };
  });
  return <><PageHeader eyebrow="PATIENT DASHBOARD" title={`Welcome back, ${user?.full_name?.split(" ")[0] || "there"} 👋`} subtitle="Take care of your health, one step at a time." action={<Link className="primary-button" to="/app/book">＋ Book a test</Link>}/><div className="metric-grid"><Metric icon="▦" label="Upcoming appointments" value={upcoming.length}/><Metric icon="☷" label="Total bookings" value={bookingPage?.total ?? bookings.length}/><Metric icon="₹" label="Total spent" value={money(spent)}/></div><section className="quick-actions"><div className="section-title"><h2>Quick actions</h2></div><div className="quick-grid"><QuickAction to="/app/book" icon="▦" title="Book a test" text="Find tests and centres"/><QuickAction to="/centres" icon="⌖" title="Find nearby centres" text="Search by location"/><QuickAction to="/app/payments" icon="▤" title="Payment history" text="Review your payments"/><QuickAction to="/app/assistant" icon="✧" title="AI assistant" text="Learn health information"/></div></section><section className="panel dashboard-panel"><div className="section-title"><div><p className="eyebrow">YOUR CARE</p><h2>Upcoming appointments</h2></div><Link className="subtle-link" to="/app/bookings">View all →</Link></div>{loading ? <p className="muted">Loading appointments…</p> : <DataTable columns={[{key:"test_name",label:"Test"},{key:"centre_name",label:"Centre"},{key:"appointment_at",label:"Date & time",render:(b)=>dateTime.format(new Date(b.appointment_at))},{key:"status",label:"Status",render:(b)=><span className={`status-pill status-${b.status}`}>{statusLabel(b.status)}</span>},{key:"actions",label:"",render:(b)=>b.status==="pending"||b.status==="payment_failed"?<Link className="text-button" to={`/app/payments?booking=${b.id}`}>Pay now →</Link>:<Link className="text-button" to="/app/bookings">Details</Link>}]} rows={rows} empty="No upcoming visits. Book your first diagnostic test."/>}</section></>;
}

function Metric({ icon, label, value }) { return <article className="metric-card"><span className="metric-icon">{icon}</span><div><small>{label}</small><b>{value}</b></div></article>; }
function QuickAction({ to, icon, title, text }) { return <Link className="quick-card" to={to}><span>{icon}</span><b>{title}</b><small>{text}</small><i>↗</i></Link>; }

export function PatientBookings() {
  const [status, setStatus] = useState("");
  const [refresh, setRefresh] = useState(0);
  const path = `/bookings?limit=100${status ? `&booking_status=${status}` : ""}`;
  const { items: bookings, loading, error } = useApi(path, refresh);
  const { items: offers } = useApi("/centre-tests?limit=100");
  const { items: centres } = useApi("/centres?limit=100");
  const { items: tests } = useApi("/tests?limit=100");
  const byOffer = Object.fromEntries(offers.map((offer)=>[offer.id,offer]));
  const byCentre = Object.fromEntries(centres.map((centre)=>[centre.id,centre]));
  const byTest = Object.fromEntries(tests.map((test)=>[test.id,test]));
  const rows = bookings.map((booking)=>{const offer=byOffer[booking.centre_test_id];return {...booking,test_name:byTest[offer?.test_id]?.name||"Diagnostic test",centre_name:byCentre[offer?.centre_id]?.name||"Diagnostic centre"};});
  const cancel = async (booking) => { if (!window.confirm("Cancel this unpaid appointment?")) return; try { await api.patch(`/bookings/${booking.id}/cancel`); setRefresh(refresh+1); } catch (e) { window.alert(e.response?.data?.detail || "Could not cancel this appointment."); } };
  return <><PageHeader eyebrow="YOUR CARE" title="My bookings" subtitle="Review appointment times and booking status." action={<Link className="primary-button" to="/app/book">＋ Book a test</Link>}/><div className="filter-row"><label>Show <select value={status} onChange={(e)=>setStatus(e.target.value)}><option value="">All bookings</option>{["pending","confirmed","payment_failed","cancelled","completed"].map((s)=><option key={s} value={s}>{statusLabel(s)}</option>)}</select></label></div>{error && <div className="notice error">{error}</div>}{loading ? <p>Loading bookings…</p> : <DataTable columns={[{key:"test_name",label:"Test"},{key:"centre_name",label:"Centre"},{key:"appointment_at",label:"Appointment",render:(b)=>dateTime.format(new Date(b.appointment_at))},{key:"amount",label:"Amount",render:(b)=>money(b.amount)},{key:"status",label:"Status",render:(b)=><span className={`status-pill status-${b.status}`}>{statusLabel(b.status)}</span>},{key:"action",label:"Actions",render:(b)=><div className="table-actions">{["pending","payment_failed"].includes(b.status)&&<Link className="text-button" to={`/app/payments?booking=${b.id}`}>Pay</Link>}{["pending","payment_failed"].includes(b.status)&&<button className="text-button danger-text" onClick={()=>cancel(b)}>Cancel</button>}</div>}]} rows={rows} empty="You have no bookings yet."/>}</>;
}

export function BookingWizard() {
  const [params] = useSearchParams();
  const [centreId, setCentreId] = useState(params.get("centre") || "");
  const [testId, setTestId] = useState(params.get("test") || "");
  const [day, setDay] = useState("");
  const [time, setTime] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();
  const { items: centres } = useApi("/centres?limit=100");
  const { items: tests } = useApi("/tests?limit=100");
  const { items: offers } = useApi(centreId ? `/centre-tests?centre_id=${centreId}&limit=100` : "/centre-tests?limit=1");
  const test = tests.find((item)=>item.id===testId);
  const offer = offers.find((item)=>item.test_id===testId);
  const centre = centres.find((item)=>item.id===centreId);
  const submit = async (event) => {
    event.preventDefault(); setBusy(true); setError("");
    try {
      if (!offer) throw new Error("Choose a test currently available at this centre.");
      const appointmentAt = new Date(`${day}T${time}`).toISOString();
      const booking = await api.post("/bookings", { centre_test_id: offer.id, appointment_at: appointmentAt });
      navigate(`/app/payments?booking=${booking.data.id}`);
    } catch (exception) { setError(exception.response?.data?.detail || exception.message || "Could not create this appointment."); }
    finally { setBusy(false); }
  };
  return <><PageHeader eyebrow="BOOK AN APPOINTMENT" title="Choose a time that works for you" subtitle="Your appointment is held as pending until payment is verified."/><form className="wizard-card" onSubmit={submit}><div className="wizard-steps"><span className="step-active">1 <small>Centre</small></span><i/><span className={centreId?"step-active":""}>2 <small>Test</small></span><i/><span className={testId?"step-active":""}>3 <small>Date & time</small></span><i/><span>4 <small>Confirm</small></span></div><div className="form-grid"><label>Diagnostic centre<select required value={centreId} onChange={(e)=>{setCentreId(e.target.value);setTestId("");}}><option value="">Select a centre</option>{centres.map((c)=><option key={c.id} value={c.id}>{c.name} · {c.city}</option>)}</select></label><label>Diagnostic test<select required value={testId} onChange={(e)=>setTestId(e.target.value)} disabled={!centreId}><option value="">Select a test</option>{offers.map((item)=>{const t=tests.find((x)=>x.id===item.test_id);return t?<option key={item.id} value={t.id}>{t.name} · ₹{Number(item.price).toFixed(0)}</option>:null;})}</select></label><label>Appointment date<input type="date" min={minDate} value={day} required onChange={(e)=>setDay(e.target.value)}/></label><label>Time<select required value={time} onChange={(e)=>setTime(e.target.value)}><option value="">Choose a time</option>{["09:00","10:00","11:00","12:00","14:00","15:00","16:00"].map((t)=><option key={t} value={t}>{new Date(`2000-01-01T${t}`).toLocaleTimeString([], {hour:"numeric",minute:"2-digit"})}</option>)}</select></label></div>{centre&&test&&<div className="order-preview"><span>Booking summary</span><b>{test.name} · {centre.name}</b><span>Price <strong>₹{Number(offer?.price||0).toFixed(2)}</strong></span></div>}{error&&<div className="notice error">{error}</div>}<div className="form-actions"><Link className="outline-button" to="/centres">Back to centres</Link><button className="primary-button" disabled={busy||!offer}>{busy?"Creating booking…":"Continue to payment →"}</button></div></form></>;
}

function loadCheckoutScript() {
  return new Promise((resolve) => {
    if (window.Razorpay) { resolve(true); return; }
    const script = document.createElement("script");
    script.src = "https://checkout.razorpay.com/v1/checkout.js";
    script.onload = () => resolve(true); script.onerror = () => resolve(false); document.body.appendChild(script);
  });
}

export function PaymentsPage() {
  const [params] = useSearchParams();
  const [refresh, setRefresh] = useState(0);
  const [message, setMessage] = useState("");
  const [busyId, setBusyId] = useState("");
  const { items: payments, error, loading } = useApi("/payments/", refresh);
  const { items: bookings } = useApi("/bookings?limit=100", refresh);
  const { user } = useAuth();
  const selectedBooking = params.get("booking");
  const pay = async (booking) => {
    setBusyId(booking.id); setMessage("");
    try {
      const sdkReady = await loadCheckoutScript();
      if (!sdkReady) throw new Error("Secure payment checkout did not load. Check your connection and try again.");
      const order = await api.post("/payments/", { booking_id: booking.id, idempotency_key: crypto.randomUUID() });
      const payment = order.data;
      if (!payment.razorpay_key_id) throw new Error("Razorpay public key is not configured.");
      const checkout = new window.Razorpay({
        key: payment.razorpay_key_id,
        amount: Math.round(Number(payment.amount) * 100),
        currency: payment.currency || "INR",
        name: "EVE Healthcare",
        description: `Booking ${booking.id.slice(0, 8)}`,
        order_id: payment.razorpay_order_id,
        handler: async (result) => {
          try { await api.post("/payments/verify", result); setMessage("Payment verified. Your appointment is confirmed."); setRefresh((value)=>value+1); }
          catch (e) { setMessage(e.response?.data?.detail || "Payment confirmation is processing. Refresh your booking shortly."); }
        },
        prefill: { name: user?.full_name || "", email: user?.email || "" },
        theme: { color: "#078d69" },
        modal: { ondismiss: () => setMessage("Payment was not completed. You can retry from this page.") },
      });
      checkout.open();
    } catch (e) { setMessage(e.response?.data?.detail || e.message || "Could not start payment."); }
    finally { setBusyId(""); }
  };
  const eligible = bookings.filter((b)=>["pending","payment_failed"].includes(b.status));
  const list = selectedBooking ? eligible.filter((b)=>b.id===selectedBooking) : eligible;
  return <><PageHeader eyebrow="PAYMENTS" title="Payment history" subtitle="Payments are confirmed by Razorpay signature verification or a verified webhook."/><div className="panel payment-eligible"><div className="section-title"><div><p className="eyebrow">ACTION NEEDED</p><h2>Complete a payment</h2></div></div>{message&&<div className="notice success">{message}</div>}{list.map((booking)=><article className="pay-booking" key={booking.id}><div className="payment-symbol">₹</div><div><b>Diagnostic appointment</b><p>{dateTime.format(new Date(booking.appointment_at))} · {statusLabel(booking.status)}</p><small>Booking {booking.id.slice(0,8)}</small></div><strong>{money(booking.amount)}</strong><button className="primary-button" disabled={busyId===booking.id} onClick={()=>pay(booking)}>{busyId===booking.id?"Starting…":"Pay securely"}</button></article>)}{!list.length&&<p className="muted">No payments need action.</p>}</div><section className="panel dashboard-panel"><div className="section-title"><div><p className="eyebrow">TRANSACTIONS</p><h2>Previous payments</h2></div></div>{error&&<div className="notice error">{error}</div>}{loading?<p>Loading payments…</p>:<DataTable columns={[{key:"created_at",label:"Date",render:(p)=>dateTime.format(new Date(p.created_at))},{key:"booking_id",label:"Booking",render:(p)=>p.booking_id.slice(0,8)},{key:"attempt_number",label:"Attempt"},{key:"amount",label:"Amount",render:(p)=>money(p.amount)},{key:"status",label:"Status",render:(p)=><span className={`status-pill status-${p.status}`}>{statusLabel(p.status)}</span>}]} rows={payments} empty="No payment records yet."/>}</section>{bookings.filter((b)=>payments.some((p)=>p.booking_id===b.id&&p.status==="failed")).length>0&&<p className="muted">A failed payment can be retried while your booking remains eligible.</p>}</>;
}

export function ProfilePage() {
  const { user, refresh } = useAuth();
  const [name, setName] = useState(user?.full_name || "");
  const [message, setMessage] = useState("");
  const save = async (e) => { e.preventDefault(); try { await api.patch("/auth/me", { full_name: name }); await refresh(); setMessage("Profile updated."); } catch (error) { setMessage(error.response?.data?.detail || "Could not update profile."); } };
  return <><PageHeader eyebrow="YOUR ACCOUNT" title="Profile" subtitle="Keep your account details up to date."/><form className="panel profile-form" onSubmit={save}><label>Full name<input maxLength={255} value={name} onChange={(e)=>setName(e.target.value)}/></label><label>Email address<input value={user?.email || ""} disabled/></label><label>Account type<input value={user?.role || "patient"} disabled/></label>{message&&<div className="notice success">{message}</div>}<button className="primary-button">Save profile</button></form></>;
}
