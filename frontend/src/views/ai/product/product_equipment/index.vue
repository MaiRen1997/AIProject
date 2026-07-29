<template>
  <div class="app-container">
    <el-form :model="queryParams" ref="queryRef" :inline="true" v-show="showSearch" label-width="120px">
      <el-form-item label="备件名称" prop="productName">
        <el-input
          v-model="queryParams.productName"
          placeholder="请输入备件名称"
          clearable
          style="width: 240px"
          @keyup.enter="handleQuery"
        />
      </el-form-item>
      <el-form-item label="备件号" prop="productNo">
        <el-input
          v-model="queryParams.productNo"
          placeholder="请输入备件号"
          clearable
          style="width: 240px"
          @keyup.enter="handleQuery"
        />
      </el-form-item>
      <el-form-item label="含税价" prop="priceIncludingTax">
        <el-input
          v-model="queryParams.priceIncludingTax"
          placeholder="请输入含税价"
          clearable
          style="width: 240px"
          @keyup.enter="handleQuery"
        />
      </el-form-item>
      <el-form-item label="进货价" prop="purchasePrice">
        <el-input
          v-model="queryParams.purchasePrice"
          placeholder="请输入进货价"
          clearable
          style="width: 240px"
          @keyup.enter="handleQuery"
        />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" icon="Search" @click="handleQuery">搜索</el-button>
        <el-button icon="Refresh" @click="resetQuery">重置</el-button>
      </el-form-item>
    </el-form>

    <el-row :gutter="10" class="mb8">
      <el-col :span="1.5">
        <el-button
          type="primary"
          plain
          icon="Plus"
          @click="handleAdd"
          v-hasPermi="['product_equipment:product_equipment:add']"
        >新增</el-button>
      </el-col>
      <el-col :span="1.5">
        <el-button
          type="success"
          plain
          icon="Edit"
          :disabled="single"
          @click="handleUpdate"
          v-hasPermi="['product_equipment:product_equipment:edit']"
        >修改</el-button>
      </el-col>
      <el-col :span="1.5">
        <el-button
          type="danger"
          plain
          icon="Delete"
          :disabled="multiple"
          @click="handleDelete"
          v-hasPermi="['product_equipment:product_equipment:remove']"
        >删除</el-button>
      </el-col>
      <el-col :span="1.5">
        <el-button
          type="warning"
          plain
          icon="Download"
          @click="handleExport"
          v-hasPermi="['product_equipment:product_equipment:export']"
        >导出</el-button>
      </el-col>
      <right-toolbar v-model:showSearch="showSearch" @queryTable="getList"></right-toolbar>
    </el-row>

    <el-table v-loading="loading" :data="product_equipmentList" @selection-change="handleSelectionChange">
      <el-table-column type="selection" width="55" align="center" />
      <el-table-column label="id唯一标识" align="center" prop="id" />
      <el-table-column label="备件名称" align="center" prop="productName" />
      <el-table-column label="备件号" align="center" prop="productNo" />
      <el-table-column label="含税价" align="center" prop="priceIncludingTax" />
      <el-table-column label="进货价" align="center" prop="purchasePrice" />
      <el-table-column label="操作" align="center" class-name="small-padding fixed-width">
        <template #default="scope">
          <el-button link type="primary" icon="Edit" @click="handleUpdate(scope.row)" v-hasPermi="['product_equipment:product_equipment:edit']">修改</el-button>
          <el-button link type="primary" icon="Delete" @click="handleDelete(scope.row)" v-hasPermi="['product_equipment:product_equipment:remove']">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <pagination
      v-show="total>0"
      :total="total"
      v-model:page="queryParams.pageNum"
      v-model:limit="queryParams.pageSize"
      @pagination="getList"
    />

    <!-- 添加或修改产品组件对话框 -->
    <el-dialog :title="title" v-model="open" width="500px" append-to-body>
      <el-form ref="product_equipmentRef" :model="form" :rules="rules" label-width="80px">
      <el-form-item v-if="renderField(true, true)" label="备件名称" prop="productName">
        <el-input v-model="form.productName" placeholder="请输入备件名称" />
      </el-form-item>
      <el-form-item v-if="renderField(true, true)" label="备件号" prop="productNo">
        <el-input v-model="form.productNo" placeholder="请输入备件号" />
      </el-form-item>
      <el-form-item v-if="renderField(true, true)" label="含税价" prop="priceIncludingTax">
        <el-input v-model="form.priceIncludingTax" placeholder="请输入含税价" />
      </el-form-item>
      <el-form-item v-if="renderField(true, true)" label="进货价" prop="purchasePrice">
        <el-input v-model="form.purchasePrice" placeholder="请输入进货价" />
      </el-form-item>

      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button type="primary" @click="submitForm">确 定</el-button>
          <el-button @click="cancel">取 消</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup name="Product_equipment">
