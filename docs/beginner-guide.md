# 3D CAD 初心者ガイド

## 無料で使える3D CADソフト

### 1. FreeCAD（完全無料・オープンソース）
- **対応OS**: Windows, macOS, Linux
- **ライセンス**: 完全無料、商用利用可
- **特徴**: 
  - パラメトリックモデリング（寸法変更が簡単）
  - STEPファイルの読み込み・編集可能
  - Linux環境で動作する
- **ダウンロード**: https://www.freecad.org/
- **学習リソース**:
  - 公式ドキュメント（日本語あり）
  - YouTube: "FreeCAD 初心者" で検索
  - おすすめチャンネル: Joko Engineerworks（日本語）

### 2. Fusion 360（個人利用無料）
- **対応OS**: Windows, macOS
- **ライセンス**: 個人・非商用利用は無料
- **特徴**: 
  - プロ向け機能が使える
  - クラウドベース
  - チュートリアルが豊富
- **ダウンロード**: https://www.autodesk.com/products/fusion-360/personal
- **学習リソース**:
  - Autodesk公式チュートリアル
  - YouTube: "Fusion 360 入門" で検索

### 3. Tinkercad（ブラウザで動作）
- **対応**: Webブラウザのみ
- **ライセンス**: 完全無料
- **特徴**: 
  - 最も簡単（初心者向け）
  - インストール不要
  - STEPファイルのインポートは制限あり
- **URL**: https://www.tinkercad.com/

## おすすめの学習順序

### ステップ1: CADの基本操作を学ぶ（1-2週間）
1. **FreeCAD または Fusion 360 をインストール**
   - Linux環境ならFreeCADがおすすめ
   
2. **基本操作のチュートリアルを実践**
   - スケッチの描き方（2D図形）
   - 押し出し（Extrude）
   - 穴あけ（Hole）
   - フィレット（角を丸める）
   
3. **簡単な形を作ってみる**
   - 立方体、円柱などの基本形状
   - 簡単なケース（箱型）

### ステップ2: STEPファイルを開いて観察（数日）
1. **roBaのSTEPファイルを開く**
   - `cad/case/top_L_LP.stp` などを読み込む
   
2. **形状を観察する**
   - どこが薄いか
   - どこに穴があるか
   - どう組み立てるか
   
3. **寸法を測定する**
   - 肉厚を測る
   - コーナーのRを確認する

### ステップ3: CNC加工について学ぶ（数日）
1. **CNC加工の基礎知識**
   - 3軸CNCでできること/できないこと
   - アンダーカットとは
   - エンドミルと最小R
   
2. **JLCCNCの仕様を確認**
   - 加工可能サイズ
   - 素材と表面処理
   - 公差と最小寸法

### ステップ4: 設計変更を実践（数週間）
1. **簡単な修正から始める**
   - 穴の位置を変える
   - フィレットを追加する
   
2. **CNC向けに最適化**
   - 薄肉部分を厚くする
   - シャープなコーナーにRを付ける
   - アンダーカットを削除

## 参考リソース

### FreeCAD学習（日本語）
- Joko Engineerworks: https://www.youtube.com/@JokoEngineeringunitedTV
- FreeCAD公式Wiki（日本語）: https://wiki.freecad.org/Main_Page/ja

### 3D CAD基礎（日本語）
- 3D CAD入門（YouTube検索推奨）
- パラメトリックモデリング入門

### CNC加工の基礎
- "CNC加工 基礎" で検索
- JLCCNCの加工ガイド: https://jlc-cnc.com/

### 3Dプリントとの違い
- CNCは削り出し → アンダーカット不可、最小R制約
- 3Dプリントは積層 → 柔軟な形状、薄肉可能

## 具体的な最初の一歩

```bash
# FreeCADのインストール（Ubuntu/Debian）
sudo apt update
sudo apt install freecad

# FreeCADを起動
freecad

# メニューから File > Open を選択
# /home/relion911/roba-v3-lp-cnc-case/cad/case/top_L_LP.stp を開く
```

## このプロジェクトでの練習方法

1. まずはSTEPファイルを開いて眺める
2. 各パーツの寸法を測ってみる
3. 簡単な変更（穴の位置など）を試す
4. 変更したファイルをSTEPで保存
5. 元のファイルと比較

焦らず、少しずつ進めていきましょう！
