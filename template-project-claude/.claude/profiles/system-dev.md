---
name: system-dev
description: フロント / バック / フルスタックの本番志向システム開発プロファイル。要件 → 計画 → TDD → レビュー → コミットを回し、LSP・E2E・横断検索・セキュリティスキャンを統合する。
enabled_plugins:
  - superpowers@claude-plugins-official
  - feature-dev@claude-plugins-official
  - code-review@claude-plugins-official
  - commit-commands@claude-plugins-official
  - context7@claude-plugins-official
  - typescript-lsp@claude-plugins-official
  - pyright-lsp@claude-plugins-official
  - playwright@claude-plugins-official
  - sourcegraph@claude-plugins-official
  - chrome-devtools-mcp@claude-plugins-official
  - security-guidance@claude-plugins-official
enabled_mcp:
  - unityMCP
scaffold:
  - src
  - tests
  - e2e
  - public
  - docs
---

# System Dev — システム開発プロファイル

## 概要
このプロジェクトは**システム開発**用途です（Web / API / SPA / バックエンド / フルスタック）。型安全・テスト網羅性・セキュリティを意識しつつ、要件定義から PR までを TDD ベースで進めます。general 軸に LSP（TS / Py）・E2E（Playwright）・ランタイムデバッグ（chrome-devtools）・横断検索（Sourcegraph）・セキュリティスキャン（OWASP Top 10）を加えます。

## 推奨プラグイン
### 必須（軸 5 個）
- `superpowers@claude-plugins-official` — TDD / systematic-debugging / writing-plans
- `feature-dev@claude-plugins-official` — 要件 → 計画 → 実装 → テスト → PR
- `code-review@claude-plugins-official` — 差分レビュー
- `commit-commands@claude-plugins-official` — Git ワークフロー自動化
- `context7@claude-plugins-official` — リアルタイム API ドキュメント検索

### 特化追加（system-dev 専用 6 個）
- `typescript-lsp@claude-plugins-official` — TypeScript 型検査 / 参照ジャンプ
- `pyright-lsp@claude-plugins-official` — Python 型推論 / 参照解析
- `playwright@claude-plugins-official` — 実ブラウザ操作・スクリーンショット・E2E テスト
- `sourcegraph@claude-plugins-official` — コードベース横断検索・参照トレース・リファクタ影響分析
- `chrome-devtools-mcp@claude-plugins-official` — ネットワーク・コンソール・ライブページデバッグ
- `security-guidance@claude-plugins-official` — OWASP Top 10 / シークレット検出 / インジェクション診断

### MCP（`.mcp.json` で管理 / `enabled_plugins` には含めない）
- **Unity MCP（AnkleBreaker, 標準）** — Unity Editor を MCP 経由で操作（scene / script / prefab / asset / physics / shader / terrain / navmesh / animation / build, 268 tools）。ゲーム / VR/AR / 物理シミュレーション開発に。Node.js 18+ が前提。
  ```bash
  claude mcp add unityMCP -- npx -y anklebreaker-unity-mcp@latest
  ```
  env に `UNITY_HUB_PATH` / `UNITY_BRIDGE_PORT=7890` / `UNITY_BRIDGE_HOST=127.0.0.1` を設定。Unity 側に AnkleBreaker
  `unity-mcp-plugin`（UPM Git URL: `https://github.com/AnkleBreaker-Studio/unity-mcp-plugin.git`）を導入し Editor を起動しておく。
  軽量な 30 tools 構成が要れば `coplay-unity-mcp`（uvx）への切替を検討（候補比較は `docs/CATALOG.md`）

## 一括インストール
```bash
/plugin install superpowers@claude-plugins-official
/plugin install feature-dev@claude-plugins-official
/plugin install code-review@claude-plugins-official
/plugin install commit-commands@claude-plugins-official
/plugin install context7@claude-plugins-official
/plugin install typescript-lsp@claude-plugins-official
/plugin install pyright-lsp@claude-plugins-official
/plugin install playwright@claude-plugins-official
/plugin install sourcegraph@claude-plugins-official
/plugin install chrome-devtools-mcp@claude-plugins-official
/plugin install security-guidance@claude-plugins-official
```

## 主要ワークフロー
### ワークフロー 1: 要件 → 計画 → TDD → レビュー → コミット
1. `feature-dev` で要件整理 → Plan Mode で計画固め
2. `superpowers` の test-driven-development で失敗テスト → 実装 → 緑化
3. 型は `typescript-lsp` / `pyright-lsp` で随時確認、API 仕様は `context7` で照会
4. フロント変更は `playwright` で E2E、`chrome-devtools` でランタイム確認
5. 大規模影響変更は `sourcegraph` で呼び出し元を一括把握
6. `security-guidance` で OWASP Top 10・シークレット混入をスキャン
7. `code-review` → `commit-commands` で PR 作成

### ワークフロー 2: Unity 開発（ゲーム / VR/AR / 物理シミュレーション）
1. `.mcp.json` の `unityMCP` 接続を確認（Unity Editor + AnkleBreaker `unity-mcp-plugin` 起動、`unity_editor_ping` で疎通確認）
2. `unity-development` skill の規約に従いシーン構築・スクリプト追加（C# は `unity_get_compilation_errors` でコンパイル成功を確認してから型を使用）
3. エラー時は `unity-debugger` subagent で原因診断 → メインで修正
4. `code-review` → `commit-commands` でコミット

## 主要 subagent
- `code-reviewer` — 差分の設計・可読性・セキュリティ・テスト網羅性レビュー
- `debugger` — ログ・スタックトレースから原因特定→修正パッチ
- `planner` — 大規模・不確実な変更の前段プラン作成（書込みなし）
- `unity-debugger` — Unity のコンパイルエラー・例外・シーン不整合を read 専用で診断

## 主要 skill
- `unity-development` — Unity MCP 操作のワークフロー規約（scene / script / prefab / physics / play mode）

## 行動指針
- 既存パターン・命名規則を踏襲、新規ファイルより既存編集を優先
- 型安全重視（TS の `any` 禁止、Python は型ヒント付与）
- 変更箇所に最低 1 つのテストを伴わせる
- セキュリティ・パフォーマンスを意識（OWASP Top 10 / N+1 / レンダーブロッキング等）
- フィーチャーブランチで作業、main 直コミット禁止
- 完了前に型チェック（`tsc --noEmit` / `pyright`）と関連テストを必ず通す

## 並列ワークフロー
- 独立機能を並行開発する場合は `git worktree add ../<repo>-feat-x feat-x` で worktree 分離
- 各 worktree で別 Claude セッションを立て、`code-reviewer` subagent でクロスレビュー
