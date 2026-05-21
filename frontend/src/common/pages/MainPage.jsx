import React, { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Grid } from "@mui/material";
import OpenButton from "../components/OpenButton.jsx";
import NavBar from "../components/NavBar.jsx";
import CreatePerson from "../popups/CreatePerson.jsx";
import CreatePj from "../popups/CreatePj.jsx";
import ProjectTable from "../components/ProjectTable.jsx";
import PersonTable from "../components/PersonTable.jsx";
import { useAuth } from "../hooks/AuthContext";

export default function MainPage() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const projectTableRef = useRef(null);
  const personTableRef = useRef(null);
  const isManager = Boolean(user);

  const [isCreatePjOpen, setIsCreatePjOpen] = useState(false);
  const [isCreatePersonOpen, setIsCreatePersonOpen] = useState(false);

  const handleRowClick = (url) => {
    navigate(url);
  };

  const openCreatePj = () => {
    setIsCreatePjOpen(true);
  };

  const closeCreatePj = () => {
    setIsCreatePjOpen(false);
    if (projectTableRef.current) {
      projectTableRef.current.refreshData();
    }
  };

  const openCreatePerson = () => {
    setIsCreatePersonOpen(true);
  };

  const closeCreatePerson = () => {
    setIsCreatePersonOpen(false);
    if (personTableRef.current) {
      personTableRef.current.refreshData();
    }
  };

  return (
    <Grid container spacing={2}>
      <Grid item xs={12}>
        <NavBar title="ManageYourProject" user={user} onLogout={logout} />
      </Grid>
      <Grid item container spacing={2} margin={1}>
        <Grid item container xs={9} spacing={2} justifyContent="flex-end" alignItems="center">
          <Grid item xs={12}>
            <ProjectTable ref={projectTableRef} onRowClick={handleRowClick} />
          </Grid>
          <Grid item xs={12}>
            <PersonTable ref={personTableRef} />
          </Grid>
        </Grid>
        <Grid item container direction="column" spacing={2} xs={3}>
          {isManager && (
            <Grid item sx={{ marginRight: "100px" }}>
              <OpenButton onClick={openCreatePj}>创建项目</OpenButton>
              {isCreatePjOpen && <CreatePj onClose={closeCreatePj} />}
            </Grid>
          )}
          {isManager && (
            <Grid item sx={{ marginRight: "100px" }}>
              <OpenButton onClick={openCreatePerson}>添加人员</OpenButton>
              {isCreatePersonOpen && <CreatePerson onClose={closeCreatePerson} />}
            </Grid>
          )}
        </Grid>
      </Grid>
    </Grid>
  );
}

