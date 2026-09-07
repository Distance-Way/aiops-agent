Control Plane 与 Worker 之间使用受控 HTTP polling（register、heartbeat、claim、complete），不引入 Redis/RabbitMQ。

原因：本地 MVP 需要零外部依赖且可被 pytest 直接覆盖；HTTP 请求模型已足够表达容量、排队与结果回传。后续若需要更低的调度延迟或更高的吞吐，可以在保持同一 Control Plane API 的前提下替换为消息队列。
