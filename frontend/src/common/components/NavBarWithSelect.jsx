import React, { useState, useEffect } from "react";
import axios from "../api/client.js";
import {
  AppBar,
  Box,
  Toolbar,
  IconButton,
  Typography,
  Menu,
  Grid,
  Container,
  Avatar,
  Tooltip,
  MenuItem,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
} from "@mui/material";
import HomeIcon from "@mui/icons-material/Home";
import { lightBlue } from "@mui/material/colors";
import { Link } from "react-router-dom";

const settings = [
  { key: "account", label: "账户信息" },
  { key: "logout", label: "退出登录" },
];

export default function NavBarWithSelect({ title, onSelectProject, defaultSelectedProject, user, onLogout }) {
  const [projectList, setProjectList] = useState([]);
  const [selectedProject, setSelectedProject] = useState(defaultSelectedProject || null);
  const [anchorElUser, setAnchorElUser] = useState(null);
  const [openDialog, setOpenDialog] = useState(false);

  useEffect(() => {
    fetchProjects();
  }, []);

  const fetchProjects = async () => {
    axios
      .get("http://localhost:8000/projects/")
      .then((res) => {
        const projectList = res.data?.data?.projects || [];
        const extractedData = projectList.map((item) => ({
          pjname: item.pjname,
          pjid: item.pjid,
        }));
        setProjectList(extractedData);
      })
      .catch((error) => {
        console.error("Error fetching data from server", error);
      });
  };

  const handleProjectChange = (event) => {
    const projectId = event.target.value;
    const projectName = projectList.find((item) => item.pjid === projectId)?.pjname;
    setSelectedProject(projectId);
    onSelectProject(projectName, projectId);
  };

  const handleOpenUserMenu = (event) => {
    setAnchorElUser(event.currentTarget);
  };

  const handleCloseUserMenu = () => {
    setAnchorElUser(null);
  };

  const handleMenuItemClick = (settingKey) => {
    handleCloseUserMenu();
    if (settingKey === "account") {
      setOpenDialog(true);
    } else if (settingKey === "logout") {
      onLogout();
    }
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
  };

  return (
    <AppBar position="static">
      <Container maxWidth="xl">
        <Toolbar disableGutters>
          <Grid container alignItems="center" direction="row">
            <Grid item xs={4}>
              <Typography
                variant="h6"
                noWrap
                component="span"
                sx={{
                  mr: 2,
                  display: { xs: "none", md: "flex" },
                  fontWeight: 700,
                  letterSpacing: ".1rem",
                  color: "inherit",
                  textDecoration: "none",
                }}
              >
                {title}
              </Typography>
            </Grid>
            <Grid item xs={5}>
              <Box
                component="form"
                sx={{
                  "& > :not(style)": { m: 1, width: "30ch" },
                }}
                noValidate
                autoComplete="off"
              >
                <TextField
                  select
                  label="选择项目"
                  variant="standard"
                  value={selectedProject || ""}
                  onChange={handleProjectChange}
                >
                  {projectList.map((item) => (
                    <MenuItem key={item.pjid} value={item.pjid}>
                      {item.pjname}
                    </MenuItem>
                  ))}
                </TextField>
              </Box>
            </Grid>
            <Grid item xs={1}>
              <Box>
                <IconButton edge="end" color="inherit" aria-label="home" component={Link} to="/">
                  <HomeIcon />
                </IconButton>
              </Box>
            </Grid>
            <Grid item xs={2}>
              <Box sx={{ flexGrow: 0, display: "flex", alignItems: "center", gap: 2 }}>
                <Tooltip title="打开菜单">
                  <IconButton onClick={handleOpenUserMenu} sx={{ p: 0 }}>
                    <Avatar sx={{ bgcolor: lightBlue[500] }}>{user?.username?.charAt(0) || "U"}</Avatar>
                  </IconButton>
                </Tooltip>
                <Button
                  color="inherit"
                  component={Link}
                  to="/AuditLog"
                  sx={{ minWidth: "auto", whiteSpace: "nowrap" }}
                >
                  操作日志
                </Button>
                <Menu
                  sx={{ mt: "45px" }}
                  id="menu-appbar"
                  anchorEl={anchorElUser}
                  anchorOrigin={{ vertical: "top", horizontal: "right" }}
                  keepMounted
                  transformOrigin={{ vertical: "top", horizontal: "right" }}
                  open={Boolean(anchorElUser)}
                  onClose={handleCloseUserMenu}
                >
                  {settings.map((setting) => (
                    <MenuItem key={setting.key} onClick={() => handleMenuItemClick(setting.key)}>
                      <Typography textAlign="center">{setting.label}</Typography>
                    </MenuItem>
                  ))}
                </Menu>
              </Box>
            </Grid>
          </Grid>
        </Toolbar>
      </Container>
      <Dialog
        open={openDialog}
        onClose={handleCloseDialog}
        PaperProps={{
          sx: {
            width: "30%",
          },
        }}
      >
        <DialogTitle>账户信息</DialogTitle>
        <DialogContent>
          <Typography variant="subtitle1">用户名：{user?.username}</Typography>
          <Typography variant="subtitle1">用户级别：{user?.level || "未知"}</Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog} color="primary">
            关闭
          </Button>
        </DialogActions>
      </Dialog>
    </AppBar>
  );
}
