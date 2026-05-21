import React, { useState, useEffect, forwardRef, useImperativeHandle } from "react";
import axios from "../api/client.js";
import Paper from "@mui/material/Paper";
import Table from "@mui/material/Table";
import TableCell from "@mui/material/TableCell";
import TableContainer from "@mui/material/TableContainer";
import TablePagination from "@mui/material/TablePagination";
import TableRow from "@mui/material/TableRow";
import { pjcolumns } from "../constants/PROJECT_INFO.js";
import SearchBox from "./SearchBox.jsx";
import Menu from "@mui/material/Menu";
import MenuItem from "@mui/material/MenuItem";
import Snackbar from "@mui/material/Snackbar";
import Alert from "@mui/material/Alert";
import { useAuth } from "../hooks/AuthContext";

const ProjectTable = forwardRef((props, ref) => {
  const [searchQuery, setSearchQuery] = useState("");
  const [projectInfo, setProjectInfo] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [rows, setRows] = useState([]);
  const [deleteId, setDeleteId] = useState(null);
  const [anchorEl, setAnchorEl] = useState(null);
  const [snackbar, setSnackbar] = useState({ open: false, message: '' });
  const { user } = useAuth();
  const isManager = Boolean(user);

  useEffect(() => {
    fetchProjectData();
  }, []);

  const fetchProjectData = () => {
    axios
      .get("http://localhost:8000/projects/")
      .then((res) => {
        const projectList = res.data?.data?.projects || [];
        const extractedData = projectList.map((item) => ({
          pjname: item.pjname,
          pjnumber: item.pjnumber,
          pjtype: item.pjtype,
          pjmanager: item.pjmanager,
          pjid: item.pjid,
        }));
        setRows(extractedData);
      })
      .catch((error) => {
        console.error("Error fetching data from server", error);
      });
  };

  const handleChangePage = (event, newPage) => {
    setProjectInfo(newPage);
  };

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(+event.target.value);
    setProjectInfo(0);
  };

  const handleRowClick = (pjname, pjid) => {
    props.onRowClick(`/PlanPage?projectName=${encodeURIComponent(pjname)}&projectId=${encodeURIComponent(pjid)}`);
  };

  const handleMenuOpen = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleSnackbarClose = () => {
    setSnackbar({ open: false, message: '' });
  };

  const handleDelete = () => {
    axios
      .delete(`http://localhost:8000/projects/${deleteId}/`)
      .then(() => {
        fetchProjectData();
        handleMenuClose();
      })
      .catch((error) => {
        console.error("Error deleting project", error);
        setSnackbar({
          open: true,
          message: error.response?.data?.message || '删除项目失败',
        });
        handleMenuClose();
      });
  };

  const normalizedSearchQuery = searchQuery.toLowerCase();
  const filteredRows = rows.filter(
    (row) =>
      String(row.pjname || "").toLowerCase().includes(normalizedSearchQuery) ||
      String(row.pjnumber || "").toLowerCase().includes(normalizedSearchQuery)
  );

  useImperativeHandle(ref, () => ({
    refreshData() {
      fetchProjectData();
    },
  }));

  return (
    <Paper sx={{ width: "90%", overflow: "hidden", padding: "20px" }}>
      <SearchBox
        label="搜索项目名称或编号..."
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
      />
      <TableContainer sx={{ maxHeight: 440 }}>
        <Table stickyHeader aria-label="project table">
          <thead>
            <TableRow>
              {pjcolumns.map((column) => (
                <TableCell
                  key={column.id}
                  align={column.align}
                  style={{ minWidth: column.minWidth }}
                >
                  {column.label}
                </TableCell>
              ))}
            </TableRow>
          </thead>
          <tbody>
            {filteredRows
              .slice(projectInfo * rowsPerPage, projectInfo * rowsPerPage + rowsPerPage)
              .map((row) => (
                <TableRow
                  hover
                  role="checkbox"
                  tabIndex={-1}
                  key={row.pjid}
                  onClick={() => handleRowClick(row.pjname, row.pjid)}
                  onContextMenu={(e) => {
                    e.preventDefault();
                    setDeleteId(row.pjid);
                    handleMenuOpen(e);
                  }}
                >
                  {pjcolumns.map((column) => {
                    if (column.id !== "pjid") {
                      const value = row[column.id];
                      return (
                        <TableCell key={column.id} align={column.align}>
                          {column.format && typeof value === "number" ? column.format(value) : value}
                        </TableCell>
                      );
                    }
                    return null;
                  })}
                </TableRow>
              ))}
          </tbody>
        </Table>
      </TableContainer>
      <TablePagination
        rowsPerPageOptions={[5, 10, 20]}
        component="div"
        count={rows.length}
        rowsPerPage={rowsPerPage}
        page={projectInfo}
        onPageChange={handleChangePage}
        onRowsPerPageChange={handleChangeRowsPerPage}
      />
      {isManager && (
        <Menu anchorEl={anchorEl} open={Boolean(anchorEl)} onClose={handleMenuClose}>
          <MenuItem onClick={handleDelete}>删除项目</MenuItem>
        </Menu>
      )}
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
  );
});

export default ProjectTable;
