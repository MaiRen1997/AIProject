<template>
  <div class="app-container chat-container">
    <el-container style="height: 100%">
      <!-- 侧边栏：会话历史 -->
      <el-aside width="260px" class="session-sidebar">
        <div class="sidebar-header">
          <el-button
            type="primary"
            class="new-chat-btn"
            icon="Plus"
            @click="generateThreadId"
            >新建对话</el-button
          >
        </div>
        <div class="session-list" v-loading="sessionLoading">
          <div
            v-for="(session,index) in sessionList"
            :key="index"
            :class="[
              'session-item',
              currentSessionId === session?.sessionId ? 'active' : '',
            ]"
            @click="loadSession(session.sessionId)"
          >
            <div class="session-icon">
              <el-icon><ChatDotRound /></el-icon>
            </div>
            <div class="session-info">
              <div class="session-title">
                {{ session.sessionTitle || "新对话" }}
              </div>
              <div class="session-time">
                {{ formatTime(session.createdAt) }}
              </div>
            </div>
            <el-button
              class="delete-btn"
              type="danger"
              link
              icon="Delete"
              @click.stop="handleDeleteSession(session.id)"
            ></el-button>
          </div>
          <div
            v-if="sessionList.length === 0 && !sessionLoading"
            class="empty-session"
          >
            暂无历史对话
          </div>
        </div>
      </el-aside>

      <!-- 主区域：对话框 -->
      <el-main class="chat-main">
        <div class="chat-header">
          <div class="header-left">
            <span class="header-title">AI 智能助手</span>
          </div>
          <div class="header-right">
            <el-button :type="isAIResponse === 1 ? 'primary' : 'success'" @click="isAIResponse = Number(!Boolean(isAIResponse))">
              {{isAIResponse === 1 ? "转人工" : "转AI"}}
            </el-button>
          </div>
        </div>

        <div class="chat-history" ref="chatHistoryRef" @scroll="handleScroll">
          <div
            class="chat-content"
            ref="chatContentRef"
            :class="{ 'is-empty': messageList.length === 0 }"
          >
            <div v-if="messageList.length === 0" class="welcome-screen">
              <div class="welcome-icon">
                <el-icon size="60"><Service /></el-icon>
              </div>
              <h2>你好！我是你的 AI 助手</h2>
              <p>请在下方输入问题开始对话...</p>
            </div>

            <div
              v-for="(msg, index) in messageList"
              :key="index"
              :class="[
                'message-row',
                msg.role === 'user' ? 'message-user' : 'message-ai',
              ]"
            >
              <div class="message-avatar">
                <el-avatar
                  :icon="msg.role === 'user' ? 'UserFilled' : 'Service'"
                  :size="40"
                  :class="msg.role === 'user' ? 'avatar-user' : 'avatar-ai'"
                ></el-avatar>
              </div>
              <div class="message-content-wrapper">
                <div class="message-sender">
                  {{ msg.role === "user" ? "我" : "AI 助手" }}
                  <span class="message-time" v-if="msg.createdAt">{{
                    formatTime(msg.createdAt)
                  }}</span>
                </div>
                <div class="message-bubble">
                  <div v-if="msg.role === 'user'">
                    <div
                      v-if="msg.images && msg.images.length > 0"
                      class="user-images"
                    >
                      <el-image
                        v-for="(img, idx) in msg.images"
                        :key="idx"
                        :src="getImageUrl(img)"
                        :preview-src-list="msg.images.map(getImageUrl)"
                        fit="cover"
                        class="user-image-item"
                      />
                    </div>
                    <div class="user-text">{{ msg.content }}</div>
                  </div>
                  <AiMessage
                    v-else
                    :content="msg.content"
                    :reasoning-content="msg.reasoningContent"
                    :loading="loading && index === messageList.length - 1"
                  />
                </div>
                <div class="message-footer">
                  <div class="footer-actions">
                    <el-tooltip content="复制" placement="top">
                      <el-button
                        link
                        type="info"
                        :icon="DocumentCopy"
                        size="small"
                        @click="copyText(msg.content)"
                      ></el-button>
                    </el-tooltip>
                    <div
                      v-if="
                        userConfig.metricsDefaultVisible == '0' &&
                        hasMetrics(msg)
                      "
                      class="message-metrics"
                    >
                      <span
                        v-if="
                          msg.metrics?.duration !== null &&
                          msg.metrics?.duration !== undefined
                        "
                        >耗时 {{ msg.metrics.duration.toFixed(3) }} s</span
                      >
                      <span
                        v-if="
                          msg.metrics?.inputTokens !== null &&
                          msg.metrics?.inputTokens !== undefined
                        "
                        >输入 {{ msg.metrics.inputTokens }} tokens</span
                      >
                      <span
                        v-if="
                          msg.metrics?.outputTokens !== null &&
                          msg.metrics?.outputTokens !== undefined
                        "
                        >输出 {{ msg.metrics.outputTokens }} tokens</span
                      >
                      <span
                        v-if="
                          msg.metrics?.totalTokens !== null &&
                          msg.metrics?.totalTokens !== undefined
                        "
                        >总 {{ msg.metrics.totalTokens }} tokens</span
                      >
                      <span
                        v-if="
                          msg.metrics?.reasoningTokens !== null &&
                          msg.metrics?.reasoningTokens !== undefined
                        "
                        >推理 {{ msg.metrics.reasoningTokens }} tokens</span
                      >
                    </div>
                  </div>
                  <div v-if="msg.role === 'assistant'" class="model-info">
                    <el-tag
                      size="small"
                      type="info"
                      effect="plain"
                      v-if="currentSessionAgentData?.model"
                    >
                      {{ currentSessionAgentData.model.provider }} /
                      {{ currentSessionAgentData.model.id }}
                    </el-tag>
                    <el-tag
                      size="small"
                      type="info"
                      effect="plain"
                      v-else-if="currentModelInfo"
                    >
                      {{ currentModelInfo.provider }} /
                      {{ currentModelInfo.modelCode }}
                    </el-tag>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="chat-input-area">
          <div class="input-wrapper">
            <el-input
              v-model="inputMessage"
              type="textarea"
              :rows="3"
              resize="none"
              placeholder="请输入您的问题... (Enter 发送，Shift + Enter 换行)"
              @keydown.enter.exact.prevent="getAIMessage"
              :disabled="loading"
            />
            <div class="input-actions">
              <div class="left-actions">
                
              </div>
              <el-button
                :type="loading ? 'danger' : 'primary'"
                :icon="loading ? 'VideoPause' : 'Promotion'"
                @click="getAIMessage"
                :disabled="
                  !loading && !inputMessage.trim() && !inputImages.length
                "
              >
                {{ loading ? "停止" : "发送" }}
              </el-button>
            </div>
          </div>
        </div>
      </el-main>
    </el-container>
  </div>
