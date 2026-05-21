import React, { useRef } from "react";
import { Grid } from "@mui/material";
import PersonList from "../components/PersonList4Pj.jsx";
import BasicBarH from "../components/BarChartH.jsx";
import ChipSelectBox from "../components/ChipSelectBox.jsx";
import CommonPage from "../components/CommonPage.jsx";
import useProjectParams from "../hooks/useProjectParams.js";
import { useAuth } from "../hooks/AuthContext";

export default function PersonnelPage() {
  const { projectName, projectId } = useProjectParams();
  const personListRef = useRef(null);
  const basicBarHRef = useRef(null);
  const { user } = useAuth();
  const isManager = Boolean(user);

  const handlePersonUpdate = () => {
    if (personListRef.current) {
      personListRef.current.refreshData();
    }
    if (basicBarHRef.current) {
      basicBarHRef.current.refreshData();
    }
  };

  return (
    <CommonPage pageName="人员管理" projectId={projectId} projectName={projectName}>
      <Grid item container spacing={2}>
        <Grid item container xs={5} marginTop={2} justifyContent="flex-start" alignItems="flex-start">
          <PersonList projectId={projectId} ref={personListRef} onUpdate={handlePersonUpdate} />
        </Grid>
        <Grid item container xs={7} spacing={2} justifyContent="flex-start" alignItems="flex-start">
          <BasicBarH pjID={projectId} ref={basicBarHRef} />
        </Grid>
      </Grid>
      <Grid item container marginTop={4}>
        {isManager && (
          <Grid item container xs={12} spacing={2} justifyContent="flex-start" alignItems="center">
            <ChipSelectBox projectId={projectId} onUpdate={handlePersonUpdate} />
          </Grid>
        )}
      </Grid>
    </CommonPage>
  );
}

