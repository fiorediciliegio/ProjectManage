import * as React from "react";
import {Button} from "@mui/material";

export default function OpenButton({ onClick, children }) {
  return (
    <Button variant="contained" onClick={onClick}>
      {children}
    </Button>
  );
}

