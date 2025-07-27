/**
 * Chat Module
 * 
 * 该模块提供聊天功能的前端实现，包括WebSocket通信、消息处理和UI交互。
 * 
 * 主要功能：
 * - WebSocket连接管理
 * - 消息发送和接收
 * - 聊天界面更新
 * - 设置管理
 * - Ollama模型集成
 * 
 * @author Cursor_for_YansongW
 * @date 2025-01-09
 * @version 0.1.0
 */

// 全局变量
let ws = null;
let messageQueue = [];
let isProcessing = false;

/**
 * 初始化WebSocket连接
 * 
 * 建立与服务器的WebSocket连接，并设置相关的事件处理器。
 * 如果连接断开，会自动尝试重新连接。
 */
function initWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;
    ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
        console.log('WebSocket连接已建立');
        // 发送任何排队的消息
        while (messageQueue.length > 0) {
            const message = messageQueue.shift();
            ws.send(JSON.stringify(message));
        }
    };
    
    ws.onmessage = (event) => {
        const response = JSON.parse(event.data);
        handleResponse(response);
    };
    
    ws.onclose = () => {
        console.log('WebSocket连接已关闭');
        // 5秒后尝试重新连接
        setTimeout(initWebSocket, 5000);
    };
    
    ws.onerror = (error) => {
        console.error('WebSocket错误:', error);
        showError('WebSocket连接错误，请检查网络连接');
    };
}

/**
 * 处理服务器响应
 * 
 * @param {Object} response - 服务器返回的响应对象
 * @param {string} response.type - 响应类型
 * @param {string} [response.content] - 消息内容
 * @param {Object} [response.memory] - 记忆对象
 * @param {string} [response.memory_id] - 记忆ID
 * @param {string} [response.message] - 错误消息
 * @param {Array} [response.models] - 模型列表
 */
function handleResponse(response) {
    console.log('收到服务器响应:', response);
    switch (response.type) {
        case 'message':
            // 从data对象中获取content
            const content = response.data?.content || response.content;
            if (content) {
                addMessage(content, 'bot');
            } else {
                console.error('消息内容为空:', response);
            }
            break;
        case 'memory_created':
            updateMemoryVisualization(response.data?.memory || response.memory);
            break;
        case 'memory_accessed':
            highlightMemory(response.data?.memory_id || response.memory_id);
            break;
        case 'error':
            const errorMessage = response.data?.message || response.message;
            showError(errorMessage || '未知错误');
            break;
        case 'models_list':
            updateModelsList(response.data?.models || response.models);
            break;
        default:
            console.log('未处理的消息类型:', response.type);
    }
    isProcessing = false;
}

// 更新模型列表
function updateModelsList(models) {
    const modelSelect = document.getElementById('ollamaModel');
    modelSelect.innerHTML = '';
    
    models.forEach(model => {
        const option = document.createElement('option');
        option.value = model;
        option.textContent = model;
        modelSelect.appendChild(option);
    });
}

/**
 * 添加消息到聊天界面
 * 
 * @param {string} content - 消息内容
 * @param {string} sender - 发送者类型 ('user' | 'bot')
 */
