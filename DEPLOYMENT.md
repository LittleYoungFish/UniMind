# UniMind AI Assistant - Docker 部署指南

> 基于多智能体架构的通用型AI助手 Docker 部署文档

## 🚀 快速开始

### 前置要求

- Docker 20.10+
- Docker Compose 2.0+
- 8GB+ 可用内存
- OpenAI API Key

### 1. 克隆项目

```bash
git clone <your-repo-url>
cd UniMind
```

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp env.docker.template .env

# 编辑环境变量文件
nano .env
```

**必须配置的变量：**
```bash
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. 构建并启动

```bash
# 构建并启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f unimind
```

### 4. 访问应用

打开浏览器访问：`http://localhost:8501`

## 📋 详细配置

### 环境变量说明

| 变量名                  | 描述              | 默认值  | 必需 |
| ----------------------- | ----------------- | ------- | ---- |
| `OPENAI_API_KEY`        | OpenAI API密钥    | -       | ✅    |
| `OPENAI_BASE_URL`       | OpenAI API基础URL | 官方API | ❌    |
| `STREAMLIT_SERVER_PORT` | Web服务端口       | 8501    | ❌    |
| `DEBUG`                 | 调试模式          | false   | ❌    |
| `LOG_LEVEL`             | 日志级别          | INFO    | ❌    |

### 数据持久化

应用数据将保存在以下目录：
- `./data` - 应用数据和配置
- `./logs` - 日志文件
- `./screenshots` - 截图文件

## 🔧 高级配置

### 1. 自定义端口

```bash
# 修改 docker-compose.yml
ports:
  - "9000:8501"  # 使用9000端口
```

### 2. 启用设备连接 (Android ADB)

```bash
# 确保USB设备权限
sudo usermod -a -G plugdev $USER

# 重启Docker服务
sudo systemctl restart docker
```

### 3. 使用中国镜像源

```bash
# 在 docker-compose.yml 中设置
args:
  pip_mirror: "true"
```

### 4. 资源限制调整

```yaml
# docker-compose.yml
deploy:
  resources:
    limits:
      cpus: '4.0'      # 调整CPU限制
      memory: 8G       # 调整内存限制
```

## 🐛 故障排除

### 常见问题

**1. 容器无法启动**
```bash
# 检查日志
docker-compose logs unimind

# 检查资源使用
docker stats
```

**2. 端口占用**
```bash
# 检查端口使用
netstat -tulpn | grep 8501

# 杀死占用进程
sudo kill -9 <PID>
```

**3. ADB设备连接失败**
```bash
# 检查设备权限
ls -la /dev/bus/usb

# 重启ADB服务
docker-compose exec unimind /app/platform-tools/adb kill-server
docker-compose exec unimind /app/platform-tools/adb start-server
```

**4. OpenAI API 连接失败**
```bash
# 检查API Key配置
docker-compose exec unimind env | grep OPENAI

# 测试API连接
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     https://api.openai.com/v1/models
```

### 日志调试

```bash
# 实时查看日志
docker-compose logs -f unimind

# 查看应用日志
docker-compose exec unimind tail -f /app/logs/universal_ai_assistant.log

# 查看智能代接日志
docker-compose exec unimind tail -f /app/logs/phone_auto_answer.log
```

## 📊 监控和维护

### 健康检查

```bash
# 检查容器健康状态
docker-compose ps

# 手动健康检查
curl -f http://localhost:8501/_stcore/health
```

### 数据备份

```bash
# 备份应用数据
tar -czf unimind_backup_$(date +%Y%m%d).tar.gz ./data ./logs

# 恢复数据
tar -xzf unimind_backup_YYYYMMDD.tar.gz
```

### 更新应用

```bash
# 拉取最新代码
git pull

# 重新构建并启动
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## 🔒 安全建议

### 生产环境部署

1. **使用强密码**
   ```bash
   SESSION_SECRET_KEY=$(openssl rand -hex 32)
   ```

2. **启用HTTPS**
   ```yaml
   # 使用nginx反向代理
   services:
     nginx:
       image: nginx:alpine
       ports:
         - "443:443"
         - "80:80"
   ```

3. **限制网络访问**
   ```yaml
   # 仅允许内网访问
   environment:
     - STREAMLIT_SERVER_ADDRESS=127.0.0.1
   ```

4. **定期更新**
   ```bash
   # 定期更新基础镜像
   docker-compose pull
   docker-compose up -d
   ```

## 🌐 生产环境部署

### 使用外部数据库

```yaml
# docker-compose.prod.yml
services:
  unimind:
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/unimind
    depends_on:
      - db
      
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: unimind
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
```

### 负载均衡

```yaml
# docker-compose.scale.yml
services:
  unimind:
    deploy:
      replicas: 3
      
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    depends_on:
      - unimind
```

## 📞 支持

如果遇到问题，请：

1. 查看本文档的故障排除部分
2. 检查 [Issues](https://github.com/your-repo/issues)
3. 提交新的 Issue 并附上：
   - 错误日志
   - 系统信息
   - 复现步骤

---

**UniMind AI Assistant** - 中国联通挑战杯比赛作品
基于多智能体架构的通用型AI助手
