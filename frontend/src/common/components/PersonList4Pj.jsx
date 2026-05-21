import React, { useState, useEffect, Fragment, forwardRef, useImperativeHandle } from 'react';
import List from '@mui/material/List';
import {
  ListItem,
  ListItemText,
  Divider,
  ListItemAvatar,
  Avatar,
  Typography,
  Paper,
  Collapse,
  IconButton,
  Menu,
  MenuItem,
  Snackbar,
  Alert,
} from '@mui/material';
import { deepPurple, lightBlue } from '@mui/material/colors';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import axios from '../api/client.js';

const PersonList = forwardRef((props, ref) => {
  const [personnel, setPersonnel] = useState([]);
  const [expanded, setExpanded] = useState(false);
  const [anchorEl, setAnchorEl] = useState(null);
  const [selectedPerson, setSelectedPerson] = useState(null);
  const [snackbar, setSnackbar] = useState({ open: false, message: '' });

  const fetchData = () => {
    axios
      .get(`http://localhost:8000/projects/${props.projectId}/persons/`)
      .then((response) => {
        console.log('Personnel data:', response.data);
        setPersonnel(response.data?.data?.persons || []);
      })
      .catch((error) => {
        console.error('Error fetching personnel data:', error);
      });
  };

  useEffect(() => {
    fetchData();
  }, []);

  useImperativeHandle(ref, () => ({
    refreshData() {
      fetchData();
    },
  }));

  const handleExpandClick = () => {
    setExpanded(!expanded);
  };

  const handleContextMenu = (event, person) => {
    event.preventDefault();
    setAnchorEl(event.currentTarget);
    setSelectedPerson(person);
  };

  const handleClose = () => {
    setAnchorEl(null);
    setSelectedPerson(null);
  };

  const handleCloseSnackbar = () => {
    setSnackbar({ open: false, message: '' });
  };

  const handleRemovePerson = () => {
    if (selectedPerson) {
      axios
        .delete(`http://localhost:8000/projects/${props.projectId}/persons/${selectedPerson.perid}/`)
        .then(() => {
          setPersonnel(personnel.filter((person) => person.perid !== selectedPerson.perid));
          handleClose();
          if (props.onUpdate) {
            props.onUpdate();
          }
        })
        .catch((error) => {
          console.error('Error removing person:', error);
          setSnackbar({
            open: true,
            message: error.response?.data?.message || '移除项目人员失败',
          });
          handleClose();
        });
    }
  };

  const renderSecondary = (person) => (
    <Fragment>
      <Typography sx={{ display: 'inline' }} component="span" variant="body2" color="text.primary">
        {person.perrole}
      </Typography>
      {`  |  ${person.permail}`}
    </Fragment>
  );

  return (
    <Paper style={{ padding: '15px' }}>
      <List sx={{ width: '100%', maxWidth: 360 }}>
        {personnel.slice(0, 3).map((person, index) => (
          <Fragment key={index}>
            <ListItem alignItems="flex-start" onContextMenu={(event) => handleContextMenu(event, person)}>
              <ListItemAvatar>
                <Avatar sx={{ bgcolor: deepPurple[500] }}>{person.pername.charAt(0)}</Avatar>
              </ListItemAvatar>
              <ListItemText primary={person.pername} secondary={renderSecondary(person)} />
            </ListItem>
            <Divider variant="inset" component="li" />
          </Fragment>
        ))}
        {personnel.length > 3 && (
          <Fragment>
            <ListItem>
              <IconButton aria-expanded={expanded} aria-label="show more" onClick={handleExpandClick}>
                <ExpandMoreIcon />
              </IconButton>
            </ListItem>
            <Collapse in={expanded} timeout="auto" unmountOnExit>
              {personnel.slice(3).map((person, index) => (
                <Fragment key={index}>
                  <ListItem alignItems="flex-start" onContextMenu={(event) => handleContextMenu(event, person)}>
                    <ListItemAvatar>
                      <Avatar sx={{ bgcolor: lightBlue[500] }}>{person.pername.charAt(0)}</Avatar>
                    </ListItemAvatar>
                    <ListItemText primary={person.pername} secondary={renderSecondary(person)} />
                  </ListItem>
                  <Divider variant="inset" component="li" />
                </Fragment>
              ))}
            </Collapse>
          </Fragment>
        )}
      </List>
      <Menu anchorEl={anchorEl} open={Boolean(anchorEl)} onClose={handleClose}>
        <MenuItem onClick={handleRemovePerson}>移除人员</MenuItem>
      </Menu>
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
    </Paper>
  );
});

export default PersonList;
