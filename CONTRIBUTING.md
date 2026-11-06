# 作業ルール

- `cad/source/roBa/` は未変更の参照データとして扱う。
- 元データ更新時は `cad/source/manifest.json` の取得元・ハッシュも更新する。
- 設計はFusionの `02_design`、ローカルでは `cad/design/` に保存する。
- 加工用出力は `cad/export/` に保存する。
- 検証結果と未確認事項を `docs/design-notes.md` に残す。
- STEPに加え、編集履歴を持つFusion形式も保存する。
- 作業ブランチを切る場合は `codex/` を先頭にする。
- コミットは `更新: 内容`、`追加: 内容`、`修正: 内容` など日本語で記す。
- 認証情報や個人設定をGitに含めない。
