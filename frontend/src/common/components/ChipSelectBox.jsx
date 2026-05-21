import React, { useState, useEffect } from 'react';
import { useTheme } from '@mui/material/styles';
import { Box, OutlinedInput, InputLabel, MenuItem, FormControl, Select, Chip, Grid, Snackbar, Alert } from '@mui/material';
import axios from '../api/client.js';
import SaveButton from '../components/SaveButton.jsx';
import useFetchData from '../hooks/useFetchData.js';

const ITEM_HEIGHT = 48;
const ITEM_PADDING_TOP = 8;
const MenuProps = {
  PaperProps: {
    style: {
      maxHeight: ITEM_HEIGHT * 4.5 + ITEM_PADDING_TOP,
      width: 250,
    },
  },
};

function getStyles(name, personName, theme) {
  return {
    fontWeight:
      personName.indexOf(name) === -1
        ? theme.typography.fontWeightRegular
        : theme.typography.fontWeightMedium,
  };
}

export default function ChipSelectBox({ projectId, onUpdate }) {
  const theme = useTheme();
  const [personName, setPersonName] = useState([]);
  const [snackbar, setSnackbar] = useState({ open: false, message: '' });
  const { data, error, fetchData } = useFetchData(`http://localhost:8000/persons/`);
  const people = data?.data?.persons || [];

  useEffect(() => {
    fetchData();
  }, []);

  const handleChange = (event) => {
    const {
      target: { value },
    } = event;
    setPersonName(typeof value === 'string' ? value.split(',') : value);
  };

  const handleCloseSnackbar = () => {
    setSnackbar({ open: false, message: '' });
  };

  const handleSaveClick = () => {
    axios
      .post(`http://localhost:8000/projects/${projectId}/persons/`, {
        person_ids: personName.map((person) => person.split(':')[3]),
      })
      .then((res) => {
        console.log('Person added to project successfully:', res.data);
        if (onUpdate) {
          onUpdate();
        }
        setPersonName([]);
      })
      .catch((error) => {
        console.error('Error adding person to project:', error);
        setSnackbar({
          open: true,
          message: error.response?.data?.message || '添加项目人员失败',
        });
      });
  };

  return (
    <Grid container spacing={2}>
      {error && <Grid item xs={12}><p>{error}</p></Grid>}
      <Grid item container xs={8} justifyContent="center" alignItems="center">
        <FormControl sx={{ m: 1, width: 600 }}>
          <InputLabel id="demo-multiple-chip-label">选择人员</InputLabel>
          <Select
            labelId="demo-multiple-chip-label"
            id="demo-multiple-chip"
            multiple
            value={personName}
            onChange={handleChange}
            input={<OutlinedInput id="select-multiple-chip" label="选择人员" />}
            renderValue={(selected) => (
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                {selected.map((value) => (
                  <Chip key={value} label={value.split(':')[0]} />
                ))}
              </Box>
            )}
            MenuProps={MenuProps}
          >
            {people.map((person) => (
              <MenuItem
                key={person.perid}
                value={`${person.pername}:${person.pernumber}:${person.perrole}:${person.perid}`}
                style={getStyles(person.pername, personName, theme)}
              >
                {`${person.pername} - NO.${person.pernumber} - ${person.perrole}`}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      </Grid>
      <Grid item container xs={4} justifyContent="flex-start" alignItems="center">
        <SaveButton children={'添加人员'} onClick={handleSaveClick} />
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
