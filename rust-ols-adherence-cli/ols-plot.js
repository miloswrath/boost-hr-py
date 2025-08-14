#!/usr/bin/env node
/* Headless D3 render -> SVG + PNG
 * CHANGE THE CONSTANTS BELOW to point at your files/dir.
 */

'use strict';

const fs = require('fs/promises');
const path = require('path');
const { JSDOM } = require('jsdom');
const d3 = require('d3');
const sharp = require('sharp');

/* =======================
   CHANGE ME (paths/sizes)
   ======================= */
const DATA_CSV   = path.resolve('./data.csv');       
const MODEL_JSON = path.resolve('./model.json');      
const OUTPUT_DIR = path.resolve('../docs/meta_plot');             // <-- CHANGE ME (where files go)

const SVG_FILENAME = 'scatter_model.svg';
const PNG_FILENAME = 'scatter_model.png';

const WIDTH  = 900;   // <-- CHANGE ME (chart width in px)
const HEIGHT = 550;   // <-- CHANGE ME (chart height in px)

// PNG scale factor: 1 = same as SVG size, 2 = 2x, etc.
const PNG_SCALE = 2;  
/* ======================= */

(async function main() {
  await fs.mkdir(OUTPUT_DIR, { recursive: true });

  // ---- Load data ----
  const csvText = await fs.readFile(DATA_CSV, 'utf8');
  const data = d3.csvParse(csvText, d => ({
    x: +d.sup_prop,
    y: +d.unsup_prop,
    den: d.unsup_den == null || d.unsup_den === '' ? null : +d.unsup_den
  }));

  const model = JSON.parse(await fs.readFile(MODEL_JSON, 'utf8'));
  const { beta0, beta1 } = model.params;

  // ---- Set up headless SVG via jsdom ----
  const dom = new JSDOM(`<!DOCTYPE html><svg id="chart" width="${WIDTH}" height="${HEIGHT}"></svg>`, {
    contentType: 'image/svg+xml'
  });
  const document = dom.window.document;
  const svg = d3.select(document.querySelector('#chart'));

  // ---- Layout & group ----
  const margin = { top: 24, right: 24, bottom: 48, left: 56 };
  const innerW = WIDTH - margin.left - margin.right;
  const innerH = HEIGHT - margin.top - margin.bottom;

  const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`);

  // ---- Scales ----
  const xExtent = d3.extent(data, d => d.x);
  const yExtent = d3.extent(data, d => d.y);
  const pad = 0.05;

  const xScale = d3.scaleLinear()
    .domain([
      Math.max(0, (xExtent[0] ?? 0) - pad),
      Math.min(1, (xExtent[1] ?? 1) + pad)
    ])
    .range([0, innerW]);

  const yScale = d3.scaleLinear()
    .domain([
      Math.max(0, (yExtent[0] ?? 0) - pad),
      Math.min(1, (yExtent[1] ?? 1) + pad)
    ])
    .nice()
    .range([innerH, 0]);

  const denValues = data.map(d => d.den ?? 1);
  const rScale = d3.scaleSqrt()
    .domain(d3.extent(denValues))
    .range([4, 11]);

  // ---- Axes + Grid ----
  const xAxis = d3.axisBottom(xScale).ticks(10).tickFormat(d3.format('.2f'));
  const yAxis = d3.axisLeft(yScale).ticks(10).tickFormat(d3.format('.2f'));

  g.append('g')
    .attr('class', 'grid')
    .attr('transform', `translate(0,${innerH})`)
    .call(d3.axisBottom(xScale).ticks(10).tickSize(-innerH).tickFormat(() => ''))
    .selectAll('line').attr('stroke', '#eee');

  g.append('g')
    .attr('class', 'grid')
    .call(d3.axisLeft(yScale).ticks(10).tickSize(-innerW).tickFormat(() => ''))
    .selectAll('line').attr('stroke', '#eee');

  g.append('g')
    .attr('class', 'axis')
    .attr('transform', `translate(0,${innerH})`)
    .call(xAxis)
    .call(g => g.append('text')
      .attr('x', innerW)
      .attr('y', 36)
      .attr('fill', '#333')
      .attr('text-anchor', 'end')
      .text('sup_prop (x)')
    );

  g.append('g')
    .attr('class', 'axis')
    .call(yAxis)
    .call(g => g.append('text')
      .attr('transform', 'rotate(-90)')
      .attr('x', -16)
      .attr('y', -44)
      .attr('dy', '0.71em')
      .attr('fill', '#333')
      .attr('text-anchor', 'end')
      .text('unsup_prop (y)')
    );

  // ---- Scatter ----
  g.selectAll('.dot')
    .data(data)
    .join('circle')
    .attr('class', 'dot')
    .attr('cx', d => xScale(d.x))
    .attr('cy', d => yScale(d.y))
    .attr('r', d => rScale(d.den ?? 1))
    .attr('fill', '#3b82f6')   // blue
    .attr('stroke', '#1e40af')
    .attr('stroke-width', 1)
    .attr('opacity', 0.85);

  // ---- Model line (ŷ = β0 + β1 x) ----
  const [x0, x1] = xScale.domain();
  const y0 = beta0 + beta1 * x0;
  const y1 = beta0 + beta1 * x1;

  g.append('path')
    .datum([{ x: x0, y: y0 }, { x: x1, y: y1 }])
    .attr('fill', 'none')
    .attr('stroke', '#ef4444')     // red
    .attr('stroke-width', 2)
    .attr('d', d3.line()
      .x(d => xScale(d.x))
      .y(d => yScale(d.y))
    );

  // ---- Equation label ----
  const fmt = v => {
    const a = Math.abs(v);
    if (a === 0) return '0';
    if (a < 1e-3 || a > 1e3) return v.toExponential(2);
    return v.toFixed(3);
  };

  g.append('text')
    .attr('x', innerW - 6)
    .attr('y', 14)
    .attr('text-anchor', 'end')
    .attr('fill', '#ef4444')
    .attr('font-size', '12px')
    .text(`ŷ = ${fmt(beta0)} + ${fmt(beta1)}·x`);

  // ---- Extract SVG string ----
  const svgNode = document.querySelector('svg');
  svgNode.setAttribute('role', 'img');
  svgNode.setAttribute('aria-label', 'Scatter plot with model fit line');
  const svgString = svgNode.outerHTML;

  // ---- Write SVG ----
  const svgPath = path.join(OUTPUT_DIR, SVG_FILENAME);
  await fs.writeFile(svgPath, svgString, 'utf8');

  // ---- Write PNG (via sharp) ----
  const pngPath = path.join(OUTPUT_DIR, PNG_FILENAME);
  // Use density to scale rasterization resolution
  const density = Math.round(72 * PNG_SCALE); // base 72dpi * scale
  await sharp(Buffer.from(svgString), { density })
    .png({ compressionLevel: 9 })
    .toFile(pngPath);

  console.log(`Saved:\n  SVG: ${svgPath}\n  PNG: ${pngPath}`);
})().catch(err => {
  console.error(err);
  process.exit(1);
});

