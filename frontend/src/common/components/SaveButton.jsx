import * as React from "react";
import {Button} from "@mui/material";

export default function SaveButton({ onClick, children }) {
  return (
    <Button 
    variant="contained" 
    onClick={onClick}  
    sx={{ width: "100px", height: "40px" }}
    >
      {children}
    </Button>
  );
}

