# 設計の節目の退避

現行は親フォルダの `left_case_two_stands_v05_NOT_FOR_MANUFACTURE.f3d`（クラウドv26）。このフォルダは変更前の履歴で、発注用・現行データではありません。既存v6〜v9以前の退避も保持しています。

| 退避名の版 | その後に行った変更 |
| --- | --- |
| cloud_v9 | リセット操作穴・上下位置決め |
| cloud_v10 | 基板絶縁・電池受け・配線・カバー側壁 |
| cloud_v11 | スタンド収納深さ3.5 mmの比較 |
| cloud_v14 | 指掛かりの反転とCHOC整理 |
| cloud_v15 | 電池42×20×5 mm・線40 mmの候補 |
| v16_before_authorized_cleanup | OLDと電池グループ・表示整理 |
| cloud_v17 | 裏当て張り出しとM2穴閉塞の修正 |
| cloud_v18 | 42 mmの連続した接地辺 |
| cloud_v19 | Choc向き180°補正とPCB支持1の移動 |
| cloud_v20 | Spring MINIにない補助固定pin3の除外（派生参照） |
| cloud_v21 | 上ケースの旧支持逃げの整理・現位置への追従 |
| cloud_v22 | コネクタ用参照の退避・基板B1直付け配線の検討 |
| cloud_v24 | 40 mm全長の余長ループと独立した開口姿勢・接着候補面 |
| cloud_v25 | 上ケースねじ固定の非金属配線保持ブラケット、下ケース逃げ／補強 |

旧上v22／下v20のSTEPも `v05_upper_v22_before_case_wire_bracket_LOCAL.step`／`v05_lower_v20_before_case_wire_bracket_LOCAL.step` に退避。

失敗直後・診断途中の重複F3Dは削除せずローカルへ保持し、`.gitignore` の個別指定でコミット対象から外しました。それらは完成した検証済み状態ではなく、診断スクリプトや旧文書にパスが残っていても通常の再開には不要です。

`v26_lower_EMPTY_FAILED_EXPORT_NOT_MODEL.step` はAPIが成功応答した空の出力を保存した診断資料で、モデルではありません。現行下ケースSTEPは独立ルート経由で再出力し、再読み込みで単一ソリッド・体積・ローカルBBoxを検証済みです。

- `v05_cloud_v26_before_consistency_audit_correction.f3d`: v27の上側M1.6壁補強・材料設定前。現行ではない。

- `v05_cloud_v27_before_individual_lead_study.f3d`: v28個別電池線の確認用モデル追加前。実体形状は現行と同じ、確認用子は12個。

- `v05_cloud_v28_WORKING_before_positive_x_straight_wall.f3d`: 右側直線化・専用電池治具の退避前。開始時の未保存状態も保持。
