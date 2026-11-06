# roBa v3 LP COROPIT CNC Case

roBa v3 LP（COROPIT対応）の左右上下ケースをアルミ削り出しで製作します。発注先はJLCCNCを予定しています。

**設計再開の準備が完了しました。CNC向けの形状変更・加工用データの作成はこれからです。現時点のSTEPをそのまま加工発注には使用しないでください。**

## 現在の状態（2026-11-06）

| 項目 | 状態 |
| --- | --- |
| 元データ | roBaからSTEP 6点を取得し、ハッシュ・サイズを検証済み |
| Fusion | 新プロジェクトに6点を保存、クラウド処理完了を確認済み |
| 参照データの保護 | 6点すべて読み取り専用。編集枠は0/10件使用（確認時点） |
| AI連携 | Fusion MCPで作成・読み取り・取り込み・保存を確認済み |
| CNC向け設計 | 未着手。固定方法・肉厚・公差などは未決定 |
| 試作・見積・発注 | 未実施 |

設計状況は [設計ノート](docs/design-notes.md)、接続方法と保存先は [Fusionセットアップ](docs/setup-fusion360.md)、更新時のルールは [CONTRIBUTING.md](CONTRIBUTING.md) を参照してください。

## 進め方

- 手元のv3対応ケースとCOROPITを使い、寸法・組み付けを確認する。
- 元のroBaから取得したSTEPを保存し、複製からCNC向け設計を始める。
- 旧Fusionプロジェクト `roba-v3-lp-cnc-case_old` は過去の作業として残す。
- 新Fusionプロジェクト `roba-v3-lp-cnc-case` で作業する。
- 操作はFusion MCP/APIを優先し、変更後は寸法・干渉・形状を検証する。画面操作が必要な場合は理由を先に説明する。

## データ

| 場所 | 用途 |
| --- | --- |
| `cad/source/roBa/` | 未変更の元STEP 6点 |
| `cad/source/manifest.json` | 元コミット、元パス、サイズ、Git blob SHA-1 |
| `cad/design/` | 今後のFusion設計データ |
| `cad/export/` | 今後の見積・加工用出力 |
| `docs/design-notes.md` | 確定事項と未確認事項 |
| `docs/setup-fusion360.md` | AI連携と保存先 |

Fusionのフォルダは `01_source_roBa`（参照）、`02_design`（設計）、`03_export`（出力）です。設計用・出力用にはまだケースの成果物はありません。Gitには元STEPと資料を保存し、今後のFusion設計は節目にF3D/F3Zとして書き出して管理します。

## 取得元と部品

[kumamuk-git/roBa](https://github.com/kumamuk-git/roBa) のコミット `69fc34d2996e6aaf63b29f6a58d104b32669f610` に固定しています。

- 左トップ: `case/v3/forLP/top_L_LP.stp`
- 左ボトム: `case/v3/bottom_L.stp`
- 右トップ: `case/v3/forLP/forCOROPIT/top_R_LP_COROPIT.stp`
- 右ボトム: `case/v3/forLP/forCOROPIT/bottom_R_LP_COROPIT.stp`
- リセット棒: `case/v3/forLP/reset_stick_LP.stp`
- 電源スイッチ: `case/v3/power_sw.stp`

左ボトムにはv3共通形状を候補として採用しています。現物適合は未確認です。補助部品のアルミ化は未決定です。PCB・COROPIT本体の3Dモデルはまだ取り込んでいません。

再取得とハッシュ検証:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/fetch-upstream.ps1
```

## 次の作業

1. 参照形状を組み合わせ、基板・COROPIT・現物との関係を確認する。
2. 固定方法、工具の到達性、無線アンテナ周辺、電池の絶縁を検討する。
3. 片側からCNC向けに設計し、試作で組み付けを確認する。
4. JLCCNCで見積・加工レビューを受ける。

## ライセンスと過去のデータ

元のroBaに準拠しGPL-3.0で公開します。[LICENSE](LICENSE) を参照してください。

従来の `cad/case/` と古いWSL向け手順・一般学習資料は、現在の構成と手順に置き換えました。過去のファイルはGit履歴に残っています。Fusionクラウドの旧設計は `_old` プロジェクトで保管します。
