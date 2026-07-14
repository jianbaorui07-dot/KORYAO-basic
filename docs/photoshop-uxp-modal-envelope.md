# Photoshop UXP 可回滚执行信封

StarBridge 的 Photoshop 写入仍只允许 typed allowlist、明确确认和 sandbox 副本。本信封不增加新的图像操作；它只让已有 `executeAsModal` 写入在占用、取消和异常时具有可验证终态。

## 目标

`uxp/photoshop-bridge/src/batchplay-runner.js` 的 `runModalJob` 统一负责：

1. 把 `timeOut` 限制在 1–30 秒，默认等待 5 秒，避免 modal 冲突时立即失败或无限等待。
2. 在 handler 前后检查 `executionContext.isCancelled`，把用户取消归类为 `cancelled`，不吞掉取消异常。
3. 对选定文档调用 `suspendHistory`；成功时 `resumeHistory(..., true)`，失败或取消时 `resumeHistory(..., false)`。
4. 返回符合 `starbridge.photoshop-modal.v1` 的脱敏 `modal` 字段，不返回文档名、文件路径、descriptor 内容或像素。
5. 保留 `registerAutoCloseDocument`：BatchPlay 失败或取消时，Photoshop 在 modal 退出后关闭临时 sandbox 文档。

## 调用策略

| 场景 | history 目标 | 说明 |
| --- | --- | --- |
| Camera Raw / 活动文档写入 | `active_document` | 进入 handler 前挂起活动文档 history |
| typed BatchPlay sandbox 副本 | `handler_document` | 复制后由 handler 指定 sandbox 文档 ID |
| 只读或纯计划 | `none` | 不挂起 history |

真实写入仍必须同时满足原有的确认、allowlist 和 sandbox 规则。`modal.status=completed` 只证明 UXP modal 正常结束，不等于视觉质量通过；用于 Illustrator 的 PNG 仍要进入 `illustrator.color_vectorize_compare`。

## 验证

```powershell
python -m unittest tests.test_photoshop_uxp_modal_envelope tests.test_photoshop_node_proxy
node --check uxp/photoshop-bridge/src/batchplay-runner.js
python scripts/security_check.py
```

Photoshop 未安装、未授权或 UXP 未连接时，只能验证协议与代码路径，不能写成桌面实测通过。
