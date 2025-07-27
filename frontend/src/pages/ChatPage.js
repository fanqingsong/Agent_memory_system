import React, { useState, useRef, useEffect } from 'react';
import { Card, Input, Button, Spin, Empty, message, Badge } from 'antd';
import { SendOutlined, RobotOutlined, UserOutlined, WifiOutlined, WifiOutlined as WifiDisconnectedOutlined } from '@ant-design/icons';
import { chatAPI } from '../services/api';
import websocketService from '../services/websocket';

const { TextArea } = Input;

const ChatPage = () => {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [wsStatus, setWsStatus] = useState('disconnected');
  const [currentBotMessage, setCurrentBotMessage] = useState(null);
  const messagesEndRef = useRef(null);
  const connectionHandlerId = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, currentBotMessage]);

  // 初始化 WebSocket 连接
  useEffect(() => {
    const initWebSocket = async () => {
      try {
        // 先注册连接状态处理器
        connectionHandlerId.current = websocketService.onConnection((status) => {
          console.log('WebSocket 状态变化:', status);
          setWsStatus(status);
          if (status === 'connected') {
            message.success('WebSocket 连接成功');
          } else if (status === 'disconnected') {
            message.warning('WebSocket 连接断开');
          }
        });

        // 注册消息处理器
        websocketService.onMessage('message', handleChatResponse);
        websocketService.onMessage('chat_stream', handleChatStream);
        websocketService.onMessage('error', handleChatError);
        websocketService.onMessage('welcome', handleWelcome);

        // 然后尝试连接
        await websocketService.connect();
        
        // 连接后立即检查状态
        const currentStatus = websocketService.getStatus();
        console.log('连接后立即检查状态:', currentStatus);
        setWsStatus(currentStatus);

      } catch (error) {
        console.error('WebSocket 连接失败:', error);
        message.error('WebSocket 连接失败，将使用 HTTP 模式');
        setWsStatus('disconnected');
      }
    };

    initWebSocket();

    // 清理函数
    return () => {
      if (connectionHandlerId.current) {
        websocketService.offConnection(connectionHandlerId.current);
      }
      websocketService.offMessage('message', handleChatResponse);
      websocketService.offMessage('chat_stream', handleChatStream);
      websocketService.offMessage('error', handleChatError);
      websocketService.offMessage('welcome', handleWelcome);
    };
  }, []);

  // 处理欢迎消息
  const handleWelcome = (data) => {
    console.log('收到欢迎消息:', data);
  };

  // 处理聊天回复
  const handleChatResponse = (data) => {
    console.log('收到聊天回复:', data);
    
    // 检查是否是错误消息
    if (data.error) {
      handleChatError(data);
      return;
    }
    
    const { content, message_id } = data.data || {};
    
    if (content) {
      const botMessage = {
        id: message_id || Date.now(),
        content: content,
        type: 'bot',
        timestamp: new Date().toISOString(),
        isComplete: true,
      };

      // 将消息添加到消息列表
      setMessages(prev => [...prev, botMessage]);
      setCurrentBotMessage(null);
      setLoading(false);
    }
  };

  // 处理流式聊天消息
  const handleChatStream = (data) => {
    console.log('收到流式消息:', data);
    const { content, message_id, is_complete } = data.data;
    
    if (currentBotMessage && currentBotMessage.id === message_id) {
      // 更新当前正在接收的消息
      setCurrentBotMessage(prev => ({
        ...prev,
        content: content,
        isComplete: is_complete
      }));
      
      if (is_complete) {
        // 将完整消息添加到消息列表
        setMessages(prev => prev.map(msg => 
          msg.id === message_id 
            ? { ...msg, content: content, isComplete: true }
            : msg
        ));
        
        setCurrentBotMessage(null);
        setLoading(false);
      }
    }
  };

  // 处理聊天错误
  const handleChatError = (data) => {
    console.error('收到聊天错误:', data);
    
    let errorContent = '抱歉，处理您的消息时出现错误。';
    let messageId = Date.now();
    
    // 处理不同的错误格式
    if (data.data && data.data.message) {
      errorContent = data.data.message;
      messageId = data.data.message_id || messageId;
    } else if (data.error) {
      errorContent = data.error;
    } else if (typeof data === 'string') {
      errorContent = data;
    }
    
    const errorMessage = {
      id: messageId,
      content: errorContent,
      type: 'bot',
      timestamp: new Date().toISOString(),
      isError: true,
    };

    setMessages(prev => [...prev, errorMessage]);
    setCurrentBotMessage(null);
    setLoading(false);
  };

  const handleSendMessage = async () => {
    if (!inputValue.trim()) {
      message.warning('请输入消息内容');
      return;
    }

    const userMessage = {
      id: Date.now(),
      content: inputValue,
      type: 'user',
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setLoading(true);

    // 创建机器人消息占位符
    const botMessageId = Date.now() + 1;
    const botMessage = {
      id: botMessageId,
      content: '',
      type: 'bot',
      timestamp: new Date().toISOString(),
      isComplete: false,
    };

    setMessages(prev => [...prev, botMessage]);
    setCurrentBotMessage(botMessage);

    // 尝试使用 WebSocket 发送消息
    console.log('当前 WebSocket 状态:', wsStatus);
    if (wsStatus === 'connected') {
      console.log('WebSocket 已连接，尝试发送消息');
      const sent = websocketService.send('message', {
        content: inputValue,
        message_id: botMessageId
      });
      
      console.log('WebSocket 发送结果:', sent);
      if (!sent) {
        console.log('WebSocket 发送失败，回退到 HTTP');
        // WebSocket 发送失败，回退到 HTTP
        await sendMessageViaHTTP(inputValue, botMessageId);
      } else {
        console.log('WebSocket 消息发送成功，等待回复');
      }
    } else {
      console.log('WebSocket 未连接，使用 HTTP');
      // WebSocket 未连接，使用 HTTP
      await sendMessageViaHTTP(inputValue, botMessageId);
    }
  };

  // HTTP 方式发送消息（回退方案）
  const sendMessageViaHTTP = async (content, messageId) => {
    try {
      const response = await chatAPI.sendMessage(content);
      
      const botMessage = {
        id: messageId,
        content: response.content || response.message || '抱歉，我无法理解您的问题。',
        type: 'bot',
        timestamp: new Date().toISOString(),
        isComplete: true,
      };

      setMessages(prev => prev.map(msg => 
        msg.id === messageId ? botMessage : msg
      ));
      setCurrentBotMessage(null);
    } catch (error) {
      console.error('HTTP 发送消息失败:', error);
      
      const errorMessage = {
        id: messageId,
        content: '抱歉，发送消息时出现错误，请重试。',
        type: 'bot',
        timestamp: new Date().toISOString(),
        isError: true,
      };

      setMessages(prev => prev.map(msg => 
        msg.id === messageId ? errorMessage : msg
      ));
      setCurrentBotMessage(null);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const renderMessage = (msg) => {
    const isUser = msg.type === 'user';
    const icon = isUser ? <UserOutlined /> : <RobotOutlined />;
    const bgColor = msg.isError ? '#ff4d4f' : (isUser ? '#1890ff' : '#f0f0f0');
    const textColor = msg.isError ? 'white' : (isUser ? 'white' : '#333');

    return (
      <div
        key={msg.id}
        style={{
          display: 'flex',
          justifyContent: isUser ? 'flex-end' : 'flex-start',
          marginBottom: 16,
        }}
      >
        <div
          style={{
            maxWidth: '70%',
            padding: '12px 16px',
            borderRadius: 12,
            backgroundColor: bgColor,
            color: textColor,
            wordWrap: 'break-word',
            display: 'flex',
            alignItems: 'flex-start',
            gap: 8,
          }}
        >
          {!isUser && <span style={{ fontSize: 16 }}>{icon}</span>}
          <div style={{ flex: 1 }}>
            <div>{msg.content}</div>
            <div
              style={{
                fontSize: 12,
                opacity: 0.7,
                marginTop: 4,
              }}
            >
              {new Date(msg.timestamp).toLocaleTimeString()}
            </div>
          </div>
          {isUser && <span style={{ fontSize: 16 }}>{icon}</span>}
        </div>
      </div>
    );
  };

  // 渲染当前正在接收的消息
  const renderCurrentMessage = () => {
    if (!currentBotMessage) return null;

    return (
      <div
        style={{
          display: 'flex',
          justifyContent: 'flex-start',
          marginBottom: 16,
        }}
      >
        <div
          style={{
            maxWidth: '70%',
            padding: '12px 16px',
            borderRadius: 12,
            backgroundColor: '#f0f0f0',
            color: '#333',
            wordWrap: 'break-word',
            display: 'flex',
            alignItems: 'flex-start',
            gap: 8,
          }}
        >
          <span style={{ fontSize: 16 }}><RobotOutlined /></span>
          <div style={{ flex: 1 }}>
            <div>
              {currentBotMessage.content || '正在思考...'}
              {!currentBotMessage.isComplete && <Spin size="small" style={{ marginLeft: 8 }} />}
            </div>
            <div
              style={{
                fontSize: 12,
                opacity: 0.7,
                marginTop: 4,
              }}
            >
              {new Date(currentBotMessage.timestamp).toLocaleTimeString()}
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div style={{ height: 'calc(100vh - 200px)', display: 'flex', flexDirection: 'column' }}>
      <Card
        title={
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span>智能对话</span>
            <Badge 
              status={wsStatus === 'connected' ? 'success' : 'error'} 
              text={
                <span style={{ fontSize: 12 }}>
                  {wsStatus === 'connected' ? (
                    <>
                      <WifiOutlined /> WebSocket
                    </>
                  ) : (
                    <>
                      <WifiDisconnectedOutlined /> HTTP
                    </>
                  )}
                </span>
              }
            />
          </div>
        }
        style={{ flex: 1, display: 'flex', flexDirection: 'column' }}
        bodyStyle={{ flex: 1, display: 'flex', flexDirection: 'column', padding: 0 }}
      >
        <div
          style={{
            flex: 1,
            overflowY: 'auto',
            padding: 16,
            backgroundColor: '#fafafa',
          }}
        >
          {messages.length === 0 ? (
            <Empty
              description="开始您的对话吧"
              style={{ marginTop: 100 }}
            />
          ) : (
            <>
              {messages.map(renderMessage)}
              {renderCurrentMessage()}
            </>
          )}
          <div ref={messagesEndRef} />
        </div>
        
        <div style={{ padding: 16, borderTop: '1px solid #f0f0f0' }}>
          <div style={{ display: 'flex', gap: 8 }}>
            <TextArea
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="输入您的消息..."
              autoSize={{ minRows: 1, maxRows: 4 }}
              disabled={loading}
              style={{ flex: 1 }}
            />
            <Button
              type="primary"
              icon={<SendOutlined />}
              onClick={handleSendMessage}
              loading={loading}
              disabled={!inputValue.trim()}
              style={{ height: 'auto' }}
            >
              发送
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default ChatPage; 