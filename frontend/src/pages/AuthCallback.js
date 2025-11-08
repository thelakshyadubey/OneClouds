import React, { useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { tokenManager } from '../services/api';
import toast from 'react-hot-toast';

const AuthCallback = () => {
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    const urlParams = new URLSearchParams(location.search);
    const token = urlParams.get('token');
    const provider = urlParams.get('provider');
    const mode = urlParams.get('mode'); // Get the mode from URL parameters
    const requires2fa = urlParams.get('requires_2fa') === 'true'; // New: Get requires_2fa
    const deviceTrusted = urlParams.get('device_trusted') === 'true'; // New: Get device_trusted

    console.log('AuthCallback received token:', token); // Diagnostic log
    console.log('AuthCallback received requires2fa:', requires2fa); // Diagnostic log
    console.log('AuthCallback received deviceTrusted:', deviceTrusted); // Diagnostic log

    if (token) {
      console.log('AuthCallback: Attempting to set token in localStorage.');
      tokenManager.set(token);
      const storedToken = tokenManager.get();
      console.log('AuthCallback: Token read from localStorage immediately after set:', storedToken);

      if (tokenManager.get()) {
        toast.success(`${provider} connected successfully!`);
        // Redirect to dashboard with the selected mode
        navigate(`/dashboard?mode=${mode}`, { replace: true });
      } else {
        console.error('AuthCallback: Token not found in localStorage after set.');
        toast.error('Failed to store token. Please log in again.');
        navigate('/login', { replace: true }); // Redirect to login, not homepage
      }
    } else if (urlParams.get('auth') === 'error') { // Check if there's an explicit error parameter
      toast.error('Failed to connect cloud storage. Please try again.');
      navigate('/dashboard', { replace: true }); // Redirect to dashboard to allow reconnecting
    } else {
      // Fallback for unexpected scenarios, redirect to login as a safe default
      navigate('/login', { replace: true });
    }
  }, [location, navigate]);

  return (
    <div className="flex justify-center items-center h-screen">
      <div className="spinner"></div>
      <p className="ml-3 text-gray-700">Authenticating...</p>
    </div>
  );
};

export default AuthCallback;