</template>

<script setup name="AiChat">
import { listModelAll } from "@/api/ai/model";
import {
  listChatSession,
  getChatSession,
  getUserChatConfig,
  saveUserChatConfig,
  cancelChatRun,
} from "@/api/ai/chat";
import { getToken } from "@/utils/auth";
import AiMessage from "./components/AiMessage.vue";
import { Picture, DocumentCopy } from "@element-plus/icons-vue";
import { v4 as uuidv4 } from "uuid";
import { useResizeObserver } from "@vueuse/core";
import { getUseMonaco } from 'markstream-vue'
import { generateSessionID } from '@/api/ai/addSession'
import { addChat_message, listChat_message } from '@/api/ai/chatMessage'
import { listSessions, addSessions, delSessions } from '@/api/ai/sessions'
import * as Api from '@/api/ai/chemical'
import { ElMessage } from "element-plus";
getUseMonaco()

const { proxy } = getCurrentInstance();

const modelOptions = ref([]);
const currentModelId = ref(undefined);
const messageList = ref([]);
const inputMessage = ref("");
const inputImages = ref([]);
const loading = ref(false);
const chatHistoryRef = ref(null);
const chatContentRef = ref(null);
const currentSessionId = ref(null);
const sessionList = ref([]);
const sessionLoading = ref(false);
const isAutoScroll = ref(true);
const currentSessionAgentData = ref(null);
const isProgrammaticScroll = ref(false);
const isAIResponse = ref(1) // 是否是AI响应，1是AI响应，0是人工响应
const wsClientRef = ref(null);
const isManualStop = ref(false);
let scrollTimeout = null;
const generateThreadId = async () => {
  const res = await generateSessionID()
  currentSessionId.value = res.data;
  sessionList.value.push({
    sessionId: res.data,
    sessionTitle: "新对话",
    createdAt: new Date().toISOString(),
  })
  return res.data
}
// 获取session
const getSession = async () => {
  const userId = JSON.parse(sessionStorage.getItem('userId'));
  const res = await listSessions({userId: userId});
  sessionList.value = res.rows || [];
}
// 添加session
const addSessionToSql = (sessionId) => {
  const userId = sessionStorage.getItem('userId');
  addSessions({userId: userId, sessionId: sessionId}).then(res => {
    if(res.code == 200) {
      // ElMessage.success('新建会话成功')
    }  
  })
}
// 根据sessionId获取信息
const getMessagesBySessionId = () => {
  if(!currentSessionId.value) {
    messageList.value = []
    return
  }
  listChat_message({
    sessionId: currentSessionId.value,
    pageNum: 1,
    pageSize: 100000000
  }).then(res => {
    if(res.code == 200) {
      const result = res.rows || []
      messageList.value = result.map(item => {
        let role = ''
        if(item.senderType === 1) {
          role = 'user'
        } else if(item.senderType === 2) {
          role = '我'
        } else if(item.senderType === 3) {
          role = 'assistant'
        } else {
          role = 'unknown'
        }
        return {
          role: role,
          content: item.content,
          createdAt: item.createdAt
        }
      })
    }  
  })
}
// 添加消息
const addMessage = (data) => {
  addChat_message(data).then(res => {

  })
}
const getAIMessage = async () => {
  if (loading.value) {
    stopGeneration();
    return;
  }

  const currentInput = inputMessage.value.trim();
  if (!currentInput && !inputImages.value.length) {
    return;
  }

  if (!currentSessionId.value) {
    await generateThreadId()
  }

  messageList.value.push({
    role: "user",
    content: currentInput,
  })
  // 添加session信息
  addSessionToSql(currentSessionId.value)
  // 添加用户消息
  addMessage({
    sessionId: currentSessionId.value,
    content: currentInput,
    senderType: "1"
  })
  loading.value = true;
  isManualStop.value = false;

  const aiMsgIndex = messageList.value.push({
    role: "assistant",
    content: "",
  }) - 1;
  inputMessage.value = "";
  scrollToBottom();
  isAutoScroll.value = true;

  try {
    const wsUrl = import.meta.env.VITE_APP_AGENT_CHAT_WS_URL;
    if (!wsUrl) {
      throw new Error("未配置 VITE_APP_AGENT_CHAT_WS_URL");
    }

    const ws = new WebSocket(wsUrl);
    wsClientRef.value = ws;

    let aiContent = "";

    await new Promise((resolve, reject) => {
      let closedByDone = false;

      ws.onopen = () => {
        ws.send(
          JSON.stringify({
            message: currentInput,
            sessionId: currentSessionId.value,
            messageType: isAIResponse.value,
          })
        );
      };

      ws.onmessage = (event) => {
        const data = parseStreamLine(event.data);
        if (!data) return;

        if (data.type === "content") {
          aiContent += data.content || "";
          if(aiMsgIndex == messageList.value.length) {
            messageList.value.push({
              role: "",
              content: "",
            })
          }
          messageList.value[aiMsgIndex].content = aiContent;
          scrollToBottom();
          return;
        }
        if (data.type === "error") {
          closedByDone = true;
          proxy.$modal.msgError(data.error || "WebSocket 返回错误");
          ws.close(1000, "error");
          return;
        }

        if (data.type === "done") {
          // 添加用户消息
          addMessage({
            sessionId: currentSessionId.value,
            content: aiContent,
            senderType: "2"
          })
          closedByDone = true;
          ws.close(1000, "done");
        }
      };

      ws.onerror = () => {
        reject(new Error("WebSocket 连接异常"));
      };

      ws.onclose = (evt) => {
        if (wsClientRef.value === ws) {
          wsClientRef.value = null;
        }

        if (isManualStop.value || closedByDone || evt.code === 1000) {
          resolve();
          return;
        }

        reject(new Error(evt.reason || `WebSocket 连接关闭(${evt.code})`));
      };
    });
  } catch (err) {
    if (!isManualStop.value) {
      proxy.$modal.msgError("请求失败: " + (err?.message || "未知错误"));
    }
  } finally {
    if (wsClientRef.value) {
      wsClientRef.value.close(1000, "cleanup");
      wsClientRef.value = null;
    }

    if (!isManualStop.value) {
      inputMessage.value = "";
    } else {
      isManualStop.value = false;
    }

    loading.value = false;
  }
}

