import React from 'react';
import {Navigate, useLocation} from 'react-router-dom';
import {useAuth} from '@src/hooks/useAuth';

const AuthGuard = ({children, requireAuth}) => {
  const location = useLocation();
  const isAuthenticated = useAuth();

  if (requireAuth && !isAuthenticated) {
    return <Navigate to="/login" state={{from: location}} replace/>;
  }

  if (!requireAuth && isAuthenticated) {
    return <Navigate to="/chat" replace/>;
  }

  return children;
};

export default AuthGuard; 