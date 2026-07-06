<template>
  <div class="app-container text-to-image-page">
    <div class="page-shell">
      <div class="chat-header">
        <div>
          <div class="page-title">文字描述生成图片</div>
          <div class="page-subtitle">输入描述词，调用多模态模型生成图片，并在当前聊天界面展示与下载。</div>
        </div>
        <div class="header-actions">
          <el-button plain @click="clearChat">清空会话</el-button>
        </div>
      </div>

      <div ref="messagePanelRef" class="message-panel">
        <div v-if="messages.length === 0" class="welcome-card">
          <div class="welcome-title">开始一次文生图对话</div>
          <div class="welcome-text">例如：生成一张雨夜霓虹街道中的赛博朋克猫咪插画。</div>
        </div>

        <div
          v-for="message in messages"
          :key="message.id"
          :class="['message-row', message.role === 'user' ? 'user-row' : 'assistant-row']"
        >
          <div class="message-avatar">{{ message.role === "user" ? "我" : "AI" }}</div>
          <div class="message-card">
            <div class="message-meta">
              <span>{{ message.role === "user" ? "提示词" : "生成结果" }}</span>
              <span>{{ formatTime(message.createdAt) }}</span>
            </div>

            <div v-if="message.role === 'user'" class="message-text">
              {{ message.content }}
            </div>

            <div v-else>
              <div v-if="message.loading" class="loading-box">
                <el-skeleton animated>
                  <template #template>
                    <el-skeleton-item variant="text" style="width: 50%" />
                    <el-skeleton-item variant="image" style="width: 100%; height: 280px; margin-top: 12px" />
                  </template>
                </el-skeleton>
              </div>

              <template v-else>
                <div class="assistant-text">{{ message.content }}</div>
                <div v-if="message.revisedPrompt" class="revised-prompt">
                  模型修订提示词：{{ message.revisedPrompt }}
                </div>
                <el-image
                  v-if="message.imageSrc"
                  :src="message.imageSrc"
                  :preview-src-list="[message.imageSrc]"
                  fit="contain"
                  class="result-image"
                />
                <div class="assistant-footer">
                  <el-tag size="small" type="info" effect="plain">
                    {{ message.modelLabel }}
                  </el-tag>
                  <el-button type="primary" link @click="downloadImage(message)">
                    下载图片
                  </el-button>
                </div>
              </template>
            </div>
          </div>
        </div>
      </div>

      <div class="input-panel">
        <el-input
          v-model="prompt"
          type="textarea"
          :rows="4"
          resize="none"
          maxlength="4000"
          show-word-limit
          placeholder="请输入图片描述，例如：一只穿宇航服的柴犬站在月球表面，电影感光影，超清细节"
          @keydown.enter.exact.prevent="handleSend"
        />
        <div class="input-actions">
          <div class="input-tip">Enter 发送，Shift + Enter 换行</div>
          <el-button
            type="primary"
            :loading="sending"
            :disabled="!prompt.trim()"
            @click="handleSend"
          >
            发送
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { generateTextToImage } from "@/api/ai/generateImg";

const { proxy } = getCurrentInstance();

const prompt = ref("生成一张雨夜霓虹街道中的赛博朋克猫咪插画");
const sending = ref(false);
const messages = ref([]);
const messagePanelRef = ref(null);

function clearChat() {
  messages.value = [];
  prompt.value = "";
}

async function handleSend() {
  const content = prompt.value.trim();
  if (!content) {
    proxy.$modal.msgWarning("请输入图片描述");
    return;
  }

  const userMessage = {
    id: `${Date.now()}-user`,
    role: "user",
    content,
    createdAt: new Date(),
  };
  const assistantMessage = {
    id: `${Date.now()}-assistant`,
    role: "assistant",
    content: "正在根据提示词生成图片...",
    createdAt: new Date(),
    loading: true,
    imageSrc: "",
    revisedPrompt: "",
    downloadFilename: "generated-image.png",
    modelLabel: "",
  };

  messages.value.push(userMessage, assistantMessage);
  const currentPrompt = content;
  prompt.value = "";
  await scrollToBottom();

  sending.value = true;
  try {
    const res = await generateTextToImage({
      prompt: currentPrompt,
    });
    const result = res.data || {};
    Object.assign(assistantMessage, {
      loading: false,
      content: "图片已生成，可以预览或下载。",
      imageSrc: result.imageDataUrl || result.imageUrl || "",
      revisedPrompt: result.revisedPrompt || "",
      downloadFilename: result.downloadFilename || "generated-image.png",
      modelLabel: `${result.provider || ""}/${result.modelCode || ""}`,
    });
  } catch (error) {
    Object.assign(assistantMessage, {
      loading: false,
      content: error?.message || "图片生成失败，请检查模型配置或稍后重试。",
    });
  } finally {
    sending.value = false;
    await scrollToBottom();
  }
}

