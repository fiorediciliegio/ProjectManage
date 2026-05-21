import React, { useState } from "react";
import { Grid, Paper, TextField, Button, Typography } from "@mui/material";
import LockOutlinedIcon from "@mui/icons-material/LockOutlined";
import api, { API_BASE_URL } from "../api/client.js";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/AuthContext";

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const navigate = useNavigate();
  const { login } = useAuth();

  const handleLogin = async () => {
    try {
      await api.get(`${API_BASE_URL}/csrf/`);
      const response = await api.post(`${API_BASE_URL}/login/`, { username, password });

      if (response.status === 200) {
        login(response.data?.data || {});
        navigate("/");
      }
    } catch (err) {
      setError(err.response?.data?.message || "用户名或密码错误");
    }
  };

  return (
    <Grid
      container
      justifyContent="center"
      alignItems="center"
      style={{
        height: "100vh",
        backgroundImage: "url('/bgpic2.jpg')",
        backgroundPosition: "center",
        backgroundSize: "cover",
      }}
    >
      <Grid item xs={10} sm={6} md={4}>
        <Paper
          elevation={3}
          style={{
            padding: "20px",
            textAlign: "center",
            backgroundColor: "rgba(250, 250, 250, 0.8)",
          }}
        >
          <LockOutlinedIcon style={{ fontSize: "50px", marginBottom: "20px" }} />
          <Typography variant="h5" gutterBottom>
            ManageYourProject 登录
          </Typography>
          <TextField
            variant="outlined"
            margin="normal"
            required
            fullWidth
            id="username"
            label="用户名"
            name="username"
            autoComplete="username"
            autoFocus
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
          <TextField
            variant="outlined"
            margin="normal"
            required
            fullWidth
            name="password"
            label="密码"
            type="password"
            id="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <Button
            type="button"
            fullWidth
            variant="contained"
            color="primary"
            style={{ marginTop: "20px" }}
            onClick={handleLogin}
          >
            登录
          </Button>
          {error && <p style={{ color: "red", marginTop: "10px" }}>{error}</p>}
        </Paper>
      </Grid>
    </Grid>
  );
}
