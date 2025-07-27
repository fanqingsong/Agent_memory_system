# 多阶段构建 - 开发阶段
FROM swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/node:18-alpine AS development

WORKDIR /app

# 复制package文件
COPY package*.json ./

# 配置npm国内镜像并安装依赖
RUN npm config set registry https://registry.npmmirror.com/ \
    && npm install

# 复制源代码
COPY . .

# 暴露端口
EXPOSE 3000

# 开发模式启动命令 - 支持热重载
CMD ["npm", "start"]

# 多阶段构建 - 生产阶段
FROM swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/node:18-alpine AS build

WORKDIR /app

# 配置npm国内镜像并安装依赖
RUN npm config set registry https://registry.npmmirror.com/ \
    && npm install

# 复制源代码
COPY . .

# 构建应用
RUN npm run build

# 生产阶段 - 使用Nginx
FROM swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/nginx:alpine AS production

# 复制构建产物
COPY --from=build /app/build /usr/share/nginx/html

# 复制Nginx配置
COPY nginx.conf /etc/nginx/nginx.conf

# 暴露端口
EXPOSE 80

# 启动Nginx
CMD ["nginx", "-g", "daemon off;"] 