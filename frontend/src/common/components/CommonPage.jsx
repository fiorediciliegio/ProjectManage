import React from "react";
import { Grid } from "@mui/material";
import SideBar from "../components/SideBar.jsx";
import NavBarRO from "../components/NavBarRO.jsx";
import { useAuth } from '../hooks/AuthContext';

export default function CommonPage({pageName, projectName,projectId,children}) {
  const { user } = useAuth();
  const { logout } = useAuth(); 

  return (
    <Grid container spacing={2}>
      {/*妞ゅ爼鍎寸€佃壈鍩呴弽?*/}
      <Grid item xs={12}>
          <NavBarRO
            title={`ManageYourProject--${pageName}`}
            projectName={projectName}
            user={user} 
            onLogout={logout}
          />
      </Grid>
      <Grid item container spacing={2}>
        {/*娓氀嗙珶閺?*/}
        <Grid
          item
          container
          justifyContent="center"
          alignItems="flex-start"
          xs={2}
        >
          <SideBar projectName={projectName} projectId={projectId}/>
        </Grid>
        {/*娑撴槒顩﹂崠鍝勭厵 */}
        <Grid item container xs={10} spacing={2} marginTop={2}>
            {children}
        </Grid>
      </Grid>
    </Grid>
  );
}

