<template>
  <div style="z-index: 999; border: 1px solid var(--el-border-color)">
    <!-- 工具栏 -->
    <Toolbar
      :editor="editorRef"
      mode="mode"
      :default-config="toolbarConfig"
      style="border-bottom: 1px solid var(--el-border-color)"
    />
    <!-- 编辑器 -->
    <Editor
      v-model="modelValue"
      :style="{ minHeight: height, overflowY: 'hidden' }"
      :default-config="editorConfig"
      mode="mode"
      @on-created="handleCreated"
      @on-change="handleChange"
    />
  </div>
</template>

<script setup lang="ts">
import "@wangeditor-next/editor/dist/css/style.css";
import { Toolbar, Editor } from "@wangeditor-next/editor-for-vue";
import { IToolbarConfig, IEditorConfig } from "@wangeditor-next/editor";

// 上传图片回调函数类型
type InsertFnType = (_url: string, _alt: string, _href: string) => void;

// 模拟文件上传API，根据实际项目进行调整
interface UploadResult {
  url: string;
  name: string;
}

const FileAPI = {
  uploadFile: async (file: File): Promise<UploadResult> => {
    // 这里应该是实际的文件上传逻辑
    // 暂时返回一个mock数据
    return Promise.resolve({
      url: "https://example.com/image.jpg",
      name: file.name,
    });
  },
};

const props = defineProps({
  height: {
    type: String,
    default: "200px",
  },
  readonly: {
    type: Boolean,
    default: false,
  },
  autoFocus: {
    type: Boolean,
    default: true,
  },
  scroll: {
    type: Boolean,
    default: true,
  },
});
// 双向绑定
const modelValue = defineModel("modelValue", {
  type: String,
  required: false,
});

// 编辑器实例，必须用 shallowRef，重要！
const editorRef = shallowRef();

// 工具栏配置
const toolbarConfig = ref<Partial<IToolbarConfig>>({});

// 编辑器配置 - 根据 props 动态生成配置
const editorConfig = ref<Partial<IEditorConfig>>({
  placeholder: "请输入内容...",
  readOnly: props.readonly,
  autoFocus: props.autoFocus,
  scroll: props.scroll,
  MENU_CONF: {
    uploadImage: {
      customUpload(file: File, insertFn: InsertFnType) {
        // 上传图片
        FileAPI.uploadFile(file).then((res) => {
          // 插入图片
          insertFn(res.url, res.name, res.url);
        });
      },
    } as any,
  },
});

// 记录 editor 实例，重要！
const handleCreated = (editor: any) => {
  editorRef.value = editor;
};

// 处理内容变化 - 获取纯文本而不是HTML
const handleChange = (editor: any) => {
  editorRef.value = editor;
  if (editorRef.value) {
    const text = editorRef.value.getText();
    modelValue.value = text;
  }
};

// 组件销毁时，也及时销毁编辑器，重要！
onBeforeUnmount(() => {
  const editor = editorRef.value;
  if (editor == null) return;
  editor.destroy();
});
</script>
