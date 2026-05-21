import React, { useState } from 'react';
import { Grid, TextField, IconButton, Typography } from '@mui/material';
import { Delete } from '@mui/icons-material';
import AddCircleIcon from '@mui/icons-material/AddCircle';
import CommonCreate from './CommonCreate';
import useFormSubmit from '../hooks/useFormSubmit.js';

export default function CreateSafTem({ onClose, projectId }) {
  const [safTemplate, setSafTemplate] = useState({ stname: '', subitems: [{ name: '', requirement: '' }] });
  const { handleSubmit, loading, error } = useFormSubmit();

  const handleChange = (index, field, value) => {
    const subitems = safTemplate.subitems.map((item, i) => (i === index ? { ...item, [field]: value } : item));
    setSafTemplate({ ...safTemplate, subitems });
  };

  const handleAddSubItem = () => {
    setSafTemplate({ ...safTemplate, subitems: [...safTemplate.subitems, { name: '', requirement: '' }] });
  };

  const handleRemoveSubItem = (index) => {
    setSafTemplate({ ...safTemplate, subitems: safTemplate.subitems.filter((_, i) => i !== index) });
  };

  const fields = [
    {
      component: <TextField label="模板名称" sx={{ width: '90%' }} value={safTemplate.stname} onChange={(e) => setSafTemplate({ ...safTemplate, stname: e.target.value })} />,
      width: 12,
    },
    ...safTemplate.subitems.map((subItem, index) => ({
      component: (
        <Grid container spacing={2} key={index} alignItems="center">
          <Grid item xs={1}>
            <Typography sx={{ textAlign: 'center' }}>{index + 1}</Typography>
          </Grid>
          <Grid item xs={4}>
            <TextField multiline label="检查项目" fullWidth value={subItem.name} onChange={(e) => handleChange(index, 'name', e.target.value)} />
          </Grid>
          <Grid item xs={5}>
            <TextField multiline label="检查标准" fullWidth value={subItem.requirement} onChange={(e) => handleChange(index, 'requirement', e.target.value)} />
          </Grid>
          <Grid item xs={2} container justifyContent="center">
            <IconButton onClick={() => handleRemoveSubItem(index)}>
              <Delete />
            </IconButton>
          </Grid>
        </Grid>
      ),
      width: 12,
    })),
    {
      component: (
        <Grid container justifyContent="center">
          <IconButton onClick={handleAddSubItem}><AddCircleIcon /></IconButton>
        </Grid>
      ),
      width: 12,
    },
  ];

  const onSubmit = () => handleSubmit(safTemplate, `http://localhost:8000/projects/${projectId}/safety/templates/`, onClose);

  return (
    <CommonCreate title="创建安全报告模板" fields={fields} onClose={onClose} onSubmit={onSubmit}>
      {loading && <p>正在提交...</p>}
      {error && <p style={{ color: 'red' }}>提交失败: {error.response?.data?.message || error.message}</p>}
    </CommonCreate>
  );
}
