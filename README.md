# roBa v3 LP COROPIT CNC Case

roBa v3 LP（COROPIT対応）の左右上下ケースをアルミ削り出しで製作します。発注先はJLCCNCを予定しています。

**参照データの準備段階です。CNC向け設計・加工用データは未完成です。**

## 進め方

- 手元のv3対応ケースとCOROPITを使い、寸法・組み付けを確認する。
- 元のroBaから取得したSTEPを保存し、複製からCNC向け設計を始める。
- 旧Fusionプロジェクト `roba-v3-lp-cnc-case_old` は過去の作業として残す。
- 新Fusionプロジェクト `roba-v3-lp-cnc-case` で作業する。
- Fusion MCPでAIから操作し、変更後は寸法・干渉・形状を検証する。

## データ

| 場所 | 用途 |
| --- | --- |
| `cad/source/roBa/` | 未変更の元STEP 6点 |
| `cad/source/manifest.json` | 元コミット、元パス、サイズ、Git blob SHA-1 |
| `cad/design/` | 今後のFusion設計データ |
| `cad/export/` | 今後の見積・加工用出力 |
| `docs/design-notes.md` | 確定事項と未確認事項 |
| `docs/setup-fusion360.md` | AI連携と保存先 |

Fusionのフォルダは `01_source_roBa`（参照）、`02_design`（設計）、`03_export`（出力）です。

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

従来の `cad/case/` と古い案内文書は今回の再整理で置き換えます。過去のファイルはGit履歴に残ります。
