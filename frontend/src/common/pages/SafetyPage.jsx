import React, { useState, useEffect, useRef } from 'react';
import axios from '../api/client.js';
import {
  Grid,
  Paper,
  Typography,
  Box,
  Menu,
  MenuItem,
  ListItemText,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Button,
  Snackbar,
  Alert,
} from '@mui/material';
import OpenButton from '../components/OpenButton.jsx';
import CreateSafety from '../popups/CreateSafety.jsx';
import CreateSafTem from '../popups/CreateSafTem.jsx';
import SafetyIssueList from '../components/SafetyIssueList.jsx';
import CommonPage from '../components/CommonPage.jsx';
import useProjectParams from '../hooks/useProjectParams.js';
import { useAuth } from '../hooks/AuthContext';

export default function SafetyPage() {
  const { projectName, projectId } = useProjectParams();
  const [templates, setTemplates] = useState([]);
  const [isTemplateDetailOpen, setIsTemplateDetailOpen] = useState(false);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });
  const { user } = useAuth();
  const isManager = Boolean(user);

  const safetyIssueListRef = useRef(null);

  useEffect(() => {
    fetchTemplates();
  }, [projectId]);

  const fetchTemplates = async () => {
    const response = await axios.get(`http://localhost:8000/projects/${projectId}/safety/templates/`);
    setTemplates(response.data?.data?.sctTemplates || []);
  };

  const [isCreateSafetyOpen, setIsCreateSafetyOpen] = useState(false);
  const openCreateSafety = () => {
    setIsCreateSafetyOpen(true);
  };
  const closeCreateSafety = () => {
    setIsCreateSafetyOpen(false);
    if (safetyIssueListRef.current) {
      safetyIssueListRef.current.refreshData();
    }
  };

  const [isCreateSafTemOpen, setIsCreateSafTemOpen] = useState(false);
  const openCreateSafTem = () => {
    setIsCreateSafTemOpen(true);
  };
  const closeCreateSafTem = () => {
    setIsCreateSafTemOpen(false);
    fetchTemplates();
  };

  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const handleTemplateClick = (template) => {
    setSelectedTemplate(template);
    setIsTemplateDetailOpen(true);
  };

  const handleCloseTemplateDetail = () => {
    setIsTemplateDetailOpen(false);
  };

  const [anchorEl, setAnchorEl] = useState(null);
  const handleTemplateDeleteClick = (event, template) => {
    event.preventDefault();
    setAnchorEl(event.currentTarget);
    setSelectedTemplate(template);
  };
  const handleCloseMenu = () => {
    setAnchorEl(null);
    setSelectedTemplate(null);
  };

  const handleSnackbarClose = () => {
    setSnackbar({ open: false, message: '', severity: 'success' });
  };

  const handleDeleteTemplate = async () => {
    try {
      await axios.delete(`http://localhost:8000/safety-templates/${selectedTemplate.id}/`);
      await fetchTemplates();
      setSnackbar({ open: true, message: '安全模板删除成功', severity: 'success' });
      handleCloseMenu();
    } catch (error) {
      setSnackbar({
        open: true,
        message: error.response?.data?.message || '删除安全模板失败',
        severity: 'error',
      });
      handleCloseMenu();
    }
  };

  return (
    <CommonPage pageName={'安全监测'} projectId={projectId} projectName={projectName}>
      <Grid item justifyContent="flex-start" alignItems="flex-start" xs={12}>
        <SafetyIssueList projectId={projectId} projectName={projectName} ref={safetyIssueListRef} />
      </Grid>
      <Grid item container xs={12} spacing={2} justifyContent="flex-start" alignItems="flex-start">
        <Paper style={{ width: '95%', height: '100%', padding: '15px' }}>
          <Grid container>
            <Grid item container xs={10} direction={'column'}>
              <Typography variant="h6">模板</Typography>
              {templates && templates.length > 0 ? (
                templates.map((template) => (
                  <Box
                    key={template.id}
                    sx={{ margin: '10px 0', cursor: 'pointer' }}
                    onClick={() => handleTemplateClick(template)}
                    onContextMenu={(event) => handleTemplateDeleteClick(event, template)}
                  >
                    <Typography variant="body1">{template.name}</Typography>
                  </Box>
                ))
              ) : (
                <Typography variant="body1">暂无模板</Typography>
              )}
            </Grid>
            <Grid item container xs={2} direction="column" spacing={2}>
              <Grid item>
                <OpenButton children={'新建安全报告'} onClick={openCreateSafety} />
                {isCreateSafetyOpen && <CreateSafety onClose={closeCreateSafety} templates={templates} projectId={projectId} />}
              </Grid>
              {isManager && (
                <Grid item>
                  <OpenButton children={'新建模板'} onClick={openCreateSafTem} />
                  {isCreateSafTemOpen && <CreateSafTem onClose={closeCreateSafTem} projectId={projectId} />}
                </Grid>
              )}
            </Grid>
          </Grid>
        </Paper>
      </Grid>
      <Dialog open={isTemplateDetailOpen} onClose={handleCloseTemplateDetail}>
        <DialogTitle>详细信息</DialogTitle>
        <DialogContent>
          <DialogContentText component="div">
            {selectedTemplate && (
              <div>
                <Typography variant="body1">模板名称：{selectedTemplate.name}</Typography>
                {selectedTemplate.items && selectedTemplate.items.length > 0 ? (
                  <ul>
                    {selectedTemplate.items.map((item) => (
                      <li key={item.id}>
                        <Typography variant="body2">
                          检查项目：{item.NAME_Item || item.name}；要求：{item.VALUE_Item || item.value}
                        </Typography>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <Typography variant="body2">暂无检查项目</Typography>
                )}
              </div>
            )}
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseTemplateDetail}>关闭</Button>
        </DialogActions>
      </Dialog>
      {selectedTemplate && (
        <Menu anchorEl={anchorEl} open={Boolean(anchorEl)} onClose={handleCloseMenu}>
          <MenuItem onClick={handleDeleteTemplate}>
            <ListItemText primary="删除模板" />
          </MenuItem>
        </Menu>
      )}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={3000}
        onClose={handleSnackbarClose}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert onClose={handleSnackbarClose} severity={snackbar.severity} sx={{ width: '100%' }}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </CommonPage>
  );
}