function parseStreamLine(raw) {
  const text = typeof raw === "string" ? raw.trim() : "";
  if (!text) return null;

  const payloadText = text.startsWith("data:")
    ? text.slice(5).trim()
    : text;

  if (!payloadText) return null;
  if (payloadText === "[DONE]") return { type: "done" };
  if (payloadText.startsWith("[ERROR]")) {
    return { type: "error", error: payloadText.replace(/^\[ERROR\]:?\s*/, "") };
  }

  try {
    const parsed = JSON.parse(payloadText);
    if (parsed?.type) {
      return parsed;
    }
    return { type: "content", content: parsed?.content ?? payloadText };
  } catch (e) {
    return { type: "content", content: payloadText };
  }
}

// 停止生成
function stopGeneration() {
  isManualStop.value = true;
  const ws = wsClientRef.value;
  if (!ws) {
    loading.value = false;
    return;
  }

  if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
    ws.close(1000, "manual stop");
  }

  loading.value = false;
}

const chatConfig = reactive({
  temperature: undefined,
  isReasoning: true,
});

const userConfig = reactive({
  chatConfigId: undefined,
  userId: undefined,
  temperature: undefined,
  addHistoryToContext: "0",
  numHistoryRuns: 3,
  systemPrompt: "",
  metricsDefaultVisible: "1",
  visionEnabled: "0",
  imageMaxSizeMb: 5,
  createTime: undefined,
  updateTime: undefined,
});

