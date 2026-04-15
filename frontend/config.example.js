/**
 * config.js — 前端配置文件
 * 
 * 把这个文件的内容填入真实值后，在 index.html 同目录下创建 config.js
 * （此文件已在 .gitignore 中，不会提交到版本库）
 */

window.YUANQI_CONFIG = {
  // 从元器平台 "调用API" 弹窗获取
  ASSISTANT_ID: 'YOUR_ASSISTANT_ID_HERE',

  // 后端代理地址（本地开发）
  PROXY_URL: 'http://localhost:3001/api/chat',

  // 设为 false 启用真实 API 调用
  DEMO_MODE: false,
};
