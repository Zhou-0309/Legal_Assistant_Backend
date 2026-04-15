# 律智助手 · 法内狂徒

> 基于腾讯元器智能体 API 的法律 AI 前端项目

---

## 文件结构

```
法内狂徒-前端/
├── index.html          # 前端主页面（直接打开即可）
├── server.js           # 后端代理（隐藏 Token，必须运行）
├── config.example.js   # 前端配置模板
├── config.js           # 你自己的配置（复制 config.example.js 后填写）
└── README.md
```

---

## 第一步：从元器平台获取 API 信息

1. 打开 https://yuanqi.tencent.com
2. 进入 **「我的创建」**，找到你已发布的智能体
3. 点击右上角 **「更多」→「调用 API」**
4. 弹窗中会显示：
   - `API Endpoint`（接口地址）
   - `assistant_id`（智能体ID）
   - `Token`（鉴权令牌）

> ⚠️ Token 请勿泄露或直接写在前端代码中！

---

## 第二步：配置后端代理

打开 `server.js`，找到这两行并填入真实值：

```javascript
const YUANQI_TOKEN = 'YOUR_TOKEN_HERE';      // 替换为你的 Token
const DEFAULT_ASSISTANT_ID = 'YOUR_ASSISTANT_ID_HERE';  // 替换为你的智能体ID
```

然后安装依赖并启动：

```bash
npm install express cors
node server.js
```

看到 `🚀 律智助手代理服务已启动` 即成功。

---

## 第三步：配置前端

复制 `config.example.js` 为 `config.js`，填入你的信息：

```javascript
window.YUANQI_CONFIG = {
  ASSISTANT_ID: 'AB1234567890abc',   // 你的智能体ID
  PROXY_URL: 'http://localhost:3001/api/chat',
  DEMO_MODE: false,   // 改为 false 启用真实 API
};
```

---

## 第四步：打开前端

直接用浏览器打开 `index.html` 即可（或用 VS Code Live Server）。

---

## Demo 模式

如果 `config.js` 不存在，或 `DEMO_MODE: true`，会使用内置模拟数据演示功能，不调用真实 API。**比赛演示可以先用 Demo 模式跑通流程。**

---

## API 调用说明

前端发给 `server.js` 的请求格式：

```json
POST http://localhost:3001/api/chat
{
  "message": "劳动合同试用期最长多久？",
  "assistant_id": "可选，不填用默认",
  "stream": true
}
```

`server.js` 会转发给元器 API（附上 Token），然后把 SSE 流式响应传回前端。

---

## 元器 API 官方文档

- 文档地址：https://docs.qq.com/aio/p/scxmsn78nzsuj64
- 接口地址：`https://yuanqi.tencent.com/openapi/v1/agent/chat/completions`
- Headers：`Authorization: Bearer {token}` + `X-source: openapi`

---

## 评分要点对照

| 评分维度 | 本项目实现 |
|---------|-----------|
| AI工具运用深度 | 接入元器智能体API，流式SSE输出，多工作流模块 |
| Demo核心功能完整可运行 | 法条检索/案例检索/合同生成三大功能 |
| 界面简洁流畅 | 专业法律风格UI，左右分栏布局，流式打字输出 |
| Prompt设计专业 | 三套场景化Prompt，引导AI输出结构化法律内容 |
