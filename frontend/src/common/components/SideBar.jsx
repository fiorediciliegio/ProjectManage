import * as React from "react";
import { Button, ButtonGroup, Box, Typography } from "@mui/material";
import { useNavigate } from "react-router-dom";

const buttons1 = [
  { key: "one", text: "项目规划", route: "/PlanPage" },
  { key: "two", text: "人员管理", route: "/PersonnelPage" },
  { key: "three", text: "成本控制", route: "/CostPage" },
  { key: "four", text: "质量监测", route: "/QualityPage" },
  { key: "five", text: "安全监测", route: "/SafetyPage" },
];

const buttons2 = [
  { key: "6-1", text: "文档", route: "/File" },
];

export default function SideBar({ projectName, projectId }) {
  const navigate = useNavigate();

  const handleClick = (route) => {
    navigate(`${route}?projectName=${projectName}&projectId=${projectId}`);
  };

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        "& > *": {
          m: 1,
        },
      }}
    >
      <Typography
        variant="h6"
        noWrap
        component="span"
        sx={{
          fontWeight: 400,
          letterSpacing: ".1rem",
          textDecoration: "none",
        }}
      >
        Management
      </Typography>
      <ButtonGroup
        orientation="vertical"
        aria-label="Vertical button group"
        variant="text"
        color="primary"
        size="large"
        fullWidth
      >
        {buttons1.map((button) => (
          <Button key={button.key} onClick={() => handleClick(button.route)}>
            {button.text}
          </Button>
        ))}
      </ButtonGroup>
      <Typography
        variant="h6"
        noWrap
        component="span"
        sx={{
          mt: 2,
          fontWeight: 400,
          letterSpacing: ".1rem",
          textDecoration: "none",
        }}
      >
        Archive
      </Typography>
      <ButtonGroup
        orientation="vertical"
        aria-label="Vertical button group"
        variant="text"
        color="primary"
        size="large"
        fullWidth
      >
        {buttons2.map((button) => (
          <Button key={button.key} onClick={() => handleClick(button.route)}>
            {button.text}
          </Button>
        ))}
      </ButtonGroup>
    </Box>
  );
}

