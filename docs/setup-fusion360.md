# FusionとAIの連携

Windows上のFusionを使用します。

## 接続

1. Fusionを起動する。
2. 基本設定 → 一般 → API → Fusion MCP Serverを有効にする。
3. 既定の接続先は `http://127.0.0.1:27182/mcp`。
4. Codexには `autodesk-fusion` として登録済み。新規登録時は `codex mcp add autodesk-fusion --url http://127.0.0.1:27182/mcp`。
5. 設定反映後、プロジェクト一覧の読み取りで接続を確認する。

2026-11-06に10×10×10mmの立方体を作り、寸法と体積1,000mm³を検証した。

操作はMCPとFusion APIを優先する。Computer Useが必要な場合は、MCP/APIで対応できない理由を先に説明する。現在確認できる `DataFile.isReadOnly` は読み取り専用プロパティであり、編集可能枠の切り替えには使えない。

## 保存先

- 旧プロジェクト: `roba-v3-lp-cnc-case_old`
- 現行プロジェクト: `roba-v3-lp-cnc-case`
- `01_source_roBa`: 元データの参照用
- `02_design`: 編集する設計用
- `03_export`: 発注・見積用

参照データの複製を設計用に保存してから編集する。設計の節目にはFusion形式（外部参照に応じてF3D/F3Z）をローカルにも書き出し、交換用にSTEPを残す。クラウド保存は非同期のため、完了を確認する。

## 公式資料

- [Fusion MCP接続](https://help.autodesk.com/cloudhelp/ENU/ADSKMCP-FusionDesktopMcp/files/ADSKMCP_FusionDesktopMcp_connecting_to_the_fusion_mcp_server_html.html)
- [Codex MCP](https://learn.chatgpt.com/docs/extend/mcp)
