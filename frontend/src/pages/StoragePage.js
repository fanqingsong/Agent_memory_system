import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Table, Tag, Spin, Button, message } from 'antd';
import { 
  DatabaseOutlined, 
  HddOutlined, 
  CloudOutlined, 
  ReloadOutlined 
} from '@ant-design/icons';
import { storageAPI } from '../services/api';

const StoragePage = () => {
  const [storageData, setStorageData] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchStorageData = async () => {
    try {
      setLoading(true);
      const data = await storageAPI.getAllStorageInfo();
      setStorageData(data);
    } catch (error) {
      console.error('获取存储数据失败:', error);
      message.error('获取存储数据失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStorageData();
  }, []);

  const vectorColumns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
    },
    {
      title: '维度',
      dataIndex: 'dimension',
      key: 'dimension',
    },
    {
      title: '样本值',
      dataIndex: 'sample_values',
      key: 'sample_values',
      render: (values) => {
        if (!values) return '-';
        if (Array.isArray(values)) {
          return `[${values.join(', ')}]`;
        }
        return String(values);
      },
    },
  ];

  const graphColumns = [
    {
      title: '标签',
      dataIndex: 'labels',
      key: 'labels',
      render: (labels) => labels?.map(label => <Tag key={label} color="blue">{label}</Tag>),
    },
    {
      title: '属性',
      dataIndex: 'properties',
      key: 'properties',
      render: (props) => (
        <div>
          {props && Object.entries(props).map(([key, value]) => (
            <div key={key} style={{ fontSize: '12px' }}>
              <strong>{key}:</strong> {String(value).substring(0, 50)}
              {String(value).length > 50 && '...'}
            </div>
          ))}
        </div>
      ),
    },
  ];

  const cacheColumns = [
    {
      title: '键名',
      dataIndex: 'key',
      key: 'key',
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      render: (type) => <Tag color="green">{type}</Tag>,
    },
    {
      title: '预览',
      dataIndex: 'value_preview',
      key: 'value_preview',
      render: (preview) => (
        <div style={{ maxWidth: 200, wordBreak: 'break-all' }}>
          {preview}
        </div>
      ),
    },
  ];

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 50 }}>
        <Spin size="large" />
        <div style={{ marginTop: 16 }}>加载存储数据中...</div>
      </div>
    );
  }

  if (!storageData) {
    return (
      <div style={{ textAlign: 'center', padding: 50 }}>
        <div>无法获取存储数据</div>
        <Button onClick={fetchStorageData} style={{ marginTop: 16 }}>
          重试
        </Button>
      </div>
    );
  }

  const { vector_storage, graph_storage, cache_storage } = storageData;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h2>存储监控</h2>
        <Button 
          icon={<ReloadOutlined />} 
          onClick={fetchStorageData}
          loading={loading}
        >
          刷新
        </Button>
      </div>

      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={8}>
          <Card>
            <Statistic
              title="向量存储"
              value={vector_storage?.total_vectors || 0}
              prefix={<DatabaseOutlined />}
              suffix="个向量"
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="图存储"
              value={graph_storage?.total_nodes || 0}
              prefix={<HddOutlined />}
              suffix="个节点"
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="缓存存储"
              value={cache_storage?.total_keys || 0}
              prefix={<CloudOutlined />}
              suffix="个键"
            />
          </Card>
        </Col>
      </Row>

      {/* 详细数据 */}
      <Row gutter={16}>
        {/* 向量存储详情 */}
        <Col span={8}>
          <Card title="向量存储详情" size="small">
            <div style={{ marginBottom: 16 }}>
              <div><strong>维度:</strong> {vector_storage?.dimension || '-'}</div>
              <div><strong>类型:</strong> {vector_storage?.index_type || '-'}</div>
              <div><strong>路径:</strong> {vector_storage?.index_path || '-'}</div>
            </div>
            {vector_storage?.recent_vectors && vector_storage.recent_vectors.length > 0 && (
              <Table
                dataSource={vector_storage.recent_vectors}
                columns={vectorColumns}
                size="small"
                pagination={false}
                scroll={{ y: 200 }}
              />
            )}
          </Card>
        </Col>

        {/* 图存储详情 */}
        <Col span={8}>
          <Card title="图存储详情" size="small">
            <div style={{ marginBottom: 16 }}>
              <div><strong>节点数:</strong> {graph_storage?.total_nodes || 0}</div>
              <div><strong>关系数:</strong> {graph_storage?.total_relationships || 0}</div>
              <div><strong>节点类型:</strong> {graph_storage?.node_types?.join(', ') || '-'}</div>
              <div><strong>关系类型:</strong> {graph_storage?.relationship_types?.join(', ') || '-'}</div>
            </div>
            {graph_storage?.recent_nodes && graph_storage.recent_nodes.length > 0 && (
              <Table
                dataSource={graph_storage.recent_nodes}
                columns={graphColumns}
                size="small"
                pagination={false}
                scroll={{ y: 200 }}
              />
            )}
          </Card>
        </Col>

        {/* 缓存存储详情 */}
        <Col span={8}>
          <Card title="缓存存储详情" size="small">
            <div style={{ marginBottom: 16 }}>
              <div><strong>Redis版本:</strong> {cache_storage?.redis_version || '-'}</div>
              <div><strong>内存使用:</strong> {cache_storage?.memory_usage || '-'}</div>
              <div><strong>类型:</strong> {cache_storage?.cache_type || '-'}</div>
            </div>
            {cache_storage?.recent_keys && cache_storage.recent_keys.length > 0 && (
              <Table
                dataSource={cache_storage.recent_keys}
                columns={cacheColumns}
                size="small"
                pagination={false}
                scroll={{ y: 200 }}
              />
            )}
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default StoragePage; 