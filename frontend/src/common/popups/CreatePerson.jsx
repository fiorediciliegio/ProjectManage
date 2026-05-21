import React, { useState } from "react";
import axios from "../api/client.js";
import { Box, TextField, Typography } from "@mui/material";
import SelectBox from "../components/SelectBox.jsx";
import InputBoxML from "../components/InputBoxML.jsx";
import CommonCreate from "./CommonCreate";
import { personroles } from "../constants/PERSON_INFO.js";

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export default function CreatePerson({ onClose }) {
  const [personInfo, setPersonInfo] = useState({
    pername: "",
    pernumber: "",
    perrole: "",
    permail: "",
    perdescription: "",
  });
  const [fieldErrors, setFieldErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [submitError, setSubmitError] = useState(null);

  const isEmailInvalid = personInfo.permail !== "" && !EMAIL_PATTERN.test(personInfo.permail);

  const handleChange = (value, fieldName) => {
    const fieldValue = value.target.value;
    setPersonInfo({ ...personInfo, [fieldName]: fieldValue });

    if (fieldName === "pernumber") {
      setFieldErrors((prev) => ({ ...prev, pernumber: "" }));
    }
    if (fieldName === "permail") {
      setFieldErrors((prev) => ({ ...prev, permail: "" }));
    }
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
        value={personInfo[fieldName]}
        onChange={(event) => handleChange(event, fieldName)}
        error={Boolean(errorText)}
        fullWidth
      />
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
    if (isEmailInvalid) {
      setFieldErrors((prev) => ({ ...prev, permail: "请输入正确的邮箱" }));
      return;
    }

    setLoading(true);
    setSubmitError(null);
    setFieldErrors({});

    try {
      await axios.post("http://localhost:8000/persons/", personInfo);
      onClose();
    } catch (err) {
      const responseData = err.response?.data;
      const backendNumberError = getBackendFieldError(responseData, "pernumber");
      if (backendNumberError) {
        setFieldErrors((prev) => ({ ...prev, pernumber: backendNumberError }));
      } else {
        setSubmitError(new Error(responseData?.message || err.message));
      }
    } finally {
      setLoading(false);
    }
  };

  const fields = [
    {
      component: renderTextField({ label: "姓名", fieldName: "pername" }),
      width: 6,
    },
    {
      component: renderTextField({
        label: "编号",
        fieldName: "pernumber",
        errorText: fieldErrors.pernumber,
      }),
      width: 6,
    },
    {
      component: renderTextField({
        label: "邮箱",
        fieldName: "permail",
        errorText: fieldErrors.permail || (isEmailInvalid ? "请输入正确的邮箱" : ""),
      }),
      width: 6,
    },
    {
      component: <SelectBox set={personroles} label="职位" value={personInfo.perrole} onChange={(event) => handleChange(event, "perrole")} width="25ch" />,
      width: 6,
    },
    {
      component: <InputBoxML label="更多描述" value={personInfo.perdescription} onChange={(event) => handleChange(event, "perdescription")} />,
      width: 12,
    },
  ];

  return (
    <CommonCreate title="创建人员" fields={fields} onClose={onClose} onSubmit={onSubmit}>
      {loading && <p>正在提交...</p>}
      {submitError && <p style={{ color: "red" }}>提交失败: {submitError.message}</p>}
    </CommonCreate>
  );
}
