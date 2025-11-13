import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import {
  Container,
  Paper,
  Typography,
  TextField,
  Button,
  Box,
  CircularProgress,
  Alert,
} from "@mui/material";
import { Email, ArrowBack } from "@mui/icons-material";
import toast from "react-hot-toast";
import api from "../services/api";

const ForgotPassword = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (!email || !email.includes("@")) {
      setError("Please enter a valid email address");
      return;
    }

    setLoading(true);
    try {
      const response = await api.post("/api/auth/forgot-password", { email });
      toast.success(response.data.message || "Password reset email sent!");
      setSubmitted(true);
    } catch (err) {
      console.error("Forgot password error:", err);
      // Still show success to prevent email enumeration
      toast.success(
        "If this email exists, a password reset link has been sent."
      );
      setSubmitted(true);
    } finally {
      setLoading(false);
    }
  };

  if (submitted) {
    return (
      <Container maxWidth="sm" sx={{ mt: 8, mb: 4 }}>
        <Paper elevation={3} sx={{ p: 4, borderRadius: 2 }}>
          <Box sx={{ textAlign: "center", mb: 3 }}>
            <Email sx={{ fontSize: 60, color: "primary.main", mb: 2 }} />
            <Typography variant="h5" gutterBottom>
              Check Your Email
            </Typography>
            <Typography variant="body1" color="text.secondary" paragraph>
              If an account exists with the email <strong>{email}</strong>, you
              will receive a password reset link shortly.
            </Typography>
            <Alert severity="info" sx={{ mt: 2, textAlign: "left" }}>
              <Typography variant="body2">
                <strong>Didn't receive the email?</strong>
              </Typography>
              <Typography variant="body2">
                • Check your spam/junk folder
                <br />
                • The link expires in 1 hour
                <br />• You can request a new link if needed
              </Typography>
            </Alert>
          </Box>

          <Box sx={{ display: "flex", gap: 2, mt: 3 }}>
            <Button
              fullWidth
              variant="outlined"
              startIcon={<ArrowBack />}
              onClick={() => navigate("/login")}
            >
              Back to Login
            </Button>
            <Button
              fullWidth
              variant="contained"
              onClick={() => {
                setSubmitted(false);
                setEmail("");
              }}
            >
              Try Another Email
            </Button>
          </Box>
        </Paper>
      </Container>
    );
  }

  return (
    <Container maxWidth="sm" sx={{ mt: 8, mb: 4 }}>
      <Paper elevation={3} sx={{ p: 4, borderRadius: 2 }}>
        <Box sx={{ mb: 3 }}>
          <Typography variant="h4" gutterBottom>
            Forgot Password?
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Enter your email address and we'll send you a link to reset your
            password.
          </Typography>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <form onSubmit={handleSubmit}>
          <TextField
            fullWidth
            label="Email Address"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            margin="normal"
            required
            autoFocus
            disabled={loading}
            InputProps={{
              startAdornment: <Email sx={{ color: "action.active", mr: 1 }} />,
            }}
          />

          <Button
            fullWidth
            type="submit"
            variant="contained"
            size="large"
            disabled={loading}
            sx={{ mt: 3, mb: 2, height: 48 }}
          >
            {loading ? (
              <CircularProgress size={24} color="inherit" />
            ) : (
              "Send Reset Link"
            )}
          </Button>

          <Box sx={{ textAlign: "center", mt: 2 }}>
            <Button
              component={Link}
              to="/login"
              startIcon={<ArrowBack />}
              sx={{ textTransform: "none" }}
            >
              Back to Login
            </Button>
          </Box>
        </form>
      </Paper>

      <Box sx={{ mt: 3, textAlign: "center" }}>
        <Typography variant="body2" color="text.secondary">
          Don't have an account?{" "}
          <Link
            to="/register"
            style={{ color: "#1976d2", textDecoration: "none" }}
          >
            Sign up
          </Link>
        </Typography>
      </Box>
    </Container>
  );
};

export default ForgotPassword;
