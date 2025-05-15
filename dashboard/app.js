// Configuration
const config = {
    nodes: {
        node_1: { host: '127.0.0.1', port: 8001 },
        node_2: { host: '127.0.0.1', port: 8002 },
        node_3: { host: '127.0.0.1', port: 8003 }
    },
    refreshInterval: 5000 // 5 seconds
};

let keyDistributionChart = null;

// Initialize the dashboard
async function initializeDashboard() {
    await updateNodeStatuses();
    setupKeyDistributionChart();
    setInterval(updateNodeStatuses, config.refreshInterval);
}

// Update node statuses
async function updateNodeStatuses() {
    const nodesContainer = document.getElementById('nodes-container');
    nodesContainer.innerHTML = '';
    
    for (const [nodeId, nodeConfig] of Object.entries(config.nodes)) {
        try {
            const status = await fetchNodeStatus(nodeId, nodeConfig);
            const nodeInfo = await fetchNodeInfo(nodeId, nodeConfig);
            
            const nodeElement = createNodeElement(nodeId, status, nodeInfo);
            nodesContainer.appendChild(nodeElement);
        } catch (error) {
            console.error(`Failed to fetch status for ${nodeId}:`, error);
        }
    }
    
    updateKeyDistributionChart();
}

// Create node status element
function createNodeElement(nodeId, status, nodeInfo) {
    const template = document.getElementById('node-template');
    const node = template.content.cloneNode(true);
    
    node.querySelector('[data-node-id]').textContent = nodeId;
    node.querySelector('.status-badge').textContent = status.status;
    node.querySelector('.uptime').textContent = status.uptime;
    node.querySelector('.key-count').textContent = status.key_count;
    node.querySelector('.memory-usage').textContent = `${nodeInfo.memory_usage.percent}%`;
    node.querySelector('.cpu-usage').textContent = `${nodeInfo.cpu_usage}%`;
    
    return node;
}

// Setup key distribution chart
function setupKeyDistributionChart() {
    const ctx = document.getElementById('keyDistributionChart').getContext('2d');
    keyDistributionChart = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: Object.keys(config.nodes),
            datasets: [{
                data: Array(Object.keys(config.nodes).length).fill(0),
                backgroundColor: [
                    'rgba(255, 99, 132, 0.8)',
                    'rgba(54, 162, 235, 0.8)',
                    'rgba(255, 206, 86, 0.8)'
                ]
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                }
            }
        }
    });
}

// Update key distribution chart
async function updateKeyDistributionChart() {
    const keyCounts = [];
    for (const [nodeId, nodeConfig] of Object.entries(config.nodes)) {
        try {
            const status = await fetchNodeStatus(nodeId, nodeConfig);
            keyCounts.push(status.key_count);
        } catch (error) {
            keyCounts.push(0);
        }
    }
    
    keyDistributionChart.data.datasets[0].data = keyCounts;
    keyDistributionChart.update();
}

// API Helpers
async function fetchNodeStatus(nodeId, nodeConfig) {
    const response = await fetch(`http://${nodeConfig.host}:${nodeConfig.port}/status`);
    return response.json();
}

async function fetchNodeInfo(nodeId, nodeConfig) {
    const response = await fetch(`http://${nodeConfig.host}:${nodeConfig.port}/node-info`);
    return response.json();
}

// CRUD Operations
async function createOrUpdate() {
    const key = document.getElementById('key-input').value;
    const value = document.getElementById('value-input').value;
    
    if (!key || !value) {
        showResult('Please provide both key and value', 'error');
        return;
    }
    
    try {
        const response = await fetch(
            `http://${config.nodes.node_1.host}:${config.nodes.node_1.port}/store/${key}?value=${encodeURIComponent(value)}`,
            {
                method: 'PUT'
            }
        );
        
        const result = await response.json();
        showResult('Value stored successfully', 'success');
        updateNodeStatuses();
    } catch (error) {
        showResult('Failed to store value', 'error');
        console.error('Error:', error);
    }
}

async function getValue() {
    const key = document.getElementById('key-input').value;
    
    if (!key) {
        showResult('Please provide a key', 'error');
        return;
    }
    
    try {
        const response = await fetch(`http://${config.nodes.node_1.host}:${config.nodes.node_1.port}/store/${key}`);
        
        if (response.ok) {
            const result = await response.json();
            showResult(`Value: ${result.value}`, 'success');
        } else {
            showResult('Key not found', 'error');
        }
    } catch (error) {
        showResult('Failed to get value', 'error');
        console.error('Error:', error);
    }
}

async function deleteKey() {
    const key = document.getElementById('key-input').value;
    
    if (!key) {
        showResult('Please provide a key', 'error');
        return;
    }
    
    try {
        const response = await fetch(
            `http://${config.nodes.node_1.host}:${config.nodes.node_1.port}/store/${key}`,
            {
                method: 'DELETE'
            }
        );
        
        if (response.ok) {
            showResult('Key deleted successfully', 'success');
            updateNodeStatuses();
        } else {
            showResult('Key not found', 'error');
        }
    } catch (error) {
        showResult('Failed to delete key', 'error');
        console.error('Error:', error);
    }
}

// Helper function to show operation results
function showResult(message, type) {
    const resultDiv = document.getElementById('operation-result');
    resultDiv.textContent = message;
    resultDiv.className = `mt-4 p-4 rounded ${type === 'error' ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}`;
    resultDiv.classList.remove('hidden');
    
    setTimeout(() => {
        resultDiv.classList.add('hidden');
    }, 3000);
}

// Initialize the dashboard when the page loads
document.addEventListener('DOMContentLoaded', initializeDashboard); 