import React from "react";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from "react-router-dom";
import { Toaster } from "react-hot-toast";
import Landing from "./pages/Landing";
import Dashboard from "./pages/Dashboard";
import Files from "./pages/Files";
import AuthCallback from "./pages/AuthCallback"; // New import
import Duplicates from "./pages/Duplicates";
import Settings from "./pages/Settings";
import Accounts from "./pages/Accounts"; // Import the new Accounts component
import LargeFiles from "./pages/LargeFiles"; // Import the new LargeFiles component
import Login from "./pages/Login"; // Import Login component
import Register from "./pages/Register"; // Import Register component
import ForgotPassword from "./pages/ForgotPassword"; // Import ForgotPassword component
import ResetPassword from "./pages/ResetPassword"; // Import ResetPassword component
import Layout from "./components/Layout";
import "./App.css";

function App() {
  return (
    <Router>
      <div className="App">
        <Toaster position="top-right" />
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />
          <Route path="/reset-password" element={<ResetPassword />} />
          <Route path="/auth/success" element={<AuthCallback />} />{" "}
          {/* Corrected path */}
          {/* All Routes - No Authentication Required */}
          <Route
            path="/dashboard"
            element={
              <Layout>
                <Dashboard />
              </Layout>
            }
          />
          <Route
            path="/files"
            element={
              <Layout>
                <Files />
              </Layout>
            }
          />
          <Route
            path="/duplicates"
            element={
              <Layout>
                <Duplicates />
              </Layout>
            }
          />
          <Route
            path="/large-files"
            element={
              <Layout>
                <LargeFiles />
              </Layout>
            }
          />
          <Route
            path="/accounts"
            element={
              <Layout>
                <Accounts />
              </Layout>
            }
          />
          <Route
            path="/settings"
            element={
              <Layout>
                <Settings />
              </Layout>
            }
          />
          {/* Ensure backend API routes are not caught by frontend router */}
          {/* This route needs to be handled carefully, typically not a frontend route */}
          {/* <Route path="/api/*" render={() => { window.location.reload(); return null; }} /> */}
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
