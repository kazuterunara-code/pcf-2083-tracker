# 2083 PCFウィークリートラッカー（GitHub Actions自動更新版）

NEXT FUNDS 日本成長株アクティブ上場投信（2083）の東証PCFを毎営業日 自動取得し、
組入銘柄の保有比率・増減をグラデーション付きで可視化するダッシュボードです。

- 取得元: `https://inav.ice.com/pcf-download/2083.csv`
- 自動実行: GitHub Actions（`.github/workflows/daily.yml`）
- 公開: GitHub Pages（`index.html`）
- 履歴データ: `data/history.json`（Actionsが毎回追記）

---

## セットアップ手順

### 1. GitHubアカウントを作る（既にあればスキップ）
https://github.com/join

### 2. 新しいリポジトリを作成する
- 右上の「+」→「New repository」
- 名前は何でもOK（例: `pcf-2083-tracker`）
- **Public** を推奨します（PCFはもともと東証が一般公開している情報なので、Publicにしても情報の機密性に問題はありません。Privateだと環境によってGitHub Pagesが使えない場合があります）
- 「Add a README file」のチェックは外したままで大丈夫です（このフォルダに既にREADMEがあるため）

### 3. このフォルダの中身をそのままアップロードする
リポジトリのトップページで「uploading an existing file」（または「Add file」→「Upload files」）を選び、
このフォルダの中身をフォルダ構成を保ったままドラッグ＆ドロップしてください。

```
（リポジトリのルート）
├── index.html
├── README.md
├── data/
│   └── history.json
├── scripts/
│   └── fetch_and_update.py
└── .github/
    └── workflows/
        └── daily.yml
```

> ブラウザの「Upload files」はフォルダ構成をそのまま反映してくれますが、うまくいかない場合は
> GitHub Desktop（無料アプリ）を使ってこのフォルダをそのままPushするのが一番簡単です。

### 4. Actionsが有効になっているか確認する
リポジトリの「Actions」タブを開きます。初回は確認画面が出る場合があるので
「I understand my workflows, go ahead and enable them」を押してください。

### 5. まず手動で1回動かしてみる（重要）
「Actions」タブ →「Update PCF history (2083)」をクリック →
右側の「Run workflow」ボタン →「Run workflow」を押す。

1分ほどで実行が終わります。緑のチェックが付けば成功です。
赤い×が付いた場合はログを開いてエラー内容を見てください
（PCFサイト側がスクリプトからのアクセスをブロックしている可能性があります。
その場合はログの内容を教えてもらえれば、ヘッダーの調整など一緒に対応できます）。

成功すると `data/history.json` に新しいスナップショットが自動でコミットされます。

### 6. GitHub Pagesを有効にする
「Settings」タブ →左メニュー「Pages」→
「Build and deployment」の「Source」を **「Deploy from a branch」** に設定 →
Branch を **`main`** / **`/ (root)`** にして「Save」。

数分後、ページ上部に表示されるURL
（`https://<あなたのユーザー名>.github.io/<リポジトリ名>/`）でダッシュボードが見られます。

### 7. 完了
これで平日16:00 JST頃に自動更新されるようになりました。
気になったときにそのURLをブラウザで開くだけで、最新の保有比率と増減（赤=増加/青=減少のグラデーション）が確認できます。

---

## よくあること・トラブルシュート

- **スケジュール実行が動いていない気がする** → GitHubの仕様で、60日間コミットが無いリポジトリは
  自動的にscheduled cronが停止します。Actionsが毎日コミットしている限りは問題になりません。
- **実行時刻が多少前後する** → GitHub Actionsのcronは混雑時に数分〜十数分ずれることがあります。
  時間に厳密な用途ではないため、通常は問題ありません。
- **ダウンロードが失敗する** → `inav.ice.com` 側がリクエスト元（GitHubのサーバー）をブロックしている
  可能性があります。Actionsのログに出るエラー内容を見て調整します
  （User-Agentの変更や、別の取得経路の検討など）。
- **別のETFコードに変えたい** → `.github/workflows/daily.yml` の
  `python scripts/fetch_and_update.py` の後ろにコード（例: `2084`）を追記してください。
  例: `run: python scripts/fetch_and_update.py 2084`
- **失敗したら通知が欲しい** → GitHubはデフォルトで、Actionsの実行が失敗すると
  登録メールアドレスに通知を送ります。追加設定は不要です。

---

## ファイルの役割

| ファイル | 役割 |
|---|---|
| `scripts/fetch_and_update.py` | PCFを取得・解析し `data/history.json` に追記するPythonスクリプト |
| `.github/workflows/daily.yml` | 毎営業日16:00 JSTにスクリプトを実行するGitHub Actions設定 |
| `data/history.json` | 日付ごとの組入銘柄スナップショットの履歴（自動更新される） |
| `index.html` | `data/history.json` を読み込んで表示するダッシュボード（GitHub Pagesで公開） |
