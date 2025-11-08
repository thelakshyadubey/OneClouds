import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { authService, tokenManager } from "../services/api";
import toast from "react-hot-toast";
import { TextField, Button } from "@mui/material";

const OtpVerification = ({ email, onVerified }) => {
  const [otp, setOtp] = useState("");
  const [deviceFingerprint] = useState(tokenManager.getDeviceFingerprint());

  const handleOtpSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await authService.verifyOtp(
        email,
        otp,
        deviceFingerprint
      );
      toast.success("Account activated and OTP verified successfully!");
      onVerified();
    } catch (error) {
      console.error(error);
      let errorMessage = "Failed to verify OTP";
      if (error.response && error.response.data) {
        if (Array.isArray(error.response.data.detail)) {
          errorMessage = error.response.data.detail
            .map((err) => {
              if (err.msg) return err.msg;
              if (err.detail) return err.detail;
              return "";
            })
            .filter(Boolean)
            .join("; ");
        } else if (typeof error.response.data.detail === "string") {
          errorMessage = error.response.data.detail;
        }
      }
      toast.error(errorMessage);
    }
  };

  return (
    <form onSubmit={handleOtpSubmit}>
      <TextField
        label="OTP"
        value={otp}
        onChange={(e) => setOtp(e.target.value)}
        fullWidth
        required
      />
      <Button type="submit" variant="contained" sx={{ mt: 2 }}>
        Verify
      </Button>
    </form>
  );
};

const Register = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [otpSent, setOtpSent] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await authService.register(email, name, password, confirmPassword);
      setOtpSent(true);
      toast.success("OTP sent to your email. Please verify.");
    } catch (error) {
      console.error(error);
      let errorMessage = "Registration failed";
      if (error.response && error.response.data) {
        if (Array.isArray(error.response.data.detail)) {
          errorMessage = error.response.data.detail
            .map((err) => err.msg || err.detail || "")
            .filter(Boolean)
            .join("; ");
        } else if (typeof error.response.data.detail === "string") {
          errorMessage = error.response.data.detail;
        }
      }
      toast.error(errorMessage);
    }
  };

  const handleRegisterSuccess = () => {
    // After OTP verified, store one-time flag and navigate to mode selection
    localStorage.setItem("showModeSelection", "true");
    navigate("/modeselection");
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-oc-white py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8 p-10 bg-oc-white rounded-xl shadow-lg z-10">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-oc-dark">
            Create a new account
          </h2>
        </div>
        {!otpSent ? (
          <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
            <TextField
              label="Full name"
              name="name"
              type="text"
              autoComplete="name"
              required
              fullWidth
              value={name}
              onChange={(e) => setName(e.target.value)}
              margin="normal"
              variant="outlined"
              size="small"
            />
            <TextField
              label="Email address"
              name="email"
              type="email"
              autoComplete="email"
              required
              fullWidth
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              margin="normal"
              variant="outlined"
              size="small"
            />
            <TextField
              label="Password"
              name="password"
              type="password"
              autoComplete="new-password"
              required
              fullWidth
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              margin="normal"
              variant="outlined"
              size="small"
            />
            <TextField
              label="Confirm Password"
              name="confirmPassword"
              type="password"
              autoComplete="new-password"
              required
              fullWidth
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              margin="normal"
              variant="outlined"
              size="small"
            />

            <Button
              type="submit"
              fullWidth
              variant="contained"
              color="primary"
              sx={{ mt: 3, mb: 2 }}
            >
              Sign up
            </Button>
          </form>
        ) : (
          <OtpVerification email={email} onVerified={handleRegisterSuccess} />
        )}

        <div className="text-center text-sm">
          <p className="text-oc-steel">
            Already have an account?{" "}
            <Link
              to="/login"
              className="font-medium text-oc-teal hover:text-oc-steel"
            >
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Register;
