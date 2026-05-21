import React, { useEffect, useState } from 'react';
import axios from '../api/client.js';
import { Button, FormControlLabel, Grid, IconButton, MenuItem, Radio, RadioGroup, TextField, Typography } from '@mui/material';
import { Delete, PhotoCamera } from '@mui/icons-material';
import TimePicker from '../components/TimePicker';
import InputBox from '../components/InputBox';
import InputBoxML from '../components/InputBoxML.jsx';
import CommonCreate from './CommonCreate';
import useFormSubmit from '../hooks/useFormSubmit.js';

export default function CreateSafety({ onClose, templates, projectId }) {
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [safetyStaff, setSafetyStaff] = useState([]);
  const [validationError, setValidationError] = useState('');
  const [report, setReport] = useState({
    srname: '',
    srpart: '',
    srperson: '',
    srins_date: '',
    srnumber: '',
    srsubitems: [{ name: '', requirement: '', result: '' }],
    srfeedback: '',
    srevaluation: '',
  });
  const [photos, setPhotos] = useState([]);
  const { handleSubmit, loading, error } = useFormSubmit();

  useEffect(() => {
    const fetchSafetyStaff = async () => {
      try {
        const response = await axios.get(`http://localhost:8000/projects/${projectId}/persons/`);
        setSafetyStaff((response.data?.data?.persons || []).filter((person) => person.perrole === '安全员'));
      } catch (err) {
        console.error('Error fetching safety staff:', err);
      }
    };

    if (projectId) fetchSafetyStaff();
  }, [projectId]);

  const handleTemplateChange = (event) => {
    const templateId = parseInt(event.target.value, 10);
    const template = templates.find((item) => item.id === templateId);
    if (!template) return;

    setSelectedTemplate(template);
    setReport((prevReport) => ({
      ...prevReport,
      srname: template.name,
      srsubitems: template.items.map((item) => ({
        name: item.name,
        requirement: item.value,
        result: '',
      })),
    }));
  };

  const handleChange = (value, fieldName, index) => {
    if (fieldName === 'srsubitems') {
      setReport((prevReport) => ({
        ...prevReport,
        srsubitems: prevReport.srsubitems.map((item, idx) => (
          idx === index ? { ...item, [value.field]: value.target.value } : item
        )),
      }));
      return;
    }

    setReport((prevReport) => ({
      ...prevReport,
      [fieldName]: value.target ? value.target.value : value,
    }));

    if (fieldName === 'srperson') {
      setValidationError('');
    }
  };

  const handlePhotoChange = (event) => {
    const files = Array.from(event.target.files || []);
    const newPhotos = files.map((file) => ({ file, preview: URL.createObjectURL(file) }));
    setPhotos((prevPhotos) => [...prevPhotos, ...newPhotos]);
  };

  const handleDeletePhoto = (index) => {
    setPhotos((prevPhotos) => prevPhotos.filter((_, currentIndex) => currentIndex !== index));
  };

  const submitForm = async () => {
    if (!report.srperson) {
      setValidationError('请选择当前项目中的安全员。');
      return;
    }

    const formData = new FormData();
    formData.append('report', JSON.stringify(report));
    photos.forEach((photo) => formData.append('images', photo.file));
    await handleSubmit(formData, `http://localhost:8000/projects/${projectId}/safety/reports/`, onClose);
  };

  const fields = [
    {
      component: (
        <TextField select label="选择模板" sx={{ width: '90%' }} value={selectedTemplate ? selectedTemplate.id : ''} onChange={handleTemplateChange}>
          {templates.map((template) => (
            <MenuItem key={template.id} value={template.id}>{template.name}</MenuItem>
          ))}
        </TextField>
      ),
      width: 12,
    },
    { component: <InputBox label="工程名称" value={report.srname} onChange={(event) => handleChange(event, 'srname')} />, width: 6 },
    { component: <InputBox label="检查部位及编号" value={report.srpart} onChange={(event) => handleChange(event, 'srpart')} />, width: 6 },
    {
      component: (
        <TextField
          select
          label="安全员"
          sx={{ m: 1, width: '25ch' }}
          value={report.srperson}
          onChange={(event) => handleChange(event, 'srperson')}
          helperText={safetyStaff.length === 0 ? '当前项目还没有添加安全员' : '只能选择当前项目中的安全员'}
        >
          {safetyStaff.map((person) => (
            <MenuItem key={person.perid} value={person.pername}>
              {person.pername}{person.pernumber ? `（${person.pernumber}）` : ''}
            </MenuItem>
          ))}
        </TextField>
      ),
      width: 6,
    },
    { component: <TimePicker label="检查时间" value={report.srins_date} onChange={(event) => handleChange(event, 'srins_date')} />, width: 6 },
    { component: <InputBox label="报告编号" value={report.srnumber} onChange={(event) => handleChange(event, 'srnumber')} />, width: 6 },
    {
      component: (
        <div>
          <Button variant="contained" component="label" sx={{ margin: 1 }} startIcon={<PhotoCamera />}>
            上传现场照片
            <input type="file" hidden accept="image/*" multiple onChange={handlePhotoChange} />
          </Button>
          {photos.length > 0 && (
            <Grid container spacing={2} sx={{ marginTop: 2 }}>
              {photos.map((photo, index) => (
                <Grid item key={photo.preview} xs={6} sm={4} md={3}>
                  <div style={{ position: 'relative' }}>
                    <img src={photo.preview} alt={photo.file.name} style={{ width: '100%', height: 'auto' }} />
                    <Typography variant="body2" noWrap>{photo.file.name}</Typography>
                    <IconButton onClick={() => handleDeletePhoto(index)} style={{ position: 'absolute', top: 5, right: 5, backgroundColor: 'rgba(255, 255, 255, 0.7)' }}>
                      <Delete />
                    </IconButton>
                  </div>
                </Grid>
              ))}
            </Grid>
          )}
        </div>
      ),
      width: 6,
    },
    {
      component: (
        <Grid item container direction="row">
          <Grid item xs={1} />
          <Grid item xs={4}><Typography sx={{ textAlign: 'center' }}>检查项目</Typography></Grid>
          <Grid item xs={4}><Typography sx={{ textAlign: 'center' }}>检查标准</Typography></Grid>
          <Grid item xs={3}><Typography sx={{ textAlign: 'center' }}>检查结果</Typography></Grid>
        </Grid>
      ),
      width: 12,
    },
    ...report.srsubitems.map((subItem, index) => ({
      component: (
        <Grid container spacing={2} key={index} alignItems="center" marginBottom={1}>
          <Grid item xs={1}><Typography sx={{ textAlign: 'center' }}>{index + 1}</Typography></Grid>
          <Grid item xs={4}><TextField fullWidth value={subItem.name} InputProps={{ readOnly: true }} /></Grid>
          <Grid item xs={4}><TextField fullWidth value={subItem.requirement} InputProps={{ readOnly: true }} /></Grid>
          <Grid item xs={3}><TextField fullWidth value={subItem.result} onChange={(event) => handleChange({ target: { value: event.target.value }, field: 'result' }, 'srsubitems', index)} /></Grid>
        </Grid>
      ),
      width: 12,
    })),
    { component: <InputBoxML label="安全员意见" value={report.srfeedback} onChange={(event) => handleChange(event, 'srfeedback')} />, width: 6 },
    {
      component: (
        <>
          <Typography>总体情况</Typography>
          <RadioGroup row aria-label="overallSafety" name="overallSafety" value={report.srevaluation} onChange={(event) => handleChange(event, 'srevaluation')}>
            <FormControlLabel value="合格" control={<Radio />} label="合格" />
            <FormControlLabel value="一般安全问题" control={<Radio />} label="一般安全问题" />
            <FormControlLabel value="重大安全问题" control={<Radio />} label="重大安全问题" />
          </RadioGroup>
        </>
      ),
      width: 6,
    },
  ];

  return (
    <CommonCreate title="新建安全报告" fields={fields} onClose={onClose} onSubmit={submitForm}>
      {validationError && <p style={{ color: 'red' }}>{validationError}</p>}
      {loading && <p>正在提交...</p>}
      {error && <p style={{ color: 'red' }}>提交失败: {error.response?.data?.message || error.message}</p>}
    </CommonCreate>
  );
}
