<template>
  <div class="assistant-wrapper">
    <el-card class="assistant-card">
      <div slot="header" class="assistant-header">
        <span class="assistant-title">
          <i class="el-icon-chat-dot-round"></i> 健康助手
        </span>
        <el-button size="mini" icon="el-icon-refresh" @click="newSession">新对话</el-button>
      </div>

      <div class="msg-list" ref="msgList">
        <div v-for="(m, i) in messages" :key="i" :class="['msg-row', m.role]">
          <div class="bubble">
            <div class="content">{{ m.content }}</div>
            <div v-if="m.sources && m.sources.length" class="sources">
              <span class="sources-label">参考文章：</span>
              <el-tag
                v-for="(s, j) in m.sources"
                :key="j"
                size="mini"
                type="info"
                class="source-tag">
                {{ s.title || ('#' + s.articleId) }}
              </el-tag>
            </div>
          </div>
        </div>
        <div v-if="loading" class="msg-row assistant">
          <div class="bubble thinking">
            <i class="el-icon-loading"></i> 正在思考中...
          </div>
        </div>
      </div>

      <div class="input-area">
        <el-input
          v-model="input"
          type="textarea"
          :rows="2"
          resize="none"
          placeholder="例如：老年人高血压饮食要注意什么？ / 生成徐老 2022-03 的健康报告"
          @keydown.native.enter.exact.prevent="send">
        </el-input>
        <el-button
          type="primary"
          icon="el-icon-position"
          :loading="loading"
          @click="send">
          发送
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script>
const WELCOME = "你好，我是健康助手，可以解答老年人健康知识问题，也可以根据健康档案生成老人健康报告。";

export default {
  name: "Assistant",
  data() {
    return {
      input: "",
      loading: false,
      sessionId: "",
      messages: [{ role: "assistant", content: WELCOME, sources: [] }],
    };
  },
  created() {
    this.newSession();
  },
  methods: {
    newSession() {
      const userId = window.sessionStorage.getItem("id") || "default";
      // 新 sessionId 对应后端全新的会话历史，实现真正“新对话”
      this.sessionId = userId + "_" + Date.now();
      this.messages = [{ role: "assistant", content: WELCOME, sources: [] }];
      this.scrollBottom();
    },
    scrollBottom() {
      this.$nextTick(() => {
        const el = this.$refs.msgList;
        if (el) el.scrollTop = el.scrollHeight;
      });
    },
    async send() {
      const text = (this.input || "").trim();
      if (!text || this.loading) return;

      this.messages.push({ role: "user", content: text, sources: [] });
      this.input = "";
      this.loading = true;
      this.scrollBottom();

      try {
        const { data: res } = await this.$http.post("/assistant/chat", {
          message: text,
          sessionId: this.sessionId,
          userId: window.sessionStorage.getItem("id") || "",
        });
        if (res && res.code === 200 && res.answer) {
          this.messages.push({
            role: "assistant",
            content: res.answer,
            sources: res.sources || [],
          });
        } else {
          this.messages.push({
            role: "assistant",
            content: (res && res.message) || "抱歉，暂时无法回答，请稍后重试。",
            sources: [],
          });
        }
      } catch (e) {
        this.messages.push({
          role: "assistant",
          content: "网络异常，请检查服务后重试。",
          sources: [],
        });
      } finally {
        this.loading = false;
        this.scrollBottom();
      }
    },
  },
};
</script>

<style lang="less" scoped>
.assistant-wrapper {
  height: 100%;
}
.assistant-card {
  height: calc(100vh - 135px);
  display: flex;
  flex-direction: column;

  ::v-deep .el-card__body {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    padding: 12px;
  }
}
.assistant-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.assistant-title {
  font-size: 17px;
  font-weight: bold;
  color: #4a5064;
}
.msg-list {
  flex: 1;
  overflow-y: auto;
  padding: 10px 6px;
  background-color: #f7f9fc;
  border-radius: 4px;
}
.msg-row {
  display: flex;
  margin-bottom: 14px;

  &.user {
    justify-content: flex-end;

    .bubble {
      background-color: #409eff;
      color: #fff;
      border-top-right-radius: 2px;
    }
  }

  &.assistant {
    justify-content: flex-start;

    .bubble {
      background-color: #fff;
      color: #303133;
      border: 1px solid #ebeef5;
      border-top-left-radius: 2px;
    }
  }
}
.bubble {
  max-width: 72%;
  padding: 10px 14px;
  border-radius: 10px;
  line-height: 1.7;
  word-break: break-word;
  white-space: pre-wrap;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}
.thinking {
  color: #909399;
}
.sources {
  margin-top: 8px;
  padding-top: 6px;
  border-top: 1px dashed #dcdfe6;
  font-size: 12px;
  color: #606266;
}
.sources-label {
  margin-right: 4px;
}
.source-tag {
  margin: 2px 4px 2px 0;
}
.input-area {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  margin-top: 12px;

  .el-button {
    height: 54px;
  }
}
</style>
