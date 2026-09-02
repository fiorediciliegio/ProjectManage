import React, { useState, useEffect, forwardRef, useImperativeHandle } from "react";
import axios from "../api/client.js";
import Paper from "@mui/material/Paper";
import Table from "@mui/material/Table";
import TableCell from "@mui/material/TableCell";
import TableContainer from "@mui/material/TableContainer";
import TablePagination from "@mui/material/TablePagination";
import TableRow from "@mui/material/TableRow";
import { percolumns } from "../constants/PERSON_INFO.js";
import SearchBox from "./SearchBox.jsx";
import Menu from "@mui/material/Menu";
import MenuItem from "@mui/material/MenuItem";
import Snackbar from "@mui/material/Snackbar";
import Alert from "@mui/material/Alert";
import { useAuth } from "../hooks/AuthContext";
import { DEFAULT_PAGE_SIZE, PAGE_SIZE_OPTIONS, emptyPagination, normalizePagination } from "../utils/pagination.js";

const PersonTable = forwardRef((props, ref) => {
  const [searchQuery, setSearchQuery] = useState("");
  const [personInfo, setPersonInfo] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(DEFAULT_PAGE_SIZE);
  const [pagination, setPagination] = useState(emptyPagination());
  const [rows, setRows] = useState([]);
  const [deleteId, setDeleteId] = useState(null);
  const [anchorEl, setAnchorEl] = useState(null);
  const [snackbar, setSnackbar] = useState({ open: false, message: '' });
  const { user } = useAuth();
  const isManager = Boolean(user);

  useEffect(() => {
    fetchPersonData(personInfo, rowsPerPage);
  }, [personInfo, rowsPerPage]);

  const fetchPersonData = (page = personInfo, pageSize = rowsPerPage) => {
    axios
      .get("http://localhost:8000/persons/", {
        params: {
          page: page + 1,
          page_size: pageSize,
        },
      })
      .then((res) => {
        const personList = res.data?.data?.persons || [];
        const nextPagination = normalizePagination(
          res.data?.data?.pagination,
          page,
          pageSize,
          personList.length
        );
        const extractedData = personList.map((item) => ({
          pername: item.pername,
          pernumber: item.pernumber,
          permail: item.permail,
          perrole: item.perrole,
          perid: item.perid,
        }));
        setRows(extractedData);
        setPagination(nextPagination);
      })
      .catch((error) => {
        console.error("Error fetching data from server", error);
      });
  };

  const handleChangePage = (event, newPage) => {
    setPersonInfo(newPage);
  };

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(+event.target.value);
    setPersonInfo(0);
  };

  const refreshFirstPage = () => {
    if (personInfo === 0) {
      fetchPersonData(0, rowsPerPage);
      return;
    }
    setPersonInfo(0);
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
      .delete(`http://localhost:8000/persons/${deleteId}/`)
      .then(() => {
        refreshFirstPage();
        handleMenuClose();
      })
      .catch((error) => {
        console.error("Error deleting person", error);
        setSnackbar({
          open: true,
          message: error.response?.data?.message || '删除人员失败',
        });
        handleMenuClose();
      });
  };

  const normalizedSearchQuery = searchQuery.toLowerCase();
  const filteredRows = rows.filter(
    (row) =>
      String(row.pername || "").toLowerCase().includes(normalizedSearchQuery) ||
      String(row.pernumber || "").toLowerCase().includes(normalizedSearchQuery)
  );

  useImperativeHandle(ref, () => ({
    refreshData() {
      fetchPersonData(personInfo, rowsPerPage);
    },
  }));

  return (
    <Paper sx={{ width: "90%", overflow: "hidden", padding: "20px" }}>
      <SearchBox
        label="搜索人员姓名或编号..."
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
      />
      <TableContainer sx={{ maxHeight: 440 }}>
        <Table stickyHeader aria-label="person table">
          <thead>
            <TableRow>
              {percolumns.map((column) => (
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
              .map((row) => (
                <TableRow
                  hover
                  role="checkbox"
                  tabIndex={-1}
                  key={row.perid}
                  onContextMenu={(e) => {
                    e.preventDefault();
                    setDeleteId(row.perid);
                    handleMenuOpen(e);
                  }}
                >
                  {percolumns.map((column) => {
                    if (column.id !== "perid") {
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
        rowsPerPageOptions={PAGE_SIZE_OPTIONS}
        component="div"
        count={pagination.total}
        rowsPerPage={rowsPerPage}
        page={personInfo}
        onPageChange={handleChangePage}
        onRowsPerPageChange={handleChangeRowsPerPage}
      />
      {isManager && (
        <Menu anchorEl={anchorEl} open={Boolean(anchorEl)} onClose={handleMenuClose}>
          <MenuItem onClick={handleDelete}>删除人员</MenuItem>
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

export default PersonTable;
