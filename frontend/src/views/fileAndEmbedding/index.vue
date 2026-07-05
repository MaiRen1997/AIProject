<template>
  <div class="app-container file-embedding-page">
    <el-card class="upload-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span>文件上传</span>
        </div>
      </template>

      <el-upload
        drag
        :auto-upload="false"
        :limit="1"
        :on-change="handleFileChange"
        :on-exceed="handleExceed"
        :show-file-list="true"
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">将文件拖到此处，或<em>点击上传</em></div>
        <template #tip>
          <div class="el-upload__tip">单次仅支持上传 1 个文件</div>
        </template>
      </el-upload>

      <div class="action-row">
        <el-button type="primary" :loading="uploading" :disabled="!selectedFile" @click="submitUpload">
          上传到 FilesTemp
        </el-button>
      </div>

      <el-descriptions v-if="uploadResult" :column="1" border class="result-box" title="上传结果">
        <el-descriptions-item label="原文件名">{{ uploadResult.originalFilename }}</el-descriptions-item>
        <el-descriptions-item label="新文件名">{{ uploadResult.newFileName }}</el-descriptions-item>
        <el-descriptions-item label="存储路径">{{ uploadResult.storagePath }}</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-card class="embedding-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span>文件向量化</span>
        </div>
      </template>

      <el-form label-width="100px">
        <el-form-item label="选择文件">
          <el-select
            v-model="selectedEmbeddingFile"
            filterable
            clearable
            placeholder="请选择需要向量化的文件"
            style="width: 100%"
          >
            <el-option
              v-for="item in embeddingFileOptions"
              :key="item.fileName"
              :label="item.fileName"
              :value="item.fileName"
            />
          </el-select>
        </el-form-item>
      </el-form>

      <div class="action-row">
        <el-button
          type="success"
          :loading="vectorizing"
          :disabled="!selectedEmbeddingFile"
          @click="submitVectorize"
        >
          执行向量化
        </el-button>
        <el-button plain @click="loadEmbeddingFiles">刷新文件列表</el-button>
      </div>

      <el-descriptions v-if="vectorizeResult" :column="1" border class="result-box" title="向量化结果">
        <el-descriptions-item label="文件名">{{ vectorizeResult.fileName }}</el-descriptions-item>
        <el-descriptions-item label="切块数量">{{ vectorizeResult.chunkCount }}</el-descriptions-item>
        <el-descriptions-item label="入库数量">{{ vectorizeResult.insertedCount }}</el-descriptions-item>
        <el-descriptions-item label="Milvus集合">{{ vectorizeResult.collectionName }}</el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<script setup>
import {
  listEmbeddingFiles,
  uploadEmbeddingFile,
  vectorizeEmbeddingFile,
} from "@/api/ai/fileAndEmbedding";

const { proxy } = getCurrentInstance();

const uploading = ref(false);
const selectedFile = ref(null);
const uploadResult = ref(null);
const embeddingFileOptions = ref([]);
const selectedEmbeddingFile = ref("");
const vectorizing = ref(false);
const vectorizeResult = ref(null);

onMounted(() => {
  loadEmbeddingFiles();
});

function handleFileChange(file) {
  selectedFile.value = file.raw || null;
  uploadResult.value = null;
}

function handleExceed() {
  proxy.$modal.msgWarning("一次只能上传一个文件");
}

async function submitUpload() {
  if (!selectedFile.value) {
    proxy.$modal.msgWarning("请先选择文件");
    return;
  }

  uploading.value = true;
  try {
    const formData = new FormData();
    formData.append("file", selectedFile.value);
    const res = await uploadEmbeddingFile(formData);
    uploadResult.value = {
      originalFilename: res.originalFilename,
      newFileName: res.newFileName,
      storagePath: res.storagePath,
    };
    proxy.$modal.msgSuccess("上传成功");
    await loadEmbeddingFiles();
  } finally {
    uploading.value = false;
  }
}

async function loadEmbeddingFiles() {
  const res = await listEmbeddingFiles();
  embeddingFileOptions.value = res.data || [];
}

async function submitVectorize() {
  if (!selectedEmbeddingFile.value) {
    proxy.$modal.msgWarning("请先选择需要向量化的文件");
    return;
  }

  vectorizing.value = true;
  try {
    const res = await vectorizeEmbeddingFile(selectedEmbeddingFile.value);
    vectorizeResult.value = res.data;
    proxy.$modal.msgSuccess("向量化完成");
  } finally {
    vectorizing.value = false;
  }
}
</script>

<style scoped>
.file-embedding-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.upload-card {
  width: min(860px, 100%);
}

.embedding-card {
  width: min(860px, 100%);
}

.card-header {
  font-size: 16px;
  font-weight: 600;
}

.action-row {
  margin-top: 16px;
}

.result-box {
  margin-top: 20px;
}
</style>
