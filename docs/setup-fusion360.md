# Fusion360セットアップガイド（WSL環境向け）

## 概要

WSL（Windows Subsystem for Linux）環境でこのプロジェクトを扱う場合、Fusion360はWindows側にインストールし、WSLのファイルシステムにアクセスする形で作業します。

## Windows側のパス

WSLのこのプロジェクトは、Windows側から以下のパスでアクセスできます：

```
\\wsl$\Ubuntu\home\relion911\roba-v3-lp-cnc-case
```

または、エクスプローラーで以下のように入力：

```
\\wsl.localhost\Ubuntu\home\relion911\roba-v3-lp-cnc-case
```

## Fusion360のインストール手順

### 1. Autodesk アカウントの作成

1. [Autodesk公式サイト](https://www.autodesk.co.jp/)にアクセス
2. 「サインイン」→「アカウントを作成」
3. 個人利用の場合は無料の個人用ライセンスを選択可能

### 2. Fusion360のダウンロード

1. [Fusion360ダウンロードページ](https://www.autodesk.co.jp/products/fusion-360/personal)にアクセス
2. 「個人用Fusion360」または「無料体験版」をダウンロード
3. インストーラーを実行してインストール

### 3. ライセンスについて

- **個人用（趣味）**: 完全無料、非商用利用
- **スタートアップ**: 年間売上10万ドル未満の企業は無料
- **商用版**: 有料（年間サブスクリプション）

## プロジェクトファイルの開き方

### 方法1: Windowsエクスプローラー経由

1. エクスプローラーで `\\wsl$\Ubuntu\home\relion911\roba-v3-lp-cnc-case\cad\case` を開く
2. ファイルをダブルクリックしてFusion360で開く

### 方法2: Fusion360内から開く

1. Fusion360を起動
2. 「ファイル」→「開く」
3. 「コンピューターから開く」を選択
4. 上記のWSLパスに移動してファイルを選択

## 推奨設定

### データパネルの同期先

Fusion360はデフォルトでクラウドに保存しますが、ローカルファイルとしても扱えます：

1. 「ファイル」→「エクスポート」でローカル保存
2. STEPファイル（.step）やF3D形式で保存推奨

### 作業フォルダ構造

```
cad/case/
├── v1/              # バージョン管理
│   ├── top.f3d
│   └── bottom.f3d
└── export/          # エクスポートファイル
    ├── top.step
    └── bottom.step
```

## 学習リソース

### 公式チュートリアル

- [Fusion360 公式チュートリアル](https://help.autodesk.com/view/fusion360/JPN/courses/)
- [Fusion360 YouTubeチャンネル](https://www.youtube.com/@Fusion360)

### キーボードケース設計向け

- 「DIY Keyboard Case Design Guide」（このプロジェクトのdocs/内、非公開）
- 第3章「Fusion360を用いて立体形状のケースを設計する」を参照

## よくある問題

### WSLファイルが見つからない

- WSLが起動しているか確認
- `\\wsl$\` ではなく `\\wsl.localhost\` を試す（Windows 11）

### ファイルが開けない

- ファイル拡張子を確認（.f3d, .step, .stp等）
- Windowsの権限設定を確認

### 保存が遅い

- WSL経由のI/Oは若干遅いため、作業中はWindows側（C:\）に一時保存し、完成後にWSL側にコピーすることも検討

## Git連携

Fusion360で編集したファイルは、WSL側のターミナルでコミット：

```bash
cd /home/relion911/roba-v3-lp-cnc-case
git add cad/case/
git commit -m "ケース設計を更新"
git push
```

## 次のステップ

1. Fusion360をインストール
2. 公式チュートリアルで基本操作を学習
3. `cad/case/source/` の既存STEPファイルを開いて構造を理解
4. 「DIY Keyboard Case Design Guide」の第3章を読みながら実践
