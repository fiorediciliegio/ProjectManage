import * as React from "react";
import { Box, TextField, Grid } from "@mui/material";

export default function ReadOnlyText({ label, value}) {
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
          <TextField 
          variant="standard" 
          value={value} 
          InputProps={{
                readOnly: true,
              }}/>
        </Box>
      </Grid>
    </Grid>
  );
}

