import React, { useEffect, forwardRef, useImperativeHandle } from 'react';
import { BarChart } from '@mui/x-charts/BarChart';
import { Box, CircularProgress, Alert } from '@mui/material';
import useFetchData from '../hooks/useFetchData.js';

const StackBar = forwardRef((props, ref) => {
  const { data, error, fetchData } = useFetchData(`http://localhost:8000/projects/${props.projectId}/quality/stats/`);

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

  const stats = data?.data?.stats;

  if (!stats || Object.keys(stats).length === 0) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height={350}>
        <CircularProgress />
      </Box>
    );
  }

  const quarters = ['Q1', 'Q2', 'Q3', 'Q4'];
  const series = Object.keys(stats).map((key) => ({
    label: key,
    data: stats[key],
    stack: 'stack',
  }));

  return <BarChart xAxis={[{ scaleType: 'band', data: quarters }]} series={series} width={500} height={350} />;
});

export default StackBar;

