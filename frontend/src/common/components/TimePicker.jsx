import React, { useState } from "react";
import { Box, Grid, TextField } from "@mui/material";
import { DatePicker } from "@mui/x-date-pickers/DatePicker";
import { AdapterDayjs } from "@mui/x-date-pickers/AdapterDayjs";
import { LocalizationProvider } from "@mui/x-date-pickers/LocalizationProvider";
import dayjs from "dayjs";

const TimePicker = ({ label, value, onChange }) => {
  const [selectedDate, setSelectedDate] = useState(value ? dayjs(value).toDate() : null);

  const handleDateChange = (date) => {
    const dateString = date ? dayjs(date).format("YYYY-MM-DD") : "";
    setSelectedDate(date);
    onChange(dateString);
  };

  return (
    <Grid container direction="column" alignItems="flex-start">
      <Grid item container>
        <Box
          component="form"
          sx={{
            "& > :not(style)": { m: 1, width: "25ch" },
          }}
          noValidate
          autoComplete="off"
        >
          <label>{label}</label>
        </Box>
      </Grid>
      <Grid item container>
        <Box
          component="form"
          sx={{
            "& > :not(style)": { m: 1, width: "25ch " },
          }}
          noValidate
          autoComplete="off"
        >
          <LocalizationProvider dateAdapter={AdapterDayjs}>
            <DatePicker
              value={selectedDate}
              onChange={handleDateChange}
              renderInput={(params) => <TextField {...params} />}
            />
          </LocalizationProvider>
        </Box>
      </Grid>
    </Grid>
  );
};

export default TimePicker;

