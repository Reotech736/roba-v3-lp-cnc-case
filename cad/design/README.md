# 設計データ（2026-11-08、クラウドv20）

現行は `left_case_two_stands_v05_NOT_FOR_MANUFACTURE`。同名F3Dが全体・履歴、同名JSONが寸法・参照座標・最新検証への入口です。クラウドとローカルの版を混同しないでください。

| データ | 内容 |
| --- | --- |
| `left_case_two_stands_v05_NOT_FOR_MANUFACTURE.f3d` | 左ケース全体、Choc23組、PCB・XIAO・電池等の参照と検討工具 |
| `…_Lower_L_LOCAL.step` | v20下ケース、単一ソリッド、部品ローカル座標 |
| `…_Upper_L_protective_roof_LOCAL.step` | v20上ケース、単一ソリッド、部品ローカル座標 |
| `…_MCU_cover_concept_LOCAL.step` | 別体カバー候補、形状更新の最終出力を維持 |
| `battery_carrier_provisional_NONMETAL_NOT_FOR_MANUFACTURE_LOCAL.step` | 42×20×5電池用の非金属受け、単一ソリッド |
| `stand_test_depth3p5_fingerD8_NOT_FOR_MANUFACTURE.*` | 現行の局所試験片。F3D/STEP/mm STL/JSON |
| `checkpoints/` | [変更前の節目](checkpoints/README.md)。現行ではない |

STEPは組立座標ではありません。下ケースは組立Z−11.5、上側Z−1の変換をF3D側で管理。現行の寸法・未認定事項は[要件](../../docs/new-case-requirements.md)、次の作業は[再開メモ](../../docs/next-session.md)。発注用のデータはまだありません。

局所試験片はくぼみ56.8×14.8×深さ3.5、R2.2、底厚2、D8指掛かり、外形64.8×18.8×5.5 mm。STLはmm・708三角形・全辺を2面で共有する閉じたメッシュを確認。方式・材質・公差・実物開閉は未検証です。旧深さ3.7の `stand_test_provisional_56p8x14p8` は比較履歴です。

`pcb_v2_functional_reference_v01` は公開KiCadの輪郭・取付穴の独立参照で、実装済みLP基板ではありません。古い30×20×4電池や旧配置試作も現行の採用値とは区別し、参照・履歴として保持しています。
