const CHART_COLORS = [
  '#0d6efd', '#198754', '#ffc107', '#dc3545',
  '#0dcaf0', '#6f42c1', '#fd7e14', '#20c997',
  '#6610f2', '#d63384'
];

const CHART_DEFAULTS = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      labels: { font: { size: 12, family: "'Inter', sans-serif" }, padding: 16 }
    }
  },
  scales: {
    x: {
      grid: { display: false },
      ticks: { font: { size: 11, family: "'Inter', sans-serif" } }
    },
    y: {
      grid: { color: '#f0f0f0' },
      ticks: { font: { size: 11, family: "'Inter', sans-serif" } }
    }
  }
};

function createBarChart(canvasId, labels, data, label) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;
  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: label,
        data: data,
        backgroundColor: CHART_COLORS[0],
        borderRadius: 4,
        maxBarThickness: 48
      }]
    },
    options: { ...CHART_DEFAULTS }
  });
}

function createLineChart(canvasId, labels, data, label) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;
  new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: label,
        data: data,
        borderColor: CHART_COLORS[0],
        backgroundColor: 'rgba(13, 110, 253, 0.1)',
        fill: true,
        tension: 0.3,
        pointRadius: 4,
        pointHoverRadius: 6
      }]
    },
    options: { ...CHART_DEFAULTS }
  });
}

function createDoughnutChart(canvasId, labels, data) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;
  new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: labels,
      datasets: [{
        data: data,
        backgroundColor: CHART_COLORS.slice(0, labels.length),
        borderWidth: 2,
        borderColor: '#fff'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom',
          labels: { font: { size: 12, family: "'Inter', sans-serif" }, padding: 12 }
        }
      }
    }
  });
}

function createHorizontalBarChart(canvasId, labels, data, label) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;
  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: label,
        data: data,
        backgroundColor: CHART_COLORS.slice(0, labels.length),
        borderRadius: 4,
        maxBarThickness: 28
      }]
    },
    options: {
      ...CHART_DEFAULTS,
      indexAxis: 'y',
      plugins: { legend: { display: false } }
    }
  });
}