const editingUserConfig = reactive({
  chatConfigId: undefined,
  userId: undefined,
  temperature: undefined,
  addHistoryToContext: "0",
  numHistoryRuns: 3,
  systemPrompt: "",
  metricsDefaultVisible: "1",
  visionEnabled: "0",
  imageMaxSizeMb: 5,
  createTime: undefined,
  updateTime: undefined,
});

const currentModelInfo = computed(() => {
  if (!currentModelId.value) return null;
  return modelOptions.value.find((m) => m.modelId === currentModelId.value);
});

function loadUserConfig() {
  getUserChatConfig().then((res) => {
    if (res.data) {
      Object.assign(userConfig, res.data);
      Object.assign(editingUserConfig, res.data);
    }
  });
}



function hasMetrics(msg) {
  const m = msg?.metrics;
  if (!m) return false;
  return (
    (m.inputTokens !== null && m.inputTokens !== undefined) ||
    (m.outputTokens !== null && m.outputTokens !== undefined) ||
    (m.totalTokens !== null && m.totalTokens !== undefined) ||
    (m.reasoningTokens !== null && m.reasoningTokens !== undefined) ||
    (m.duration !== null && m.duration !== undefined)
  );
}

function getImageUrl(url) {
  if (!url) return "";
  if (
    url.startsWith("http") ||
    url.startsWith("https") ||
    url.startsWith("blob:")
  ) {
    return url;
  }
  return import.meta.env.VITE_APP_BASE_API + url;
}

function formatTime(timeStr) {
  if (!timeStr) return "";
  try {
    const date = new Date(timeStr);
    return date.toLocaleString();
  } catch (e) {
    return timeStr;
  }
}


// 监听模型切换，更新默认配置
watch(currentModelId, (newVal) => {
  const model = modelOptions.value.find((m) => m.modelId === newVal);
  if (model) {
    chatConfig.temperature = model.temperature;
  }
});

// 加载会话历史
function loadSession(sessionId) {
  currentSessionId.value = sessionId;
  getMessagesBySessionId()
}

function handleDeleteSession(id) {
  proxy.$modal
    .confirm("是否确认删除该会话？")
    .then(function () {
    })
    .then(() => {
      delSessions(id).then(res => {
        if(res.code == 200) {
          ElMessage.success('删除会话成功')
          initSessionList()
        }  
      })
    })
    .catch(() => {});
}


