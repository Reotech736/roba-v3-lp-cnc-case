# 次セッションの開始メモ

更新: 2026-11-08。v20を一区切りとして、調査・CAD修正・引き継ぎをGitへ分割記録しました。過去段階文書の「未コミット」等は当時の履歴です。今回pushは行いません。現状は発注用ではありません。

## 最初に読むもの

1. `README.md`、`CONTRIBUTING.md`、このメモ。
2. [現行要件](new-case-requirements.md)、[Choc向き補正](choc-lp-orientation-correction.md)。
3. 必要に応じ[スタンド／M2修正](stand-and-M2-correction.md)、[接地辺](continuous-contact-edge.md)、[電池配置](battery42-layout-development.md)。

## 再開する設計と保護する資料

- 現行は `roba-v3-lp-cnc-case/02_design/left_case_two_stands_v05_NOT_FOR_MANUFACTURE`、クラウドv20。ファイル名のv05とクラウド版v20は別。ID `urn:adsk.wipprod:dm.lineage:H9Nq8f1PSl6GXmxJMgIkbw`。
- 最終確認時は保存・処理完了・未保存変更なし。ただし再開時にAPIで状態を読み取り、ユーザーの未保存変更を上書きしない。
- 全体F3D、上下ケースSTEP、主JSONは `cad/design/` の同名ファイル。STEPは部品ローカル座標、組立変換はF3D。下ケースZ−11.5、上側Z−1、PCB下面Z0。
- 元STEP6点・公開PCB・第三者部品STEP・旧プロジェクトは読み取り参照。旧ケース外形を新ケースの設計ベースとして継承しない。
- `balo43_L` はChocの穴配置を調べた機械参照で、現物PCBの電気的な版を確定する資料ではない。読み取り後、保存せず閉じた。
- 右ケースは未設計。COROPIT実固定部・可動域は未確定。

## 現行の重要条件

| 対象 | 現行 |
| --- | --- |
| LP配置 | Choc側のみ。23スイッチ＋23ソケット。モデル角度=公開footprint角度+180°、キー中心は維持。MX側に合わせない |
| PCB支持1 | X−106.12〜−103.82、Y−53〜−45、上端Z−0.2。上側逃げと0.2 mm仮絶縁材も対応 |
| キー参照 | Spring MINI ChocV2、Tai-Haoロープロファイル。汎用Redモデルは厳密なSpring MINI製品データではない |
| 左上側 | 23個の14.1角LP開口とキー間を覆う屋根。周囲だけの輪ではない |
| 電池 | 設計対象42×20×5、線40 mm。受け43×21、角から仮経路31.08 mm。残り8.92 mmは整備ループ成立の保証ではない |
| スタンド | 横向き2本、56.8×14.8×深さ3.5、R2.2、指掛かりD8・X正側、残肉2 |
| 収納位置 | 始点(−52.5,−68.5)/(−52.5,−24.5)、指掛かり中心(4.3,−61.1)/(4.3,−17.1) |
| スタンド現物 | 本体56×14.4・金属厚4、テープ／ゴム込み最大約4.2、R約2。付属両面テープ固定 |
| 接地辺 | X−111.119997、Z−11.5、Y−59〜−17の42 mm。元選択辺より2.5 mm外側、ケース最大外接寸法は維持 |
| ケースねじ | M2×12候補4箇所、D2.2通路・D4.2深さ2.2頭座、上側D1.6深さ4.5パイロット |
| MCU | キー側XIAO nRF52840。旧単体詳細参照を使用。別体カバーM1.6×6候補2本 |
| COROPIT | Imagine Blackレジン、概寸40×25×最大高26、固定面〜球頂点約25 |

OLD_NOT_CURRENTは非表示で旧12個を保持。CHOC46個を一括表示可。BATTERY_ASSEMBLY_CELL42_WIRE40_PROVISIONALの実体候補4個と、内部のCLEARANCE_STUDIES_NOT_PARTS（確認用6個）を分離。表示はユーザーの確認作業で変わるため、再開時に読み取る。

## 次セッションの優先タスク

**最初のテーマは「左ケースのLP実装・組立の未確定事項を絞る」。右ケースへ広げる前に、以下を順に進める。**

