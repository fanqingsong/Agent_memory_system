/**
 * Memory Visualization Module
 * 
 * 该模块提供记忆可视化功能，包括关系图和列表视图。
 * 
 * 主要功能：
 * - 记忆关系图可视化
 * - 记忆列表展示
 * - 记忆搜索
 * - 记忆高亮
 * 
 * @author Cursor_for_YansongW
 * @date 2025-01-09
 * @version 0.1.0
 */

// 全局变量
let memoryChart = null;
let memoryData = {
    nodes: [],
    edges: []
};

/**
 * 初始化记忆图表
 */
function initMemoryChart() {
    const chartDom = document.getElementById('memoryGraph');
    memoryChart = echarts.init(chartDom);
    
    const option = {
        title: {
            text: '记忆关系图'
        },
        tooltip: {},
        animationDurationUpdate: 1500,
        animationEasingUpdate: 'quinticInOut',
        series: [{
            type: 'graph',
            layout: 'force',
            data: memoryData.nodes,
            links: memoryData.edges,
            roam: true,
            label: {
                show: true,
                position: 'right'
            },
            force: {
                repulsion: 100
            }
        }]
    };
    
    memoryChart.setOption(option);
}

/**
 * 更新记忆可视化
 * 
 * @param {Object} memory - 记忆对象
 */
function updateMemoryVisualization(memory) {
    // 添加新节点
    const newNode = {
        id: memory.memory_id,
        name: memory.content.substring(0, 20) + '...',
        symbolSize: memory.importance * 5,
        category: memory.memory_type
    };
    
    // 检查节点是否已存在
    const existingNodeIndex = memoryData.nodes.findIndex(
        node => node.id === memory.memory_id
    );
    
    if (existingNodeIndex === -1) {
        memoryData.nodes.push(newNode);
    } else {
        memoryData.nodes[existingNodeIndex] = newNode;
    }
    
    // 添加关系边
    memory.relations.forEach(relation => {
        const newEdge = {
            source: memory.memory_id,
            target: relation.target_id,
            value: relation.relation_type
        };
        
        // 检查边是否已存在
        const existingEdgeIndex = memoryData.edges.findIndex(
            edge => edge.source === newEdge.source && 
                   edge.target === newEdge.target
        );
        
        if (existingEdgeIndex === -1) {
            memoryData.edges.push(newEdge);
        } else {
            memoryData.edges[existingEdgeIndex] = newEdge;
        }
    });
    
    // 更新图表
    memoryChart.setOption({
        series: [{
            data: memoryData.nodes,
            links: memoryData.edges
        }]
    });
    
    // 更新列表视图
    updateMemoryList(memory);
}

/**
 * 更新记忆列表
 * 
 * @param {Object} memory - 记忆对象
 */
function updateMemoryList(memory) {
    const memoryList = document.getElementById('memoryList');
    
    // 检查是否已存在
    const existingCard = document.getElementById(`memory-${memory.memory_id}`);
    if (existingCard) {
        existingCard.remove();
    }
    
    // 创建新卡片
    const card = document.createElement('div');
    card.id = `memory-${memory.memory_id}`;
    card.className = 'card memory-card';
    card.innerHTML = `
        <div class="card-body">
            <h6 class="card-subtitle mb-2 text-muted">
                ${memory.memory_type} - 重要性: ${memory.importance}
            </h6>
            <p class="card-text">${memory.content}</p>
            <div class="text-muted small">
                创建时间: ${new Date(memory.created_at).toLocaleString()}
            </div>
        </div>
    `;
    
    // 添加点击事件
    card.addEventListener('click', () => {
        highlightMemory(memory.memory_id);
    });
    
    // 添加到列表
    memoryList.insertBefore(card, memoryList.firstChild);
}

/**
 * 高亮显示记忆
 * 
 * @param {string} memoryId - 记忆ID
 */
function highlightMemory(memoryId) {
    // 高亮图表中的节点
    const highlightNode = memoryData.nodes.find(node => node.id === memoryId);
    if (highlightNode) {
        memoryChart.dispatchAction({
            type: 'highlight',
            dataIndex: memoryData.nodes.indexOf(highlightNode)
        });
    }
    
    // 高亮列表中的卡片
    const cards = document.querySelectorAll('.memory-card');
    cards.forEach(card => {
        if (card.id === `memory-${memoryId}`) {
            card.classList.add('border-primary');
            card.scrollIntoView({ behavior: 'smooth' });
        } else {
            card.classList.remove('border-primary');
        }
    });
}

/**
 * 搜索记忆
 * 
 * @param {string} query - 搜索关键词
 */
function searchMemories(query) {
    const cards = document.querySelectorAll('.memory-card');
    cards.forEach(card => {
        const content = card.querySelector('.card-text').textContent;
        if (content.toLowerCase().includes(query.toLowerCase())) {
            card.style.display = 'block';
        } else {
            card.style.display = 'none';
        }
    });
}

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    // 初始化图表
    initMemoryChart();
    
    // 监听搜索输入
    const searchInput = document.getElementById('searchInput');
    searchInput.addEventListener('input', (e) => {
        searchMemories(e.target.value);
    });
    
    // 监听窗口大小变化
    window.addEventListener('resize', () => {
        memoryChart.resize();
    });
}); 