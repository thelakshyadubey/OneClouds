import React, { useState, useEffect } from "react";
import { useNavigate, useSearchParams, Link } from "react-router-dom";
import {
  Container,
  Paper,
  Typography,
  TextField,
  Button,
  Box,
  CircularProgress,
  Alert,
  InputAdornment,
  IconButton,
} from "@mui/material";
import {
  LockReset,
  Visibility,
  VisibilityOff,
  CheckCircle,
} from "@mui/icons-material";
import toast from "react-hot-toast";
import api from "../services/api";

const ResetPassword = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token");

  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token) {
      setError(
        "Invalid or missing reset token. Please request a new password reset link."
      );
    }
  }, [token]);

  const validatePassword = () => {
    if (!newPassword || newPassword.length < 8) {
      setError("Password must be at least 8 characters long");
      return false;
    }
    if (newPassword !== confirmPassword) {
      setError("Passwords do not match");
      return false;
    }
    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (!token) {
      setError("Invalid reset token");
      return;
    }

    if (!validatePassword()) {
      return;
    }

    setLoading(true);
    try {
      const response = await api.post("/api/auth/reset-password", {
        token,
        new_password: newPassword,
        confirm_password: confirmPassword,
      });

      toast.success(response.data.message || "Password reset successful!");
      setSuccess(true);

      // Redirect to login after 3 seconds
      setTimeout(() => {
        navigate("/login");
      }, 3000);
    } catch (err) {
      console.error("Reset password error:", err);
      const errorMsg =
        err.response?.data?.detail ||
        "Failed to reset password. The link may have expired.";
      setError(errorMsg);
      toast.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <Container maxWidth="sm" sx={{ mt: 8, mb: 4 }}>
        <Paper elevation={3} sx={{ p: 4, borderRadius: 2 }}>
          <Box sx={{ textAlign: "center" }}>
            <CheckCircle sx={{ fontSize: 80, color: "success.main", mb: 2 }} />
            <Typography variant="h5" gutterBottom>
              Password Reset Successful!
            </Typography>
            <Typography variant="body1" color="text.secondary" paragraph>
              Your password has been successfully reset. You can now login with
              your new password.
            </Typography>
            <Alert severity="info" sx={{ mt: 2, mb: 3 }}>
              For security reasons, you have been logged out from all devices.
              Please login again with your new password.
            </Alert>
            <Button
              fullWidth
              variant="contained"
              size="large"
              onClick={() => navigate("/login")}
            >
              Go to Login
            </Button>
          </Box>
        </Paper>
      </Container>
    );
  }

  return (
    <Container maxWidth="sm" sx={{ mt: 8, mb: 4 }}>
      <Paper elevation={3} sx={{ p: 4, borderRadius: 2 }}>
        <Box sx={{ mb: 3, textAlign: "center" }}>
          <LockReset sx={{ fontSize: 60, color: "primary.main", mb: 2 }} />
          <Typography variant="h4" gutterBottom>
            Reset Your Password
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Enter your new password below.
          </Typography>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {!token && (
          <Alert severity="warning" sx={{ mb: 2 }}>
            No reset token found. Please request a new password reset link from
            the{" "}
            <Link
              to="/forgot-password"
              style={{ color: "inherit", fontWeight: "bold" }}
            >
              forgot password page
            </Link>
            .
          </Alert>
        )}

        <form onSubmit={handleSubmit}>
          <TextField
            fullWidth
            label="New Password"
            type={showPassword ? "text" : "password"}
            value={newPassword}
            onChange={(e) => {
              setNewPassword(e.target.value);
              setError("");
            }}
            margin="normal"
            required
            autoFocus
            disabled={loading || !token}
            helperText="Must be at least 8 characters"
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton
                    onClick={() => setShowPassword(!showPassword)}
                    edge="end"
                  >
                    {showPassword ? <VisibilityOff /> : <Visibility />}
                  </IconButton>
                </InputAdornment>
              ),
            }}
          />

          <TextField
            fullWidth
            label="Confirm New Password"
            type={showConfirmPassword ? "text" : "password"}
            value={confirmPassword}
            onChange={(e) => {
              setConfirmPassword(e.target.value);
              setError("");
            }}
            margin="normal"
            required
            disabled={loading || !token}
            error={confirmPassword && newPassword !== confirmPassword}
            helperText={
              confirmPassword && newPassword !== confirmPassword
                ? "Passwords do not match"
                : "Re-enter your new password"
            }
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    edge="end"
                  >
                    {showConfirmPassword ? <VisibilityOff /> : <Visibility />}
                  </IconButton>
                </InputAdornment>
              ),
            }}
          />

          <Button
            fullWidth
            type="submit"
            variant="contained"
            size="large"
            disabled={loading || !token || !newPassword || !confirmPassword}
            sx={{ mt: 3, mb: 2, height: 48 }}
          >
            {loading ? (
              <CircularProgress size={24} color="inherit" />
            ) : (
              "Reset Password"
            )}
          </Button>

          <Box sx={{ textAlign: "center", mt: 2 }}>
            <Typography variant="body2" color="text.secondary">
              Remember your password?{" "}
              <Link
                to="/login"
                style={{ color: "#1976d2", textDecoration: "none" }}
              >
                Login
              </Link>
            </Typography>
          </Box>
        </form>

        <Alert severity="info" sx={{ mt: 3 }}>
          <Typography variant="body2">
            <strong>Security Notice:</strong> After resetting your password, you
            will be logged out from all devices for security reasons.
          </Typography>
        </Alert>
      </Paper>
    </Container>
  );
};

export default ResetPassword;