function downloadImage(message) {
  if (!message.imageSrc) {
    proxy.$modal.msgWarning("当前没有可下载的图片");
    return;
  }
  const link = document.createElement("a");
  link.href = message.imageSrc;
  link.download = message.downloadFilename || "generated-image.png";
  link.target = "_blank";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

function formatTime(value) {
  if (!value) {
    return "";
  }
  const date = value instanceof Date ? value : new Date(value);
  const pad = (num) => String(num).padStart(2, "0");
  return `${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`;
}

async function scrollToBottom() {
  await nextTick();
  if (!messagePanelRef.value) {
    return;
  }
  messagePanelRef.value.scrollTop = messagePanelRef.value.scrollHeight;
}
</script>

<style scoped>
.text-to-image-page {
  min-height: calc(100vh - 84px);
  padding-bottom: 24px;
  background:
    radial-gradient(circle at top left, rgba(19, 112, 255, 0.14), transparent 28%),
    radial-gradient(circle at top right, rgba(19, 183, 146, 0.16), transparent 24%),
    linear-gradient(180deg, #f5f9ff 0%, #edf4f2 100%);
}

.page-shell {
  width: min(1080px, 100%);
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 24px 28px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.86);
  box-shadow: 0 14px 44px rgba(22, 44, 77, 0.08);
  backdrop-filter: blur(14px);
}

.page-title {
  font-size: 28px;
  font-weight: 700;
  color: #0f2742;
}

.page-subtitle {
  margin-top: 6px;
  color: #5d7088;
  font-size: 14px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.message-panel {
  min-height: 520px;
  max-height: 62vh;
  overflow-y: auto;
  padding: 24px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.78);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.6), 0 20px 50px rgba(24, 53, 88, 0.08);
}

.welcome-card {
  padding: 36px;
  border-radius: 20px;
  background: linear-gradient(135deg, rgba(15, 39, 66, 0.94), rgba(27, 113, 122, 0.92));
  color: #fff;
}

.welcome-title {
  font-size: 22px;
  font-weight: 700;
}

.welcome-text {
  margin-top: 10px;
  color: rgba(255, 255, 255, 0.82);
}

.message-row {
  display: flex;
  gap: 14px;
  margin-top: 18px;
}

.user-row {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 44px;
  height: 44px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  color: #fff;
  background: linear-gradient(135deg, #1d4ed8, #0f766e);
  flex-shrink: 0;
}

.assistant-row .message-avatar {
  background: linear-gradient(135deg, #111827, #334155);
}

.message-card {
  width: min(760px, calc(100% - 58px));
  padding: 18px;
  border-radius: 20px;
  background: #ffffff;
  box-shadow: 0 12px 30px rgba(15, 39, 66, 0.08);
}

.message-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #6b7f96;
  font-size: 12px;
  margin-bottom: 10px;
}

.message-text,
.assistant-text,
.revised-prompt {
  line-height: 1.7;
  color: #10263f;
  white-space: pre-wrap;
  word-break: break-word;
}

.revised-prompt {
  margin-top: 12px;
  padding: 10px 12px;
  border-radius: 14px;
  background: #f3f7fb;
  color: #4f647d;
  font-size: 13px;
}

.loading-box {
  margin-top: 8px;
}

.result-image {
  width: 100%;
  margin-top: 14px;
  border-radius: 18px;
  background: #eef3f8;
}

.assistant-footer {
  margin-top: 14px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.input-panel {
  padding: 18px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 14px 40px rgba(17, 43, 72, 0.08);
}

.input-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 12px;
}

.input-tip {
  font-size: 12px;
  color: #718399;
}

@media (max-width: 768px) {
  .chat-header {
    flex-direction: column;
    align-items: stretch;
  }

  .header-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .message-card {
    width: calc(100% - 58px);
  }

  .assistant-footer,
  .input-actions {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>