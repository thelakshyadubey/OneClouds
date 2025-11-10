import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { authService, tokenManager } from "../services/api";
import toast from "react-hot-toast";
import { TextField, Button } from "@mui/material";

const Register = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await authService.register(
        email,
        name,
        password,
        confirmPassword
      );
      // Store tokens and navigate directly to mode selection
      tokenManager.setTokens(response.access_token, response.refresh_token);
      localStorage.setItem("showModeSelection", "true");
      toast.success("Registration successful!");
      navigate("/modeselection");
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

  return (
    <div className="min-h-screen flex items-center justify-center bg-oc-white py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8 p-10 bg-oc-white rounded-xl shadow-lg z-10">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-oc-dark">
            Create a new account
          </h2>
        </div>
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
