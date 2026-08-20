---
name: figma-integration
description: Figma 連携の入口ガイド。公式 Figma MCP（mcp__claude_ai_Figma__*）を使った design→code（get_design_context / get_screenshot / get_metadata）、code→design（use_figma）、Code Connect マッピング、design tokens / variables、FigJam 図、および Figma Slides（プレゼン資料）作成の使い分けと、サーバ同梱 /figma-* skill のロード順を示す。Figma URL を渡された時・UI / デザインシステム構築時・スライド作成時に発火する。Use when implementing a Figma design as code, pushing code into Figma, building a design system, or creating Figma Slides.
---

# Figma 連携 (figma-integration)

このスキルは公式 Figma MCP サーバ（`mcp__claude_ai_Figma__*`）を使う際の **入口ガイドとプロジェクト規約** を提供する。
個々の操作の詳細フローはサーバ同梱の `/figma-*` skill が持つため、本スキルは「どの用途でどの tool / skill を使うか」の
振り分けと、UI 設計・デザインシステム・**Figma Slides** 作成の規約に集中する（詳細手順を重複させない）。

## いつ発火させるか

- ユーザーが figma.com の URL を渡した
- UI / 画面 / コンポーネント / モックを作る・実装する（design→code または code→design）
- デザインシステム / design tokens / コンポーネントライブラリを構築・同期する
- FigJam で図・ダイアグラムを作る
- **Figma Slides でプレゼン資料・スライドを作る**

## 前提（接続）

- `.mcp.json` に `figma`（`https://mcp.figma.com/mcp`, http transport）登録済み。初回接続時に OAuth 認証
  （`whoami` で接続確認）
- 代替: Figma Desktop の Dev Mode ローカル MCP（`http://127.0.0.1:3845/sse`）。デスクトップアプリ起動が前提
- ツール名前空間: `.mcp.json` の server 名が `figma` のため tool は `mcp__figma__*`。claude.ai の Figma コネクタ接続時は `mcp__claude_ai_Figma__*`。`figma-reviewer` subagent は両方を許可済み
- URL パース: `figma.com/design/:fileKey/...?node-id=:nodeId` から fileKey / nodeId を抽出し、
  nodeId は `-` を `:` に変換して使う

## サーバ同梱 skill のロード順（重要）

操作の前に対応する `/figma-*` skill を **先にロード** する。特に以下は MANDATORY:

- `use_figma` を呼ぶ前 → **`/figma-use`**（必須）
- `generate_diagram` を呼ぶ前 → **`/figma-generate-diagram`**（必須）
- design→Figma 変換 → `/figma-generate-design`
- code からデザインシステム構築 → `/figma-generate-library`
- Code Connect マッピング → `/figma-code-connect`
- FigJam フロー → `/figma-use-figjam`

## 用途別の振り分け

### A. design→code（Figma から実装）
1. `get_metadata` でノード構造を把握 → `get_screenshot` で見た目確認
2. `get_design_context` で実装に必要なコンテキスト取得
3. `get_variable_defs` で design tokens（色・spacing・typography）を取得しコードのトークンへマップ
4. 既存コンポーネントへのマッピングは `get_code_connect_map` を確認

### B. code→design（コードを Figma へ）
1. `/figma-use` をロード（必須）
2. `use_figma` で画面 / コンポーネントを Figma に生成・更新
3. 既存デザインシステムがあれば `search_design_system` / `get_libraries` で整合を取る

### C. Code Connect（component ↔ コード対応）
- `get_code_connect_map` で現状確認 → `add_code_connect_map` / `send_code_connect_mappings` で対応付け
- 提案は `get_code_connect_suggestions` を活用

### D. デザインシステム / tokens
- `get_variable_defs` / `search_design_system` / `get_libraries` でトークン・ライブラリを取得・統一

### E. Figma Slides（プレゼン資料作成）
- `/figma-use` をロードのうえ `use_figma` でスライド（Figma Slides）を生成・編集する
- 既定のスライド構成テンプレ（特に指定がなければ）:
  1. タイトル（演題・発表者・日付）
  2. アジェンダ / 概要
  3. 背景・課題
  4. 提案・本論（1 スライド 1 メッセージ）
  5. 結果・デモ
  6. まとめ・ネクストステップ
- 1 スライド 1 主題、箇条書きは 6 行以内を目安。design tokens / ブランドカラーがあれば `get_variable_defs` で取得し統一
- 図解が要るときは FigJam（`/figma-use-figjam`）や `generate_diagram`（要 `/figma-generate-diagram`）を併用

## 連携

- デザイン / スライドのレビュー: `figma-reviewer` subagent（read 専用で整合・tokens・a11y・スライド構成を点検）
- UI コード生成: `frontend-design` plugin（AI っぽくない実装コード）
- プロファイル: `design`（UI/UX・デザインシステム・スライド）

## 注意

- `use_figma` / `generate_diagram` は対応 skill を **先にロード** してから呼ぶ
- Figma への書き込み（生成・更新）は外向き操作。既存ファイルを上書きする前に対象を確認する
- 秘匿情報は `.env` / `.claude/settings.local.json` へ。`.mcp.json` にはサーバ定義のみ置く
