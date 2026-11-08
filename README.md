# roBa v3 LP COROPIT CNC Case

roBa v3 LP（COROPIT対応）の左右上下ケースをアルミ削り出しで製作します。発注先はJLCCNCを予定しています。

**現行v05に横向きスタンド2本、左ボトム、キー間を覆う天板と23か所のLP開口、別体XIAOカバー候補を反映しました。実物の係止・押下時の隙間・カバー固定・右ケースは未完成／未検証です。現時点のSTEPを加工発注には使用しないでください。**

## 現在の状態（2026-11-08）

現行は `02_design/left_case_two_stands_v05_NOT_FOR_MANUFACTURE` のクラウドv21。全体F3Dはv21、形状不変の上下ケースSTEPはv20を維持しています。右ケース・実物適合・製造条件は未完成です。

| 項目 | 現行と検証範囲 |
| --- | --- |
| LP配置 | Choc側だけを基準に23スイッチ・23ソケットを180°補正。Spring MINI写真にない補助pin3を派生参照から除外。旧LP穴と照合、支持1・対応逃げ・絶縁材も修正。[詳細](docs/choc-lp-orientation-correction.md) |
| スタンド | 横向き2本、収納56.8×14.8×深さ3.5・指掛かりD8・残肉2。穴閉塞と裏当て張り出しを修正。[詳細](docs/stand-and-M2-correction.md) |
| 接地辺 | ねじ座外端へ揃えた連続42 mm。最大外接寸法を維持し、指定した理想傾斜平面で検査。[詳細](docs/continuous-contact-edge.md) |
| 電池 | 設計対象42×20×5・線40 mm、受け内寸43×21・仮経路31.08 mm。実端子・曲げ・交換は未確認。[詳細](docs/battery42-layout-development.md) |
| 表示管理 | 旧12個をOLD、Choc46個と電池一式をグループ化。[操作](docs/component-organization.md) |
| 参照保護 | 元STEP6点・公開PCB・第三者部品の保存バイトとハッシュを検証。旧モデルは読み取り参照のみ |
| 試作・見積・発注 | 未実施。指定の幾何検査合格を、実物適合・強度・加工成立の認定としない |

Spring MINIと汎用Choc V2の固定ピン差は[調査・除外記録](docs/spring-mini-fix-pin-removal.md)を参照してください。

次のセッションは[再開メモ](docs/next-session.md)から開始してください。[現行要件](docs/new-case-requirements.md)と[CAD一覧](cad/design/README.md)も整理しました。過去段階の「未確認」「未コミット」などの記載は作成時の履歴です。現在のコミット状態はGit履歴を参照してください。

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
| `cad/design/` | 現行と比較用のFusion設計データ・STEP・検証JSON |
| `cad/export/` | 今後の見積・加工用出力 |
| `docs/design-notes.md` | 確定事項と未確認事項 |
| `docs/setup-fusion360.md` | AI連携と保存先 |

Fusionのフォルダは `01_source_roBa`（参照）、`02_design`（設計、旧試作はold）、`03_export`（出力）です。現行v05だけ編集可能にし、同じファイルのバージョン更新を基本とします。元STEPと資料、設計の節目のF3D/F3Zを管理します。加工発注用の成果物はまだありません。

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

[再開メモ](docs/next-session.md)に現行の保存先・検証範囲・未確認事項と作業順を整理しています。

1. LPスイッチの着座・爪保持と、THTキーキャップの押下時の高さ、XIAOカバー周囲の隙間を詰める。
2. カバー固定・上下の位置決め、PCB支持・絶縁、電池固定、USB・電源・リセット・アンテナ周辺を具体化する。
3. 横向きスタンド2本の指掛かり・開閉軌跡・接地安定性を確認する。
4. COROPITの機能位置・必要空間から右ケースを設計する。
5. 実物試作とDFMを経て、JLCCNC提出用の部品別STEPと図面を作る。

現行の方針は[新規ケースの要件](docs/new-case-requirements.md)、参照調査は[LP・COROPIT](docs/lp-coropit-layout-study.md)、[旧設計とJLCCNC](docs/old-design-and-jlccnc.md)、[形状調査](docs/cnc-investigation.md)を参照してください。

## ライセンスと過去のデータ

元のroBaに準拠しGPL-3.0で公開します。[LICENSE](LICENSE) を参照してください。

他者の部品参照CADと、それを含む組立F3D・画像には別の表記があります。[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)と各manifestを参照してください。Choc参照はkoktoh氏のCC BY-NC-SA 4.0で、ケースのみのSTEPには参照部品を含めていません。

従来の `cad/case/` と古いWSL向け手順・一般学習資料は、現在の構成と手順に置き換えました。過去のファイルはGit履歴に残っています。Fusionクラウドの旧設計は `_old` プロジェクトで保管します。
