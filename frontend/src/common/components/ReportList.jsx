import React, { useEffect, useState, forwardRef, useImperativeHandle } from 'react';
import PropTypes from 'prop-types';
import axios from '../api/client.js';
import { Box, Button, Collapse, IconButton, Snackbar, Alert, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Typography, Paper } from '@mui/material';
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown';
import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUp';
import EditQuality from '../popups/EditQuality.jsx';

function createData(qrname, qrpart, qrevaluation, qrins_date, qrfeedback, more, reportId) {
  return { qrname, qrpart, qrevaluation, qrins_date, qrfeedback, more, reportId };
}

function Row({ row, onDelete, onEdit }) {
  const [open, setOpen] = React.useState(false);

  return (
    <React.Fragment>
      <TableRow sx={{ '& > *': { borderBottom: 'unset' } }}>
        <TableCell>
          <IconButton aria-label="expand row" size="small" onClick={() => setOpen(!open)}>
            {open ? <KeyboardArrowUpIcon /> : <KeyboardArrowDownIcon />}
          </IconButton>
        </TableCell>
        <TableCell component="th" scope="row">{row.qrname}</TableCell>
        <TableCell align="right">{row.qrpart}</TableCell>
        <TableCell align="right">{row.qrevaluation}</TableCell>
        <TableCell align="right">{row.qrins_date}</TableCell>
        <TableCell align="right">{row.qrfeedback}</TableCell>
      </TableRow>
      <TableRow>
        <TableCell style={{ paddingBottom: 0, paddingTop: 0 }} colSpan={6}>
          <Collapse in={open} timeout="auto" unmountOnExit>
            <Box sx={{ margin: 1 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="h6" component="div">详情</Typography>
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <Button size="small" variant="outlined" onClick={() => onEdit(row.reportId)}>
                    修改报告
                  </Button>
                  <Button size="small" color="error" variant="outlined" onClick={() => onDelete(row.reportId)}>
                    删除报告
                  </Button>
                </Box>
              </Box>
              <Table size="small" aria-label="quality details">
                <TableHead>
                  <TableRow>
                    <TableCell>质检员</TableCell>
                    <TableCell>质检意见</TableCell>
                    <TableCell>施工时间</TableCell>
                    <TableCell align="right">报告编号</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {row.more.map((moreRow, index) => (
                    <TableRow key={index}>
                      <TableCell component="th" scope="row">{moreRow.qrperson}</TableCell>
                      <TableCell>{moreRow.qrfeedback}</TableCell>
                      <TableCell>{moreRow.qrcons_date}</TableCell>
                      <TableCell align="right">{moreRow.qrnumber}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Box>
          </Collapse>
        </TableCell>
      </TableRow>
    </React.Fragment>
  );
}

Row.propTypes = {
  row: PropTypes.shape({
    qrname: PropTypes.string.isRequired,
    qrpart: PropTypes.string.isRequired,
    qrevaluation: PropTypes.string.isRequired,
    qrins_date: PropTypes.string.isRequired,
    qrfeedback: PropTypes.string,
    reportId: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
    more: PropTypes.arrayOf(
      PropTypes.shape({
        qrperson: PropTypes.string.isRequired,
        qrfeedback: PropTypes.string,
        qrcons_date: PropTypes.string.isRequired,
        qrnumber: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
      })
    ).isRequired,
  }).isRequired,
  onDelete: PropTypes.func.isRequired,
  onEdit: PropTypes.func.isRequired,
};

const ReportList = forwardRef((props, ref) => {
  const [rows, setRows] = useState([]);
  const [snackbar, setSnackbar] = useState({ open: false, message: '' });
  const [editingReportId, setEditingReportId] = useState(null);

  const fetchData = () => {
    axios.get(`http://localhost:8000/projects/${props.projectId}/quality/reports/`)
      .then((response) => {
        const reports = response.data?.data?.reports || [];
        const fetchedData = reports.map((item) =>
          createData(item.qrname, item.qrpart, item.qrevaluation, item.qrins_date, item.qrfeedback, [{
            qrperson: item.qrperson,
            qrfeedback: item.qrfeedback,
            qrcons_date: item.qrcons_date,
            qrnumber: item.qrnumber,
          }], item.report_id)
        );
        setRows(fetchedData);
      })
      .catch((error) => {
        console.error('Error fetching data: ', error);
      });
  };

  useEffect(() => {
    fetchData();
  }, [props.projectId]);

  useImperativeHandle(ref, () => ({
    refreshData() {
      fetchData();
    },
  }));

  const handleCloseSnackbar = () => {
    setSnackbar({ open: false, message: '' });
  };

  const handleDeleteReport = async (reportId) => {
    if (!reportId) {
      return;
    }

    try {
      await axios.delete(`http://localhost:8000/quality-reports/${reportId}/`);
      fetchData();
      if (props.onReportDeleted) {
        props.onReportDeleted();
      }
    } catch (error) {
      setSnackbar({
        open: true,
        message: error.response?.data?.message || '删除质量报告失败',
      });
    }
  };

  const handleEditReport = (reportId) => {
    setEditingReportId(reportId);
  };

  const handleReportUpdated = () => {
    fetchData();
    if (props.onReportUpdated) {
      props.onReportUpdated();
    }
  };


  return (
    <Box style={{ display: 'flex', flexDirection: 'column', justifyContent: 'flex-start', alignItems: 'flex-start', width: '95%', height: '100%' }}>
      <TableContainer component={Paper} sx={{ marginTop: '16px', maxHeight: 440, overflowY: 'auto' }}>
        <Table aria-label="collapsible table">
          <TableHead>
            <TableRow>
              <TableCell />
              <TableCell>检验工程</TableCell>
              <TableCell align="right">部位及编号</TableCell>
              <TableCell align="right">检验情况</TableCell>
              <TableCell align="right">检验日期</TableCell>
              <TableCell align="right">反馈意见</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {rows.map((row) => (
              <Row key={row.reportId || `${row.qrname}-${row.qrins_date}`} row={row} onDelete={handleDeleteReport} onEdit={handleEditReport} />
            ))}
          </TableBody>
        </Table>
      </TableContainer>
      {editingReportId && (
        <EditQuality
          reportId={editingReportId}
          projectId={props.projectId}
          onClose={() => setEditingReportId(null)}
          onUpdated={handleReportUpdated}
          onError={(message) => setSnackbar({ open: true, message })}
        />
      )}
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
    </Box>
  );
});

ReportList.propTypes = {
  projectId: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
  onReportDeleted: PropTypes.func,
  onReportUpdated: PropTypes.func,
};

export default ReportList;
