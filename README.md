# roBa v3 LP COROPIT CNC Case

roBa v3 LP（COROPIT対応）の左右上下ケースをアルミ削り出しで製作します。発注先はJLCCNCを予定しています。

**参照調査と仮寸法の試験片・基板参照作成まで進みました。ケース本体の新規設計と加工用データの作成はこれからです。現時点のSTEPをそのまま加工発注には使用しないでください。**

## 現在の状態（2026-11-07）

| 項目 | 状態 |
| --- | --- |
| 元データ | roBaからSTEP 6点を取得し、ハッシュ・サイズを検証済み |
| Fusion | 新プロジェクトに6点を保存、クラウド処理完了を確認済み |
| 参照データの保護 | 2026-11-07に6点すべて読み取り専用・処理完了を再確認。試験片は編集用として別管理 |
| AI連携 | Fusion MCPで作成・読み取り・取り込み・保存を確認済み |
| CNC向け設計 | 02_designにスタンド試験片、独立した基板参照、電池・ねじ軸の仮配置案を保存。Spring Mini Choc V2とImagine Black版COROPITの資料調査済み。実機適合・ケース本体は未検証・未作成 |
| 試作・見積・発注 | 未実施 |

設計状況は [設計ノート](docs/design-notes.md)、接続方法と保存先は [Fusionセットアップ](docs/setup-fusion360.md)、更新時のルールは [CONTRIBUTING.md](CONTRIBUTING.md) を参照してください。

## 進め方

- 手元のv3対応ケースとCOROPITを使い、寸法・組み付けを確認する。
- 元のroBaから取得したSTEPを未変更で保存し、機能形状を確認する参照資料としてCNC向けの新規設計に使う。
- 旧Fusionプロジェクト `roba-v3-lp-cnc-case_old` は過去の作業として残す。
- ケース本体は一から設計する。旧設計は嵌合・固定方法の比較資料に留め、形状・肉厚・穴位置を設計ベースとして引き継がない。
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

Fusionのフォルダは `01_source_roBa`（参照）、`02_design`（設計）、`03_export`（出力）です。02_designとローカルcad/designには仮寸法スタンド試験片があります。ケース全体や加工発注用の成果物はまだありません。元STEPと資料、設計の節目のF3D/F3Zを管理します。

## 取得元と部品

[kumamuk-git/roBa](https://github.com/kumamuk-git/roBa) のコミット `69fc34d2996e6aaf63b29f6a58d104b32669f610` に固定しています。

- 左トップ: `case/v3/forLP/top_L_LP.stp`
- 左ボトム: `case/v3/bottom_L.stp`
- 右トップ: `case/v3/forLP/forCOROPIT/top_R_LP_COROPIT.stp`
- 右ボトム: `case/v3/forLP/forCOROPIT/bottom_R_LP_COROPIT.stp`
- リセット棒: `case/v3/forLP/reset_stick_LP.stp`
- 電源スイッチ: `case/v3/power_sw.stp`

左ボトムの参照はv3共通形状です。現物適合は未確認です。補助部品のアルミ化は未決定です。公開v2 PCBから基板輪郭・取付穴の仮参照を新規作成しましたが、実装部品とLP実機の整合は未確認です。COROPIT本体モデルは未登録です。

再取得とハッシュ検証:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/fetch-upstream.ps1
```

## 次の作業

次回は[再開メモ](docs/next-session.md)から確認してください。LPスイッチ・ソケットとCOROPITの必要空間を調べ、内部配置、支持・締結、新規ケース形状の順で進めます。

2026-11-07の[LP・COROPIT・内部配置の調査](docs/lp-coropit-layout-study.md)に、メーカー図面、COROPIT参照穴ピッチ16 mm、電池と外側ねじの仮配置、スタンドくぼみと底厚の積み上げを記録しました。次はLP支持部と、電池・スタンドの重複を避ける配置案を具体化します。

新ケースの現行方針は[新規ケース設計の要件と検討順](docs/new-case-requirements.md)を参照してください。確定要件、仮寸法、不足する部品情報、上下の役割と固定方式の比較案をまとめています。

2026-11-07の[旧設計・水平ケース・JLCCNC調査](docs/old-design-and-jlccnc.md)を追記しました。旧左ケースの側面M2固定と水平底面を確認し、底面ねじ案との比較事項を整理しています。

2026-11-06の[形状調査とCNC変更候補](docs/cnc-investigation.md)を記録しました。参照データは読み取り専用のまま保持しています。

1. 参照形状を組み合わせ、基板・COROPIT・現物との関係を確認する。
2. 固定方法、工具の到達性、無線アンテナ周辺、電池の絶縁を検討する。
3. 片側からCNC向けに設計し、試作で組み付けを確認する。
4. JLCCNCで見積・加工レビューを受ける。

## ライセンスと過去のデータ

元のroBaに準拠しGPL-3.0で公開します。[LICENSE](LICENSE) を参照してください。

従来の `cad/case/` と古いWSL向け手順・一般学習資料は、現在の構成と手順に置き換えました。過去のファイルはGit履歴に残っています。Fusionクラウドの旧設計は `_old` プロジェクトで保管します。
