<template>
  <div class="app-container resume-filter-page">
    <div class="page-shell">
      <div class="page-header">
        <div>
          <div class="page-title">简历匹配筛选</div>
          <div class="page-subtitle">上传简历后自动 OCR，左侧可人工修正，右侧配置招聘标准与权重后进行匹配评分。</div>
        </div>
      </div>

      <div class="upload-panel">
        <el-upload
          :auto-upload="false"
          :limit="1"
          :show-file-list="true"
          :on-change="handleFileChange"
          :on-remove="handleFileRemove"
          accept=".pdf,.doc,.docx,.png,.jpg,.jpeg,.bmp,.webp"
        >
          <template #trigger>
            <el-button type="primary" plain>选择简历文件</el-button>
          </template>
          <template #tip>
            <div class="upload-tip">支持 PDF / DOC / DOCX / 常见图片格式</div>
          </template>
        </el-upload>

        <el-button
          type="success"
          :loading="ocrLoading"
          :disabled="!selectedFile"
          @click="handleOcr"
        >
          {{ ocrLoading ? "OCR识别中" : "调用OCR识别" }}
        </el-button>
      </div>

      <div class="content-grid">
        <div class="editor-card">
          <div class="card-title">简历文本（OCR结果可编辑）</div>
          <el-input
            v-model="resumeText"
            type="textarea"
            :rows="22"
            maxlength="30000"
            show-word-limit
            placeholder="OCR识别后的简历内容会显示在这里，可手工修正后用于评分"
          />

          <div class="form-block">
            <div class="form-title">候选人信息（OCR自动回填）</div>
            <el-row :gutter="10">
              <el-col :span="8">
                <el-input v-model="candidateForm.name" placeholder="姓名" clearable />
              </el-col>
              <el-col :span="8">
                <el-input v-model="candidateForm.email" placeholder="邮箱" clearable />
              </el-col>
              <el-col :span="8">
                <el-input v-model="candidateForm.phone" placeholder="手机号" clearable />
              </el-col>
            </el-row>
          </div>
        </div>

        <div class="action-center">
          <el-button
            type="primary"
            class="score-btn"
            :loading="scoreLoading"
            :disabled="!canScore"
            @click="handleScore"
          >
            {{ scoreButtonLabel }}
          </el-button>
          <div class="score-tip">点击后调用大模型评分接口</div>

          <el-button
            type="warning"
            class="invite-btn"
            :loading="inviteLoading"
            @click="handleSendInvite"
          >
            发送面试邀约
          </el-button>
          <div class="score-tip">会先校验姓名、邮箱、岗位名称、HR联系方式</div>
        </div>

        <div class="editor-card">
          <div class="card-title-row">
            <div class="card-title">招聘筛选标准与加权赋分</div>
            <el-button type="primary" link @click="addCriteria">新增标准</el-button>
          </div>

          <div class="criteria-list">
            <div
              v-for="(item, index) in criteriaList"
              :key="index"
              class="criteria-item"
            >
              <el-input
                v-model="item.criterion"
                placeholder="例如：具备 3 年以上 Python 后端开发经验"
                maxlength="200"
              />
              <el-input-number
                v-model="item.weight"
                :min="0"
                :max="100"
                :step="1"
                controls-position="right"
                class="weight-input"
              />
              <el-button
                type="danger"
                link
                :disabled="criteriaList.length === 1"
                @click="removeCriteria(index)"
              >
                删除
              </el-button>
            </div>
          </div>

          <el-divider />
          <div class="form-title">岗位与HR信息</div>
          <el-row :gutter="10" class="job-form-row">
            <el-col :span="12">
              <el-input v-model="jobForm.jobName" placeholder="岗位名称" clearable />
            </el-col>
            <el-col :span="12">
              <el-input v-model="jobForm.hrContact" placeholder="HR联系方式" clearable />
            </el-col>
          </el-row>
          <el-date-picker
            v-model="jobForm.meetingTime"
            type="datetime"
            value-format="YYYY-MM-DD HH:mm"
            format="YYYY-MM-DD HH:mm"
            placeholder="会议时间（不填默认次日10:00）"
            class="meeting-time-picker"
          />

          <el-divider />
          <div class="criteria-note">说明：权重用于表达该标准的重要程度，系统会结合权重进行综合评分。</div>
        </div>
      </div>

      <div v-if="inviteMessage" class="score-detail-card">
        <div class="score-detail-header">
          <div class="card-title">面试邀约文案</div>
        </div>
        <el-input
          v-model="inviteMessage"
          type="textarea"
          :rows="4"
          readonly
        />
      </div>

      <div v-if="scoreBreakdown.length" class="score-detail-card">
        <div class="score-detail-header">
          <div class="card-title">评分明细</div>
          <el-tag type="success" effect="dark">总分：{{ finalScore }}</el-tag>
        </div>

        <div v-if="scoreSummary" class="score-summary">综合评价：{{ scoreSummary }}</div>

        <el-table :data="scoreBreakdown" border stripe>
          <el-table-column label="序号" type="index" width="64" align="center" />
          <el-table-column label="筛选标准" prop="criterion" min-width="300" show-overflow-tooltip />
          <el-table-column label="权重" prop="weight" width="100" align="center" />
          <el-table-column label="得分" prop="score" width="100" align="center" />
          <el-table-column label="打分说明" prop="reason" min-width="360" show-overflow-tooltip />
        </el-table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ElMessage } from "element-plus";