function copyText(text) {
  if (!text) {
    proxy.$modal.msgWarning("内容为空，无法复制");
    return;
  }
  navigator.clipboard
    .writeText(text)
    .then(() => {
      proxy.$modal.msgSuccess("复制成功");
    })
    .catch(() => {
      proxy.$modal.msgError("复制失败");
    });
}
function handleScroll(e) {
  if (isProgrammaticScroll.value) return;

  const { scrollTop, scrollHeight, clientHeight } = e.target;
  const distanceToBottom = scrollHeight - scrollTop - clientHeight;

  // If user scrolls up (distance from bottom > 100px), disable auto-scroll
  if (distanceToBottom > 100) {
    isAutoScroll.value = false;
  } else if (distanceToBottom < 20) {
    // If user scrolls back to bottom, re-enable auto-scroll
    isAutoScroll.value = true;
  }
}

function scrollToBottom() {
  if (isAutoScroll.value && chatHistoryRef.value) {
    isProgrammaticScroll.value = true;

    // Force scroll to bottom immediately
    chatHistoryRef.value.scrollTop = chatHistoryRef.value.scrollHeight;

    // Double check in next frames to catch layout shifts (like Mermaid rendering)
    requestAnimationFrame(() => {
      if (chatHistoryRef.value && isAutoScroll.value) {
        chatHistoryRef.value.scrollTop = chatHistoryRef.value.scrollHeight;
      }
    });

    // Reset flag after a short delay, clearing any previous timer
    if (scrollTimeout) clearTimeout(scrollTimeout);

    scrollTimeout = setTimeout(() => {
      isProgrammaticScroll.value = false;
      scrollTimeout = null;
    }, 100);
  }
}

function handleMainAction() {
  if (loading.value) {
    stopGeneration();
  } else {
    handleSend();
  }
}

// 监听内容变化，自动滚动
useResizeObserver(chatContentRef, () => {
  if (isAutoScroll.value) {
    scrollToBottom();
  }
});
const initSessionList = async () => {
  await getSession()
  currentSessionId.value = sessionList.value.length > 0 ? sessionList.value[0].sessionId : null
  if(!currentSessionId.value) {
    messageList.value = []
  } else {
    // 有sessionId,则获取消息
    await getMessagesBySessionId()
  }
}
onMounted(async () => {
  await initSessionList()
});
</script>

