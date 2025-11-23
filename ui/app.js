let rawData = [];
let dynamicChartInstance = null;

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    await loadDashboard();
    await loadTable();
});

async function loadDashboard() {
    const res = await fetch('/api/dashboard');
    const data = await res.json();

    renderChart('chartHistory', 'line', 'Total Historical Sales', data.historical.map(d => d.Date), data.historical.map(d => d.Sales), 'Week', 'Sales Qty');
    renderChart('chartForecast', 'line', 'Total Forecast (Constrained)', data.forecast.map(d => d.Date), data.forecast.map(d => d.Constrained_Plan), 'Week', 'Forecast Qty');
    renderChart('chartTop5', 'bar', 'Forecast Volume', data.top_products.map(d => d.SKU), data.top_products.map(d => d.Constrained_Plan), 'Product', 'Total Qty');
}

async function loadTable() {
    try {
        const res = await fetch('/api/table');
        rawData = await res.json();
        console.log("Table Data Loaded:", rawData.length, "rows");
        renderTable(rawData);
    } catch (e) {
        console.error("Error loading table:", e);
        document.querySelector('#demandTable tbody').innerHTML = `<tr><td colspan="100">Error loading data: ${e.message}</td></tr>`;
    }
}

function renderChart(canvasId, type, label, labels, dataPoints, xTitle, yTitle) {
    const ctx = document.getElementById(canvasId).getContext('2d');

    // Decimation Logic for Line Charts
    let finalLabels = labels;
    let finalData = dataPoints;

    if (type === 'line' && dataPoints.length > 20) {
        // Find min, max, and average
        const minVal = Math.min(...dataPoints);
        const maxVal = Math.max(...dataPoints);
        const sum = dataPoints.reduce((a, b) => a + b, 0);
        const avgVal = sum / dataPoints.length;

        // Find indices closest to these values
        // This is a simplified "smart" sampling to show interesting points
        // For a true "min/max/avg" line, we might want to just plot those 3 points?
        // The user asked for "at least 3 data points... min, max, and value closest to average".
        // Let's filter the dataset to just these points for clarity, or highlight them.
        // If we only show 3 points, the line might look weird. 
        // Let's try to show a decimated view but ensure those 3 are present.
        // Actually, user said "not all the values". So let's just show those 3-5 key points.

        const indices = [];
        // Add Min
        indices.push(dataPoints.indexOf(minVal));
        // Add Max
        indices.push(dataPoints.indexOf(maxVal));
        // Add closest to Avg
        const closestAvg = dataPoints.reduce((prev, curr) => Math.abs(curr - avgVal) < Math.abs(prev - avgVal) ? curr : prev);
        indices.push(dataPoints.indexOf(closestAvg));

        // Sort indices and deduplicate
        const uniqueIndices = [...new Set(indices)].sort((a, b) => a - b);

        finalLabels = uniqueIndices.map(i => labels[i]);
        finalData = uniqueIndices.map(i => dataPoints[i]);
    }

    new Chart(ctx, {
        type: type,
        data: {
            labels: finalLabels,
            datasets: [{
                label: label,
                data: finalData,
                borderColor: '#3b82f6',
                backgroundColor: 'rgba(59, 130, 246, 0.5)',
                tension: 0.4,
                pointRadius: 6, // Make points visible
                pointHoverRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    labels: { color: '#94a3b8' }
                },
                tooltip: {
                    enabled: true,
                    mode: 'index',
                    intersect: false,
                }
            },
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: xTitle || 'Date',
                        color: '#94a3b8'
                    },
                    ticks: { color: '#94a3b8' },
                    grid: { color: '#334155' }
                },
                y: {
                    display: true,
                    title: {
                        display: true,
                        text: yTitle || 'Value',
                        color: '#94a3b8'
                    },
                    ticks: { color: '#94a3b8' },
                    grid: { color: '#334155' }
                }
            }
        }
    });
}

function renderTable(data) {
    const thead = document.querySelector('#demandTable thead');
    const tbody = document.querySelector('#demandTable tbody');

    if (!data || data.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5">No data available</td></tr>';
        return;
    }

    // 1. Get Unique Dates (sorted) for Columns
    // Filter dates to next 12 weeks to keep it manageable, or take all
    const allDates = [...new Set(data.map(d => d.Date))].sort();

    // 2. Group data by SKU
    const skuGroups = {};
    data.forEach(row => {
        if (!skuGroups[row.SKU]) skuGroups[row.SKU] = {};
        skuGroups[row.SKU][row.Date] = row;
    });

    // 3. Build Header
    let headerHTML = '<tr><th>SKU</th><th>Metric</th>';
    allDates.forEach(date => {
        headerHTML += `<th>${date}</th>`;
    });
    headerHTML += '</tr>';
    thead.innerHTML = headerHTML;

    // 4. Build Rows
    tbody.innerHTML = '';

    Object.keys(skuGroups).sort().forEach(sku => {
        const skuData = skuGroups[sku];

        // Define metrics to show
        const metrics = [
            { key: 'Baseline_P50', label: 'Baseline' },
            { key: 'Constrained_Plan', label: 'Constrained Plan' },
            { key: 'Upside', label: 'Upside' }
        ];

        metrics.forEach(metric => {
            const tr = document.createElement('tr');

            // SKU Cell (only for first metric, or repeat?)
            // Let's repeat for clarity or use rowspan if we wanted to get fancy
            tr.innerHTML = `<td class="font-medium">${sku}</td><td class="text-secondary">${metric.label}</td>`;

            allDates.forEach(date => {
                const record = skuData[date];
                let val = '-';
                if (record && record[metric.key] !== null && record[metric.key] !== undefined) {
                    val = parseFloat(record[metric.key]).toFixed(0);
                }
                tr.innerHTML += `<td>${val}</td>`;
            });

            tbody.appendChild(tr);
        });

        // Add a spacer row or border
        // tbody.innerHTML += '<tr class="spacer"><td colspan="100%" style="height: 10px; background: var(--bg-dark);"></td></tr>';
    });
}

