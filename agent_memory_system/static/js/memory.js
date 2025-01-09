/**
 * Memory Visualization Module
 * 
 * 该模块提供记忆可视化功能的前端实现，包括图形化展示和列表展示。
 * 
 * 主要功能：
 * - 记忆关系图的初始化和更新
 * - 记忆列表的展示和管理
 * - 记忆详情的展示
 * - 记忆节点的高亮显示
 * 
 * 依赖：
 * - ECharts: 用于图形化展示
 * - Bootstrap: 用于UI组件
 * 
 * @author Cursor_for_YansongW
 * @date 2025-01-09
 * @version 0.1.0
 */

// ECharts实例
let memoryGraph = null;

/**
 * 初始化记忆关系图
 * 
 * 创建并配置ECharts实例，设置图表的基本属性和事件监听。
 * 图表包含节点分类、工具提示、布局设置等。
 */
function initMemoryGraph() {
    const container = document.getElementById('memoryGraph');
    memoryGraph = echarts.init(container);
    
    // 配置图表
    const option = {
        title: {
            text: '记忆关系图'
        },
        tooltip: {
            trigger: 'item',
            formatter: function(params) {
                if (params.dataType === 'node') {
                    return `
                        <div>
                            <strong>${params.data.content}</strong><br>
                            类型: ${params.data.memory_type}<br>
                            重要性: ${params.data.importance}<br>
                            创建时间: ${new Date(params.data.created_at).toLocaleString()}
                        </div>
                    `;
                } else {
                    return `关系: ${params.data.relation_type}`;
                }
            }
        },
        legend: {
            data: ['短期记忆', '长期记忆', '工作记忆', '技能记忆']
        },
        animationDurationUpdate: 1500,
        animationEasingUpdate: 'quinticInOut',
        series: [{
            type: 'graph',
            layout: 'force',
            data: [],
            links: [],
            categories: [
                { name: '短期记忆' },
                { name: '长期记忆' },
                { name: '工作记忆' },
                { name: '技能记忆' }
            ],
            roam: true,
            label: {
                show: true,
                position: 'right',
                formatter: '{b}'
            },
            force: {
                repulsion: 100,
                edgeLength: 100
            },
            edgeSymbol: ['circle', 'arrow'],
            edgeSymbolSize: [4, 8],
            edgeLabel: {
                fontSize: 12
            },
            lineStyle: {
                opacity: 0.9,
                width: 2,
                curveness: 0
            }
        }]
    };
    
    memoryGraph.setOption(option);
    
    // 监听窗口大小变化
    window.addEventListener('resize', () => {
        memoryGraph.resize();
    });
    
    // 监听节点点击事件
    memoryGraph.on('click', (params) => {
        if (params.dataType === 'node') {
            showMemoryDetails(params.data);
        }
    });
}

/**
 * 更新图表数据
 * 
 * @param {Array} memories - 记忆节点数组
 * @param {Array} relations - 记忆关系数组
 */
function updateMemoryGraph(memories, relations) {
    const nodes = memories.map(memory => ({
        id: memory.id,
        name: memory.content.substring(0, 20) + (memory.content.length > 20 ? '...' : ''),
        content: memory.content,
        memory_type: memory.memory_type,
        importance: memory.importance,
        created_at: memory.created_at,
        category: getMemoryCategory(memory.memory_type),
        symbolSize: memory.importance * 5,
        value: memory.access_count
    }));
    
    const edges = relations.map(relation => ({
        source: relation.source_id,
        target: relation.target_id,
        relation_type: relation.relation_type,
        value: relation.weight,
        lineStyle: {
            width: relation.weight * 2
        }
    }));
    
    memoryGraph.setOption({
        series: [{
            data: nodes,
            links: edges
        }]
    });
}

/**
 * 获取记忆类型对应的分类索引
 * 
 * @param {string} type - 记忆类型
 * @returns {number} 分类索引
 */
function getMemoryCategory(type) {
    const categories = {
        'SHORT_TERM': 0,
        'LONG_TERM': 1,
        'WORKING': 2,
        'SKILL': 3
    };
    return categories[type] || 0;
}

/**
 * 更新记忆列表
 * 
 * @param {Array} memories - 记忆数组
 */
