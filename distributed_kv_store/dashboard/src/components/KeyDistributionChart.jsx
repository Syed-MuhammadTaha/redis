import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import { useTheme } from '@mui/material/styles';

function KeyDistributionChart({ nodes, nodeStatuses }) {
  const svgRef = useRef(null);
  const theme = useTheme();

  useEffect(() => {
    if (!svgRef.current) return;

    const width = 400;
    const height = 300;
    const radius = Math.min(width, height) / 2 * 0.8;

    // Clear previous SVG content
    d3.select(svgRef.current).selectAll("*").remove();

    // Create SVG
    const svg = d3.select(svgRef.current)
      .attr("width", width)
      .attr("height", height)
      .append("g")
      .attr("transform", `translate(${width / 2},${height / 2})`);

    // Prepare data
    const data = nodes.map(node => ({
      id: node.id,
      value: nodeStatuses[node.id]?.key_count || 0,
      status: nodeStatuses[node.id]?.status || 'unhealthy'
    }));

    const totalKeys = data.reduce((sum, d) => sum + d.value, 0);

    // Color scale
    const color = d3.scaleOrdinal()
      .domain(nodes.map(n => n.id))
      .range([theme.palette.primary.main, theme.palette.secondary.main, theme.palette.success.main]);

    // Create pie chart
    const pie = d3.pie()
      .value(d => d.value)
      .sort(null);

    const arc = d3.arc()
      .innerRadius(radius * 0.6) // Create a donut chart
      .outerRadius(radius);

    // Add arcs
    const arcs = svg.selectAll("path")
      .data(pie(data))
      .enter()
      .append("path")
      .attr("d", arc)
      .attr("fill", d => color(d.data.id))
      .attr("stroke", theme.palette.background.paper)
      .style("opacity", d => d.data.status === 'healthy' ? 1 : 0.5)
      .transition()
      .duration(1000)
      .attrTween("d", function(d) {
        const interpolate = d3.interpolate({ startAngle: 0, endAngle: 0 }, d);
        return function(t) {
          return arc(interpolate(t));
        };
      });

    // Add labels
    const arcLabel = d3.arc()
      .innerRadius(radius * 0.8)
      .outerRadius(radius * 0.8);

    const labels = svg.selectAll("text")
      .data(pie(data))
      .enter()
      .append("text")
      .attr("transform", d => `translate(${arcLabel.centroid(d)})`)
      .attr("dy", "0.35em")
      .attr("text-anchor", "middle")
      .style("fill", theme.palette.text.primary)
      .style("font-size", "12px")
      .style("opacity", 0)
      .text(d => d.data.value)
      .transition()
      .duration(1000)
      .style("opacity", 1);

    // Add center text
    svg.append("text")
      .attr("text-anchor", "middle")
      .attr("dy", "-0.5em")
      .style("fill", theme.palette.text.primary)
      .style("font-size", "14px")
      .text("Total Keys");

    svg.append("text")
      .attr("text-anchor", "middle")
      .attr("dy", "1em")
      .style("fill", theme.palette.text.primary)
      .style("font-size", "20px")
      .text(totalKeys);

    // Add legend
    const legend = svg.append("g")
      .attr("transform", `translate(${-width/2 + 20},${height/2 - 60})`);

    nodes.forEach((node, i) => {
      const legendRow = legend.append("g")
        .attr("transform", `translate(0,${i * 20})`);

      legendRow.append("rect")
        .attr("width", 12)
        .attr("height", 12)
        .attr("fill", color(node.id))
        .style("opacity", nodeStatuses[node.id]?.status === 'healthy' ? 1 : 0.5);

      legendRow.append("text")
        .attr("x", 20)
        .attr("y", 10)
        .style("fill", theme.palette.text.primary)
        .style("font-size", "12px")
        .text(`${node.id} (${nodeStatuses[node.id]?.key_count || 0})`);
    });

  }, [nodes, nodeStatuses, theme]);

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Key Distribution
      </Typography>
      <Box display="flex" justifyContent="center" alignItems="center" height={300}>
        <svg ref={svgRef}></svg>
      </Box>
    </Box>
  );
}

export default KeyDistributionChart; 