<style scoped lang="scss">
.chat-container {
  --tech-blue-1: #0c45de;
  --tech-blue-2: #18b3ff;
  --tech-blue-3: #2f6dff;
  --tech-cyan: #46e4ff;
  --glass-bg: rgba(255, 255, 255, 0.72);
  --glass-border: rgba(58, 123, 255, 0.28);
  --panel-shadow: 0 14px 32px rgba(15, 76, 255, 0.12);
  --card-shadow: 0 8px 20px rgba(58, 123, 255, 0.1);
  --hover-lift: translateY(-2px);
  height: calc(100vh - 84px);
  padding: 0;
  background:
    radial-gradient(circle at 10% 8%, rgba(70, 228, 255, 0.3), transparent 34%),
    radial-gradient(circle at 90% 82%, rgba(47, 109, 255, 0.26), transparent 36%),
    linear-gradient(138deg, #e8f2ff 0%, #d9e9ff 42%, #eaf4ff 100%);
  overflow: hidden;
}

.session-sidebar {
  border-right: 1px solid var(--glass-border);
  background: linear-gradient(180deg, rgba(235, 245, 255, 0.96), rgba(223, 239, 255, 0.9));
  backdrop-filter: blur(10px);
  display: flex;
  flex-direction: column;
  box-shadow: inset -1px 0 0 rgba(255, 255, 255, 0.65), var(--panel-shadow);
  z-index: 10;
  margin-bottom: 0;
  overflow: hidden;
  transition: box-shadow 0.35s ease, background 0.35s ease;

  .sidebar-header {
    padding: 20px;
    border-bottom: 1px solid rgba(58, 123, 255, 0.16);

    .new-chat-btn {
      width: 100%;
      border: none;
      border-radius: 14px;
      height: 40px;
      font-size: 14px;
      background: linear-gradient(120deg, var(--tech-blue-1), var(--tech-blue-2));
      box-shadow: 0 10px 24px rgba(15, 76, 255, 0.28);
      transition: transform 0.25s ease, box-shadow 0.25s ease, filter 0.25s ease;

      &:hover {
        transform: translateY(-1px);
        filter: brightness(1.04);
        box-shadow: 0 14px 28px rgba(15, 76, 255, 0.34);
      }

      &:active {
        transform: translateY(0);
        box-shadow: 0 6px 16px rgba(15, 76, 255, 0.3);
      }
    }
  }

  .session-list {
    flex: 1;
    overflow-y: auto;
    padding: 10px;
    scroll-behavior: smooth;

    &::-webkit-scrollbar {
      width: 6px;
    }
    &::-webkit-scrollbar-thumb {
      background: linear-gradient(180deg, rgba(58, 123, 255, 0.5), rgba(0, 180, 255, 0.5));
      border-radius: 999px;
    }

    .session-item {
      display: flex;
      align-items: center;
      padding: 12px;
      margin-bottom: 8px;
      background-color: rgba(255, 255, 255, 0.6);
      border-radius: 14px;
      cursor: pointer;
      transition: transform 0.24s ease, box-shadow 0.28s ease, border-color 0.28s ease,
        background-color 0.28s ease;
      position: relative;
      border: 1px solid rgba(58, 123, 255, 0.12);

      &:hover {
        transform: var(--hover-lift);
        background-color: rgba(255, 255, 255, 0.92);
        border-color: rgba(58, 123, 255, 0.32);
        box-shadow: var(--card-shadow);
      }

      &.active {
        background: linear-gradient(135deg, rgba(58, 123, 255, 0.16), rgba(55, 231, 255, 0.14));
        border-color: rgba(58, 123, 255, 0.45);
        box-shadow: 0 10px 24px rgba(58, 123, 255, 0.16);

        .session-icon {
          color: var(--el-color-primary);
        }

        .session-title {
          color: var(--el-color-primary);
        }
      }

      html.dark & {
        &.active {
          background: linear-gradient(135deg, rgba(58, 123, 255, 0.28), rgba(55, 231, 255, 0.22));
          border-color: rgba(133, 171, 255, 0.7);

          .session-icon {
            color: var(--el-color-primary);
          }

          .session-title {
            color: var(--el-color-primary);
          }
        }
      }

      .session-icon {
        margin-right: 10px;
        color: var(--el-text-color-secondary);
        display: flex;
        align-items: center;
        transition: transform 0.24s ease, color 0.24s ease;
      }

      .session-info {
        flex: 1;
        overflow: hidden;

        .session-title {
          font-size: 14px;
          color: var(--el-text-color-primary);
          margin-bottom: 4px;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .session-time {
          font-size: 12px;
          color: var(--el-text-color-secondary);
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }
      }

      .delete-btn {
        opacity: 0;
        transform: translateX(4px);
        transition: opacity 0.22s ease, transform 0.22s ease;
        padding: 4px;
      }

      &:hover .delete-btn {
        opacity: 1;
        transform: translateX(0);
      }

      &:hover .session-icon {
        transform: scale(1.06);
      }
    }

    .empty-session {
      text-align: center;
      color: var(--el-text-color-secondary);
      font-size: 13px;
      margin-top: 40px;
    }
  }
}

.chat-main {
  padding: 0;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: linear-gradient(180deg, rgba(232, 244, 255, 0.88), rgba(220, 238, 255, 0.92));
  position: relative;
  overflow: hidden;

  &::before {
    content: "";
    position: absolute;
    inset: 0;
    pointer-events: none;
    background:
      radial-gradient(circle at 88% 8%, rgba(47, 109, 255, 0.22), transparent 34%),
      radial-gradient(circle at 15% 70%, rgba(70, 228, 255, 0.14), transparent 38%);
    z-index: 0;
  }

  .chat-header {
    height: 60px;
    background: linear-gradient(100deg, rgba(236, 246, 255, 0.94), rgba(221, 238, 255, 0.94));
    border-bottom: 1px solid rgba(58, 123, 255, 0.16);
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0 20px;
    box-shadow: 0 8px 20px rgba(58, 123, 255, 0.08);
    backdrop-filter: blur(8px);
    position: relative;
    z-index: 1;

    .header-title {
      font-size: 16px;
      font-weight: 600;
      letter-spacing: 0.3px;
      color: #1f3f8c;
      text-shadow: 0 1px 0 rgba(255, 255, 255, 0.7);
    }

    .header-right :deep(.el-button) {
      border: 1px solid rgba(58, 123, 255, 0.2);
      border-radius: 999px;
      transition: transform 0.22s ease, box-shadow 0.22s ease;

      &:hover {
        transform: translateY(-1px);
        box-shadow: 0 8px 18px rgba(58, 123, 255, 0.16);
      }
    }
  }

  .chat-history {
    flex: 1;
    overflow-y: auto;
    padding: 20px;
    position: relative;
    z-index: 1;
    scroll-behavior: smooth;

    &::-webkit-scrollbar {
      width: 7px;
    }

    &::-webkit-scrollbar-thumb {
      border-radius: 999px;
      background: linear-gradient(180deg, rgba(58, 123, 255, 0.5), rgba(0, 180, 255, 0.45));
    }

    .chat-content {
      min-height: 100%;
      padding-bottom: 20px;

      &.is-empty {
        display: flex;
        flex-direction: column;
        height: 100%;
      }
    }

    .welcome-screen {
      flex: 1;
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      color: var(--el-text-color-secondary);
      opacity: 0.8;
      animation: fade-up 0.45s ease both;

      .welcome-icon {
        background: linear-gradient(140deg, rgba(58, 123, 255, 0.16), rgba(55, 231, 255, 0.25));
        border-radius: 50%;
        padding: 20px;
        margin-bottom: 20px;
        color: var(--tech-blue-1);
        box-shadow: 0 10px 22px rgba(58, 123, 255, 0.18);
      }

      h2 {
        margin-bottom: 10px;
        font-weight: 500;
      }
    }

    .message-row {
      display: flex;
      max-width: 900px;
      margin-bottom: 24px;
      margin-left: auto;
      margin-right: auto;
      animation: fade-up 0.35s ease both;

      .message-avatar {
        flex-shrink: 0;
        margin-right: 12px;
        margin-top: 2px;
        transition: transform 0.24s ease;

        .avatar-user {
          background: linear-gradient(135deg, var(--tech-blue-1), var(--tech-blue-2));
          box-shadow: 0 8px 18px rgba(15, 76, 255, 0.28);
        }

        .avatar-ai {
          background: linear-gradient(135deg, #2f66ff, #4bc4ff);
          box-shadow: 0 8px 18px rgba(58, 123, 255, 0.24);
        }
      }

      .message-content-wrapper {
        flex: 1;
        display: flex;
        flex-direction: column;
        max-width: calc(100% - 52px);

        .message-sender {
          font-size: 12px;
          color: var(--el-text-color-secondary);
          margin-bottom: 4px;
          display: flex;
          align-items: center;
          gap: 10px;
        }

        .message-time {
          font-size: 11px;
          opacity: 0.8;
        }

        .message-bubble {
          padding: 12px 16px;
          border-radius: 16px;
          font-size: 15px;
          line-height: 1.6;
          max-width: 100%;
          min-width: 60px;
          transition: transform 0.24s ease, box-shadow 0.24s ease, border-color 0.24s ease,
            background-color 0.24s ease;
        }

        .message-footer {
          margin-top: 6px;
          display: flex;
          justify-content: space-between;
          align-items: center;
          width: 100%;

          .message-metrics {
            font-size: 12px;
            color: var(--el-text-color-secondary);
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
          }

          .footer-actions {
            display: flex;
            align-items: center;
            gap: 10px;

            :deep(.el-button) {
              border-radius: 999px;
              transition: transform 0.2s ease, color 0.2s ease;

              &:hover {
                transform: scale(1.08);
                color: var(--tech-blue-1);
              }
            }
          }

          .model-info {
            margin-left: auto;
          }
        }
      }

      &.message-user {
        flex-direction: row-reverse;
        padding-left: 52px;

        .message-avatar {
          margin-left: 12px;
          margin-right: 0;
        }

        .message-content-wrapper {
          align-items: flex-end;

          .message-sender {
            flex-direction: row-reverse;
          }

          .message-bubble {
            background: linear-gradient(130deg, #1d63ff 0%, #2098ff 55%, #00b8ff 100%);
            color: #fff;
            border-top-right-radius: 6px;
            box-shadow: 0 10px 24px rgba(29, 99, 255, 0.28);

            .user-text {
              white-space: pre-wrap;
              word-break: break-word;
            }

            .user-images {
              display: flex;
              flex-wrap: wrap;
              gap: 8px;
              margin-bottom: 8px;
              justify-content: flex-end;

              .user-image-item {
                width: 100px;
                height: 100px;
                border-radius: 10px;
                cursor: pointer;
                background-color: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.24);
                transition: transform 0.22s ease, filter 0.22s ease;

                &:hover {
                  transform: translateY(-1px);
                  filter: brightness(1.04);
                }
              }
            }
          }

          .message-footer {
            justify-content: flex-end;

            .footer-actions {
              flex-direction: row-reverse;
            }
          }
        }
      }

      &.message-ai {
        padding-right: 52px;

        .message-content-wrapper {
          align-items: stretch;

          .message-bubble {
            background: linear-gradient(145deg, rgba(255, 255, 255, 0.95), rgba(245, 250, 255, 0.92));
            border: 1px solid rgba(58, 123, 255, 0.2);
            border-top-left-radius: 6px;
            box-shadow: 0 8px 20px rgba(58, 123, 255, 0.08);

            &:hover {
              transform: translateY(-1px);
              box-shadow: 0 12px 24px rgba(58, 123, 255, 0.14);
            }
          }
        }
      }

      &:hover .message-avatar {
        transform: scale(1.03);
      }
    }
  }

  .chat-input-area {
    width: 100%;
    background: linear-gradient(180deg, rgba(234, 246, 255, 0.96), rgba(221, 239, 255, 0.96));
    padding: 20px;
    border-top: 1px solid rgba(58, 123, 255, 0.18);
    position: relative;
    z-index: 1;

    .input-wrapper {
      // max-width: 900px;
      margin: 0 auto;
      border: 1px solid rgba(58, 123, 255, 0.24);
      border-radius: 18px;
      padding: 10px;
      background: var(--glass-bg);
      backdrop-filter: blur(8px);
      box-shadow: 0 10px 24px rgba(58, 123, 255, 0.1);
      transition: border-color 0.3s ease, box-shadow 0.3s ease, transform 0.3s ease;

      &:focus-within {
        border-color: rgba(58, 123, 255, 0.55);
        box-shadow: 0 14px 30px rgba(58, 123, 255, 0.18);
        transform: translateY(-1px);
      }

      .selected-images {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 8px;

        .selected-image-item {
          width: 60px;
          height: 60px;
          border-radius: 10px;
          cursor: pointer;
          border: 1px solid rgba(58, 123, 255, 0.22);
          background-color: var(--el-fill-color-light);
          transition: transform 0.2s ease, box-shadow 0.2s ease;

          &:hover {
            transform: translateY(-1px);
            box-shadow: 0 8px 16px rgba(58, 123, 255, 0.14);
          }
        }
      }

      :deep(.el-textarea__inner) {
        border: none;
        box-shadow: none;
        padding: 0;
        resize: none;
        max-height: 200px;
        background-color: transparent;
        color: var(--el-text-color-primary);

        &:focus {
          box-shadow: none;
        }
      }

      .input-actions {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 10px;
        padding-top: 10px;
        border-top: 1px solid rgba(58, 123, 255, 0.15);

        .left-actions {
          display: flex;
          align-items: center;

          .toggle-chip {
            border-radius: 999px;
            margin-left: 0;
          }
        }

        :deep(.el-button--primary) {
          border: none;
          border-radius: 12px;
          background: linear-gradient(120deg, var(--tech-blue-1), var(--tech-blue-2));
          box-shadow: 0 10px 22px rgba(15, 76, 255, 0.28);
          transition: transform 0.22s ease, box-shadow 0.22s ease, filter 0.22s ease;

          &:hover {
            transform: translateY(-1px);
            filter: brightness(1.04);
            box-shadow: 0 14px 26px rgba(15, 76, 255, 0.32);
          }

          &:active {
            transform: translateY(0);
          }
        }

        :deep(.el-button--danger) {
          border-radius: 12px;
          transition: transform 0.22s ease;

          &:hover {
            transform: translateY(-1px);
          }
        }
      }
    }
  }
}

.chat-config-dialog {
  :deep(.el-dialog__body) {
    padding-top: 10px;
    padding-bottom: 10px;
  }

  :deep(.el-form-item) {
    margin-bottom: 16px;
  }

  :deep(.el-form-item__label) {
    font-size: 13px;
    color: var(--el-text-color-secondary);
  }
}

@keyframes fade-up {
  0% {
    opacity: 0;
    transform: translateY(8px);
  }
  100% {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 992px) {
  .chat-main {
    .chat-history {
      padding: 14px;

      .message-row {
        margin-bottom: 18px;

        &.message-user {
          padding-left: 12px;
        }

        &.message-ai {
          padding-right: 12px;
        }
      }
    }

    .chat-input-area {
      padding: 12px;
    }
  }
}
</style>
