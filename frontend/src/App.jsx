import { Navigate, Outlet, Route, Routes, useLocation } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext.jsx";
import { useAuth } from "./context/useAuth";
import { DashboardLayout } from "./components/Layout";
import Login from "./pages/Login";
import Home, { CentreDetailPage, CentresPage, TestsPage } from "./pages/Public";
import { BookingWizard, PaymentsPage, PatientBookings, PatientDashboard, ProfilePage } from "./pages/Patient";
import AssistantPage from "./pages/Assistant";
import StaffWorkspace from "./pages/Staff";
import AdminWorkspace from "./pages/Admin";

function RequireAuth() {
  const { user, loading } = useAuth();
  const location = useLocation();
  if (loading) return <main className="auth-loading"><span className="loading-mark">♡</span><p>Loading your secure EVE account…</p></main>;
  return user ? <Outlet/> : <Navigate to="/login" state={{from:location.pathname+location.search}} replace/>;
}

function RequireRoles({ roles }) {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace/>;
  if (!roles.includes(user.role)) return <Navigate to={user.role === "admin" ? "/admin" : user.role === "staff" ? "/staff" : "/app"} replace/>;
  return <Outlet/>;
}

function AppRoutes() {
  const { user } = useAuth();
  const homeForUser = user?.role === "admin" ? "/admin" : user?.role === "staff" ? "/staff" : "/app";
  return <Routes>
    <Route path="/" element={<Home/>}/>
    <Route path="/centres" element={<CentresPage/>}/>
    <Route path="/centres/:centreId" element={<CentreDetailPage/>}/>
    <Route path="/tests" element={<TestsPage/>}/>
    <Route path="/login" element={user?<Navigate to={homeForUser} replace/>:<Login/>}/>
    <Route element={<RequireAuth/>}>
      <Route element={<RequireRoles roles={["patient","admin"]}/> }>
        <Route element={<DashboardLayout kind="patient"/>}>
          <Route path="/app" element={<PatientDashboard/>}/>
          <Route path="/app/bookings" element={<PatientBookings/>}/>
          <Route path="/app/book" element={<BookingWizard/>}/>
          <Route path="/app/payments" element={<PaymentsPage/>}/>
          <Route path="/app/profile" element={<ProfilePage/>}/>
          <Route path="/app/assistant" element={<AssistantPage/>}/>
        </Route>
      </Route>
      <Route element={<RequireRoles roles={["staff","admin"]}/> }>
        <Route element={<DashboardLayout kind="staff"/>}>
          <Route path="/staff" element={<StaffWorkspace/>}/>
          <Route path="/staff/centres" element={<StaffWorkspace/>}/>
          <Route path="/staff/tests" element={<StaffWorkspace/>}/>
          <Route path="/staff/bookings" element={<StaffWorkspace/>}/>
          <Route path="/staff/reports" element={<StaffWorkspace/>}/>
        </Route>
      </Route>
      <Route element={<RequireRoles roles={["admin"]}/> }>
        <Route element={<DashboardLayout kind="admin"/>}>
          <Route path="/admin" element={<AdminWorkspace/>}/>
          <Route path="/admin/users" element={<AdminWorkspace/>}/>
          <Route path="/admin/centres" element={<AdminWorkspace/>}/>
          <Route path="/admin/tests" element={<AdminWorkspace/>}/>
          <Route path="/admin/bookings" element={<AdminWorkspace/>}/>
          <Route path="/admin/audit" element={<AdminWorkspace/>}/>
          <Route path="/admin/notifications" element={<AdminWorkspace/>}/>
        </Route>
      </Route>
    </Route>
    <Route path="*" element={<Navigate to={user?homeForUser:"/"} replace/>}/>
  </Routes>;
}

export default function App() {
  return <AuthProvider><AppRoutes/></AuthProvider>;
}
