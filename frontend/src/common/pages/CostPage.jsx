import React, { useRef } from "react";
import { Grid } from "@mui/material";
import GaugeChart from "../components/GaugeChart.jsx";
import LineChartSt from "../components/LineChartSt.jsx";
import CostTable from "../components/CostTable.jsx";
import CommonPage from "../components/CommonPage.jsx";
import useProjectParams from "../hooks/useProjectParams.js";

export default function CostPage() {
  const { projectName, projectId } = useProjectParams();
  const gaugeChartRef = useRef(null);
  const lineChartStRef = useRef(null);

  const handleUpdate = () => {
    if (gaugeChartRef.current) {
      gaugeChartRef.current.refreshData();
    }
    if (lineChartStRef.current) {
      lineChartStRef.current.refreshData();
    }
  };

  return (
    <CommonPage pageName="成本控制" projectId={projectId} projectName={projectName}>
      <Grid item container xs={7} direction="column" spacing={2}>
        <Grid item>
          <CostTable projectId={projectId} projectName={projectName} onUpdate={handleUpdate} />
        </Grid>
        <Grid item marginTop={2}>
          <LineChartSt projectId={projectId} ref={lineChartStRef} />
        </Grid>
      </Grid>
      <Grid item container xs={5}>
        <GaugeChart projectId={projectId} ref={gaugeChartRef} />
      </Grid>
    </CommonPage>
  );
}
