import * as React from 'react';
import {  GaugeContainer, GaugeValueArc,GaugeReferenceArc } from '@mui/x-charts/Gauge';
import {  Grid, Box, Typography } from '@mui/material';

const Large = {
  width: 200,
  height: 200,
  startAngle: -110,
  endAngle: 110,
  innerRadius:"70%",
  outerRadius:"100%",
};

const Small = {
  width: 120,
  height: 120,
  startAngle: -110,
  endAngle: 110,
  innerRadius:"70%",
  outerRadius:"100%",
};

  
export default function GaugeItem({size, label, value, ratio} ) {
  const getColor = (value) => {
    return value > 100 ? '#ff0000'  : '#52b202';
  };
  const setting = size === 'large' ? Large : Small;
  const fontsize1 = size === 'large' ? "h4" :"h6" ;
  const fontsize2 = size === 'large' ? "body1" :"body2" ;

  return (
    <Box>
      <Grid container direction={"column"} alignContent={"center"} justifyContent={"center"} marginBottom={2}>
        <Grid item marginBottom={-2}>
          <GaugeContainer
            {...setting}
            value={value}
            cornerRadius="50%">
                <GaugeReferenceArc />
                <GaugeValueArc sx={{fill: getColor(value)}}/>
           </GaugeContainer>
           </Grid>
           <Grid item container direction={"column"} alignContent={"center"} justifyContent={"center"}>
                <Typography variant={fontsize1}  align='center'>{ratio}</Typography>
                <Typography variant={fontsize2}  align='center'>{label}</Typography>
          </Grid>
        </Grid>
       </Box>
  );
}
