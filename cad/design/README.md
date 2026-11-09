# 設計データ（2026-11-09、クラウドv28）

現行は `left_case_two_stands_v05_NOT_FOR_MANUFACTURE` のv28。[ケース固定の配線保持部](../../docs/case-mounted-wire-restraint.md)を追加し、上下ケースSTEP・全体F3Dを更新。非金属ブラケットはケースのアルミ部品から分離する。40 mm仮R3ループは維持し、旧PCB接着候補面は履歴へ退避した。保持力・強度・実線の曲げ・連続開閉は未認定。

v27の[再点検](../../docs/design-consistency-review.md)で上側2穴の周囲を補強し、上下ケースへJLCCNC6061-T6仮材料を設定。ブラケットは材質未選定なのでSTEP材料属性を省略。

v28で[電池線2本の確認用経路](../../docs/individual-battery-leads.md)を追加。F3Dはv28、実体形状・材料不変の上下ケース／ブラケットSTEPはv27を継続。

同名F3Dが全体・履歴、同名JSONが寸法・参照座標・最新検証への入口です。クラウドとローカルの版を混同しないでください。

v24までの[直付け電池条件](../../docs/lp-and-direct-solder-current-review.md)と、v25の[余長ループ](../../docs/battery-service-loop.md)は比較履歴。当時のケース形状不変／STEP上v22・下v20の記述はv26より前の状態であり、現行のケースSTEPは以下のv27を使用する。配線包絡は部品ではないため加工用STEPへ含めない。

| データ | 内容 |
| --- | --- |
| `left_case_two_stands_v05_NOT_FOR_MANUFACTURE.f3d` | 左ケース全体、Choc23組、PCB・XIAO・電池等の参照と検討工具 |
| `…_Lower_L_LOCAL.step` | v27下ケース、単一ソリッド、部品ローカル座標 |
| `…_Upper_L_protective_roof_LOCAL.step` | v27上ケース、単一ソリッド、部品ローカル座標 |
| `wire_strain_relief_case_bracket_NONMETAL_NOT_FOR_MANUFACTURE_LOCAL.step` | v27非金属保持ブラケット、単一ソリッド。上下ケースと共にSTEP再読み込み・体積・ローカルBBoxを検証 |
| `…_MCU_cover_concept_LOCAL.step` | 別体カバー候補、形状更新の最終出力を維持 |
| `battery_carrier_provisional_NONMETAL_NOT_FOR_MANUFACTURE_LOCAL.step` | 42×20×5電池用の非金属受け、単一ソリッド |
| `stand_test_depth3p5_fingerD8_NOT_FOR_MANUFACTURE.*` | 現行の局所試験片。F3D/STEP/mm STL/JSON |
| `checkpoints/` | [変更前の節目](checkpoints/README.md)。現行ではない |

STEPは組立座標ではありません。下ケースは組立Z−11.5、上側Z−1の変換をF3D側で管理。現行の寸法・未認定事項は[要件](../../docs/new-case-requirements.md)、次の作業は[再開メモ](../../docs/next-session.md)。発注用のデータはまだありません。

局所試験片はくぼみ56.8×14.8×深さ3.5、R2.2、底厚2、D8指掛かり、外形64.8×18.8×5.5 mm。STLはmm・708三角形・全辺を2面で共有する閉じたメッシュを確認。方式・材質・公差・実物開閉は未検証です。旧深さ3.7の `stand_test_provisional_56p8x14p8` は比較履歴です。

`pcb_v2_functional_reference_v01` は公開KiCadの輪郭・取付穴の独立参照で、実装済みLP基板ではありません。古い30×20×4電池や旧配置試作も現行の採用値とは区別し、参照・履歴として保持しています。

v21ではSpring MINI用派生参照の補助固定pin3を除外しました。全体F3D・主JSONはv21、ケース形状が変わらない上下STEPはv20です。[調査と検証](../../docs/spring-mini-fix-pin-removal.md)を参照。

v22では上ケースの旧支持逃げを整理し、全体F3D・上ケースSTEPを更新。下ケースSTEPはv20形状です。[修正記録](../../docs/upper-support-relief-alignment.md)を参照。
