# 测试客户端设计

## 1. H5聊天界面

### 1.1 界面布局

```html
<!-- 主布局 -->
<div class="chat-container">
    <!-- 顶部导航栏 -->
    <nav class="chat-nav">
        <div class="title">Memory System Test</div>
        <div class="actions">
            <button class="settings-btn">设置</button>
            <button class="theme-btn">主题</button>
        </div>
    </nav>
    
    <!-- 聊天区域 -->
    <div class="chat-main">
        <div class="message-list">
            <!-- 消息气泡 -->
            <div class="message user">
                <div class="avatar"></div>
                <div class="content"></div>
                <div class="time"></div>
            </div>
            <div class="message bot">
                <div class="avatar"></div>
                <div class="content markdown-body"></div>
                <div class="time"></div>
            </div>
        </div>
    </div>
    
    <!-- 输入区域 -->
    <div class="chat-input">
        <textarea placeholder="输入消息..."></textarea>
        <button class="send-btn">发送</button>
    </div>
</div>

<!-- 设置弹窗 -->
<div class="settings-modal">
    <div class="modal-content">
        <h3>模型配置</h3>
        <form>
            <!-- 模型选择 -->
            <div class="form-item">
                <label>模型类型</label>
                <select name="model">
                    <option value="openai">OpenAI</option>
                    <option value="azure">Azure OpenAI</option>
                </select>
            </div>
            
            <!-- API配置 -->
            <div class="form-item">
                <label>API Key</label>
                <input type="password" name="apiKey">
            </div>
            
            <!-- 模型参数 -->
            <div class="form-item">
                <label>温度</label>
                <input type="range" name="temperature" min="0" max="1" step="0.1">
            </div>
            
            <div class="form-item">
                <label>最大长度</label>
                <input type="number" name="maxLength">
            </div>
        </form>
    </div>
</div>
```

### 1.2 功能设计

```typescript
// 配置接口
interface ModelConfig {
    type: 'openai' | 'azure';
    apiKey?: string;
    baseUrl?: string;
    model: string;
    temperature: number;
    maxLength: number;
}

// 消息接口
interface Message {
    id: string;
    role: 'user' | 'bot';
    content: string;
    timestamp: number;
    status: 'sending' | 'success' | 'error';
}

// 聊天管理器
class ChatManager {
    private config: ModelConfig;
    private messages: Message[];
    private modelClient: ModelClient;
    
    // 发送消息
    async sendMessage(content: string): Promise<void> {
        try {
            // 添加用户消息
            const userMsg = this.addMessage('user', content);
            
            // 创建机器人消息
            const botMsg = this.addMessage('bot', '', 'sending');
            
            // 调用模型API
            const response = await this.modelClient.chat(content);
            
            // 更新机器人消息
            this.updateMessage(botMsg.id, response);
        } catch (error) {
            // 错误处理
            this.handleError(error);
        }
    }
    
    // 配置更新
    updateConfig(config: ModelConfig): void {
        this.config = config;
        this.modelClient = this.createModelClient(config);
        localStorage.setItem('chatConfig', JSON.stringify(config));
    }
}

// 渲染管理器
class RenderManager {
    // Markdown渲染
    renderMarkdown(content: string): string {
        return marked(content);
    }
    
    // 代码高亮
    highlightCode(code: string, language: string): string {
        return Prism.highlight(code, Prism.languages[language]);
    }
    
    // 打字机效果
    async typeWriter(element: HTMLElement, text: string): Promise<void> {
        // 实现打字机效果
    }
}

// 主题管理器
class ThemeManager {
    // 主题切换
    toggleTheme(): void {
        const theme = localStorage.getItem('theme') === 'dark' ? 'light' : 'dark';
        document.body.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
    }
}
```

### 1.3 样式设计

```scss
// 主题变量
:root {
    // 亮色主题
    --bg-primary: #ffffff;
    --bg-secondary: #f5f5f5;
    --text-primary: #333333;
    --text-secondary: #666666;
    --accent-color: #2196f3;
    --border-color: #e0e0e0;
    
    // 暗色主题
    &[data-theme='dark'] {
        --bg-primary: #1a1a1a;
        --bg-secondary: #2d2d2d;
        --text-primary: #ffffff;
        --text-secondary: #b0b0b0;
        --accent-color: #64b5f6;
        --border-color: #404040;
    }
}

// 布局样式
.chat-container {
    display: flex;
    flex-direction: column;
    height: 100vh;
    background: var(--bg-primary);
    color: var(--text-primary);
}

// 消息气泡
.message {
    display: flex;
    margin: 1rem;
    
    .content {
        max-width: 70%;
        padding: 1rem;
        border-radius: 1rem;
        background: var(--bg-secondary);
    }
    
    &.user .content {
        background: var(--accent-color);
        color: white;
    }
}

// 响应式设计
@media (max-width: 768px) {
    .message .content {
        max-width: 85%;
    }
}
```

