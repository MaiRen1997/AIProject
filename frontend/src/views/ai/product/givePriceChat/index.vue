<template>
  <div class="app-container give-price-chat">
    <div class="chat-panel">
      <div class="chat-header">
        <div class="title">产品报价助手</div>
        <div class="desc">输入产品名称和型号，自动匹配配件并输出 markdown 表格</div>
      </div>

      <div ref="messageListRef" class="message-list">
        <div v-if="messages.length === 0" class="empty-tip">
          示例：产品名称: 变频器, 型号: VF-2026
        </div>

        <div
          v-for="(item, idx) in messages"
          :key="idx"
          :class="['msg-row', item.role === 'user' ? 'is-user' : 'is-assistant']"
        >
          <div class="msg-bubble">
            <div class="msg-role">{{ item.role === 'user' ? '我' : '助手' }}</div>
            <pre class="msg-content">{{ item.display }}</pre>
          </div>
        </div>
      </div>

      <div class="action-row">
        <el-button
          type="success"
          :disabled="!canDownload || downloading"
          :loading="downloading"
          @click="handleDownload"
        >
          下载 Excel
        </el-button>
      </div>

      <div class="input-row">
        <el-input
          v-model="inputText"
          type="textarea"
          :rows="3"
          resize="none"
          placeholder="请输入产品名称和型号，例如：产品名称: 变频器, 型号: VF-2026"
          :disabled="loading"
          @keydown.enter.exact.prevent="handleSend"
        />
        <el-button
          type="primary"
          :loading="loading"
          :disabled="!inputText.trim()"
          @click="handleSend"
        >
          发送
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup name="GivePriceChat">
import { nextTick, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { queryGivePriceChat } from '@/api/ai/givePriceChat'

const { proxy } = getCurrentInstance()

const inputText = ref('')
const loading = ref(false)
const downloading = ref(false)
const canDownload = ref(false)
const latestMarkdownTable = ref('')
const messages = ref([])
const messageListRef = ref(null)

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

const scrollToBottom = async () => {
  await nextTick()
  const el = messageListRef.value
  if (!el) return
  el.scrollTop = el.scrollHeight
}

const appendMessage = async (role, text = '') => {
  messages.value.push({
    role,
    display: text,
  })
  await scrollToBottom()
  return messages.value.length - 1
}

const typewriterFill = async (index, fullText) => {
  const content = String(fullText || '')
  for (let i = 0; i < content.length; i++) {
    if (!messages.value[index]) break
    messages.value[index].display += content[i]
    if (i % 3 === 0) {
      await scrollToBottom()
    }
    await sleep(10)
  }
  await scrollToBottom()
}

const handleSend = async () => {
  const text = inputText.value.trim()
  if (!text || loading.value) {
    return
  }

  await appendMessage('user', text)
  inputText.value = ''
  loading.value = true
  canDownload.value = false
  latestMarkdownTable.value = ''

  const assistantIdx = await appendMessage('assistant', '')

  try {
    const res = await queryGivePriceChat({ userInput: text })
    const data = res?.data || {}
    const markdownTable = data.markdownTable || ''
    const productName = data.productName || '-'
    const productNo = data.productNo || '-'

    const responseText = [
      `已识别产品名称: ${productName}`,
      `已识别型号: ${productNo}`,
      '',
      '以下是产品所需配件明细（markdown表格）：',
      markdownTable,
    ].join('\n')

    await typewriterFill(assistantIdx, responseText)
    latestMarkdownTable.value = markdownTable
    canDownload.value = Boolean(markdownTable)
  } catch (error) {
    const msg = error?.message || '查询失败'
    await typewriterFill(assistantIdx, `查询失败：${msg}`)
    canDownload.value = false
    latestMarkdownTable.value = ''
  } finally {
    loading.value = false
  }
}

const handleDownload = async () => {
  if (!latestMarkdownTable.value || downloading.value) {
    return
  }
  downloading.value = true
  try {
    await proxy.download(
      'product_equipment/givePriceChat/markdown/export',
      { markdownContent: latestMarkdownTable.value },
      `give_price_${new Date().getTime()}.xlsx`
    )
    ElMessage.success('下载成功')
  } finally {
    downloading.value = false
  }
}
</script>

<style scoped lang="scss">
.give-price-chat {
  height: calc(100vh - 84px);
  display: flex;
  align-items: stretch;
  background: linear-gradient(135deg, #f3f9ff 0%, #e7f5ef 100%);
}

.chat-panel {
  width: min(980px, 100%);
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
}

.chat-header {
  padding: 16px;
  border-radius: 12px;
  background: #ffffffcc;
  border: 1px solid #dce9f5;

  .title {
    font-size: 20px;
    font-weight: 700;
    color: #174a7a;
  }

  .desc {
    margin-top: 6px;
    color: #4b6478;
    font-size: 13px;
  }
}

.message-list {
  flex: 1;
  min-height: 260px;
  max-height: calc(100vh - 340px);
  overflow-y: auto;
  border-radius: 12px;
  border: 1px solid #dbe6ef;
  background: #ffffffd9;
  padding: 16px;
}

.empty-tip {
  color: #6b7d8c;
  text-align: center;
  margin-top: 48px;
}

.msg-row {
  display: flex;
  margin-bottom: 12px;

  &.is-user {
    justify-content: flex-end;

    .msg-bubble {
      background: #e8f3ff;
      border-color: #bfdcff;
    }
  }

  &.is-assistant {
    justify-content: flex-start;

    .msg-bubble {
      background: #f2fbf4;
      border-color: #cdeed4;
    }
  }
}

.msg-bubble {
  max-width: 90%;
  border: 1px solid;
  border-radius: 10px;
  padding: 10px 12px;
}

.msg-role {
  font-size: 12px;
  color: #5d7387;
  margin-bottom: 6px;
}

.msg-content {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.5;
  font-family: Consolas, 'Courier New', monospace;
  color: #233746;
}

.action-row {
  display: flex;
  justify-content: flex-end;
}

.input-row {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 10px;
  align-items: end;
}

@media (max-width: 768px) {
  .chat-panel {
    padding: 12px;
  }

  .message-list {
    max-height: calc(100vh - 360px);
  }

  .input-row {
    grid-template-columns: 1fr;
  }
}
</style>
