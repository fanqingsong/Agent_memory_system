/**
 * H5客户端主逻辑
 * 
 * 功能：
 * - 消息发送和接收
 * - WebSocket连接管理
 * - 主题切换
 * - 设置管理
 * - Markdown渲染
 */

// 配置管理
class ConfigManager {
    constructor() {
        this.config = this.loadConfig();
    }
    
    // 加载配置
    loadConfig() {
        const defaultConfig = {
            theme: 'light',
            model: 'openai',
            apiKey: '',
            temperature: 0.7,
            maxLength: 2048
        };
        
        const savedConfig = localStorage.getItem('chatConfig');
        return savedConfig ? JSON.parse(savedConfig) : defaultConfig;
    }
    
    // 保存配置
    saveConfig(config) {
        this.config = config;
        localStorage.setItem('chatConfig', JSON.stringify(config));
    }
    
    // 获取配置
    getConfig() {
        return this.config;
    }
}

// WebSocket管理器
class WebSocketManager {
    constructor(url) {
        this.url = url;
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.listeners = new Map();
    }
    
    // 连接WebSocket
    connect() {
        try {
            this.ws = new WebSocket(this.url);
            
            this.ws.onopen = () => {
                console.log('WebSocket连接成功');
                this.reconnectAttempts = 0;
                this.emit('connected');
            };
            
            this.ws.onclose = () => {
                console.log('WebSocket连接关闭');
                this.emit('disconnected');
                this.reconnect();
            };
            
            this.ws.onerror = (error) => {
                console.error('WebSocket错误:', error);
                this.emit('error', error);
            };
            
            this.ws.onmessage = (event) => {
                const message = JSON.parse(event.data);
                this.emit('message', message);
            };
            
        } catch (error) {
            console.error('WebSocket连接失败:', error);
            this.reconnect();
        }
    }
    