import { listProduct_equipment, getProduct_equipment, delProduct_equipment, addProduct_equipment, updateProduct_equipment } from "@/api/ai/product_equipment";

const { proxy } = getCurrentInstance();

const product_equipmentList = ref([]);
const open = ref(false);
const loading = ref(true);
const showSearch = ref(true);
const ids = ref([]);
const single = ref(true);
const multiple = ref(true);
const total = ref(0);
const title = ref("");

const data = reactive({
  form: {},
  queryParams: {
    pageNum: 1,
    pageSize: 10,
    productName: null,
    productNo: null,
    priceIncludingTax: null,
    purchasePrice: null,
  },
  rules: {
    productName: [
      { required: true, message: "备件名称不能为空", trigger: "blur" }
    ],
    productNo: [
      { required: true, message: "备件号不能为空", trigger: "blur" }
    ],
    priceIncludingTax: [
      { required: true, message: "含税价不能为空", trigger: "blur" }
    ],
    purchasePrice: [
      { required: true, message: "进货价不能为空", trigger: "blur" }
    ],
  }
});

const { queryParams, form, rules } = toRefs(data);

/** 查询产品组件列表 */
function getList() {
  loading.value = true;
  listProduct_equipment(queryParams.value).then(response => {
    product_equipmentList.value = response.rows;
    total.value = response.total;
    loading.value = false;
  });
}

/** 取消按钮 */
function cancel() {
  open.value = false;
  reset();
}

/** 表单重置 */
function reset() {
  form.value = {
    id: null,
    productName: null,
    productNo: null,
    priceIncludingTax: null,
    purchasePrice: null,
  };
  proxy.resetForm("product_equipmentRef");
}

/** 搜索按钮操作 */
function handleQuery() {
  queryParams.value.pageNum = 1;
  getList();
}

/** 重置按钮操作 */
function resetQuery() {
  proxy.resetForm("queryRef");
  handleQuery();
}

/** 多选框选中数据  */
function handleSelectionChange(selection) {
  ids.value = selection.map(item => item.id);
  single.value = selection.length != 1;
  multiple.value = !selection.length;
}

/** 新增按钮操作 */
function handleAdd() {
  reset();
  open.value = true;
  title.value = "添加产品组件";
}

/** 修改按钮操作 */
function handleUpdate(row) {
  reset();
  const _id = row.id || ids.value;
  getProduct_equipment(_id).then(response => {
    form.value = response.data;
    open.value = true;
    title.value = "修改产品组件";
  });
}

/** 提交按钮 */
function submitForm() {
  proxy.$refs["product_equipmentRef"].validate(valid => {
    if (valid) {
      if (form.value.id != null) {
        updateProduct_equipment(form.value).then(response => {
          proxy.$modal.msgSuccess("修改成功");
          open.value = false;
          getList();
        });
      } else {
        addProduct_equipment(form.value).then(response => {
          proxy.$modal.msgSuccess("新增成功");
          open.value = false;
          getList();
        });
      }
    }
  });
}

/** 删除按钮操作 */
function handleDelete(row) {
  const _ids = row.id || ids.value;
  proxy.$modal.confirm('是否确认删除产品组件编号为"' + _ids + '"的数据项？').then(function() {
    return delProduct_equipment(_ids);
  }).then(() => {
    getList();
    proxy.$modal.msgSuccess("删除成功");
  }).catch(() => {});
}


/** 导出按钮操作 */
function handleExport() {
  proxy.download('product_equipment/product_equipment/export', {
    ...queryParams.value
  }, `product_equipment_${new Date().getTime()}.xlsx`);
}

/** 是否渲染字段 */
function renderField(insert, edit) {
  return form.value.id == null ? insert : edit;
}

getList();
</script>