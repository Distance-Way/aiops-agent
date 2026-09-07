const { createApp } = Vue;

createApp({
  data() {
    return {
      apiKey: localStorage.getItem("aiops_api_key") || "",
      activeTab: "chat",
      messages: [],
      sessions: [],
      currentSessionId: "",
      input: "",
      loading: false,
      errorText: "",
      documents: [],
      uploading: false,
      status: null,
      jobs: [],
      workers: [],
      jobType: "system_status",
      jobPriority: "normal",
      jobText: "",
      submittingJob: false,
    };
  },
  mounted() {
    this.refreshSessions();
    this.loadDocuments();
    this.loadStatus();
    this.loadJobsAndWorkers();
  },
  methods: {
    rememberKey() {
      localStorage.setItem("aiops_api_key", this.apiKey);
    },
    headers(json = false) {
      if (!this.apiKey) {
        throw new Error("请先填写并保存 X-API-Key");
      }
      const result = { "X-API-Key": this.apiKey };
      if (json) result["Content-Type"] = "application/json";
      return result;
    },
    async request(path, options = {}) {
      const response = await fetch(path, options);
      if (!response.ok) {
        let detail = `请求失败（${response.status}）`;
        try {
          const data = await response.json();
          detail = data.detail || detail;
        } catch (_) {}
        throw new Error(detail);
      }
      if (response.status === 204) return null;
      return response.json();
    },
    async refreshSessions() {
      try {
        this.sessions = await this.request("/api/sessions", { headers: this.headers() });
      } catch (error) {
        this.errorText = error.message;
      }
    },
    async startNewSession() {
      this.currentSessionId = "";
      this.messages = [];
      await this.refreshSessions();
    },
    async loadMessages() {
      if (!this.currentSessionId) {
        this.messages = [];
        return;
      }
      try {
        this.messages = await this.request(
          `/api/sessions/${this.currentSessionId}/messages`,
          { headers: this.headers() }
        );
      } catch (error) {
        this.errorText = error.message;
      }
    },
    async sendMessage() {
      const message = this.input.trim();
      if (!message || this.loading) return;
      this.loading = true;
      this.errorText = "";
      try {
        const data = await this.request("/api/chat", {
          method: "POST",
          headers: this.headers(true),
          body: JSON.stringify({
            message,
            session_id: this.currentSessionId || null,
            use_rag: true,
            top_k: 3,
          }),
        });
        this.currentSessionId = data.session_id;
        this.messages.push(
          { role: "user", content: message },
          {
            role: "assistant",
            content: data.reply,
            tools: data.tools_executed,
            sources: data.sources,
          }
        );
        this.input = "";
        await this.refreshSessions();
      } catch (error) {
        this.errorText = error.message;
      } finally {
        this.loading = false;
        this.$nextTick(() => {
          const log = this.$refs.chatLog;
          if (log) log.scrollTop = log.scrollHeight;
        });
      }
    },
    async loadDocuments() {
      try {
        this.documents = await this.request("/api/documents", { headers: this.headers() });
      } catch (error) {
        this.errorText = error.message;
      }
    },
    async uploadManual(event) {
      const file = event.target.files && event.target.files[0];
      if (!file) return;
      this.uploading = true;
      this.errorText = "";
      const form = new FormData();
      form.append("file", file);
      try {
        await this.request("/api/documents", {
          method: "POST",
          headers: this.headers(),
          body: form,
        });
        await this.loadDocuments();
      } catch (error) {
        this.errorText = error.message;
      } finally {
        this.uploading = false;
        event.target.value = "";
      }
    },
    async removeDocument(documentId) {
      try {
        await this.request(`/api/documents/${documentId}`, {
          method: "DELETE",
          headers: this.headers(),
        });
        await this.loadDocuments();
      } catch (error) {
        this.errorText = error.message;
      }
    },
    async loadStatus() {
      try {
        this.status = await this.request("/api/status", { headers: this.headers() });
        this.errorText = "";
      } catch (error) {
        this.errorText = error.message;
      }
    },
    async loadJobsAndWorkers() {
      try {
        const headers = this.headers();
        const [jobs, workers] = await Promise.all([
          this.request("/api/jobs", { headers }),
          this.request("/api/workers", { headers }),
        ]);
        this.jobs = jobs;
        this.workers = workers;
        this.errorText = "";
      } catch (error) {
        this.errorText = error.message;
      }
    },
    buildJobPayload() {
      if (this.jobType === "service_check") {
        const port = Number.parseInt(this.jobText, 10);
        return { port: Number.isFinite(port) ? port : 8000 };
      }
      if (this.jobType === "query_logs") {
        return {
          keyword: this.jobText.trim() || "ERROR",
          max_lines: 20,
          since_minutes: 60,
        };
      }
      if (this.jobType === "log_inference") {
        return { text: this.jobText.trim() };
      }
      return {};
    },
    async submitJob() {
      if (this.submittingJob) return;
      this.submittingJob = true;
      this.errorText = "";
      try {
        await this.request("/api/jobs", {
          method: "POST",
          headers: this.headers(true),
          body: JSON.stringify({
            type: this.jobType,
            priority: this.jobPriority,
            cpu_request: 1,
            memory_request_mb: 256,
            payload: this.buildJobPayload(),
          }),
        });
        this.jobText = "";
        await this.loadJobsAndWorkers();
      } catch (error) {
        this.errorText = error.message;
      } finally {
        this.submittingJob = false;
      }
    },
  },
}).mount("#app");
