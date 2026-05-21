import React, { useEffect, useState } from 'react';
import axios from '../api/client.js';
import { FormControlLabel, Grid, MenuItem, Radio, RadioGroup, TextField, Typography } from '@mui/material';
import TimePicker from '../components/TimePicker';
import InputBox from '../components/InputBox';
import InputBoxML from '../components/InputBoxML.jsx';
import CommonCreate from './CommonCreate';
import useFormSubmit from '../hooks/useFormSubmit.js';

export default function CreateQuality({ onClose, templates, projectId }) {
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [qualityStaff, setQualityStaff] = useState([]);
  const [validationError, setValidationError] = useState('');
  const [report, setReport] = useState({
    qrname: '',
    qrpart: '',
    qrperson: '',
    qrcons_date: '',
    qrins_date: '',
    qrnumber: '',
    qrsubitems: [{ name: '', requirement: '', result: '' }],
    qrfeedback: '',
    qrevaluation: '',
  });

  useEffect(() => {
    const fetchQualityStaff = async () => {
      try {
        const response = await axios.get(`http://localhost:8000/projects/${projectId}/persons/`);
        setQualityStaff((response.data?.data?.persons || []).filter((person) => person.perrole === '质量员'));
      } catch (error) {
        console.error('Error fetching quality staff:', error);
      }
    };

    if (projectId) fetchQualityStaff();
  }, [projectId]);

  const handleTemplateChange = (event) => {
    const templateId = parseInt(event.target.value, 10);
    const template = templates.find((item) => item.id === templateId);
    if (!template) return;

    setSelectedTemplate(template);
    setReport((prevReport) => ({
      ...prevReport,
      qrname: template.name,
      qrsubitems: template.items.map((item) => ({
        name: item.NAME_Item,
        requirement: item.VALUE_Item,
        result: '',
      })),
    }));
  };

  const handleChange = (value, fieldName, index) => {
    if (fieldName === 'qrsubitems') {
      setReport((prevReport) => ({
        ...prevReport,
        qrsubitems: prevReport.qrsubitems.map((item, idx) => (
          idx === index ? { ...item, [value.field]: value.target.value } : item
        )),
      }));
      return;
    }

    setReport((prevReport) => ({
      ...prevReport,
      [fieldName]: value.target ? value.target.value : value,
    }));

    if (fieldName === 'qrperson') {
      setValidationError('');
    }
  };

  const { handleSubmit, loading, error } = useFormSubmit();

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
    { component: <InputBox label="工程名称" value={report.qrname} onChange={(event) => handleChange(event, 'qrname')} />, width: 6 },
    { component: <InputBox label="检验部位及编号" value={report.qrpart} onChange={(event) => handleChange(event, 'qrpart')} />, width: 6 },
    {
      component: (
        <TextField
          select
          label="质检员"
          sx={{ m: 1, width: '25ch' }}
          value={report.qrperson}
          onChange={(event) => handleChange(event, 'qrperson')}
          helperText={qualityStaff.length === 0 ? '当前项目还没有添加质量员' : '只能选择当前项目中的质量员'}
        >
          {qualityStaff.map((person) => (
            <MenuItem key={person.perid} value={person.pername}>
              {person.pername}{person.pernumber ? `（${person.pernumber}）` : ''}
            </MenuItem>
          ))}
        </TextField>
      ),
      width: 6,
    },
    { component: <TimePicker label="施工时间" value={report.qrcons_date} onChange={(event) => handleChange(event, 'qrcons_date')} />, width: 6 },
    { component: <TimePicker label="检验时间" value={report.qrins_date} onChange={(event) => handleChange(event, 'qrins_date')} />, width: 6 },
    { component: <InputBox label="报告编号" value={report.qrnumber} onChange={(event) => handleChange(event, 'qrnumber')} />, width: 6 },
    {
      component: (
        <Grid item container direction="row">
          <Grid item xs={1} />
          <Grid item xs={4}><Typography sx={{ textAlign: 'center' }}>检验项目</Typography></Grid>
          <Grid item xs={4}><Typography sx={{ textAlign: 'center' }}>规定值或允许偏差</Typography></Grid>
          <Grid item xs={3}><Typography sx={{ textAlign: 'center' }}>检验结果</Typography></Grid>
        </Grid>
      ),
      width: 12,
    },
    ...report.qrsubitems.map((subItem, index) => ({
      component: (
        <Grid item container spacing={2} key={index} alignItems="center">
          <Grid item xs={1}><Typography sx={{ textAlign: 'center' }}>{index + 1}</Typography></Grid>
          <Grid item xs={4}><TextField fullWidth value={subItem.name} InputProps={{ readOnly: true }} /></Grid>
          <Grid item xs={4}><TextField fullWidth value={subItem.requirement} InputProps={{ readOnly: true }} /></Grid>
          <Grid item xs={3}><TextField fullWidth value={subItem.result} onChange={(event) => handleChange({ target: { value: event.target.value }, field: 'result' }, 'qrsubitems', index)} /></Grid>
        </Grid>
      ),
      width: 12,
    })),
    { component: <InputBoxML label="质检员意见" value={report.qrfeedback} onChange={(event) => handleChange(event, 'qrfeedback')} />, width: 6 },
    {
      component: (
        <>
          <Typography>总体情况</Typography>
          <RadioGroup row aria-label="overallQuality" name="overallQuality" value={report.qrevaluation} onChange={(event) => handleChange(event, 'qrevaluation')}>
            <FormControlLabel value="合格" control={<Radio />} label="合格" />
            <FormControlLabel value="一般质量问题" control={<Radio />} label="一般质量问题" />
            <FormControlLabel value="重大质量问题" control={<Radio />} label="重大质量问题" />
          </RadioGroup>
        </>
      ),
      width: 6,
    },
  ];

  const onSubmit = () => {
    if (!report.qrperson) {
      setValidationError('请选择当前项目中的质量员。');
      return;
    }
    handleSubmit(report, `http://localhost:8000/projects/${projectId}/quality/reports/`, onClose);
  };

  return (
    <CommonCreate title="新建质检报告" fields={fields} onClose={onClose} onSubmit={onSubmit}>
      {validationError && <p style={{ color: 'red' }}>{validationError}</p>}
      {loading && <p>正在提交...</p>}
      {error && <p style={{ color: 'red' }}>提交失败: {error.response?.data?.message || error.message}</p>}
    </CommonCreate>
  );
}
