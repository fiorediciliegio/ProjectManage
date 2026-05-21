import React, { createContext, useEffect, useState, useContext } from 'react';
import api, { API_BASE_URL } from '../api/client.js';

const AuthContext = createContext();

const getLevelLabel = (sysRole) => {
  if (sysRole === 'admin' || sysRole === 'project_manager') {
    return '管理者';
  }
  return '普通成员';
};

const normalizeUser = (userData) => {
  if (!userData) {
    return null;
  }

  return {
    username: userData.username || '',
    level: getLevelLabel(userData.sys_role),
    sys_role: userData.sys_role || null,
    person_role: userData.person_role || null,
    person_name: userData.person_name || null,
    person_id: userData.person_id || null,
    is_superuser: Boolean(userData.is_superuser),
    is_staff: Boolean(userData.is_staff),
  };
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);

  useEffect(() => {
    const bootstrapAuth = async () => {
      try {
        await api.get(`${API_BASE_URL}/csrf/`);
        const response = await api.get(`${API_BASE_URL}/current-user/`);
        setUser(normalizeUser(response.data?.data));
      } catch (error) {
        setUser(null);
      }
    };

    bootstrapAuth();
  }, []);

  const login = (userData) => {
    setUser(normalizeUser(userData));
  };

  const logout = async () => {
    try {
      await api.post(`${API_BASE_URL}/logout/`, {});
    } catch (error) {
      console.error('Logout request failed:', error);
    } finally {
      setUser(null);
    }
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, apiBaseUrl: API_BASE_URL }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
