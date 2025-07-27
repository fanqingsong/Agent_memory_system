import React, { useState, useEffect } from 'react';
import { Card, Form, Input, Select, InputNumber, Switch, Button, Divider, message, Row, Col } from 'antd';
import { SaveOutlined, ReloadOutlined } from '@ant-design/icons';

const SettingsPage = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // 加载默认设置
    form.setFieldsValue({
      openaiApiKey: '',
      openaiApiBaseUrl: 'https://api.siliconflow.cn/v1',
      openaiModel: 'THUDM/GLM-4-9B-0414',
      openaiEmbeddingModel: 'BAAI/bge-large-zh-v1.5',
      embeddingDimension: 1024,
      memoryImportanceThreshold: 5,
      memoryRetentionDays: 7,
      memoryMaxSize: 10000,
      batchSize: 32,
      numWorkers: 4,
      cacheSize: 1000,
      logLevel: 'INFO',
      enableEncryption: true,
      enableCors: true,
    });
  }, [form]);

  const handleSave = async (values) => {
    try {
      setLoading(true);
      // 这里可以调用API保存设置
      console.log('保存设置:', values);
      message.success('设置保存成功');
    } catch (error) {
      console.error('保存设置失败:', error);
      message.error('保存设置失败');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    form.resetFields();
    message.info('设置已重置');
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h2>系统设置</h2>
        <div>
          <Button icon={<ReloadOutlined />} onClick={handleReset} style={{ marginRight: 8 }}>
            重置
          </Button>
          <Button type="primary" icon={<SaveOutlined />} onClick={() => form.submit()} loading={loading}>
            保存设置
          </Button>
        </div>
      </div>

      <Form
        form={form}
        layout="vertical"
        onFinish={handleSave}
        style={{ maxWidth: 800 }}
      >
        {/* OpenAI配置 */}
        <Card title="OpenAI配置" style={{ marginBottom: 24 }}>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="openaiApiKey"
                label="API密钥"
                rules={[{ required: true, message: '请输入API密钥' }]}
              >
                <Input.Password placeholder="请输入API密钥" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="openaiApiBaseUrl"
                label="API基础URL"
                rules={[{ required: true, message: '请输入API基础URL' }]}
              >
                <Input placeholder="例如: https://api.siliconflow.cn/v1" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="openaiModel"
                label="OpenAI模型"
                rules={[{ required: true, message: '请输入模型名称' }]}
              >
                <Input placeholder="例如: THUDM/GLM-4-9B-0414" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="openaiEmbeddingModel"
                label="嵌入模型"
                rules={[{ required: true, message: '请输入嵌入模型名称' }]}
              >
                <Input placeholder="例如: BAAI/bge-large-zh-v1.5" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="embeddingDimension"
                label="嵌入维度"
                rules={[{ required: true, message: '请输入嵌入维度' }]}
              >
                <InputNumber
                  min={1}
                  max={4096}
                  placeholder="例如: 1024"
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
          </Row>
        </Card>

        {/* 记忆配置 */}
        <Card title="记忆配置" style={{ marginBottom: 24 }}>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                name="memoryImportanceThreshold"
                label="重要性阈值"
                rules={[{ required: true, message: '请设置重要性阈值' }]}
              >
                <InputNumber
                  min={1}
                  max={10}
                  placeholder="1-10"
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="memoryRetentionDays"
                label="保留天数"
                rules={[{ required: true, message: '请设置保留天数' }]}
              >
                <InputNumber
                  min={1}
                  max={365}
                  placeholder="例如: 7"
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="memoryMaxSize"
                label="最大记忆数量"
                rules={[{ required: true, message: '请设置最大记忆数量' }]}
              >
                <InputNumber
                  min={100}
                  max={100000}
                  placeholder="例如: 10000"
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
          </Row>
        </Card>

        {/* 性能配置 */}
        <Card title="性能配置" style={{ marginBottom: 24 }}>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                name="batchSize"
                label="批处理大小"
                rules={[{ required: true, message: '请设置批处理大小' }]}
              >
                <InputNumber
                  min={1}
                  max={1000}
                  placeholder="例如: 32"
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="numWorkers"
                label="工作线程数"
                rules={[{ required: true, message: '请设置工作线程数' }]}
              >
                <InputNumber
                  min={1}
                  max={16}
                  placeholder="例如: 4"
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="cacheSize"
                label="缓存大小"
                rules={[{ required: true, message: '请设置缓存大小' }]}
              >
                <InputNumber
                  min={100}
                  max={10000}
                  placeholder="例如: 1000"
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
          </Row>
        </Card>

        {/* 日志配置 */}
        <Card title="日志配置" style={{ marginBottom: 24 }}>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="logLevel"
                label="日志级别"
                rules={[{ required: true, message: '请选择日志级别' }]}
              >
                <Select>
                  <Select.Option value="DEBUG">DEBUG</Select.Option>
                  <Select.Option value="INFO">INFO</Select.Option>
                  <Select.Option value="WARNING">WARNING</Select.Option>
                  <Select.Option value="ERROR">ERROR</Select.Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
        </Card>

        {/* 安全配置 */}
        <Card title="安全配置" style={{ marginBottom: 24 }}>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="enableEncryption"
                label="启用加密"
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="enableCors"
                label="启用CORS"
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>
            </Col>
          </Row>
        </Card>
      </Form>
    </div>
  );
};

export default SettingsPage; 