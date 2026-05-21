import * as React from "react";
import { Box, TextField, MenuItem, Grid } from "@mui/material";

export default function SelectBox({ label, set, value, onChange, width }) {
  return (
    <Grid
      container
      direction="column"
      justifyContent="center"
      alignItems="flex-start"
    >
      <Grid item container>
        <Box
          component="form"
          sx={{
            "& > :not(style)": { m: 1, width: {width} },
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
            "& > :not(style)": { m: 1, width: {width} },
          }}
          noValidate
          autoComplete="off"
        >
          <TextField
            select
            value={value}
            onChange={onChange}
            defaultValue={set[0].value}
          >
            {set.map((option) => (
              <MenuItem key={option.value} value={option.value}>
                {option.label}
              </MenuItem>
            ))}
          </TextField>
        </Box>
      </Grid>
    </Grid>
  );
}