import { scoreResumeMatch, sendInterviewInvite, uploadResumeAndOcr } from "@/api/ai/filterResume";

const selectedFile = ref(null);
const ocrLoading = ref(false);
const scoreLoading = ref(false);
const inviteLoading = ref(false);
const resumeText = ref("");
const finalScore = ref(null);
const scoreSummary = ref("");
const scoreBreakdown = ref([]);
const inviteMessage = ref("");

const candidateForm = reactive({
  name: "",
  email: "",
  phone: "",
});

const jobForm = reactive({
  jobName: "",
  hrContact: "",
  meetingTime: "",
});

const criteriaList = ref([
  { criterion: "本科及以上学历，计算机相关专业优先", weight: 20 },
  { criterion: "至少 3 年 Python/FastAPI 项目经验", weight: 30 },
  { criterion: "熟悉 MySQL/Redis 和接口性能优化", weight: 25 },
  { criterion: "具备良好沟通协作能力", weight: 25 },
]);

const canScore = computed(() => {
  return !!resumeText.value.trim() && criteriaList.value.some((item) => item.criterion.trim());
});

const scoreButtonLabel = computed(() => {
  if (scoreLoading.value) {
    return "评分中";
  }
  if (finalScore.value === null || finalScore.value === undefined) {
    return "开始评分";
  }
  return `评分：${finalScore.value}`;
});

function handleFileChange(file) {
  selectedFile.value = file?.raw || null;
}

function handleFileRemove() {
  selectedFile.value = null;
}

function addCriteria() {
  criteriaList.value.push({ criterion: "", weight: 10 });
}

function removeCriteria(index) {
  if (criteriaList.value.length === 1) {
    return;
  }
  criteriaList.value.splice(index, 1);
}

async function handleOcr() {
  if (!selectedFile.value) {
    ElMessage.warning("请先选择简历文件");
    return;
  }

  const formData = new FormData();
  formData.append("file", selectedFile.value);

  ocrLoading.value = true;
  try {
    const res = await uploadResumeAndOcr(formData);
    const data = res.data || {};
    resumeText.value = data.ocrText || "";
    candidateForm.name = data.candidateName || "";
    candidateForm.email = data.candidateEmail || "";
    candidateForm.phone = data.candidatePhone || "";
    if (!resumeText.value.trim()) {
      ElMessage.warning("OCR识别完成，但未提取到有效文本");
      return;
    }
    ElMessage.success("OCR识别成功，已回填文本与候选人信息");
  } catch (error) {
    ElMessage.error(error?.message || "OCR识别失败");
  } finally {
    ocrLoading.value = false;
  }
}

async function handleScore() {
  if (!canScore.value) {
    ElMessage.warning("请完善简历文本和筛选标准");
    return;
  }

  const criteria = criteriaList.value
    .map((item) => ({
      criterion: item.criterion.trim(),
      weight: Number(item.weight || 0),
    }))
    .filter((item) => item.criterion);

  if (!criteria.length) {
    ElMessage.warning("请至少填写一条有效筛选标准");
    return;
  }

  scoreLoading.value = true;
  try {
    const res = await scoreResumeMatch({
      resumeText: resumeText.value,
      criteria,
    });
    const data = res.data || {};
    finalScore.value = data.score;
    scoreSummary.value = data.summary || "";
    scoreBreakdown.value = Array.isArray(data.breakdown) ? data.breakdown : [];
    ElMessage.success("评分完成");
  } catch (error) {
    ElMessage.error(error?.message || "评分失败");
  } finally {
    scoreLoading.value = false;
  }
}