    // 重连
    reconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`尝试重连(${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
            setTimeout(() => this.connect(), 1000 * Math.pow(2, this.reconnectAttempts));
        } else {
            console.error('WebSocket重连失败');
            this.emit('reconnectFailed');
        }
    }
    
    // 发送消息
    send(message) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(message));
        } else {
            console.error('WebSocket未连接');
        }
    }
    
    // 添加事件监听
    on(event, callback) {
        if (!this.listeners.has(event)) {
            this.listeners.set(event, []);
        }
        this.listeners.get(event).push(callback);
    }
    
    // 触发事件
    emit(event, data) {
        const callbacks = this.listeners.get(event);
        if (callbacks) {
            callbacks.forEach(callback => callback(data));
        }
    }
    
    // 关闭连接
    close() {
        if (this.ws) {
            this.ws.close();
        }
    }
}

// UI管理器
class UIManager {
    constructor() {
        // DOM元素
        this.messageList = document.querySelector('.message-list');
        this.messageTemplate = document.querySelector('#message-template');
        this.input = document.querySelector('.chat-input textarea');
        this.sendButton = document.querySelector('.chat-input button');
        this.settingsButton = document.querySelector('.settings-btn');
        this.themeButton = document.querySelector('.theme-btn');
        this.settingsModal = document.querySelector('.settings-modal');
        this.settingsForm = document.querySelector('.settings-modal form');
        
        // 绑定事件
        this.bindEvents();
    }
    
    // 绑定事件
    bindEvents() {
        // 发送消息
        this.sendButton.addEventListener('click', () => this.handleSend());
        this.input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.handleSend();
            }
        });
        
        // 设置相关
        this.settingsButton.addEventListener('click', () => this.toggleSettings());
        this.settingsForm.addEventListener('submit', (e) => this.handleSettingsSave(e));
        this.settingsModal.querySelector('.cancel').addEventListener('click', () => this.toggleSettings());
        
        // 主题切换
        this.themeButton.addEventListener('click', () => this.toggleTheme());
        
        // 范围输入实时更新
        const rangeInput = this.settingsForm.querySelector('input[type="range"]');
        const rangeValue = rangeInput.nextElementSibling;
        rangeInput.addEventListener('input', () => {
            rangeValue.textContent = rangeInput.value;
        });
    }
    
    // 处理消息发送
    handleSend() {
        const content = this.input.value.trim();
        if (content) {
            this.addMessage('user', content);
            this.input.value = '';
            this.emit('send', content);
        }
    }
    
    // 添加消息
    addMessage(role, content) {
        const message = this.messageTemplate.content.cloneNode(true);
        const messageDiv = message.querySelector('.message');
        const contentDiv = message.querySelector('.content');
        const timeDiv = message.querySelector('.time');
        
        messageDiv.classList.add(role);
        contentDiv.innerHTML = marked.parse(content);
        timeDiv.textContent = new Date().toLocaleTimeString();
        
        this.messageList.appendChild(message);
        this.scrollToBottom();
        
        // 代码高亮
        Prism.highlightAllUnder(contentDiv);
    }
    
    // 滚动到底部
    scrollToBottom() {
        this.messageList.scrollTop = this.messageList.scrollHeight;
    }
    
    // 切换设置弹窗
    toggleSettings() {
        this.settingsModal.classList.toggle('active');
    }
    
    // 处理设置保存
    handleSettingsSave(e) {
        e.preventDefault();
        const formData = new FormData(e.target);
        const config = {
            model: formData.get('model'),
            apiKey: formData.get('apiKey'),
            temperature: parseFloat(formData.get('temperature')),
            maxLength: parseInt(formData.get('maxLength'))
        };
        this.emit('configSave', config);
        this.toggleSettings();
    }
    
    // 切换主题
    toggleTheme() {
        const theme = document.body.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
        document.body.setAttribute('data-theme', theme);
        this.emit('themeChange', theme);
    }
    
    // 更新设置表单
    updateSettingsForm(config) {
        const form = this.settingsForm;
        form.querySelector('select[name="model"]').value = config.model;
        form.querySelector('input[name="apiKey"]').value = config.apiKey;
        form.querySelector('input[name="temperature"]').value = config.temperature;
        form.querySelector('input[name="temperature"] + .value').textContent = config.temperature;
        form.querySelector('input[name="maxLength"]').value = config.maxLength;
    }
}

// 应用主类
class App {
    constructor() {
        // 初始化组件
        this.config = new ConfigManager();
        this.ws = new WebSocketManager('ws://localhost:8000/ws');
        this.ui = new UIManager();
        
        // 绑定事件
        this.bindEvents();
        
        // 初始化
        this.initialize();
    }
    
    // 绑定事件
    bindEvents() {
        // WebSocket事件
        this.ws.on('message', (message) => this.handleMessage(message));
        this.ws.on('error', (error) => this.handleError(error));
        
        // UI事件
        this.ui.on('send', (content) => this.handleSend(content));
        this.ui.on('configSave', (config) => this.handleConfigSave(config));
        this.ui.on('themeChange', (theme) => this.handleThemeChange(theme));
    }
    
    // 初始化
    initialize() {
        // 加载配置
        const config = this.config.getConfig();
        
        // 设置主题
        document.body.setAttribute('data-theme', config.theme);
        
        // 更新设置表单
        this.ui.updateSettingsForm(config);
        
        // 连接WebSocket
        this.ws.connect();
    }
    
    // 处理消息发送
    handleSend(content) {
        const message = {
            type: 'message',
            content,
            config: this.config.getConfig()
        };
        this.ws.send(message);
    }
    
    // 处理接收消息
    handleMessage(message) {
        if (message.type === 'message') {
            this.ui.addMessage('bot', message.content);
        }
    }
    
    // 处理错误
    handleError(error) {
        this.ui.addMessage('bot', `错误: ${error.message}`);
    }
    
    // 处理配置保存
    handleConfigSave(config) {
        this.config.saveConfig(config);
    }
    
    // 处理主题切换
    handleThemeChange(theme) {
        const config = this.config.getConfig();
        config.theme = theme;
        this.config.saveConfig(config);
    }
}

// 启动应用
window.addEventListener('DOMContentLoaded', () => {
    window.app = new App();
}); 