import * as React from "react";
import { Box, TextField } from "@mui/material";

export default function SearchBox({ label,value,onChange }) {
  return (
    <Box
      sx={{
        width: 500,
        maxWidth: "100%",
        position: "relative", 
        zIndex: 0, 
      }}
    >
      <TextField fullWidth label={label} id="search" value={value} onChange={onChange}/>
    </Box>
  );
}

