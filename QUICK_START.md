# UniMind AI Assistant - 快速开始

> 基于多智能体架构的通用型AI助手 - 快速部署指南

## 🚀 一键部署

### Windows 用户

```cmd
# 1. 配置环境变量
copy env.docker.template .env
notepad .env

# 2. 一键部署
deploy.bat
```

### Linux/macOS 用户

```bash
# 1. 配置环境变量
cp env.docker.template .env
nano .env

# 2. 一键部署
./deploy.sh
```

## ⚙️ 必需配置

编辑 `.env` 文件，至少配置以下内容：

```bash
OPENAI_API_KEY=your_openai_api_key_here
```

## 🌐 访问应用

部署成功后，打开浏览器访问：

**http://localhost:8501**

## 📋 功能特性

- **智能对话助手** - 基于 OpenAI GPT 的智能对话
- **智能代接** - 自动接听电话并智能回复
- **联通服务** - 查询话费、流量等服务
- **多智能体架构** - 分布式任务处理

## 🔧 常用命令

```bash
# Windows
deploy.bat status    # 查看状态
deploy.bat logs      # 查看日志
deploy.bat stop      # 停止服务
deploy.bat restart   # 重启服务

# Linux/macOS
./deploy.sh status   # 查看状态
./deploy.sh logs     # 查看日志
./deploy.sh stop     # 停止服务
./deploy.sh restart  # 重启服务
```

## 🛠️ 手动部署

如果自动部署脚本无法使用，可以手动执行：

```bash
# 1. 创建环境变量文件
cp env.docker.template .env

# 2. 编辑 OpenAI API Key
# 编辑 .env 文件，设置 OPENAI_API_KEY

# 3. 构建并启动
docker-compose up -d

# 4. 查看状态
docker-compose ps
```

## 📱 Android 设备连接

如需使用智能代接功能，请：

1. **启用开发者选项** - 在手机设置中启用
2. **开启USB调试** - 在开发者选项中开启
3. **连接设备** - 使用USB连接电脑
4. **授权调试** - 手机弹窗时点击"允许"

## 🔧 故障排除

### 常见问题

**端口已被占用**
```bash
# Windows
netstat -ano | findstr 8501
taskkill /F /PID <PID>

# Linux/macOS
lsof -ti:8501 | xargs kill -9
```

**Docker 无法启动**
```bash
# 检查 Docker 是否运行
docker --version
docker-compose --version

# 查看详细错误
docker-compose logs unimind
```

**API Key 错误**
```bash
# 检查环境变量
docker-compose exec unimind env | grep OPENAI
```

## 📞 技术支持

如遇问题，请查看 `DEPLOYMENT.md` 详细文档或提交 Issue。

---

**UniMind AI Assistant** - 中国联通挑战杯比赛作品  
基于多智能体架构的通用型AI助手
