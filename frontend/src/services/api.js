import axios from 'axios';

// 创建axios实例
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 可以在这里添加认证token等
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response.data;
  },
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

// 记忆相关API
export const memoryAPI = {
  // 获取所有记忆
  getMemories: () => api.get('/memories'),
  
  // 获取单个记忆
  getMemory: (id) => api.get(`/memories/${id}`),
  
  // 创建记忆
  createMemory: (memory) => api.post('/memories', memory),
  
  // 更新记忆
  updateMemory: (id, memory) => api.put(`/memories/${id}`, memory),
  
  // 删除记忆
  deleteMemory: (id) => api.delete(`/memories/${id}`),
  
  // 搜索记忆
  searchMemories: (query, strategy = 'hybrid', limit = 10) => 
    api.post('/memories/search', { query, strategy, limit }),
};

// 聊天相关API
export const chatAPI = {
  // 发送消息
  sendMessage: (message) => api.post('/chat/message', { content: message }),
};

// 存储相关API
export const storageAPI = {
  // 获取所有存储信息
  getAllStorageInfo: () => api.get('/storage/all'),
  
  // 获取向量存储信息
  getVectorStorageInfo: () => api.get('/storage/vector'),
  
  // 获取图存储信息
  getGraphStorageInfo: () => api.get('/storage/graph'),
  
  // 获取缓存存储信息
  getCacheStorageInfo: () => api.get('/storage/cache'),
};

// 系统相关API
export const systemAPI = {
  // 健康检查
  healthCheck: () => api.get('/health'),
  
  // 获取系统信息
  getSystemInfo: () => api.get('/system/info'),
};

export default api; 