function updateMemoryList(memories) {
    const container = document.getElementById('memoryList');
    container.innerHTML = '';
    
    memories.forEach(memory => {
        const card = document.createElement('div');
        card.className = 'card memory-card';
        card.innerHTML = `
            <div class="card-body">
                <h6 class="card-title">${memory.content}</h6>
                <div class="card-text">
                    <small class="text-muted">
                        类型: ${memory.memory_type} | 
                        重要性: ${memory.importance} | 
                        创建时间: ${new Date(memory.created_at).toLocaleString()}
                    </small>
                </div>
            </div>
        `;
        
        card.addEventListener('click', () => {
            showMemoryDetails(memory);
        });
        
        container.appendChild(card);
    });
}

/**
 * 显示记忆详情
 * 
 * @param {Object} memory - 记忆对象
 * @param {string} memory.content - 记忆内容
 * @param {string} memory.memory_type - 记忆类型
 * @param {number} memory.importance - 重要性
 * @param {string} memory.created_at - 创建时间
 * @param {number} memory.access_count - 访问次数
 * @param {Object} memory.metadata - 元数据
 */
function showMemoryDetails(memory) {
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.innerHTML = `
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">记忆详情</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <div class="mb-3">
                        <label class="form-label">内容</label>
                        <textarea class="form-control" rows="3" readonly>${memory.content}</textarea>
                    </div>
                    <div class="row">
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label class="form-label">类型</label>
                                <input type="text" class="form-control" value="${memory.memory_type}" readonly>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label class="form-label">重要性</label>
                                <input type="text" class="form-control" value="${memory.importance}" readonly>
                            </div>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label class="form-label">创建时间</label>
                                <input type="text" class="form-control" value="${new Date(memory.created_at).toLocaleString()}" readonly>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label class="form-label">访问次数</label>
                                <input type="text" class="form-control" value="${memory.access_count}" readonly>
                            </div>
                        </div>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">元数据</label>
                        <pre class="form-control" style="max-height: 200px; overflow-y: auto;">${JSON.stringify(memory.metadata, null, 2)}</pre>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    const modalInstance = new bootstrap.Modal(modal);
    modalInstance.show();
    
    modal.addEventListener('hidden.bs.modal', () => {
        document.body.removeChild(modal);
    });
}

/**
 * 高亮显示记忆节点
 * 
 * @param {string} memoryId - 要高亮显示的记忆ID
 */
function highlightMemory(memoryId) {
    const series = memoryGraph.getOption().series[0];
    const nodeIndex = series.data.findIndex(node => node.id === memoryId);
    
    if (nodeIndex !== -1) {
        // 创建高亮动画
        const originSize = series.data[nodeIndex].symbolSize;
        const highlightSize = originSize * 1.5;
        
        memoryGraph.setOption({
            series: [{
                data: series.data.map((node, index) => {
                    if (index === nodeIndex) {
                        return {
                            ...node,
                            symbolSize: highlightSize,
                            itemStyle: {
                                color: '#ff4444'
                            }
                        };
                    }
                    return node;
                })
            }]
        });
        
        // 2秒后恢复原状
        setTimeout(() => {
            memoryGraph.setOption({
                series: [{
                    data: series.data.map((node, index) => {
                        if (index === nodeIndex) {
                            return {
                                ...node,
                                symbolSize: originSize,
                                itemStyle: null
                            };
                        }
                        return node;
                    })
                }]
            });
        }, 2000);
    }
}

// 搜索记忆
function searchMemories(query) {
    fetch(`/api/memories/search?q=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(memories => {
            updateMemoryList(memories);
        })
        .catch(error => {
            console.error('搜索记忆失败:', error);
            showError('搜索记忆失败');
        });
}

// 事件监听器
document.addEventListener('DOMContentLoaded', () => {
    // 初始化图表
    initMemoryGraph();
    
    // 加载初始数据
    fetch('/api/memories')
        .then(response => response.json())
        .then(data => {
            updateMemoryGraph(data.memories, data.relations);
            updateMemoryList(data.memories);
        })
        .catch(error => {
            console.error('加载记忆数据失败:', error);
            showError('加载记忆数据失败');
        });
    
    // 搜索输入框事件
    const searchInput = document.getElementById('searchInput');
    let searchTimeout = null;
    
    searchInput.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            searchMemories(e.target.value);
        }, 500);
    });
}); 