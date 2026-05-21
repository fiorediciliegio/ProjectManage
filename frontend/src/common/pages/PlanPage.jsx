import React, { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import Axios from "../api/client.js";
import { Alert, Button, Grid, Snackbar } from "@mui/material";
import SideBar from "../components/SideBar.jsx";
import NavBarWithSelect from "../components/NavBarWithSelect.jsx";
import InfoDisplay from "../components/InfoDisplay.jsx";
import TimeLineWithAdd from "../components/TimeLineWithAdd.jsx";
import BasicPie from "../components/PieChart.jsx";
import useProjectParams from "../hooks/useProjectParams.js";
import { useAuth } from '../hooks/AuthContext';
import EditProject from "../popups/EditProject.jsx";

export default function PlanPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const { projectName, projectId } = useProjectParams();
  const [selectedProjectInfo, setSelectedProjectInfo] = useState(null);
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [snackbar, setSnackbar] = useState({ open: false, message: "" });
  const basicPieRef = useRef(null);

  const handleSelectProject = async (projectName, projectId) => {
    try {
      const response = await Axios.get(`http://localhost:8000/projects/${projectId}/`);
      setSelectedProjectInfo(response.data?.data?.project || null);
      navigate(`?projectName=${projectName}&projectId=${projectId}`);
    } catch (error) {
      console.error("Error fetching project information:", error);
    }
  };

  useEffect(() => {
    handleSelectProject(projectName, projectId);
  }, [projectName, projectId]);

  const handleTimelineUpdate = () => {
    if (basicPieRef.current) {
      basicPieRef.current.refreshData();
    }
  };

  const handleProjectUpdated = (project) => {
    if (project) {
      setSelectedProjectInfo(project);
    } else {
      handleSelectProject(projectName, projectId);
    }
  };

  const handleCloseSnackbar = () => {
    setSnackbar({ open: false, message: "" });
  };

  return (
    <Grid container spacing={2}>
      <Grid item xs={12}>
        <NavBarWithSelect
          title="ManageYourProject--项目规划"
          defaultSelectedProject={projectId}
          onSelectProject={handleSelectProject}
          user={user}
          onLogout={logout}
        />
      </Grid>
      <Grid item container xs={12} spacing={2}>
        <Grid item container justifyContent="center" alignItems="flex-start" xs={2}>
          <SideBar projectName={projectName} projectId={projectId} />
        </Grid>
        <Grid item container xs={6} direction="column" spacing={2}>
          <Grid item container justifyContent="center" alignContent="center">
            <BasicPie pjID={projectId} ref={basicPieRef} />
          </Grid>
          <Grid item>
            <Grid container justifyContent="center" sx={{ mb: 1 }}>
              <Button
                variant="contained"
                onClick={() => setIsEditOpen(true)}
                disabled={!selectedProjectInfo}
              >
                修改项目详情
              </Button>
            </Grid>
            <InfoDisplay
              line1={`项目编号：${selectedProjectInfo ? selectedProjectInfo.pjnumber : ""}`}
              line2={`负责人：${selectedProjectInfo ? selectedProjectInfo.pjmanager : ""}`}
              line3={`项目价值：${selectedProjectInfo ? `${selectedProjectInfo.pjvalue} ${selectedProjectInfo.pjcurrency}` : ""}`}
              line4={`项目起止日期：${selectedProjectInfo ? `${selectedProjectInfo.pjstart_date} 至 ${selectedProjectInfo.pjend_date}` : ""}`}
              line5={`项目地址：${selectedProjectInfo ? selectedProjectInfo.pjaddress : ""}`}
              line6={`项目描述：${selectedProjectInfo ? selectedProjectInfo.pjdescription : ""}`}
            />
          </Grid>
        </Grid>
        <Grid item container xs={4} alignItems="flex-start" direction="column">
          <p>节点时间轴：</p>
          <Grid item sx={{ width: '100%' }}>
            <TimeLineWithAdd pjID={projectId} onTimelineUpdate={handleTimelineUpdate} />
          </Grid>
        </Grid>
      </Grid>
      {isEditOpen && selectedProjectInfo && (
        <EditProject
          project={selectedProjectInfo}
          onClose={() => setIsEditOpen(false)}
          onUpdated={handleProjectUpdated}
          onError={(message) => setSnackbar({ open: true, message })}
        />
      )}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={3000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: "bottom", horizontal: "right" }}
      >
        <Alert onClose={handleCloseSnackbar} severity="error" sx={{ width: "100%" }}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Grid>
  );
}
