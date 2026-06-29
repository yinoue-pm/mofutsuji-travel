# mofutsuji-travel — 1ファイル完結 HTML / 崩れない PDF ジェネレーター

構造化データ（YAML / JSON）1枚から、

- **スマホで美しく読める「単一 HTML」**（CSS・JS インライン、画像不使用、オフラインでもレイアウト維持）
- **そのまま崩れない「A4 PDF」**（背景色・色分け・装飾を保持）

を生成する静的ドキュメント・ジェネレーターです。サンプルとして四国7泊8日の温泉旅程を同梱しています。
「**サマリ統計 ＋ 目次/ルート ＋ セクションごとのタイムライン ＋ カード強調 ＋ 集計サマリ**」という汎用構造なので、
旅程に限らずレポートや行程ガイドへ展開できます。

```
データ(YAML/JSON) ──▶ 検証(schema) ──▶ Jinja2(theme+macros) ──▶ 単一HTML ──▶ Playwright ──▶ A4 PDF
```

---

## クイックスタート

```bash
# 1) 依存導入（HTML だけなら install、PDF/テストも使うなら install-dev）
make install-dev          # = venv作成 + pip + playwright install chromium

# 2) HTML 生成（dist/index.html と 公開用 ./index.html）
make build

# 3) ブラウザ確認
make serve                # http://localhost:8000/dist/

# 4) PDF 生成（A4・背景色保持）
make pdf                  # dist/itinerary.pdf
```

`make` を使わない場合:

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
python -m playwright install chromium

python scripts/build.py data/shikoku.yaml dist/index.html --root
python scripts/to_pdf.py dist/index.html dist/itinerary.pdf
```

---

## 技術選定（なぜこれを選んだか）

| 論点 | 採用 | 理由 |
|---|---|---|
| テンプレート | **Jinja2** | ループ・条件分岐・マクロ・**自動エスケープ（XSS 対策）** が揃う。長文 HTML を f-string で組むと可読性・保守性が破綻する |
| データ形式 | **YAML**（JSON も可） | コメント可・複数行の長文 desc が書きやすい・記号が少なく手編集での量産に最適。JSON も同じスキーマで読める |
| PDF 化 | **Playwright (Chromium)** 主 / weasyprint 代替 | 実ブラウザの print CSS をそのまま使うため**背景色・装飾の忠実性が最高**。`print_background=True` で「背景のグラフィック」相当を常時 ON |
| 配信 | **静的ホスティング**（GitHub Pages / Cloudflare Pages） | 単一 HTML を置くだけ。ビルド成果物に外部依存（Webフォント CDN 以外）がない |

> **weasyprint との比較**：weasyprint はブラウザ不要・軽量だが、flexbox / grid / 一部 CSS の対応が限定的でレイアウトが簡略化される。
> 本テンプレートは grid を多用するため、忠実性重視で Chromium を第一候補にしています。

---

## ディレクトリ構成

```
mofutsuji-travel/
├── data/
│   ├── shikoku.yaml        # サンプル旅程（四国7泊8日）★編集対象
│   └── sample.json         # JSON 入力＆別テーマのデモ
├── src/
│   ├── schema.py           # dataclass 定義＋検証/正規化（parse_document）
│   ├── theme.py            # 配色・フォントのデザイントークン（THEMES）
│   └── generator.py        # 読込→検証→Jinja2描画（render_* 関数群）
├── templates/
│   ├── base.html.j2        # 単一HTMLのスケルトン（CSS/JSインライン・印刷CSS）
│   └── macros.html.j2      # icon/hero/section/timeline_item/lodging_card/cost_summary
├── scripts/
│   ├── build.py            # HTML 出力
│   └── to_pdf.py           # PDF 出力（Playwright）
├── tests/                  # 検証/スナップショット/PDF テスト
├── dist/                   # 生成物（index.html, itinerary.pdf）
├── index.html              # 公開用（Pages のルート）
└── .github/workflows/pages.yml
```

### 主要関数（責務）

| 関数 | シグネチャ | 責務 |
|---|---|---|
| `load_data` | `(path) -> dict` | 拡張子から YAML/JSON を判別して読込 |
| `parse_document` | `(raw: dict) -> Document` | 検証＋正規化。不正は `ValidationError` に**全件**集約 |
| `render_hero` | `(doc) -> str` | hero（タイトル＋統計＋ルート）断片 |
| `render_section` | `(section) -> str` | 1日分のセクション断片 |
| `render_item` | `(item, sec_slug, idx) -> str` | タイムライン1アイテム断片 |
| `render_card` | `(card) -> str` | 宿泊強調カード断片 |
| `render_summary` | `(summary) -> str` | 集計（横棒グラフ）断片 |
| `render_document` | `(doc) -> str` | 単一 HTML 全体（CSS/JS インライン） |

---

## データスキーマ

```yaml
meta:                       # 必須: title
  title: "四国の旅"
  subtitle: "7泊8日 …"      # 任意
  period: "2026年7月6日 〜 7月13日"
  route: "福津〜呉〜今治♨〜…"
  created: "2026年4月22日 (Ver.1.0)"

theme: "onsen"              # onsen | ocean | mono（src/theme.py）

hero_stats:                 # 任意: heroの統計チップ（label/value 必須）
  - { label: "走行距離", value: "1,697", unit: "km", icon: "drive" }

