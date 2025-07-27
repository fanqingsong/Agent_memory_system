import React, { useState, useEffect } from 'react';
import { Card, Table, Button, Input, Modal, Form, Select, InputNumber, Tag, Space, message, Popconfirm } from 'antd';
import { PlusOutlined, SearchOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { memoryAPI } from '../services/api';

const { Search } = Input;
const { TextArea } = Input;

const MemoryPage = () => {
  const [memories, setMemories] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchText, setSearchText] = useState('');
  const [modalVisible, setModalVisible] = useState(false);
  const [editingMemory, setEditingMemory] = useState(null);
  const [form] = Form.useForm();

  const fetchMemories = async () => {
    try {
      setLoading(true);
      const data = await memoryAPI.getMemories();
      setMemories(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('获取记忆失败:', error);
      message.error('获取记忆失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMemories();
  }, []);

  const handleSearch = async (value) => {
    if (!value.trim()) {
      fetchMemories();
      return;
    }

    try {
      setLoading(true);
      const data = await memoryAPI.searchMemories(value);
      setMemories(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('搜索记忆失败:', error);
      message.error('搜索记忆失败');
    } finally {
      setLoading(false);
    }
  };

  const handleAdd = () => {
    setEditingMemory(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleEdit = (record) => {
    setEditingMemory(record);
    form.setFieldsValue(record);
    setModalVisible(true);
  };

  const handleDelete = async (id) => {
    try {
      await memoryAPI.deleteMemory(id);
      message.success('删除成功');
      fetchMemories();
    } catch (error) {
      console.error('删除记忆失败:', error);
      message.error('删除记忆失败');
    }
  };

  const handleSubmit = async (values) => {
    try {
      if (editingMemory) {
        await memoryAPI.updateMemory(editingMemory.id, values);
        message.success('更新成功');
      } else {
        await memoryAPI.createMemory(values);
        message.success('创建成功');
      }
      setModalVisible(false);
      fetchMemories();
    } catch (error) {
      console.error('保存记忆失败:', error);
      message.error('保存记忆失败');
    }
  };

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 200,
      ellipsis: true,
    },
    {
      title: '内容',
      dataIndex: 'content',
      key: 'content',
      ellipsis: true,
      render: (text) => (
        <div style={{ maxWidth: 300 }}>
          {text?.substring(0, 100)}
          {text && text.length > 100 && '...'}
        </div>
      ),
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      width: 120,
      render: (type) => {
        const colorMap = {
          short_term: 'blue',
          long_term: 'green',
          episodic: 'orange',
          semantic: 'purple',
        };
        return <Tag color={colorMap[type] || 'default'}>{type}</Tag>;
      },
    },
    {
      title: '重要性',
      dataIndex: 'importance',
      key: 'importance',
      width: 100,
      render: (importance) => (
        <Tag color={importance >= 8 ? 'red' : importance >= 5 ? 'orange' : 'green'}>
          {importance}
        </Tag>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status) => (
        <Tag color={status === 'active' ? 'green' : 'red'}>
          {status === 'active' ? '活跃' : '非活跃'}
        </Tag>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (date) => new Date(date).toLocaleString(),
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      render: (_, record) => (
        <Space>
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
            size="small"
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除这个记忆吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button
              type="link"
              danger
              icon={<DeleteOutlined />}
              size="small"
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h2>记忆管理</h2>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
          添加记忆
        </Button>
      </div>

      <Card>
        <div style={{ marginBottom: 16 }}>
          <Search
            placeholder="搜索记忆内容..."
            allowClear
            enterButton={<SearchOutlined />}
            size="large"
            onSearch={handleSearch}
            onChange={(e) => setSearchText(e.target.value)}
            value={searchText}
          />
        </div>

        <Table
          columns={columns}
          dataSource={memories}
          rowKey="id"
          loading={loading}
          pagination={{
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
          }}
          scroll={{ x: 1200 }}
        />
      </Card>

      <Modal
        title={editingMemory ? '编辑记忆' : '添加记忆'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          <Form.Item
            name="content"
            label="记忆内容"
            rules={[{ required: true, message: '请输入记忆内容' }]}
          >
            <TextArea rows={4} placeholder="请输入记忆内容..." />
          </Form.Item>

          <Form.Item
            name="type"
            label="记忆类型"
            rules={[{ required: true, message: '请选择记忆类型' }]}
          >
            <Select placeholder="请选择记忆类型">
              <Select.Option value="short_term">短期记忆</Select.Option>
              <Select.Option value="long_term">长期记忆</Select.Option>
              <Select.Option value="episodic">情节记忆</Select.Option>
              <Select.Option value="semantic">语义记忆</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="importance"
            label="重要性"
            rules={[{ required: true, message: '请设置重要性' }]}
          >
            <InputNumber
              min={1}
              max={10}
              placeholder="1-10"
              style={{ width: '100%' }}
            />
          </Form.Item>

          <Form.Item
            name="status"
            label="状态"
            rules={[{ required: true, message: '请选择状态' }]}
          >
            <Select placeholder="请选择状态">
              <Select.Option value="active">活跃</Select.Option>
              <Select.Option value="inactive">非活跃</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                {editingMemory ? '更新' : '创建'}
              </Button>
              <Button onClick={() => setModalVisible(false)}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default MemoryPage; 