import React, { useEffect, useState } from 'react';
import axios from '../api/client.js';
import { Grid, MenuItem, TextField } from '@mui/material';
import InputBox from '../components/InputBox.jsx';
import InputBoxML from '../components/InputBoxML.jsx';
import SelectBox from '../components/SelectBox.jsx';
import TimePicker from '../components/TimePicker.jsx';
import { currencies } from '../constants/UNIT.js';
import { expenseTypes } from '../constants/COST_INFO.js';
import CommonCreate from './CommonCreate.jsx';
import useFormSubmit from '../hooks/useFormSubmit.js';
import { useAuth } from '../hooks/AuthContext';

export default function CreateCost({ projectName, projectId, onClose }) {
  const [costReport, setCostReport] = useState({
    costName: '',
    projectName,
    date: '',
    expenseType: '',
    accountant: '',
    budgetAmount: '',
    currency: '',
    costAmount: '',
    description: '',
  });
  const [budgetStaff, setBudgetStaff] = useState([]);
  const [validationError, setValidationError] = useState('');
  const { apiBaseUrl } = useAuth();
  const { handleSubmit, loading, error } = useFormSubmit();

  useEffect(() => {
    const fetchBudgetStaff = async () => {
      try {
        const response = await axios.get(`${apiBaseUrl}/projects/${projectId}/persons/`, {
          withCredentials: true,
        });
        const persons = response.data?.data?.persons || [];
        setBudgetStaff(persons.filter((person) => person.perrole === '预算员'));
      } catch (fetchError) {
        console.error('Error fetching budget staff:', fetchError);
      }
    };

    if (projectId) {
      fetchBudgetStaff();
    }
  }, [apiBaseUrl, projectId]);

  const handleChange = (value, fieldName) => {
    const fieldValue = fieldName === 'date' ? value : value.target.value;
    setCostReport({ ...costReport, [fieldName]: fieldValue });

    if (fieldName === 'expenseType' || fieldName === 'description' || fieldName === 'accountant') {
      setValidationError('');
    }
  };

  const fields = [
    {
      component: (
        <TextField
          label="输入成本名称"
          sx={{ width: '90%' }}
          value={costReport.costName}
          onChange={(event) => handleChange(event, 'costName')}
        />
      ),
      width: 12,
    },
    {
      component: (
        <InputBox
          label="所属项目"
          value={costReport.projectName}
          onChange={(event) => handleChange(event, 'projectName')}
        />
      ),
      width: 6,
    },
    {
      component: (
        <TimePicker
          label="日期"
          value={costReport.date}
          onChange={(event) => handleChange(event, 'date')}
        />
      ),
      width: 6,
    },
    {
      component: (
        <SelectBox
          label="费用类型"
          set={expenseTypes}
          value={costReport.expenseType}
          onChange={(event) => handleChange(event, 'expenseType')}
          width="25ch"
        />
      ),
      width: 6,
    },
    {
      component: (
        <TextField
          select
          label="财务人员"
          sx={{ m: 1, width: '25ch' }}
          value={costReport.accountant}
          onChange={(event) => handleChange(event, 'accountant')}
          helperText={budgetStaff.length === 0 ? '当前项目还没有添加预算员' : '只能选择当前项目中的预算员'}
        >
          {budgetStaff.map((person) => (
            <MenuItem key={person.perid} value={person.pername}>
              {person.pername}{person.pernumber ? `（${person.pernumber}）` : ''}
            </MenuItem>
          ))}
        </TextField>
      ),
      width: 6,
    },
    {
      component: (
        <Grid container direction="row">
          <Grid item xs={8}>
            <InputBox
              label="预算金额"
              value={costReport.budgetAmount}
              onChange={(event) => handleChange(event, 'budgetAmount')}
            />
          </Grid>
          <Grid item xs={4}>
            <SelectBox
              set={currencies}
              label="货币"
              value={costReport.currency}
              onChange={(event) => handleChange(event, 'currency')}
              width="10ch"
            />
          </Grid>
        </Grid>
      ),
      width: 6,
    },
    {
      component: (
        <Grid container direction="row">
          <Grid item xs={8}>
            <InputBox
              label="执行金额"
              value={costReport.costAmount}
              onChange={(event) => handleChange(event, 'costAmount')}
            />
          </Grid>
          <Grid item xs={4}>
            <SelectBox
              set={currencies}
              label="货币"
              value={costReport.currency}
              onChange={(event) => handleChange(event, 'currency')}
              width="10ch"
            />
          </Grid>
        </Grid>
      ),
      width: 6,
    },
    {
      component: (
        <InputBoxML
          label={costReport.expenseType === '其他费用' ? '描述（其他费用必填）' : '描述'}
          value={costReport.description}
          onChange={(event) => handleChange(event, 'description')}
        />
      ),
      width: 6,
    },
  ];

  const onSubmit = () => {
    if (!costReport.accountant) {
      setValidationError('请选择当前项目中的预算员作为财务人员。');
      return;
    }

    if (costReport.expenseType === '其他费用' && !costReport.description.trim()) {
      setValidationError('费用类型为“其他费用”时，描述为必填项。');
      return;
    }

    handleSubmit(costReport, `${apiBaseUrl}/projects/${projectId}/costs/`, onClose);
  };

  return (
    <CommonCreate title="新建成本单" fields={fields} onClose={onClose} onSubmit={onSubmit}>
      {validationError && <p style={{ color: 'red' }}>{validationError}</p>}
      {loading && <p>正在提交...</p>}
      {error && <p style={{ color: 'red' }}>提交失败: {error.response?.data?.message || error.message}</p>}
    </CommonCreate>
  );
}

