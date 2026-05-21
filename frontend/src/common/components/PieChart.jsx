import React, { useEffect, forwardRef, useImperativeHandle } from 'react';
import { PieChart } from '@mui/x-charts/PieChart';
import { Box, CircularProgress, Alert } from "@mui/material";
import useFetchData from '../hooks/useFetchData.js';

const BasicPie = forwardRef((props,ref) => {
  const { data, error, fetchData} = useFetchData(`http://localhost:8000/projectnode/collect/${props.pjID}/`);

  useEffect(() => {
    fetchData();
  }, [props.pjID]);
  
  // 浣跨敤 useImperativeHandle 鍚戠埗缁勪欢鏆撮湶鍒锋柊鏁版嵁鐨勬柟娉?
   useImperativeHandle(ref, () => ({
    refreshData() {
      fetchData();
    }
  }));


  if (error) {
    return <Alert severity="error">{error}</Alert>;
  }

  const summary = data?.data?.summary;

  if (!summary) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height={275}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box
      style={{
        display: "flex",
        flexDirection: "column",
        justifyContent: "flex-start",
        alignItems: "flex-start",
        width: "100%",
        height: "100%",
      }}
    >
      <PieChart
        series={[
          {
            data: [
              { id: 0, value: summary.completed_count, label: '\u5df2\u5b8c\u6210' },
              { id: 1, value: summary.in_progress_count, label: '\u8fdb\u884c\u4e2d' },
              { id: 2, value: summary.pending_count, label: '\u672a\u5904\u7406' },
            ],
            innerRadius: 30,
            outerRadius: 100,
            paddingAngle: 0,
            cornerRadius: 5,
            cx: 150,
            cy: 150,
          },
        ]}
        width={400}
        height={275}
      />
    </Box>
  );
});
export default BasicPie;


