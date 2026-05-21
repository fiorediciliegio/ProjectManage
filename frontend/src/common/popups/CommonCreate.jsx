import React from "react";
import Modal from "react-modal";
import { Grid } from "@mui/material";
import TopBar from "../components/TopBar.jsx";
import SaveButton from "../components/SaveButton.jsx";

Modal.setAppElement("#root");

const CommonCreate = ({ title, fields, onClose, onSubmit, children }) => {
  return (
    <Modal
      isOpen={true}
      onRequestClose={onClose}
      style={{
        overlay: { zIndex: 1300 },
        content: { width: "60%", height: "80%", margin: "auto", zIndex: 1301 },
      }}
    >
      <div style={{ width: "100%", display: "flex", flexDirection: "column" }}>
        <TopBar title={title} close={onClose} />
        <Grid container spacing={2} style={{ margin: "10px" }}>
          {fields.map((field, index) => (
            <Grid item xs={field.width || 12} key={index}>
              {field.component}
            </Grid>
          ))}
          {children && (
            <Grid item xs={12}>
              {children}
            </Grid>
          )}
          <Grid item container justifyContent="flex-end" alignItems="center" marginRight={4}>
            <SaveButton children="保存" onClick={onSubmit} />
          </Grid>
        </Grid>
      </div>
    </Modal>
  );
};

export default CommonCreate;


