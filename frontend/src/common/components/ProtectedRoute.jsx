import React from 'react';
import { Route, useNavigate } from 'react-router-dom';
import { useAuth } from './AuthContext';

function ProtectedRoute({ element: Component, requiredRole, ...rest }) {
  const { isAuthenticated, userRole } = useAuth();
  const navigate = useNavigate();

  if (!isAuthenticated || (requiredRole && userRole !== requiredRole)) {
    navigate('/Login');
    return null; // 娑撳秵瑕嗛弻鎾叉崲娴ｆ洖鍞寸€?  }

  return <Route {...rest} element={<Component />} />;
}

export default ProtectedRoute;

