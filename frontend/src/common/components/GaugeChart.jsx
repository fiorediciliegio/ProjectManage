import React, { useEffect, forwardRef, useImperativeHandle } from 'react';
import { Box, Paper, Grid, CircularProgress, Alert } from '@mui/material';
import GaugeItem from '../components/GaugeItem.jsx';
import useFetchData from '../hooks/useFetchData.js';

const GaugeChart = forwardRef((props, ref) => {
  const { data, error, fetchData } = useFetchData(`http://localhost:8000/cost/collect/total/${props.projectId}/`);

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

  const summary = data?.data?.summary;

  if (!summary) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height={400}>
        <CircularProgress />
      </Box>
    );
  }

  const totalBudget = Number(summary.TotalBudget) || 0;
  const totalCost = Number(summary.TotalCost) || 0;
  const totalCostRatio = totalBudget > 0 ? (totalCost / totalBudget) * 100 : 0;
  const totalCostRatioStr = `${totalCost}/${totalBudget}`;

  return (
    <Grid container margin={1}>
      <Paper style={{ width: '100%', height: '100%', padding: '15px' }}>
        <Grid container direction="column">
          <Grid item container xs={12} justifyContent="center">
            <GaugeItem size="large" label="总费用" value={totalCostRatio} ratio={totalCostRatioStr} />
          </Grid>
          <Grid item container justifyContent="space-between">
            {Object.entries(summary.detail || {}).map(([expenseType, { totalbudget, totalcost }]) => {
              const budget = Number(totalbudget) || 0;
              const cost = Number(totalcost) || 0;
              const ratio = budget > 0 ? (cost / budget) * 100 : 0;
              return (
                <Grid key={expenseType} item container justifyContent="center" xs={4}>
                  <GaugeItem size="small" label={expenseType} value={ratio} ratio={`${cost}/${budget}`} />
                </Grid>
              );
            })}
          </Grid>
        </Grid>
      </Paper>
    </Grid>
  );
});

export default GaugeChart;
