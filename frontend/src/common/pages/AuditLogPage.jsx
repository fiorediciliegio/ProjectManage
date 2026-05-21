import React, { useEffect, useState } from 'react';
import dayjs from 'dayjs';
import {
  Alert,
  Box,
  Grid,
  Paper,
  Snackbar,
  TextField,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import api from '../api/client.js';
import NavBarRO from '../components/NavBarRO.jsx';
import { useAuth } from '../hooks/AuthContext';
import useProjectParams from '../hooks/useProjectParams.js';

export default function AuditLogPage() {
  const { projectName } = useProjectParams();
  const { user, logout } = useAuth();
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [snackbar, setSnackbar] = useState({ open: false, message: '' });
  const [dateFilter, setDateFilter] = useState('');
  const [moduleFilter, setModuleFilter] = useState('');
  const [actionFilter, setActionFilter] = useState('');

  useEffect(() => {
    fetchLogs();
  }, []);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const response = await api.get('http://localhost:8000/audit-logs/');
      setLogs(response.data?.data?.logs || []);
    } catch (error) {
      setSnackbar({
        open: true,
        message: error.response?.data?.message || '获取操作日志失败',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleCloseSnackbar = () => {
    setSnackbar({ open: false, message: '' });
  };

  const moduleOptions = Array.from(new Set(logs.map((log) => log.module).filter(Boolean))).sort();
  const actionOptions = Array.from(new Set(logs.map((log) => log.action).filter(Boolean))).sort();
  const filteredLogs = logs.filter((log) => {
    const matchesDate = !dateFilter || (log.created_at || '').startsWith(dateFilter);
    const matchesModule = !moduleFilter || log.module === moduleFilter;
    const matchesAction = !actionFilter || log.action === actionFilter;
    return matchesDate && matchesModule && matchesAction;
  });

  return (
    <Grid container spacing={2}>
      <Grid item xs={12}>
        <NavBarRO
          title="ManageYourProject--操作日志"
          projectName={projectName || ''}
          user={user}
          onLogout={logout}
        />
      </Grid>
      <Grid item xs={12}>
        <Box sx={{ px: 4, pt: 3 }}>
          <Paper sx={{ width: '100%', p: 2 }}>
            <Typography variant="h6" sx={{ mb: 2 }}>
              操作日志
            </Typography>
            {loading && <Typography sx={{ mb: 2 }}>正在加载...</Typography>}
            <TableContainer sx={{ maxHeight: 620 }}>
              <Table stickyHeader aria-label="audit log table">
                <TableHead>
                  <TableRow>
                    <TableCell sx={{ minWidth: 190 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                        <Typography variant="body2" sx={{ fontWeight: 600, whiteSpace: 'nowrap' }}>
                          时间
                        </Typography>
                        <LocalizationProvider dateAdapter={AdapterDayjs}>
                          <DatePicker
                            value={dateFilter ? dayjs(dateFilter) : null}
                            onChange={(date) => setDateFilter(date ? dayjs(date).format('YYYY-MM-DD') : '')}
                            inputFormat="YYYY-MM-DD"
                            renderInput={(params) => (
                              <TextField
                                {...params}
                                size="small"
                                sx={{ width: 140 }}
                                inputProps={{
                                  ...params.inputProps,
                                  placeholder: '',
                                  'aria-label': '按日期筛选',
                                }}
                              />
                            )}
                          />
                        </LocalizationProvider>
                      </Box>
                    </TableCell>
                    <TableCell sx={{ minWidth: 120 }}>操作人</TableCell>
                    <TableCell sx={{ minWidth: 170 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                        <Typography variant="body2" sx={{ fontWeight: 600, whiteSpace: 'nowrap' }}>
                          模块
                        </Typography>
                        <TextField
                          select
                          size="small"
                          value={moduleFilter}
                          onChange={(event) => setModuleFilter(event.target.value)}
                          sx={{ width: 110 }}
                          SelectProps={{ native: true }}
                          inputProps={{ 'aria-label': '按模块筛选' }}
                        >
                          <option value="">全部</option>
                          {moduleOptions.map((moduleName) => (
                            <option key={moduleName} value={moduleName}>
                              {moduleName}
                            </option>
                          ))}
                        </TextField>
                      </Box>
                    </TableCell>
                    <TableCell sx={{ minWidth: 190 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                        <Typography variant="body2" sx={{ fontWeight: 600, whiteSpace: 'nowrap' }}>
                          操作类型
                        </Typography>
                        <TextField
                          select
                          size="small"
                          value={actionFilter}
                          onChange={(event) => setActionFilter(event.target.value)}
                          sx={{ width: 100 }}
                          SelectProps={{ native: true }}
                          inputProps={{ 'aria-label': '按操作类型筛选' }}
                        >
                          <option value="">全部</option>
                          {actionOptions.map((actionName) => (
                            <option key={actionName} value={actionName}>
                              {actionName}
                            </option>
                          ))}
                        </TextField>
                      </Box>
                    </TableCell>
                    <TableCell sx={{ minWidth: 170 }}>对象名称</TableCell>
                    <TableCell>操作描述</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {filteredLogs.map((log) => (
                    <TableRow key={log.id} hover>
                      <TableCell>{log.created_at || ''}</TableCell>
                      <TableCell sx={{ minWidth: 120, whiteSpace: 'nowrap' }}>{log.person_name || log.username || ''}</TableCell>
                      <TableCell>{log.module || ''}</TableCell>
                      <TableCell>{log.action || ''}</TableCell>
                      <TableCell sx={{ minWidth: 170, whiteSpace: 'nowrap' }}>{log.target_name || ''}</TableCell>
                      <TableCell>{log.description || ''}</TableCell>
                    </TableRow>
                  ))}
                  {!loading && filteredLogs.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={6} align="center">
                        暂无操作日志
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>
        </Box>
      </Grid>
      <Snackbar
        open={snackbar.open}
        autoHideDuration={3000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert onClose={handleCloseSnackbar} severity="error" sx={{ width: '100%' }}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Grid>
  );
}