## 2. 功能模块

### 2.1 模型客户端

```typescript
// 模型客户端接口
interface ModelClient {
    chat(message: string): Promise<string>;
    stream(message: string): AsyncIterator<string>;
}

// OpenAI客户端
class OpenAIClient implements ModelClient {
    constructor(private config: ModelConfig) {}
    
    async chat(message: string): Promise<string> {
        const response = await fetch('https://api.openai.com/v1/chat/completions', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.config.apiKey}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                model: this.config.model,
                messages: [{ role: 'user', content: message }],
                temperature: this.config.temperature
            })
        });
        
        const data = await response.json();
        return data.choices[0].message.content;
    }
}


```

### 2.2 错误处理

```typescript
// 错误类型
enum ErrorType {
    NetworkError = 'NETWORK_ERROR',
    APIError = 'API_ERROR',
    AuthError = 'AUTH_ERROR',
    RateLimit = 'RATE_LIMIT',
    Unknown = 'UNKNOWN'
}

// 错误处理器
class ErrorHandler {
    handle(error: any): void {
        // 确定错误类型
        const type = this.getErrorType(error);
        
        // 显示错误消息
        this.showError(type, error.message);
        
        // 记录错误日志
        this.logError(type, error);
        
        // 执行恢复操作
        this.recover(type);
    }
    
    private showError(type: ErrorType, message: string): void {
        const toast = document.createElement('div');
        toast.className = 'error-toast';
        toast.textContent = this.getErrorMessage(type, message);
        document.body.appendChild(toast);
        
        setTimeout(() => toast.remove(), 3000);
    }
}
```

### 2.3 会话管理

```typescript
// 会话存储
class SessionStorage {
    // 保存会话
    saveSession(messages: Message[]): void {
        const session = {
            id: Date.now().toString(),
            messages,
            timestamp: Date.now()
        };
        
        const sessions = this.getSessions();
        sessions.unshift(session);
        
        // 最多保存20个会话
        if (sessions.length > 20) {
            sessions.pop();
        }
        
        localStorage.setItem('sessions', JSON.stringify(sessions));
    }
    
    // 加载会话
    loadSession(id: string): Message[] {
        const sessions = this.getSessions();
        const session = sessions.find(s => s.id === id);
        return session ? session.messages : [];
    }
}
```

## 3. 测试场景

### 3.1 功能测试

```typescript
// 测试用例
const testCases = [
    {
        name: '基本对话测试',
        input: '你好',
        expected: response => response.length > 0
    },
    {
        name: '长文本测试',
        input: '请生成一篇500字的文章',
        expected: response => response.length >= 500
    },
    {
        name: '代码生成测试',
        input: '写一个冒泡排序',
        expected: response => response.includes('function')
    }
];

// 测试执行器
class TestRunner {
    async runTests(): Promise<TestResult[]> {
        const results = [];
        
        for (const test of testCases) {
            try {
                const response = await chatManager.sendMessage(test.input);
                const passed = test.expected(response);
                
                results.push({
                    name: test.name,
                    passed,
                    error: null
                });
            } catch (error) {
                results.push({
                    name: test.name,
                    passed: false,
                    error
                });
            }
        }
        
        return results;
    }
}
```

### 3.2 性能测试

```typescript
// 性能测试配置
interface PerformanceTestConfig {
    concurrentUsers: number;
    requestsPerUser: number;
    delayBetweenRequests: number;
}

// 性能测试执行器
class PerformanceTestRunner {
    async runTest(config: PerformanceTestConfig): Promise<PerformanceResult> {
        const startTime = Date.now();
        const results = [];
        
        // 创建用户
        const users = Array(config.concurrentUsers).fill(null).map(() => {
            return this.simulateUser(config.requestsPerUser, config.delayBetweenRequests);
        });
        
        // 等待所有用户完成
        await Promise.all(users);
        
        const endTime = Date.now();
        const duration = endTime - startTime;
        
        return {
            totalRequests: config.concurrentUsers * config.requestsPerUser,
            duration,
            averageResponseTime: results.reduce((a, b) => a + b) / results.length,
            successRate: results.filter(r => r < 1000).length / results.length
        };
    }
}
``` 