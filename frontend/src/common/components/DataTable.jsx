import React, { useState } from 'react';
import PropTypes from 'prop-types';
import Paper from "@mui/material/Paper";
import Table from "@mui/material/Table";
import TableCell from "@mui/material/TableCell";
import TableContainer from "@mui/material/TableContainer";
import TablePagination from "@mui/material/TablePagination";
import TableRow from "@mui/material/TableRow";
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import SearchBox from './SearchBox';

const DataTable = ({ columns, data, onDelete, searchLabel, onRowClick }) => {
  const [searchQuery, setSearchQuery] = useState("");
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [anchorEl, setAnchorEl] = useState(null);
  const [deleteId, setDeleteId] = useState(null);

  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(+event.target.value);
    setPage(0);
  };
  // 打开右键菜单
  const handleMenuOpen = (event) => {
    setAnchorEl(event.currentTarget);
  };

  // 关闭右键菜单
  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleDelete = () => {
    onDelete(deleteId);
    handleMenuClose();
  };

  const filteredRows = data.filter((row) =>
    row.name?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <Paper sx={{ width: "90%", overflow: "hidden", padding: "20px" }}>
      <SearchBox
        label={searchLabel}
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
      />
      <TableContainer sx={{ maxHeight: 440 }}>
        <Table stickyHeader aria-label="data table">
          <thead>
            <TableRow>
              {columns.map((column) => (
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
              .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
              .map((row) => (
                <TableRow
                  hover
                  role="checkbox"
                  tabIndex={-1}
                  key={row.id}
                  onClick={() => onRowClick(row.name, row.id)}
                  onContextMenu={(e) => {
                    e.preventDefault();
                    setDeleteId(row.id);
                    handleMenuOpen(e);
                  }}
                >
                  {columns.map((column) => {
                    if (column.id !== 'id') {
                      const value = row[column.id];
                      return (
                        <TableCell key={column.id} align={column.align}>
                          {column.format && typeof value === "number"
                            ? column.format(value)
                            : value}
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
        count={filteredRows.length}
        rowsPerPage={rowsPerPage}
        page={page}
        onPageChange={handleChangePage}
        onRowsPerPageChange={handleChangeRowsPerPage}
      />
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={handleDelete}>删除</MenuItem>
      </Menu>
    </Paper>
  );
};

DataTable.propTypes = {
  columns: PropTypes.array.isRequired,
  data: PropTypes.array.isRequired,
  onDelete: PropTypes.func.isRequired,
  searchLabel: PropTypes.string.isRequired,
  onRowClick: PropTypes.func.isRequired,
};

export default DataTable;