1. **LPの非対称な穴・端子・ソケット位置を照合。** キー中心や見た目だけでなく、Choc側の2受け・実端子・第三突起等を確認。旧balo43_Lの全23組とソケット受けは一致したが、全ピン／ランド・実機版は未認定。通常キーの公開SW_MXをそのまま実装済みLP基板と見なさない。汎用Redの2番端子中心には約0.1 mmの差もある。必要ならユーザーへ型番・実機裏面の確認を依頼する。
2. **ねじと組立の作業性。** M2／M1.6の規格、頭形状、有効掛かり、タップ食付き・ドリル先端、工具の進入、締付順、PCB／カバーの着脱を検討。頭座の名目壁0.9 mmは形状確認値で、強度／DFMの認定値ではない。
3. **電池・配線・スタンド。** 線40 mmの測定端点、出口角、曲げ半径、引張り逃げ、閉める際の挟み込み、交換を検討。接地辺の仕上げ・保護材、スタンドの実開閉軌跡・脚／ゴム・接地安定性は未確認。
4. 上記の前提を整理後、COROPITと右基板の機能位置から右ケースを新規設計。実物試作とJLCCNCのDFMを経て発注用データへ進む。

仮寸法でも自走してよいが、不足情報を確認済みに置き換えない。形状変更はMCP/APIを優先し、参照データは変更しない。

## 検証結果と再実行の注意

- [v20の配置](choc-v2-placement-verification.json): 46原点・23ステム上端、向き補正後に再計算・再確認。
- [詳細部品](detailed-choc-fit-verification.json)と[内部保持](internal-retention-fit-verification.json): 指定部品間の外部重複0。部品内部の重複やPCB機能穴を省略した参照は別扱い。
- [M2穴](fastening-and-overhang-current-audit.json): 通路・頭座・名目ねじを全4箇所で検査。
- [収納／残肉](corrected-stand-solid-verification.json): 空隙と残肉2 mmを名目立体で比較。裏当ての全投影検査は別JSON。
- [接地辺](continuous-contact-edge-verification.json): 指定6姿勢の理想平面を検査。実スタンドの角度・安定性を保証するものではない。

v17では穴が追加材で塞がれたことと外周張り出しを「部品間重複0」で見落とした。今後も穴の空隙、局所肉厚、予定外形、工具・接地・組立を別々に検査し、対象を列挙して報告する。

履歴用の一回限りスクリプトを現行へ再実行しない。`group-battery-assembly.py` は失敗した履歴として実行をブロック済み。検査の入口は `check-detailed-choc-fit.py`、`check-internal-retention-fit.py`、`audit-m2-holes-and-stand-overhang.py`、`verify-corrected-stand-solids.py`。更新後の検証で上書きされるJSONと、版固定の履歴JSONを区別する。

表示の再設定は `set-current-review-visibility.py`。承認済み配置は `current-approved-component-state.json` と照合するが、新たに設計変更した場合は検証後に基準を更新すること。旧変換をコピーして現在のChoc補正を戻さない。

節目の退避は `cad/design/checkpoints/README.md`。失敗途中の重複F3Dはローカルに残しGit対象外。通常の再開には不要。元STEP6点と第三者参照はハッシュで保護する。

## 新しいセッションへ渡す文

> README.md、CONTRIBUTING.md、docs/next-session.mdを読んで、クラウドv20のleft_case_two_stands_v05_NOT_FOR_MANUFACTUREを引き継いでください。LP版なのでChoc側だけを基準にします。最初はLPの穴・端子・ソケットと組立の未確定事項を整理し、次にねじ・工具の作業性を検討してください。MCP/API優先、元参照と旧モデルは変更せず、実物未確認を確認済みにしないでください。

## 今回のコミット

- `dd1afa4`: 内部保持・接地辺・固定穴の設計調査と検証履歴。
- `9e7628b`: Choc側の向きとPCB支持を補正し、現行v20 CADと照合結果を保存。
- この再開メモ・README・現行要件・CAD案内の整理は、その後のドキュメントコミットに記録。実際のIDと順序は `git log -3 --oneline` で確認。

今回はlocalのmainへコミットし、pushは行っていません。