function addMessage(content, sender) {
    const chatContainer = document.getElementById('chatContainer');
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${sender}-message`;
    
    // 处理Markdown格式
    if (sender === 'bot') {
        try {
            // 检查marked是否可用
            if (typeof marked === 'function') {
                const formattedContent = marked(content);
                messageDiv.innerHTML = formattedContent;
            } else {
                // 如果marked不可用，使用简单的文本处理
                messageDiv.textContent = content;
                console.warn('marked库未加载，使用纯文本显示');
            }
        } catch (error) {
            console.error('Markdown处理错误:', error);
            messageDiv.textContent = content;
        }
    } else {
        messageDiv.textContent = content;
    }
    
    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

/**
 * 发送消息到服务器
 * 
 * @param {string} content - 要发送的消息内容
 */
function sendMessage(content) {
    if (!content.trim()) return;
    
    // 添加用户消息到界面
    addMessage(content, 'user');
    
    const message = {
        type: 'message',
        content: content,
        timestamp: new Date().toISOString()
    };
    
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify(message));
    } else {
        messageQueue.push(message);
    }
    
    // 清空输入框
    document.getElementById('messageInput').value = '';
}

// 显示错误消息
function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'alert alert-danger alert-dismissible fade show';
    errorDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.insertBefore(errorDiv, document.body.firstChild);
}

// 获取Ollama模型列表
async function fetchOllamaModels() {
    const baseUrl = document.getElementById('ollamaBaseUrl').value;
    try {
        const response = await fetch(`${baseUrl}/api/tags`);
        if (!response.ok) throw new Error('获取模型列表失败');
        const data = await response.json();
        return data.models.map(model => model.name);
    } catch (error) {
        console.error('获取Ollama模型列表失败:', error);
        showError('无法连接到Ollama服务');
        return [];
    }
}

// 事件监听器
document.addEventListener('DOMContentLoaded', () => {
    // 初始化WebSocket
    initWebSocket();
    
    // 初始化默认设置 - 默认选择Ollama
    const provider = document.getElementById('llmProvider').value;
    const apiKeyGroup = document.getElementById('apiKeyGroup');
    const ollamaSettingsGroup = document.getElementById('ollamaSettingsGroup');
    
    if (provider === 'openai') {
        apiKeyGroup.style.display = 'block';
        ollamaSettingsGroup.style.display = 'none';
    } else {
        apiKeyGroup.style.display = 'none';
        ollamaSettingsGroup.style.display = 'block';
        
        // 获取Ollama模型列表
        fetchOllamaModels().then(models => {
            updateModelsList(models);
        });
    }
    
    // LLM提供者切换事件
    document.getElementById('llmProvider').addEventListener('change', async (e) => {
        const provider = e.target.value;
        const apiKeyGroup = document.getElementById('apiKeyGroup');
        const ollamaSettingsGroup = document.getElementById('ollamaSettingsGroup');
        
        if (provider === 'openai') {
            apiKeyGroup.style.display = 'block';
            ollamaSettingsGroup.style.display = 'none';
        } else {
            apiKeyGroup.style.display = 'none';
            ollamaSettingsGroup.style.display = 'block';
            
            // 获取Ollama模型列表
            const models = await fetchOllamaModels();
            updateModelsList(models);
        }
    });
    
    // Ollama服务地址变更事件
    document.getElementById('ollamaBaseUrl').addEventListener('change', async () => {
        const models = await fetchOllamaModels();
        updateModelsList(models);
    });
    
    // 发送按钮点击事件
    document.getElementById('sendButton').addEventListener('click', () => {
        const input = document.getElementById('messageInput');
        sendMessage(input.value);
    });
    
    // 输入框回车事件
    document.getElementById('messageInput').addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage(e.target.value);
        }
    });
    
    // 保存设置按钮点击事件
    document.getElementById('saveSettings').addEventListener('click', () => {
        const provider = document.getElementById('llmProvider').value;
        const settings = {
            provider: provider,
            importanceThreshold: document.getElementById('importanceThreshold').value,
            retentionDays: document.getElementById('retentionDays').value
        };
        
        if (provider === 'openai') {
            settings.apiKey = document.getElementById('apiKey').value;
        } else {
            settings.ollamaBaseUrl = document.getElementById('ollamaBaseUrl').value;
            settings.ollamaModel = document.getElementById('ollamaModel').value;
        }
        
        // 发送设置到服务器
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({
                type: 'settings',
                settings: settings
            }));
        }
        
        // 关闭模态框
        const modal = bootstrap.Modal.getInstance(document.getElementById('settingsModal'));
        modal.hide();
    });
    
    // 重要性阈值滑块事件
    document.getElementById('importanceThreshold').addEventListener('input', (e) => {
        document.getElementById('importanceValue').textContent = e.target.value;
    });
});