sections:                   # 必須: 1件以上
  - label: "1日目"          # 必須
    date: "7/6"
    weekday: "月"
    leg: "自宅 → 今治(湯ノ浦温泉)"
    dist_km: 441
    items:                  # 1件以上推奨（空だと検証エラー）
      - time: "10:30-12:00"
        type: "sight"       # meal | sight | drive | ferry | lodging
        title: "大和ミュージアム"   # 必須
        desc: "…"
        cost: 2300
        cost_label: "観覧料"
        rating: 3.48        # 任意（4.0以上で自動的に強調）
        card:               # 任意: 宿泊などの強調カード
          name: "湯ノ浦温泉 ♨"     # 必須
          address: "…"
          tel: "0898-47-0707"
          room: "…"
          plan: "…"
          spring: "低張性弱アルカリ性冷鉱泉"   # 泉質
          benefits: "神経痛・筋肉痛・…"        # 効能
          price: 20700
          discount: -5000   # 負数で割引
          discount_label: "シルバー＋SPウイーク"

summary:                    # 任意: 横棒グラフ（total は内訳合計と一致が必須）
  total: 249297
  note: "概算予算"
  breakdown:
    - { label: "ホテル代", amount: 161940 }
    - { label: "割引", amount: -30000 }   # 負数は別色（緑）で描画
```

### バリデーション（`make test` / build 時）

- `meta.title` 欠落、`sections` 空 → エラー
- `type` が許可外、`cost`/`price`/`rating` の型不一致 → エラー
- 空 `items` のセクション → エラー（壊れた表示を防ぐ）
- `summary.total` ≠ 内訳合計 → エラー（計算ミス検知）

---

## 機能

**必須機能（実装済み）**
- レスポンシブ（モバイルファースト）／種別アイコン（インライン SVG）
- 固定ナビ＋スクロール進捗バー
- カード強調（宿泊・高評価アイテム）
- 集計の横棒グラフ（割引は別色）
- 「PDF・印刷」ボタン（`window.print()`）
- スクロール出現演出（IntersectionObserver、`prefers-reduced-motion` 尊重）
- アイテムをタップで「訪問済み」チェック＋ `localStorage` 保存（try/catch でガードし、保存不可環境でもメモリ動作）
- 目次ジャンプ／ルート概要

**やらなくてよい（今回スコープ外・必要なら追加）**
- 多言語化・QRコード・ランタイムのテーマ切替 UI（テーマはビルド時に `theme:` で選択）

---

## 印刷 / PDF 忠実化のポイント（`@media print`）

- `print-color-adjust: exact` を全要素に強制 → ブラウザの「背景のグラフィック」OFF でも色が出る
- 出現演出（初期透明）と集計バー幅を**確定描画**（`opacity:1 / transform:none / width:var(--w)`）
- `break-inside: avoid` でカード・アイテムの分断を防止、見出しの孤立を防ぐ
- 操作系（ナビ・進捗・ボタン = `.no-print`）を非表示
- グラデーション文字は**単色フォールバック**を適用して確実に視認
- `@page { size: A4 }`、`color-scheme: light` で端末のダークモード強制（forced dark）でも反転しない

> ブラウザ手動で PDF 化する場合は「**背景のグラフィック**」を必ず ON にしてください（Playwright 経由なら自動）。

---

## デプロイ（GitHub Pages / Cloudflare Pages）

**A. 自動（推奨）** — 同梱の `.github/workflows/pages.yml`
`main` に push すると Actions が `python scripts/build.py` を実行し Pages へデプロイ。
リポジトリの **Settings → Pages → Build and deployment → Source: GitHub Actions** を選択しておく。

**B. 手動** — ルートの `index.html` をそのまま配信
`make build` で `./index.html` が更新される。Pages の Source を「Deploy from a branch（/root）」にすれば push だけで公開。

**Cloudflare Pages**：ビルドコマンド `pip install -r requirements.txt && python scripts/build.py data/shikoku.yaml dist/index.html`、出力ディレクトリ `dist`。

---

## 別ドキュメントを量産するフロー

1. `data/your.yaml` を作成（上のスキーマに沿う。`sample.json` でも可）
2. `python scripts/build.py data/your.yaml dist/your.html`
3. 必要なら `python scripts/to_pdf.py dist/your.html dist/your.pdf`

テーマは `theme: onsen|ocean|mono`。新テーマは `src/theme.py` の `THEMES` に1エントリ追加するだけ。

---

## エッジケースの扱い

| ケース | 挙動 |
|---|---|
| 必須欠落・型不一致 | ビルド前に `ValidationError`（全件表示）で停止 |
| 空セクション | 検証エラー（意図的に空にしたい場合はダミー item を 1 件） |
| 極端な長文 | `word-break` と折返しで崩れない。カードは grid で 1/2 カラム自動 |
| Web フォント未読込 | システムフォント（Hiragino/Yu Gothic/Meiryo）へ自動フォールバック |
| `localStorage` 不可（プライベートブラウズ等） | try/catch でメモリ動作に切替（チェックは保持されないが UI は動く） |
| 端末のダークモード強制 | `color-scheme: light` で反転を抑止 |

---

## テスト

```bash
make test     # = pytest
```

- `test_schema.py`：検証ロジック（欠落・型・合計整合・空セクション）
- `test_generate.py`：HTML スナップショット（主要要素の存在・自己完結性・autoescape）
- `test_pdf.py`：Playwright で PDF 生成・ボタン非表示（Chromium 未導入なら自動スキップ）

---

## 段階的な進め方（このリポジトリの構築順）

1. **フェーズ1（MVP）**：データ1種＋単一 HTML（hero＋タイムライン＋集計）
2. **フェーズ2**：印刷/PDF 忠実化＋PDF 生成スクリプト
3. **フェーズ3**：チェック/進捗/出現演出/テーマ等の UI ＋ `index.html` 公開
4. **フェーズ4**：スキーマ汎用化・バリデーション・テスト・README
