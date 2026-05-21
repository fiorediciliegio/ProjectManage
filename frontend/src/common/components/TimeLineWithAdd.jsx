import React, { useState, useEffect } from "react";
import axios from '../api/client.js';
import {
  Grid,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Radio,
  RadioGroup,
  FormControlLabel,
  IconButton,
  Snackbar,
  Alert,
} from "@mui/material";
import { Timeline } from "antd";
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import dayjs from 'dayjs';
import AddCircleIcon from '@mui/icons-material/AddCircle';
import MoreVertIcon from '@mui/icons-material/MoreVert';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import { useAuth } from '../hooks/AuthContext';

export default function TimeLineWithAdd({ pjID, onTimelineUpdate }) {
  const [events, setEvents] = useState([]);
  const [open, setOpen] = useState(false);
  const [newEvent, setNewEvent] = useState("");
  const [newEventDescription, setNewEventDescription] = useState("");
  const [newEventDate, setNewEventDate] = useState(null);
  const [newEventStatus, setNewEventStatus] = useState('未处理');
  const [anchorEl, setAnchorEl] = useState(null);
  const [selectedNodeId, setSelectedNodeId] = useState(null);
  const [selectedNodeStatus, setSelectedNodeStatus] = useState("");
  const [searchKeyword, setSearchKeyword] = useState("");
  const [statusFilter, setStatusFilter] = useState('全部');
  const [snackbar, setSnackbar] = useState({ open: false, message: '' });
  const { user } = useAuth();
  const isManager = Boolean(user);
  const filteredEvents = events.filter((event) => {
    const matchesName = String(event.eventname || '')
      .toLowerCase()
      .includes(searchKeyword.trim().toLowerCase());
    const matchesStatus = statusFilter === '全部' || event.eventstatus === statusFilter;
    return matchesName && matchesStatus;
  });

  const fetchEvents = () => {
    if (!pjID) return;
    axios
      .get(`http://localhost:8000/projects/${pjID}/nodes/`)
      .then((res) => {
        const projectNodes = res.data?.data?.project_nodes || [];
        const eventData = projectNodes.map((node) => ({
          eventid: node.pjn_id,
          eventname: node.pjn_name,
          eventdescription: node.pjn_des,
          eventdate: dayjs(node.pjn_ddl),
          eventstatus: node.pjn_status,
        }));
        eventData.sort((a, b) => a.eventdate - b.eventdate);
        setEvents(eventData);
      })
      .catch((error) => {
        console.error("Error fetching events:", error);
      });
  };

  useEffect(() => {
    fetchEvents();
  }, [pjID]);

  const handleOpenDialog = () => {
    setOpen(true);
  };

  const handleSnackbarClose = () => {
    setSnackbar({ open: false, message: '' });
  };

  const handleCloseDialog = () => {
    setOpen(false);
    setNewEvent("");
    setNewEventDescription("");
    setNewEventDate(null);
    setNewEventStatus('未处理');
    fetchEvents();
    if (onTimelineUpdate) {
      onTimelineUpdate();
    }
  };

  const handleSaveEvent = async () => {
    if (newEvent.trim() === "" || newEventDescription.trim() === "" || !newEventDate) {
      return;
    }

    const newEventData = {
      pjn_name: newEvent,
      pjn_des: newEventDescription,
      pjn_ddl: dayjs(newEventDate).format('YYYY-MM-DD'),
      pjn_status: newEventStatus,
      pj_id: pjID,
    };

    try {
      await axios.post("http://localhost:8000/project-nodes/", newEventData);
      handleCloseDialog();
      fetchEvents();
    } catch (error) {
      console.error("Error saving event:", error);
      setSnackbar({
        open: true,
        message: error.response?.data?.message || '创建节点失败',
      });
    }
  };

  const handleMenuOpen = (event, eventId, eventStatus) => {
    setSelectedNodeId(eventId);
    setSelectedNodeStatus(eventStatus);
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleDelete = async () => {
    try {
      await axios.delete(`http://localhost:8000/project-nodes/${selectedNodeId}/`);
      fetchEvents();
      if (onTimelineUpdate) {
        onTimelineUpdate();
      }
    } catch (error) {
      console.error("删除节点出错:", error);
      setSnackbar({
        open: true,
        message: error.response?.data?.message || '删除节点失败',
      });
    }
    handleMenuClose();
  };

  const handleStatusChange = (newStatus) => {
    axios
      .patch(`http://localhost:8000/project-nodes/${selectedNodeId}/`, { pjn_status: newStatus })
      .then(() => {
        handleMenuClose();
        fetchEvents();
        if (onTimelineUpdate) {
          onTimelineUpdate();
        }
      })
      .catch((error) => {
        console.error("Error updating event status", error);
        setSnackbar({
          open: true,
          message: error.response?.data?.message || '更新节点状态失败',
        });
        handleMenuClose();
      });
  };

  return (
    <Grid container direction="column" justifyContent="center" alignItems="flex-start">
      <Grid item container spacing={1} sx={{ width: '100%', mb: 1 }}>
        <Grid item xs={8}>
          <TextField
            label="搜索节点"
            placeholder="按节点事件名称搜索"
            value={searchKeyword}
            onChange={(e) => setSearchKeyword(e.target.value)}
            size="small"
            fullWidth
          />
        </Grid>
        <Grid item xs={4}>
          <TextField
            select
            label="状态"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            size="small"
            fullWidth
          >
            {['全部', '未处理', '进行中', '已完成'].map((status) => (
              <MenuItem key={status} value={status}>
                {status}
              </MenuItem>
            ))}
          </TextField>
        </Grid>
      </Grid>
      <Grid
        item
        container
        sx={{
          maxHeight: '70vh',
          overflowY: 'auto',
          overflowX: 'hidden',
          pr: 1,
          width: '100%',
        }}
      >
        <Timeline>
          {filteredEvents.map((event) => (
            <Timeline.Item key={event.eventid}>
              <p>{event.eventname}</p>
              <p>{event.eventdescription}</p>
              <p>{dayjs(event.eventdate).format('YYYY-MM-DD')}</p>
              <p>状态: {event.eventstatus}</p>
              {isManager && (
                <IconButton onClick={(e) => handleMenuOpen(e, event.eventid, event.eventstatus)}>
                  <MoreVertIcon />
                </IconButton>
              )}
            </Timeline.Item>
          ))}
        </Timeline>
      </Grid>
      {isManager && (
        <Grid item container justifyContent="flex-end">
          <IconButton onClick={handleOpenDialog}>
            <AddCircleIcon />
          </IconButton>
        </Grid>
      )}
      <Dialog open={open} onClose={handleCloseDialog}>
        <DialogTitle>创建节点</DialogTitle>
        <DialogContent>
          <TextField
            label="节点事件"
            value={newEvent}
            onChange={(e) => setNewEvent(e.target.value)}
            size="small"
            fullWidth
            margin="normal"
          />
          <TextField
            multiline
            label="描述"
            value={newEventDescription}
            onChange={(e) => setNewEventDescription(e.target.value)}
            size="small"
            fullWidth
            margin="normal"
          />
          <LocalizationProvider dateAdapter={AdapterDayjs}>
            <DatePicker
              value={newEventDate}
              onChange={(date) => setNewEventDate(date)}
              renderInput={(params) => <TextField {...params} size="small" fullWidth margin="normal" inputFormat="yyyy-MM-dd" />}
            />
          </LocalizationProvider>
          <RadioGroup row value={newEventStatus} onChange={(e) => setNewEventStatus(e.target.value)}>
            <FormControlLabel value="未处理" control={<Radio />} label="未处理" />
            <FormControlLabel value="进行中" control={<Radio />} label="进行中" />
            <FormControlLabel value="已完成" control={<Radio />} label="已完成" />
          </RadioGroup>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>取消</Button>
          <Button onClick={handleSaveEvent} variant="contained" autoFocus>
            保存
          </Button>
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
      <Menu anchorEl={anchorEl} open={Boolean(anchorEl)} onClose={handleMenuClose}>
        {selectedNodeStatus === '未处理' && (
          <MenuItem onClick={() => handleStatusChange('进行中')}>标记为进行中</MenuItem>
        )}
        {selectedNodeStatus === '进行中' && (
          <MenuItem onClick={() => handleStatusChange('已完成')}>标记为已完成</MenuItem>
        )}
        <MenuItem onClick={handleDelete}>删除节点</MenuItem>
      </Menu>
    </Grid>
  );
}
