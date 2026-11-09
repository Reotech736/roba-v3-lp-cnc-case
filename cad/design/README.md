# 設計データ（2026-11-10、クラウドv30）

現行は `left_case_two_stands_v05_NOT_FOR_MANUFACTURE` のv30。右側もM2座外端を42 mm直線で接続。v30で旧ブラケット用窪みと専用下穴2つを撤去。[撤去検証](../../docs/removed-fixture-machining.md)。専用電池受け・配線ブラケットは製作必須から外し、非表示の比較として保存。電池は基板側の絶縁／緩衝・テープ固定案で、実固定方法は未認定。[最新判断](../../docs/simple-battery-mount-and-right-wall.md)。

| データ | 現行の扱い |
| --- | --- |
| `left_case_two_stands_v05_NOT_FOR_MANUFACTURE.f3d` | 全体v30、履歴・589構成・退避部品・確認用工具を含む |
| 同名JSON | 現行寸法・座標・未確認事項・最新検証への入口 |
| `…_Lower_L_LOCAL.step` | v30下ケース、単一ソリッド、ローカル座標、6061-T6仮材料 |
| `…_Upper_L_protective_roof_LOCAL.step` | v30上ケース、単一ソリッド、ローカル座標、6061-T6仮材料 |
| `…_MCU_cover_concept_LOCAL.step` | 従来の別体カバー候補。製法・固定・材料は未認定 |
| `battery_carrier_provisional_NONMETAL_NOT_FOR_MANUFACTURE_LOCAL.step` | **廃案比較用。現行の必須製作部品ではない** |
| `wire_strain_relief_case_bracket_NONMETAL_NOT_FOR_MANUFACTURE_LOCAL.step` | **廃案比較用。現行の必須製作部品ではない** |
| `stand_test_depth3p5_fingerD8_NOT_FOR_MANUFACTURE.*` | 現行寸法の局所試験片、実物適合未認定 |
| `checkpoints/` | 変更前の退避。[一覧](checkpoints/README.md)。現行ではない |

上下STEPは再読込・単一ソリッド・体積・ローカル境界を照合。組立座標ではなく、下Z−11.5／上Z−1の変換はF3D側。PCB下面Z0。ケース最大外接寸法、LP23組の向き・pin3除外、支持4／逃げ8、スタンド収納、左42 mm接地辺を維持。

電池グループ内は電池1候補、RETIREDの旧受け・旧接着層2・旧配線ブラケット4候補、確認用子14個。個別D1線の閉状態は確認用。電池も底と動く旧開姿勢は廃案比較。現在は基板側へ電池・線を残して底だけ外す案であり、実テープ保持は未確認。

加工発注用データはまだない。旧受け・ブラケットを一括で加工依頼しない。[要件](../../docs/new-case-requirements.md)、[再開メモ](../../docs/next-session.md)、[v30出力照合](../../docs/removed-fixture-machining-step-roundtrip.json)を参照。

元STEP・公開PCB・第三者参照は変更しない。旧v20〜v28のSTEP／F3Dは比較履歴で、現在のケース形状と混同しない。参照部品・仮配線・工具の包絡は加工部品ではない。
