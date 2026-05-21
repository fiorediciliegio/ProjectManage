import React, { useEffect, useState } from "react";
import axios from "../api/client.js";
import { Box, Grid, MenuItem, TextField, Typography } from "@mui/material";
import SelectBox from "../components/SelectBox.jsx";
import InputBoxML from "../components/InputBoxML.jsx";
import TimePicker from "../components/TimePicker.jsx";
import { currencies } from "../constants/UNIT.js";
import { projecttype } from "../constants/PROJECT_INFO.js";
import CommonCreate from "./CommonCreate";

export default function CreatePj({ onClose }) {
  const [projectInfo, setProjectInfo] = useState({
    pjname: "",
    pjnumber: "",
    pjmanager: "",
    pjmanager_id: "",
    pjtype: "",
    pjvalue: "",
    pjcurrency: "",
    pjstart_date: "",
    pjend_date: "",
    pjaddress: "",
    pjdescription: "",
  });
  const [projectManagers, setProjectManagers] = useState([]);
  const [fieldErrors, setFieldErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [managersLoading, setManagersLoading] = useState(false);
  const [submitError, setSubmitError] = useState(null);

  useEffect(() => {
    let isMounted = true;
    const fetchProjectManagers = async () => {
      setManagersLoading(true);
      try {
        const response = await axios.get("http://localhost:8000/persons/");
        const managers = (response.data?.data?.persons || []).filter(
          (person) => person.perrole === "项目经理"
        );
        if (isMounted) {
          setProjectManagers(managers);
        }
      } catch (err) {
        if (isMounted) {
          setSubmitError(new Error(err.response?.data?.message || "获取项目经理列表失败"));
        }
      } finally {
        if (isMounted) {
          setManagersLoading(false);
        }
      }
    };

    fetchProjectManagers();
    return () => {
      isMounted = false;
    };
  }, []);

  const handleChange = (value, fieldName) => {
    const fieldValue = fieldName === "pjstart_date" || fieldName === "pjend_date"
      ? value
      : value.target.value;

    setProjectInfo({ ...projectInfo, [fieldName]: fieldValue });

    if (fieldName === "pjnumber") {
      setFieldErrors((prev) => ({ ...prev, pjnumber: "" }));
    }
  };

  const handleManagerChange = (event) => {
    const managerId = event.target.value;
    const manager = projectManagers.find((item) => String(item.perid) === String(managerId));
    setProjectInfo({
      ...projectInfo,
      pjmanager_id: managerId,
      pjmanager: manager?.pername || "",
    });
    setFieldErrors((prev) => ({ ...prev, pjmanager_id: "" }));
  };

  const renderTextField = ({ label, fieldName, errorText }) => (
    <Box sx={{ m: 1, width: "25ch" }}>
      <Typography>{label}</Typography>
      {errorText && (
        <Typography color="error" variant="body2" sx={{ mt: 0.5 }}>
          {errorText}
        </Typography>
      )}
      <TextField
        variant="outlined"
        value={projectInfo[fieldName]}
        onChange={(event) => handleChange(event, fieldName)}
        error={Boolean(errorText)}
        fullWidth
      />
    </Box>
  );

  const renderManagerSelect = () => (
    <Box sx={{ m: 1, width: "25ch" }}>
      <Typography>项目负责人</Typography>
      <TextField
        select
        variant="outlined"
        value={projectInfo.pjmanager_id}
        onChange={handleManagerChange}
        error={Boolean(fieldErrors.pjmanager_id)}
        helperText={fieldErrors.pjmanager_id || (managersLoading ? "正在加载项目经理..." : "只能选择职位为项目经理的人员")}
        fullWidth
      >
        {projectManagers.map((manager) => (
          <MenuItem key={manager.perid} value={manager.perid}>
            {manager.pername}
          </MenuItem>
        ))}
      </TextField>
    </Box>
  );

  const getBackendFieldError = (responseData, fieldName) => {
    const fieldError = responseData?.data?.[fieldName];
    if (Array.isArray(fieldError)) {
      return fieldError[0];
    }
    return fieldError || "";
  };

  const onSubmit = async () => {
    setLoading(true);
    setSubmitError(null);
    setFieldErrors({});

    try {
      await axios.post("http://localhost:8000/projects/", projectInfo);
      onClose();
    } catch (err) {
      const responseData = err.response?.data;
      const backendNumberError = getBackendFieldError(responseData, "pjnumber");
      const backendManagerError = getBackendFieldError(responseData, "pjmanager_id");
      if (backendNumberError || backendManagerError) {
        setFieldErrors((prev) => ({
          ...prev,
          pjnumber: backendNumberError,
          pjmanager_id: backendManagerError,
        }));
      } else {
        setSubmitError(new Error(responseData?.message || err.message));
      }
    } finally {
      setLoading(false);
    }
  };

  const fields = [
    {
      component: renderTextField({ label: "项目名称", fieldName: "pjname" }),
      width: 6,
    },
    {
      component: <TimePicker label="项目开始时间" value={projectInfo.pjstart_date} onChange={(event) => handleChange(event, "pjstart_date")} />,
      width: 6,
    },
    {
      component: renderTextField({
        label: "项目编号",
        fieldName: "pjnumber",
        errorText: fieldErrors.pjnumber,
      }),
      width: 6,
    },
    {
      component: <TimePicker label="项目结束时间" value={projectInfo.pjend_date} onChange={(event) => handleChange(event, "pjend_date")} />,
      width: 6,
    },
    {
      component: renderManagerSelect(),
      width: 6,
    },
    {
      component: <InputBoxML label="项目地址" value={projectInfo.pjaddress} onChange={(event) => handleChange(event, "pjaddress")} />,
      width: 6,
    },
    {
      component: <SelectBox set={projecttype} label="项目类型" value={projectInfo.pjtype} onChange={(event) => handleChange(event, "pjtype")} width="25ch" />,
      width: 6,
    },
    {
      component: <InputBoxML label="项目描述" value={projectInfo.pjdescription} onChange={(event) => handleChange(event, "pjdescription")} />,
      width: 6,
    },
    {
      component: (
        <Grid container direction="row">
          <Grid item xs={8}>
            {renderTextField({ label: "项目价值", fieldName: "pjvalue" })}
          </Grid>
          <Grid item xs={4}>
            <SelectBox set={currencies} label="货币" value={projectInfo.pjcurrency} onChange={(event) => handleChange(event, "pjcurrency")} width="10ch" />
          </Grid>
        </Grid>
      ),
      width: 6,
    },
  ];

  return (
    <CommonCreate title="创建项目" fields={fields} onClose={onClose} onSubmit={onSubmit}>
      {loading && <p>正在提交...</p>}
      {submitError && <p style={{ color: "red" }}>提交失败: {submitError.message}</p>}
    </CommonCreate>
  );
}
