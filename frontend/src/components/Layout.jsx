import { Link, NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../context/useAuth";

const patientLinks = [["/app", "⌂", "Dashboard"], ["/app/bookings", "▦", "My bookings"], ["/centres", "⌖", "Find centres"], ["/tests", "✚", "Test catalogue"], ["/app/payments", "▤", "Payment history"], ["/app/assistant", "✧", "AI assistant"], ["/app/profile", "◉", "Profile"]];
const staffLinks = [["/staff", "⌂", "Dashboard"], ["/staff/centres", "⌖", "My centre"], ["/staff/tests", "✚", "Test management"], ["/staff/bookings", "▦", "Bookings"], ["/staff/reports", "▤", "Reports"]];
const adminLinks = [["/admin", "⌂", "Overview"], ["/admin/users", "◉", "Users"], ["/admin/centres", "⌖", "Diagnostic centres"], ["/admin/tests", "✚", "Tests"], ["/admin/bookings", "▦", "Bookings"], ["/admin/audit", "◷", "Audit log"], ["/admin/notifications", "♧", "Notifications"]];

export function PublicHeader() {
  const { user, signOut } = useAuth();
  return <header className="site-header"><Link className="brand" to="/">♡ <b>EVE Healthcare</b></Link><nav><NavLink to="/">Home</NavLink><NavLink to="/centres">Diagnostic Centres</NavLink><NavLink to="/tests">Tests</NavLink><a href="/#about">About</a><a href="/#contact">Contact</a></nav><div className="header-actions">{user ? <><Link className="login-link" to={user.role === "admin" ? "/admin" : user.role === "staff" ? "/staff" : "/app"}>Dashboard</Link><button className="text-button" onClick={signOut}>Sign out</button></> : <><Link className="login-link" to="/login">Login</Link><Link className="primary-button" to="/login">Get started</Link></>}</div></header>;
}

export function DashboardLayout({ kind = "patient" }) {
  const { user, signOut } = useAuth();
  const links = kind === "admin" ? adminLinks : kind === "staff" ? staffLinks : patientLinks;
  const base = kind === "admin" ? "EVE Platform" : kind === "staff" ? "Centre Workspace" : "My Healthcare";
  return <div className="dashboard-shell"><aside className="sidebar"><Link className="brand" to="/">♡ <b>EVE Healthcare</b></Link><div className="sidebar-label">{base}</div><nav>{links.map(([to, icon, label]) => <NavLink key={to} end={to === "/app" || to === "/admin" || to === "/staff"} to={to}><span>{icon}</span>{label}</NavLink>)}</nav><div className="sidebar-bottom"><div className="mini-avatar">{user?.full_name?.[0] || user?.email?.[0] || "E"}</div><div className="sidebar-user"><b>{user?.full_name || user?.email}</b><small>{kind === "admin" ? "Administrator" : kind === "staff" ? "Centre staff" : "Patient"}</small></div><button title="Sign out" className="icon-button" onClick={signOut}>↗</button></div></aside><main className="dashboard-content"><div className="mobile-dashboard-bar"><Link className="brand" to="/">♡ EVE</Link><button className="outline-button" onClick={signOut}>Sign out</button></div><nav className="mobile-bottom-nav">{links.map(([to,icon,label])=><NavLink key={to} to={to} end={to==="/app"||to==="/staff"||to==="/admin"}><span>{icon}</span><small>{label}</small></NavLink>)}</nav><Outlet /></main></div>;
}

export function PageHeader({ eyebrow, title, subtitle, action }) {
  return <div className="page-heading"><div><p className="eyebrow">{eyebrow}</p><h1>{title}</h1>{subtitle && <p className="muted">{subtitle}</p>}</div>{action}</div>;
}

export function DataTable({ columns, rows, empty = "Nothing to show yet." }) {
  if (!rows?.length) return <div className="empty-state"><span>♡</span><b>{empty}</b></div>;
  return <div className="table-wrap"><table><thead><tr>{columns.map((col) => <th key={col.key}>{col.label}</th>)}</tr></thead><tbody>{rows.map((row, i) => <tr key={row.id || i}>{columns.map((col) => <td key={col.key}>{col.render ? col.render(row) : row[col.key]}</td>)}</tr>)}</tbody></table></div>;
}