// Filtering
function filterTable() {
    const sku = document.getElementById('skuFilter').value.toLowerCase();
    const filtered = rawData.filter(row => row.SKU.toLowerCase().includes(sku));
    renderTable(filtered);
}

function updateTableBucket() {
    const bucket = document.getElementById('bucketFilter').value;

    if (bucket === 'weekly') {
        renderTable(rawData);
        return;
    }

    // Aggregation Logic for Monthly
    const aggregated = {};

    rawData.forEach(row => {
        // Assume Date is YYYY-MM-DD, extract YYYY-MM
        const month = row.Date.substring(0, 7);
        const key = `${row.SKU}_${month}`;

        if (!aggregated[key]) {
            aggregated[key] = {
                Date: month,
                SKU: row.SKU,
                Baseline_P50: 0,
                Plan: 0,
                Constrained_Plan: 0,
                Upside: 0
            };
        }

        // Sum metrics, treating null/empty as 0
        aggregated[key].Baseline_P50 += Number(row.Baseline_P50) || 0;
        aggregated[key].Plan += Number(row.Plan) || 0;
        aggregated[key].Constrained_Plan += Number(row.Constrained_Plan) || 0;
        aggregated[key].Upside += Number(row.Upside) || 0;
    });

    const monthlyData = Object.values(aggregated);
    renderTable(monthlyData);
}

// View Toggling
function toggleView(view) {
    document.querySelectorAll('.view-section').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.controls button').forEach(el => el.classList.remove('active'));

    document.getElementById(view === 'table' ? 'tableView' : 'chartView').classList.add('active');
    document.getElementById(view === 'table' ? 'btnTable' : 'btnChart').classList.add('active');
}

// Chat
async function sendMessage() {
    const input = document.getElementById('chatInput');
    const msg = input.value;
    if (!msg) return;

    addMessage('user', msg);
    input.value = '';

    const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: msg })
    });
    const data = await res.json();
    addMessage('agent', data.response);
}

function addMessage(role, text) {
    const div = document.createElement('div');
    div.className = `message ${role}`;
    div.textContent = text;
    document.getElementById('chatHistory').appendChild(div);
    document.getElementById('chatHistory').scrollTop = document.getElementById('chatHistory').scrollHeight;
}

// Chart Agent
async function requestChart() {
    const query = prompt("What chart would you like to see? (e.g., 'Show me sales for SKU_001')");
    if (!query) return;

    toggleView('chart');
    document.getElementById('chartStatus').textContent = "Generating chart...";

    const res = await fetch('/api/chart', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: query })
    });
    const data = await res.json();

    try {
        const config = JSON.parse(data.config);

        if (dynamicChartInstance) {
            dynamicChartInstance.destroy();
        }

        const ctx = document.getElementById('dynamicChart').getContext('2d');
        dynamicChartInstance = new Chart(ctx, config);
        document.getElementById('chartStatus').textContent = "";

    } catch (e) {
        document.getElementById('chartStatus').textContent = "Error generating chart: " + e.message;
    }
}

// History
async function loadHistory() {
    const res = await fetch('/api/history');
    const history = await res.json();

    const chatContainer = document.getElementById('chatHistory');
    chatContainer.innerHTML = ''; // Clear current chat

    if (history.length === 0) {
        addMessage('system', 'No history found.');
        return;
    }

    history.forEach(item => {
        addMessage('user', `[${item.timestamp.substring(0, 16)}] ${item.user_query}`);
        addMessage('agent', `${item.agent}: ${item.agent_response}`);
    });

    addMessage('system', '--- End of History ---');
}
async function runPlanningCycle() {
    addMessage("user", "Running full End-to-End Planning Cycle...");
    addMessage("system", "🚀 Initiating Orchestrator... Please wait.");

    try {
        const response = await fetch('/api/run_planning', {
            method: 'POST'
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        // Display logs
        if (data.logs && data.logs.length > 0) {
            data.logs.forEach(log => {
                // Format log message slightly
                let type = "system";
                if (log.includes("Error")) type = "system"; // Could use error style
                addMessage(type, log);
            });
        }

        // Display final report
        if (data.report) {
            addMessage("agent", "📋 **Final Report:**\n" + data.report);
        }

        addMessage("system", "✅ Planning Cycle Complete. Dashboard updated.");

        // Refresh data
        loadDashboard();
        loadTable();

    } catch (error) {
        console.error("Error running planning cycle:", error);
        addMessage("system", "❌ Error running planning cycle: " + error.message);
    }
}

// Also handle "run planning" in chat
// Also handle "run planning" in chat
const originalSendMessage = sendMessage;
sendMessage = async function () {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();

    if (message.toLowerCase().includes("run planning") || message.toLowerCase().includes("start planning")) {
        input.value = '';
        runPlanningCycle();
        return;
    }

    // Delegate to original function for normal messages
    await originalSendMessage();
}
