import React, { useState, useEffect } from 'react';
import {
  Paper,
  Table,
  TableCell,
  TableContainer,
  Grid,
  TableRow,
  Box,
  Button,
  CircularProgress,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Menu,
  MenuItem,
  Snackbar,
} from '@mui/material';
import SearchBox from '../components/SearchBox';
import CreateCost from '../popups/CreateCost';
import EditCost from '../popups/EditCost';
import OpenButton from '../components/OpenButton.jsx';
import Axios from '../api/client.js';

const columns = [
  { id: 'name', label: '成本名称', minWidth: 170 },
  { id: 'date', label: '日期', minWidth: 100, align: 'right' },
];

export default function CostTable({ projectId, projectName, onUpdate }) {
  const [searchQuery, setSearchQuery] = useState('');
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedCost, setSelectedCost] = useState(null);
  const [isCreateCostOpen, setIsCreatCostOpen] = useState(false);
  const [isEditCostOpen, setIsEditCostOpen] = useState(false);
  const [contextMenu, setContextMenu] = useState(null);
  const [snackbar, setSnackbar] = useState({ open: false, message: '' });

  const fetchCostData = async (targetProjectId) => {
    try {
      setLoading(true);
      const res = await Axios.get(`http://localhost:8000/projects/${targetProjectId}/costs/`);
      setRows(res.data?.data?.costs || []);
      setError(null);
    } catch (err) {
      setError(err.response?.data?.message || '获取成本单列表失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCostData(projectId);
  }, [projectId]);

  const openCreateCost = () => {
    setIsCreatCostOpen(true);
  };

  const closeCreateCost = () => {
    setIsCreatCostOpen(false);
    fetchCostData(projectId);
    if (onUpdate) {
      onUpdate();
    }
  };

  const handleDialogOpen = (cost) => {
    setSelectedCost(cost);
    setDialogOpen(true);
  };

  const handleDialogClose = () => {
    setDialogOpen(false);
    if (!isEditCostOpen) {
      setSelectedCost(null);
    }
  };

  const handleEditCostOpen = () => {
    if (!selectedCost?.costId) {
      return;
    }
    setDialogOpen(false);
    setIsEditCostOpen(true);
  };

  const handleEditCostClose = () => {
    setIsEditCostOpen(false);
    setSelectedCost(null);
  };

  const handleEditCostUpdated = () => {
    fetchCostData(projectId);
    if (onUpdate) {
      onUpdate();
    }
  };

  const handleEditCostError = (message) => {
    setSnackbar({ open: true, message });
  };

  const handleContextMenu = (event, cost) => {
    event.preventDefault();
    setSelectedCost(cost);
    setContextMenu(
      contextMenu === null
        ? {
            mouseX: event.clientX + 2,
            mouseY: event.clientY - 6,
          }
        : null
    );
  };

  const handleContextMenuClose = () => {
    setContextMenu(null);
  };

  const handleSnackbarClose = () => {
    setSnackbar({ open: false, message: '' });
  };

  const handleDeleteCost = async () => {
    if (!selectedCost?.costId) {
      handleContextMenuClose();
      return;
    }

    try {
      await Axios.delete(`http://localhost:8000/costs/${selectedCost.costId}/`);
      handleContextMenuClose();
      setSelectedCost(null);
      fetchCostData(projectId);
      if (onUpdate) {
        onUpdate();
      }
    } catch (err) {
      setSnackbar({
        open: true,
        message: err.response?.data?.message || '删除成本单失败',
      });
      handleContextMenuClose();
    }
  };

  const filteredRows = rows.filter((row) => row.costName.toLowerCase().includes(searchQuery.toLowerCase()));

  return (
    <Grid container marginTop={1}>
      <Paper sx={{ width: '90%', overflow: 'hidden', padding: '20px' }}>
        <Grid container direction="column" spacing={1}>
          <Grid item container direction="row" spacing={1}>
            <Grid item xs={9} alignContent="center">
              <SearchBox label="搜索成本名称..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} />
            </Grid>
            <Grid item xs={3} alignContent="center">
              <OpenButton onClick={openCreateCost}>新建成本单</OpenButton>
              {isCreateCostOpen && (
                <CreateCost onClose={closeCreateCost} projectId={projectId} projectName={projectName} />
              )}
              {isEditCostOpen && selectedCost && (
                <EditCost
                  cost={selectedCost}
                  onClose={handleEditCostClose}
                  onUpdated={handleEditCostUpdated}
                  onError={handleEditCostError}
                  projectId={projectId}
                  projectName={projectName}
                />
              )}
            </Grid>
          </Grid>
          <Grid item container direction="row" spacing={1}>
            <TableContainer sx={{ maxHeight: 440, overflowY: 'auto' }}>
              <Table stickyHeader aria-label="cost table">
                <thead>
                  <TableRow>
                    {columns.map((column) => (
                      <TableCell key={column.id} align={column.align} style={{ minWidth: column.minWidth }}>
                        {column.label}
                      </TableCell>
                    ))}
                  </TableRow>
                </thead>
                <tbody>
                  {loading ? (
                    <TableRow>
                      <TableCell colSpan={columns.length} align="center">
                        <Box display="flex" justifyContent="center" alignItems="center">
                          <CircularProgress />
                        </Box>
                      </TableCell>
                    </TableRow>
                  ) : error ? (
                    <TableRow>
                      <TableCell colSpan={columns.length} align="center">
                        <Alert severity="error">{error}</Alert>
                      </TableCell>
                    </TableRow>
                  ) : (
                    filteredRows.map((row) => (
                      <TableRow
                        hover
                        role="checkbox"
                        tabIndex={-1}
                        key={row.costId || `${row.costName}-${row.date}`}
                        onClick={() => handleDialogOpen(row)}
                        onContextMenu={(event) => handleContextMenu(event, row)}
                        sx={{ cursor: 'context-menu' }}
                      >
                        <TableCell>{row.costName}</TableCell>
                        <TableCell align="right">{row.date}</TableCell>
                      </TableRow>
                    ))
                  )}
                </tbody>
              </Table>
            </TableContainer>
          </Grid>
        </Grid>

        <Menu
          open={contextMenu !== null}
          onClose={handleContextMenuClose}
          anchorReference="anchorPosition"
          anchorPosition={
            contextMenu !== null
              ? { top: contextMenu.mouseY, left: contextMenu.mouseX }
              : undefined
          }
        >
          <MenuItem onClick={handleDeleteCost}>删除成本单</MenuItem>
        </Menu>

        <Dialog
          open={dialogOpen}
          onClose={handleDialogClose}
          PaperProps={{
            style: {
              width: '500px',
              maxWidth: 'none',
            },
          }}
        >
          <DialogTitle>成本单详细信息</DialogTitle>
          <DialogContent>
            {selectedCost && (
              <Box>
                <p><strong>成本单:</strong> {selectedCost.costName}</p>
                <p><strong>日期:</strong> {selectedCost.date}</p>
                <p><strong>所属项目:</strong> {selectedCost.projectName}</p>
                <p><strong>费用类型:</strong> {selectedCost.expenseType}</p>
                <p><strong>财务人员:</strong> {selectedCost.accountant}</p>
                <p><strong>预算金额:</strong> {selectedCost.budgetAmount}</p>
                <p><strong>执行金额:</strong> {selectedCost.costAmount}</p>
                <p><strong>描述:</strong> {selectedCost.description}</p>
              </Box>
            )}
          </DialogContent>
          <DialogActions>
            <Button onClick={handleEditCostOpen} color="primary">编辑</Button>
            <Button onClick={handleDialogClose} color="primary">关闭</Button>
          </DialogActions>
        </Dialog>
        <Snackbar
          open={snackbar.open}
          autoHideDuration={3000}
          onClose={handleSnackbarClose}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
        >
          <Alert onClose={handleSnackbarClose} severity="error" sx={{ width: '100%' }}>
            {snackbar.message}
          </Alert>
        </Snackbar>
      </Paper>
    </Grid>
  );
}
