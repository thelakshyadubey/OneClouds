import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { authService, tokenManager } from "../services/api";
import toast from "react-hot-toast";
import {
  TextField,
  Button,
  Box,
  Typography,
  CircularProgress,
} from "@mui/material";
import { Email, CheckCircle } from "@mui/icons-material";
import api from "../services/api";

const Register = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [otp, setOtp] = useState("");
  const [step, setStep] = useState(1); // 1: Registration form, 2: OTP verification
  const [loading, setLoading] = useState(false);
  const [resendingOtp, setResendingOtp] = useState(false);

  const handleRegisterSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await api.post("/api/auth/register", {
        email,
        name,
        password,
        confirm_password: confirmPassword,
      });
      toast.success(
        response.data.message ||
          "Registration successful! Please check your email for OTP."
      );
      setStep(2); // Move to OTP verification step
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
    } finally {
      setLoading(false);
    }
  };

  const handleOtpSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await api.post("/api/auth/verify-otp", {
        email,
        otp,
      });
      // Store tokens and navigate to dashboard
      tokenManager.setTokens(
        response.data.access_token,
        response.data.refresh_token
      );
      toast.success("Email verified successfully! Welcome to OneClouds!");
      navigate("/dashboard");
    } catch (error) {
      console.error(error);
      const errorMessage =
        error.response?.data?.detail || "OTP verification failed";
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleResendOtp = async () => {
    setResendingOtp(true);
    try {
      const response = await api.post("/api/auth/resend-otp", { email });
      toast.success(response.data.message || "OTP resent successfully!");
    } catch (error) {
      console.error(error);
      const errorMessage =
        error.response?.data?.detail || "Failed to resend OTP";
      toast.error(errorMessage);
    } finally {
      setResendingOtp(false);
    }
  };

  if (step === 2) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-oc-white py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-md w-full space-y-8 p-10 bg-oc-white rounded-xl shadow-lg z-10">
          <Box sx={{ textAlign: "center", mb: 3 }}>
            <Email sx={{ fontSize: 60, color: "primary.main", mb: 2 }} />
            <Typography variant="h5" gutterBottom>
              Verify Your Email
            </Typography>
            <Typography variant="body1" color="text.secondary">
              We've sent a 6-digit code to <strong>{email}</strong>
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              The code is valid for 10 minutes
            </Typography>
          </Box>

          <form onSubmit={handleOtpSubmit} className="mt-8 space-y-6">
            <TextField
              label="Enter OTP Code"
              name="otp"
              type="text"
              required
              fullWidth
              value={otp}
              onChange={(e) =>
                setOtp(e.target.value.replace(/\D/g, "").slice(0, 6))
              }
              margin="normal"
              variant="outlined"
              placeholder="000000"
              inputProps={{
                maxLength: 6,
                style: {
                  textAlign: "center",
                  fontSize: "24px",
                  letterSpacing: "8px",
                },
              }}
            />

            <Button
              type="submit"
              fullWidth
              variant="contained"
              color="primary"
              disabled={loading || otp.length !== 6}
              sx={{ mt: 3, mb: 2, height: 48 }}
            >
              {loading ? (
                <CircularProgress size={24} color="inherit" />
              ) : (
                "Verify Email"
              )}
            </Button>

            <Box sx={{ textAlign: "center", mt: 2 }}>
              <Typography variant="body2" color="text.secondary">
                Didn't receive the code?{" "}
                <Button
                  onClick={handleResendOtp}
                  disabled={resendingOtp}
                  sx={{ textTransform: "none", p: 0, minWidth: 0 }}
                >
                  {resendingOtp ? "Sending..." : "Resend OTP"}
                </Button>
              </Typography>
            </Box>

            <Box sx={{ textAlign: "center", mt: 2 }}>
              <Button onClick={() => setStep(1)} sx={{ textTransform: "none" }}>
                Back to Registration
              </Button>
            </Box>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-oc-white py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8 p-10 bg-oc-white rounded-xl shadow-lg z-10">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-oc-dark">
            Create a new account
          </h2>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleRegisterSubmit}>
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
            disabled={loading}
            sx={{ mt: 3, mb: 2, height: 48 }}
          >
            {loading ? (
              <CircularProgress size={24} color="inherit" />
            ) : (
              "Sign up"
            )}
          </Button>
        </form>

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
