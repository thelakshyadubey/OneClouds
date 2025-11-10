import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { authService, tokenManager } from "../services/api";
import toast from "react-hot-toast";
import { TextField, Button } from "@mui/material";

const Login = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await authService.login(email, password);

      console.log(
        "handleSubmit: Login response access_token:",
        response.access_token
      );
      console.log(
        "handleSubmit: Login response refresh_token:",
        response.refresh_token
      );

      tokenManager.setTokens(response.access_token, response.refresh_token);
      toast.success("Login successful!");
      navigate("/mode-selection");
    } catch (error) {
      console.error("Login failed:", error);
      const errorMessage = error.response?.data?.detail
        ? typeof error.response.data.detail === "string"
          ? error.response.data.detail
          : JSON.stringify(error.response.data.detail)
        : "Login failed. Please check your credentials.";
      toast.error(errorMessage);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-oc-white py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8 p-10 bg-oc-white rounded-xl shadow-lg z-10">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-oc-dark">
            Sign in to your account
          </h2>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="rounded-md shadow-sm -space-y-px">
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
              autoComplete="current-password"
              required
              fullWidth
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              margin="normal"
              variant="outlined"
              size="small"
            />
          </div>

          <Button
            type="submit"
            fullWidth
            variant="contained"
            color="primary"
            sx={{ mt: 3, mb: 2 }}
          >
            Sign in
          </Button>
        </form>

        <div className="text-center text-sm">
          <p className="text-oc-steel">
            Don't have an account?{" "}
            <Link
              to="/register"
              className="font-medium text-oc-teal hover:text-oc-steel"
            >
              Sign up
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;
