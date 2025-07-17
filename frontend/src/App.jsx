// src/App.jsx
import React from 'react';
// 1. Add BrowserRouter to the import
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
// 2. Import AuthProvider as well, not just useAuth
import { AuthProvider, useAuth } from './context/AuthContext';
import Navbar from './components/Navbar';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import FlightsPage from './pages/FlightsPage';
import NotFoundPage from './pages/NotFoundPage';

// Helper component for protected routes
function PrivateRoute({ children }) {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    // Optional: Render a loading indicator while auth status is being determined
    return <div className="loading-screen">Loading authentication...</div>;
  }

  // If not authenticated, redirect to login page
  return isAuthenticated ? children : <Navigate to="/login" replace />;
}

function App() {
  // We use useAuth inside PrivateRoute and potentially other components.
  // The App component itself doesn't directly consume isAuthenticated here,
  // but it needs to ensure AuthProvider wraps the router.

  return (
    // 3. Wrap everything in <Router>
    <Router>
      {/* 4. Wrap everything that uses authentication context in <AuthProvider> */}
      <AuthProvider>
        <Navbar /> {/* Navbar is outside of Routes because it's always present */}
        <main>
          <Routes>
            {/* Public Routes - Accessible without login, redirects if logged in */}
            <Route
              path="/login"
              element={<AuthRedirect component={LoginPage} />}
            />
            <Route
              path="/register"
              element={<AuthRedirect component={RegisterPage} />}
            />

            {/* Protected Routes - require authentication */}
            <Route
              path="/flights"
              element={
                <PrivateRoute>
                  <FlightsPage />
                </PrivateRoute>
              }
            />
            {/* The edit route should ideally render FlightForm in an overlay or a separate page,
                but for now, it can point to FlightsPage, which handles the form display. */}
            <Route
              path="/flights/edit/:flightId"
              element={
                <PrivateRoute>
                  <FlightsPage />
                </PrivateRoute>
              }
            />

            {/* Default Route: Redirect based on authentication status */}
            <Route path="/" element={<HomeRedirect />} />

            {/* Catch-all for undefined routes */}
            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </main>
      </AuthProvider>
    </Router>
  );
}

// Helper component to redirect logged-in users from login/register pages
function AuthRedirect({ component: Component }) {
  const { isAuthenticated, loading } = useAuth();
  if (loading) {
    return <div className="loading-screen">Loading...</div>;
  }
  return isAuthenticated ? <Navigate to="/flights" replace /> : <Component />;
}

// Helper component for the root path redirection
function HomeRedirect() {
  const { isAuthenticated, loading } = useAuth();
  if (loading) {
    return <div className="loading-screen">Loading...</div>;
  }
  return isAuthenticated ? <Navigate to="/flights" replace /> : <Navigate to="/login" replace />;
}


export default App;