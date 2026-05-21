import React, { useEffect, forwardRef, useImperativeHandle } from 'react';
import { LineChart } from '@mui/x-charts/LineChart';
import { Box, CircularProgress, Alert, Grid, Typography } from '@mui/material';
import useFetchData from '../hooks/useFetchData.js';

const keyToLabel = {
  material: '材料费用',
  equipment: '设备费用',
  labour: '人工费用',
  manage: '管理费用',
  tax: '规费税金',
  other: '其他费用',
};

const colors = {
  material: '#1f77b4',
  equipment: '#ff7f0e',
  labour: '#2ca02c',
  manage: '#d62728',
  tax: '#9467bd',
  other: '#8c564b',
};

const stackStrategy = {
  stack: 'total',
  area: true,
  stackOffset: 'none',
};

const customize = {
  height: 300,
  legend: { hidden: true },
  margin: { top: 5 },
  stackingOrder: 'descending',
};

const LineChartSt = forwardRef((props, ref) => {
  const { data, error, fetchData } = useFetchData(`http://localhost:8000/cost/collect/monthly/${props.projectId}/`);

  useEffect(() => {
    fetchData();
  }, [props.projectId]);

  useImperativeHandle(ref, () => ({
    refreshData() {
      fetchData();
    },
  }));

  if (error) {
    return <Alert severity="error">{error}</Alert>;
  }

  const monthlyCosts = data?.data?.monthlyCosts || [];

  if (monthlyCosts.length === 0) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height={400}>
        <CircularProgress />
      </Box>
    );
  }

  const baseData = Array.from({ length: 12 }, (_, i) => ({
    month: (i + 1).toString(),
    material: 0,
    equipment: 0,
    labour: 0,
    manage: 0,
    tax: 0,
    other: 0,
  }));

  monthlyCosts.forEach((item) => {
    const monthIndex = new Date(item.month).getMonth();
    baseData[monthIndex] = {
      month: (monthIndex + 1).toString(),
      material: item.material,
      equipment: item.equipment,
      labour: item.labour,
      manage: item.manage,
      tax: item.tax,
      other: item.other,
    };
  });

  return (
    <Grid container direction="column" spacing={2}>
      <Grid item container justifyContent="center">
        <Typography variant="h6">月度执行费用统计</Typography>
      </Grid>
      <Grid item>
        <LineChart
          xAxis={[
            {
              dataKey: 'month',
              valueFormatter: (value) => `${value}月`,
              min: 1,
              max: 12,
            },
          ]}
          series={Object.keys(keyToLabel).map((key) => ({
            dataKey: key,
            label: keyToLabel[key],
            color: colors[key],
            showMark: false,
            ...stackStrategy,
          }))}
          dataset={baseData}
          {...customize}
        />
      </Grid>
    </Grid>
  );
});

export default LineChartSt;
