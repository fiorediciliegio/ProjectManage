import React, { useState, useEffect, forwardRef, useImperativeHandle } from 'react';
import axios from '../api/client.js';
import {
  Typography,
  CircularProgress,
  Grid,
  Button,
  Paper,
  Card,
  TextField,
  CardContent,
  CardActionArea,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Box,
  Divider,
  Menu,
  MenuItem,
  Snackbar,
  Alert,
} from '@mui/material';
import { DatePicker, LocalizationProvider } from '@mui/x-date-pickers';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import dayjs from 'dayjs';

const API_BASE = 'http://localhost:8000';

const SafetyIssueList = forwardRef((props, ref) => {
  const [issues, setIssues] = useState([]);
  const [resolvedIssues, setResolvedIssues] = useState([]);
  const [loading, setLoading] = useState(true);
  const [resolvedLoading, setResolvedLoading] = useState(true);
  const [error, setError] = useState(null);
  const [resolvedError, setResolvedError] = useState(null);
  const [issueSearchReportNumber, setIssueSearchReportNumber] = useState('');
  const [searchReportNumber, setSearchReportNumber] = useState('');
  const [openDialog, setOpenDialog] = useState(false);
  const [selectedIssue, setSelectedIssue] = useState(null);
  const [contextMenu, setContextMenu] = useState(null);
  const [selectedDeleteIssue, setSelectedDeleteIssue] = useState(null);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });
  const [resolutionFeedback, setResolutionFeedback] = useState('');
  const [resolutionDate, setResolutionDate] = useState(dayjs());

  const normalizeList = (responseData, key) => {
    if (Array.isArray(responseData?.data?.[key])) {
      return responseData.data[key];
    }
    return [];
  };

  const fetchIssues = async () => {
    try {
      setError(null);
      setLoading(true);
      const response = await axios.get(`${API_BASE}/projects/${props.projectId}/safety/issues/`);
      setIssues(normalizeList(response.data, 'filteredReports'));
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  };

  const fetchResolvedIssues = async () => {
    try {
      setResolvedError(null);
      setResolvedLoading(true);
      const response = await axios.get(`${API_BASE}/projects/${props.projectId}/safety/issues/resolved/`);
      setResolvedIssues(normalizeList(response.data, 'resolvedReports'));
    } catch (err) {
      setResolvedError(err);
    } finally {
      setResolvedLoading(false);
    }
  };

  const refreshData = () => {
    fetchIssues();
    fetchResolvedIssues();
  };

  useEffect(() => {
    refreshData();
  }, [props.projectId]);

  useImperativeHandle(ref, () => ({ refreshData }));

  const getCardStyle = (statusText) => {
    switch (statusText) {
      case '一般安全问题':
        return { backgroundColor: 'rgba(255, 224, 70, 0.5)' };
      case '重大安全问题':
        return { backgroundColor: 'rgba(255, 100, 100, 0.5)' };
      case '合格':
        return { backgroundColor: 'rgba(102, 187, 106, 0.18)' };
      default:
        return {};
    }
  };

  const handleOpenDialog = (issue) => {
    setSelectedIssue(issue);
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setSelectedIssue(null);
    setResolutionFeedback('');
    setResolutionDate(dayjs());
  };

  const handleContextMenu = (event, issue) => {
    event.preventDefault();
    setSelectedDeleteIssue(issue);
    setContextMenu({ mouseX: event.clientX + 2, mouseY: event.clientY - 6 });
  };

  const handleCloseContextMenu = () => {
    setContextMenu(null);
    setSelectedDeleteIssue(null);
  };

  const handleSnackbarClose = () => {
    setSnackbar({ open: false, message: '', severity: 'success' });
  };

  const handleDeleteIssue = async () => {
    if (!selectedDeleteIssue?.report_id) {
      handleCloseContextMenu();
      return;
    }

    try {
      await axios.delete(`${API_BASE}/safety-issues/${selectedDeleteIssue.report_id}/`);
      setSnackbar({ open: true, message: '现存安全问题删除成功', severity: 'success' });
      handleCloseContextMenu();
      refreshData();
    } catch (err) {
      setSnackbar({
        open: true,
        message: err.response?.data?.message || '删除现存安全问题失败',
        severity: 'error',
      });
      handleCloseContextMenu();
    }
  };

  const handleSafetyIssue = async () => {
    if (!selectedIssue || !resolutionFeedback.trim()) {
      setError(new Error('请填写处理方案后再确认处理'));
      return;
    }

    try {
      await axios.post(`${API_BASE}/safety-reports/${selectedIssue.report_id}/solutions/`, {
        issueId: selectedIssue.report_id,
        resolution: resolutionFeedback.trim(),
        res_Date: resolutionDate.format('YYYY-MM-DD'),
      });
      handleCloseDialog();
      refreshData();
    } catch (err) {
      setError(err);
    }
  };

  const filteredIssues = issues.filter((issue) => {
    const keyword = issueSearchReportNumber.trim();
    if (!keyword) return true;
    return String(issue.srnumber || '').includes(keyword);
  });

  const filteredResolvedIssues = resolvedIssues.filter((issue) => {
    const keyword = searchReportNumber.trim();
    if (!keyword) return true;
    return String(issue.srnumber || '').includes(keyword);
  });

  const renderIssueCard = (issue, options = {}) => {
    const latestSolution = issue.solutions?.[0];

    return (
      <Grid item xs={12} key={issue.report_id} marginBottom={1}>
        <Card
          variant="outlined"
          sx={{ ...getCardStyle(issue.srevaluation), minHeight: '100%' }}
          onContextMenu={options.resolved ? undefined : (event) => handleContextMenu(event, issue)}
        >
          <CardActionArea disabled={options.resolved} onClick={() => handleOpenDialog(issue)}>
            <CardContent>
              <Typography variant="h6" component="div">{issue.srname}</Typography>
              <Typography variant="body2" component="div">报告编号：{issue.srnumber || '未填写'}</Typography>
              <Typography variant="body2" component="div">安全员：{issue.srperson || '未填写'}</Typography>
              <Typography variant="body2" component="div">问题描述：{issue.srfeedback || '未填写'}</Typography>
              <Typography variant="caption" component="div">检查日期：{issue.srins_date || '未填写'}</Typography>
              {options.resolved && latestSolution && (
                <Box sx={{ mt: 1, pt: 1, borderTop: '1px solid rgba(0,0,0,0.12)' }}>
                  <Typography variant="body2">处理日期：{latestSolution.solution_date}</Typography>
                  <Typography variant="body2">处理方案：{latestSolution.solution_description}</Typography>
                </Box>
              )}
            </CardContent>
          </CardActionArea>
        </Card>
      </Grid>
    );
  };

  const renderListContent = ({ loading: isLoading, error: listError, list, emptyText, resolved = false }) => {
    if (isLoading) return <CircularProgress />;
    if (listError) return <Typography variant="body2" color="error">错误：{listError.message}</Typography>;
    if (list.length === 0) return <Typography variant="body2">{emptyText}</Typography>;
    return list.map((issue) => renderIssueCard(issue, { resolved }));
  };

  return (
    <Box sx={{ width: '95%' }}>
      <Grid container spacing={1}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ width: '100%', height: 420, p: 2, boxSizing: 'border-box', display: 'flex', flexDirection: 'column' }}>
            <Typography variant="h6" gutterBottom>现存安全问题</Typography>
            <TextField
              label="按报告编号搜索"
              placeholder="输入报告编号"
              fullWidth
              size="small"
              value={issueSearchReportNumber}
              onChange={(event) => setIssueSearchReportNumber(event.target.value)}
              sx={{ mb: 2 }}
            />
            <Divider sx={{ mb: 2 }} />
            <Box sx={{ flex: 1, overflowY: 'auto', pr: 1 }}>
              {renderListContent({ loading, error, list: filteredIssues, emptyText: '没有发现安全问题。' })}
            </Box>
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ width: '100%', height: 420, p: 2, boxSizing: 'border-box', display: 'flex', flexDirection: 'column' }}>
            <Typography variant="h6" gutterBottom>已处理安全问题</Typography>
            <TextField
              label="按报告编号搜索"
              placeholder="输入报告编号"
              fullWidth
              size="small"
              value={searchReportNumber}
              onChange={(event) => setSearchReportNumber(event.target.value)}
              sx={{ mb: 2 }}
            />
            <Divider sx={{ mb: 2 }} />
            <Box sx={{ flex: 1, overflowY: 'auto', pr: 1 }}>
              {renderListContent({
                loading: resolvedLoading,
                error: resolvedError,
                list: filteredResolvedIssues,
                emptyText: '暂无已处理安全问题。',
                resolved: true,
              })}
            </Box>
          </Paper>
        </Grid>
      </Grid>

      <Menu
        open={Boolean(contextMenu)}
        onClose={handleCloseContextMenu}
        anchorReference="anchorPosition"
        anchorPosition={
          contextMenu ? { top: contextMenu.mouseY, left: contextMenu.mouseX } : undefined
        }
      >
        <MenuItem onClick={handleDeleteIssue}>删除安全问题</MenuItem>
      </Menu>

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

      {selectedIssue && (
        <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="md" fullWidth>
          <DialogTitle sx={{ background: 'lightBlue' }}>处理安全问题</DialogTitle>
          <DialogContent sx={{ minWidth: 500, minHeight: 300 }}>
            <Grid container spacing={2} direction="column">
              <Grid item marginTop={1}>
                <Typography variant="h6" gutterBottom align="center">{selectedIssue.srname} 安全报告</Typography>
              </Grid>
              <Grid item container spacing={1} direction="row">
                <Grid item container xs={6} direction="column">
                  <Typography variant="body2" gutterBottom>所属项目：{props.projectName}</Typography>
                  <Typography variant="body2" gutterBottom>安全员：{selectedIssue.srperson}</Typography>
                  <Typography variant="body2" gutterBottom>报告编号：{selectedIssue.srnumber}</Typography>
                </Grid>
                <Grid item container xs={6} direction="column">
                  <Typography variant="body2" gutterBottom>检查部位及编号：{selectedIssue.srpart}</Typography>
                  <Typography variant="body2" gutterBottom>检查日期：{selectedIssue.srins_date}</Typography>
                </Grid>
              </Grid>
              <Grid item container spacing={1} direction="row">
                {(selectedIssue.srsubitems || []).map((subItem, index) => (
                  <Grid item container key={`${selectedIssue.report_id}-${index}`}>
                    <Grid item xs={1}><Typography variant="body2" gutterBottom>{index + 1}</Typography></Grid>
                    <Grid item xs={4}><Typography variant="body2" gutterBottom>检查项目：{subItem.item}</Typography></Grid>
                    <Grid item xs={4}><Typography variant="body2" gutterBottom>检查标准：{subItem.requirement}</Typography></Grid>
                    <Grid item xs={3}><Typography variant="body2" gutterBottom>检查结果：{subItem.result}</Typography></Grid>
                  </Grid>
                ))}
              </Grid>
              <Grid item container spacing={1} direction="row">
                <TextField
                  label="处理方案"
                  fullWidth
                  multiline
                  required
                  sx={{ marginBottom: 2 }}
                  minRows={4}
                  value={resolutionFeedback}
                  onChange={(event) => setResolutionFeedback(event.target.value)}
                />
                <LocalizationProvider dateAdapter={AdapterDayjs}>
                  <DatePicker
                    label="处理日期"
                    value={resolutionDate}
                    onChange={(date) => setResolutionDate(date || dayjs())}
                    renderInput={(params) => <TextField {...params} fullWidth margin="normal" />}
                    inputFormat="yyyy-MM-dd"
                  />
                </LocalizationProvider>
              </Grid>
            </Grid>
          </DialogContent>
          <DialogActions>
            <Button onClick={handleCloseDialog}>取消</Button>
            <Button onClick={handleSafetyIssue} variant="contained">确认处理</Button>
          </DialogActions>
        </Dialog>
      )}
    </Box>
  );
});

export default SafetyIssueList;
