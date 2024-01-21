import * as d3 from 'd3'

export const createSongWaveform = (yValues: number[], width: number, height: number) => {
    const margin = {top: 10, right: 30, bottom: 30, left: 60};
    width -= (margin.left + margin.right);
    height -= (margin.top + margin.bottom);

    const svg = d3.create("svg")
        .attr("viewBox", [0, 0, width + margin.left + margin.right, height + margin.top + margin.bottom])
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom);

    const g = svg
        .append("g")
        .attr("transform",
            "translate(" + margin.left + "," + margin.top + ")");

    const xScale = d3.scaleLinear()
        .domain([0, yValues.length])
        .range([0, width]);

    g.append("g")
        .attr("transform", "translate(0," + height + ")")
        .call(d3.axisBottom(xScale));

    const yScale = d3.scaleLinear()
        .domain([d3.min(yValues) || -1, d3.max(yValues) || 1])
        .range([height, 0]);

    g.append("g")
        .call(d3.axisLeft(yScale));

    const line = d3.line<number>()
        .x((d, i) => xScale(i))
        .y((d) => yScale(d))
        .curve(d3.curveMonotoneX);

    g.append("path")
        .datum(yValues)
        .attr("fill", "none")
        .attr("stroke", "steelblue")
        .attr("stroke-width", 1.5)
        .attr("d", line);

    return svg.node();
}