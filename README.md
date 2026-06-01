### 传输层加解密配置说明

后端密钥配置与轮换说明：[agent-fastapi-backend/docs/transport_crypto_config.md](./agent-fastapi-backend/docs/transport_crypto_config.md)

### 开发

```bash
# 克隆项目
git clone https://gitee.com/insistence2022/RuoYi-Vue3-FastAPI.git

# 进入项目根目录
cd Agent-Vue3-FastAPI
```

#### 前端


```bash
# 进入前端目录
cd agent-fastapi-frontend

# 安装依赖
npm install 或 yarn --registry=https://registry.npmmirror.com

# 建议不要直接使用 cnpm 安装依赖，会有各种诡异的 bug。可以通过如下操作解决 npm 下载速度慢的问题
npm install --registry=https://registry.npmmirror.com

# 启动服务
npm run dev 或 yarn dev
```

#### 移动端

```bash
# 进入移动端目录
cd agent-fastapi-app

# 安装依赖
npm install -g pnpm
pnpm install

# 启动 H5
pnpm dev:h5

# 启动微信小程序
pnpm dev:mp-weixin
```

移动端详细文档请参考：[agent-fastapi-app/README.md](./agent-fastapi-app/README.md)

#### 后端

```bash
# 进入后端目录
cd agent-fastapi-backend

# 如果使用的是MySQL数据库，请执行以下命令安装项目依赖环境
pip3 install -r requirements.txt
# 如果使用的是PostgreSQL数据库，请执行以下命令安装项目依赖环境
pip3 install -r requirements-pg.txt

# 配置环境
在.env.dev文件中配置开发环境的数据库和redis

# 运行sql文件
1.新建数据库ruoyi-fastapi(默认，可修改)
2.如果使用的是MySQL数据库，使用命令或数据库连接工具运行sql文件夹下的agent-fastapi.sql；如果使用的是PostgreSQL数据库，使用命令或数据库连接工具运行sql文件夹下的agent-fastapi-pg.sql

# 运行后端
agent app run --env=dev
```

后端 CLI 使用说明请参考：[agent-fastapi-backend/docs/cli_usage.md](./agent-fastapi-backend/docs/cli_usage.md)

#### 访问

```bash
# 默认账号密码
账号：admin
密码：admin123

# 浏览器访问
地址：http://localhost:80
```

### 发布

#### 前端

```bash
# 构建测试环境
npm run build:stage 或 yarn build:stage

# 构建生产环境
npm run build:prod 或 yarn build:prod
```

#### 后端

```bash
# 配置环境
在.env.prod文件中配置生产环境的数据库和redis

# 运行后端
ruoyi app run --env=prod
```

### Docker Compose部署方式

> ⚠️ **警告：** 默认未做数据持久化配置，请注意数据备份或自行配置持久化

#### MySQL版本

```bash
docker compose -f docker-compose.my.yml up -d --build
```

#### PostgreSQL版本

```bash
docker compose -f docker-compose.pg.yml up -d --build
```