import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { authService, tokenManager } from '../services/api'; // Import tokenManager
import toast from 'react-hot-toast';
import { Checkbox, FormControlLabel, TextField, Button } from '@mui/material'; // Import Material-UI components

const OtpVerification = ({ email, onVerified }) => {
  const [otp, setOtp] = useState('');
  const [deviceFingerprint] = useState(tokenManager.getDeviceFingerprint()); // Get existing fingerprint or generate

  const handleOtpSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await authService.verifyOtp(email, otp, deviceFingerprint);
      toast.success('OTP verified successfully!');
      onVerified(response.access_token, response.refresh_token, response.expires_in, response.device_trusted);
    } catch (error) {
      console.error('OTP verification failed:', error);
      toast.error(error.response?.data?.detail || 'Invalid OTP. Please try again.');
    }
  };

  return (
    <form className="space-y-6" onSubmit={handleOtpSubmit}>
      <TextField
        label="OTP"
        name="otp"
        type="text"
        autoComplete="one-time-code"
        required
        fullWidth
        value={otp}
        onChange={(e) => setOtp(e.target.value)}
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
        Verify OTP
      </Button>
    </form>
  );
};

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [requires2Fa, setRequires2Fa] = useState(false);
  const navigate = useNavigate();

  const handleLoginSuccess = (accessToken, refreshToken, expiresIn, deviceTrusted) => {
    console.log("handleLoginSuccess: Received accessToken:", accessToken);
    console.log("handleLoginSuccess: Received refreshToken:", refreshToken);
    tokenManager.setTokens(accessToken, refreshToken); // Correctly set both tokens
    if (deviceTrusted) {
      toast.success('Login successful! Device trusted.');
    } else {
      toast.success('Login successful!');
    }
    navigate('/mode-selection'); // Redirect to mode selection after successful login
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const deviceFingerprint = tokenManager.getDeviceFingerprint(); // Get or generate device fingerprint
      const response = await authService.login(email, password, deviceFingerprint); // Removed 'false' for stayLoggedIn

      console.log("handleSubmit: Login response access_token:", response.access_token);
      console.log("handleSubmit: Login response refresh_token:", response.refresh_token);

      if (response.requires_2fa) {
        setRequires2Fa(true);
        toast.info('2FA required. Please check your email for OTP.');
      } else {
        handleLoginSuccess(response.access_token, response.refresh_token, response.expires_in, response.device_trusted);
      }
    } catch (error) {
      console.error('Login failed:', error);
      const errorMessage = error.response?.data?.detail
        ? (typeof error.response.data.detail === 'string' 
           ? error.response.data.detail 
           : JSON.stringify(error.response.data.detail))
        : 'Login failed. Please check your credentials.';
      toast.error(errorMessage);
      setRequires2Fa(false); // Reset 2FA state on general login failure
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
        {!requires2Fa ? (
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
        ) : (
          <OtpVerification email={email} onVerified={handleLoginSuccess} />
        )}

        <div className="text-center text-sm">
          <p className="text-oc-steel">
            Don't have an account?{' '}
            <Link to="/register" className="font-medium text-oc-teal hover:text-oc-steel">
              Sign up
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;
