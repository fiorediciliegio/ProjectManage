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
} from '@mui/material';
import StackBar from '../components/BarChartSt.jsx';
import ReportList from '../components/ReportList.jsx';
import OpenButton from '../components/OpenButton.jsx';
import CreateQuality from '../popups/CreateQuality.jsx';
import CreateQuaTem from '../popups/CreateQuaTem.jsx';
import CommonPage from '../components/CommonPage.jsx';
import useProjectParams from '../hooks/useProjectParams.js';
import { useAuth } from '../hooks/AuthContext';

export default function QualityPage() {
  const { projectName, projectId } = useProjectParams();
  const [templates, setTemplates] = useState([]);
  const [isTemplateDetailOpen, setIsTemplateDetailOpen] = useState(false);
  const { user } = useAuth();
  const isManager = Boolean(user);

  const reportListRef = useRef(null);
  const stackBarRef = useRef(null);

  useEffect(() => {
    fetchTemplates();
  }, [projectId]);

  const fetchTemplates = async () => {
    const response = await axios.get(`http://localhost:8000/projects/${projectId}/quality/templates/`);
    setTemplates(response.data?.data?.qitTemplates || []);
  };

  const [isCreateQualityOpen, setIsCreateQualityOpen] = useState(false);
  const openCreateQuality = () => {
    setIsCreateQualityOpen(true);
  };
  const closeCreateQuality = () => {
    setIsCreateQualityOpen(false);
    if (reportListRef.current) {
      reportListRef.current.refreshData();
    }
    if (stackBarRef.current) {
      stackBarRef.current.refreshData();
    }
  };

  const [isCreateQuaTemOpen, setIsCreateQuaTemOpen] = useState(false);
  const openCreateQuaTem = () => {
    setIsCreateQuaTemOpen(true);
  };
  const closeCreateQuaTem = () => {
    setIsCreateQuaTemOpen(false);
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

  const handleDeleteTemplate = async () => {
    await axios.delete(`http://localhost:8000/quality-templates/${selectedTemplate.id}/`);
    await fetchTemplates();
    handleCloseMenu();
  };

  return (
    <CommonPage pageName={'质量监测'} projectId={projectId} projectName={projectName}>
      <Grid item container xs={5} spacing={2} justifyContent="flex-start" alignItems="flex-start">
        <StackBar projectId={projectId} ref={stackBarRef} />
      </Grid>
      <Grid item container xs={7} spacing={2} justifyContent="flex-start" alignItems="flex-start">
        <ReportList projectId={projectId} ref={reportListRef} onReportDeleted={() => stackBarRef.current?.refreshData()} onReportUpdated={() => stackBarRef.current?.refreshData()} />
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
                <OpenButton children={'新建质检报告'} onClick={openCreateQuality} />
                {isCreateQualityOpen && <CreateQuality onClose={closeCreateQuality} templates={templates} projectId={projectId} />}
              </Grid>
              {isManager && (
                <Grid item>
                  <OpenButton children={'新建模板'} onClick={openCreateQuaTem} />
                  {isCreateQuaTemOpen && <CreateQuaTem onClose={closeCreateQuaTem} projectId={projectId} />}
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
                          检验项目：{item.NAME_Item || item.name}；要求：{item.VALUE_Item || item.value}
                        </Typography>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <Typography variant="body2">暂无检验项目</Typography>
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
        <Menu anchorEl={anchorEl} open={Boolean(anchorEl)} onClose={handleCloseMenu} onClick={handleCloseMenu}>
          <MenuItem onClick={handleDeleteTemplate}>
            <ListItemText primary="删除模板" />
          </MenuItem>
        </Menu>
      )}
    </CommonPage>
  );
}