function validateInviteForm() {
  if (!candidateForm.name.trim()) {
    ElMessage.warning("请完善候选人姓名");
    return false;
  }
  if (!candidateForm.email.trim()) {
    ElMessage.warning("请完善候选人邮箱");
    return false;
  }
  if (!jobForm.jobName.trim()) {
    ElMessage.warning("请完善岗位名称");
    return false;
  }
  if (!jobForm.hrContact.trim()) {
    ElMessage.warning("请完善HR联系方式");
    return false;
  }
  return true;
}

async function handleSendInvite() {
  if (!validateInviteForm()) {
    return;
  }

  inviteLoading.value = true;
  try {
    const res = await sendInterviewInvite({
      candidateName: candidateForm.name,
      candidateEmail: candidateForm.email,
      candidatePhone: candidateForm.phone,
      jobName: jobForm.jobName,
      hrContact: jobForm.hrContact,
      meetingTime: jobForm.meetingTime || undefined,
    });
    const data = res.data || {};
    inviteMessage.value = data.inviteMessage || "";
    if (!jobForm.meetingTime && data.meetingTime) {
      jobForm.meetingTime = data.meetingTime;
    }
    ElMessage.success("面试邀约已生成");
  } catch (error) {
    ElMessage.error(error?.message || "发送面试邀约失败");
  } finally {
    inviteLoading.value = false;
  }
}
</script>

<style scoped>
.resume-filter-page {
  min-height: calc(100vh - 84px);
  padding-bottom: 24px;
  background:
    radial-gradient(circle at left top, rgba(23, 117, 255, 0.16), transparent 28%),
    radial-gradient(circle at right top, rgba(35, 163, 125, 0.2), transparent 24%),
    linear-gradient(180deg, #f3f8ff 0%, #eef6f1 100%);
}

.page-shell {
  width: min(1320px, 100%);
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.page-header {
  border-radius: 18px;
  padding: 22px 24px;
  background: rgba(255, 255, 255, 0.86);
  box-shadow: 0 12px 36px rgba(16, 38, 66, 0.08);
}

.page-title {
  font-size: 26px;
  font-weight: 700;
  color: #0f2b49;
}

.page-subtitle {
  margin-top: 8px;
  color: #5f738b;
  font-size: 14px;
}

.upload-panel {
  border-radius: 16px;
  padding: 16px 20px;
  background: rgba(255, 255, 255, 0.88);
  box-shadow: 0 10px 30px rgba(27, 56, 91, 0.07);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  flex-wrap: wrap;
}

.upload-tip {
  color: #6d7f95;
  font-size: 12px;
}

.content-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 150px minmax(0, 1fr);
  gap: 14px;
  align-items: stretch;
}

.editor-card {
  border-radius: 18px;
  padding: 18px;
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 12px 30px rgba(19, 45, 76, 0.08);
  min-height: 640px;
}

.card-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.card-title {
  font-size: 16px;
  font-weight: 700;
  color: #14365a;
  margin-bottom: 12px;
}

.form-block {
  margin-top: 14px;
}

.form-title {
  margin-bottom: 10px;
  color: #1f3f63;
  font-size: 14px;
  font-weight: 600;
}

.action-center {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.score-btn {
  min-width: 130px;
  height: 46px;
  font-size: 15px;
  font-weight: 600;
}

.invite-btn {
  min-width: 130px;
  height: 44px;
  font-size: 14px;
  font-weight: 600;
}

.score-tip {
  color: #5b6c80;
  font-size: 12px;
  text-align: center;
}

.criteria-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: 520px;
  overflow: auto;
  padding-right: 4px;
}

.criteria-item {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 120px 48px;
  gap: 8px;
  align-items: center;
}

.weight-input {
  width: 120px;
}

.job-form-row {
  margin-bottom: 10px;
}

.meeting-time-picker {
  width: 100%;
}

.criteria-note {
  color: #607487;
  font-size: 13px;
  line-height: 1.6;
}

.score-detail-card {
  border-radius: 18px;
  padding: 18px;
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 12px 30px rgba(19, 45, 76, 0.08);
}

.score-detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 12px;
}

.score-summary {
  margin-bottom: 12px;
  color: #4f657d;
  line-height: 1.7;
}

@media (max-width: 1024px) {
  .content-grid {
    grid-template-columns: 1fr;
  }

  .action-center {
    order: 3;
    padding: 6px 0 10px;
  }

  .editor-card {
    min-height: 420px;
  }
}
</style>
