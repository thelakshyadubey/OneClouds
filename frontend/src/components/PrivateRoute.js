import React from 'react';
import { Navigate } from 'react-router-dom';
import { tokenManager } from '../services/api';

const PrivateRoute = ({ children }) => {
  const isAuthenticated = tokenManager.get(); // Check if a token exists

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return children;
};

export default PrivateRoute;
