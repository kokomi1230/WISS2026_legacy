<!-- PROFILE: design -->
このプロジェクトは**デザイン**の用途です（UI・グラフィック・ブランディング・アート）。

## 行動指針
- ブランドガイドラインがあれば必ず参照。色・フォント・余白を統一。
- アクセシビリティ（コントラスト比、キーボード操作、スクリーンリーダー）を考慮。
- 出力は閲覧用 HTML/SVG/PNG を含める。
- バリエーション 3 案を出す習慣（A/B/C プラン）。
- フィードバックループを意識（早く・低品質で → 改善）。

## 主要スキル（プラグイン非収録のローカルツールのみ残置）
- `pptx` — プレゼンテーション
- `image-generator` — Nano Banana 2 CLI（Gemini 3.1）で画像生成
- `local-image-gen` — ローカル Gemini/GPT image API でオフライン生成
- `image-optimizer` — 画像最適化
- `awesome-design` — 70+ DESIGN.md カタログ（参照資料）

## プラグインで代替される機能
- UI デザイン・Web 表現・生成アート・キャンバス・テーマ・Slack GIF → `frontend-design@claude-plugins-official`
- ブランドガイドライン → `brand-voice@knowledge-work-plugins`
- 3+ 案並列比較 → `superpowers@claude-plugins-official` (dispatching-parallel-agents)

## 主要 subagent
- `planner` — デザインプラン作成（書込みなし）

## 推奨ディレクトリ構造
```
assets/         # 画像・SVG・フォント
mockups/        # モックアップ・ワイヤフレーム
brand/          # ブランドガイドライン・カラーパレット
output/         # 最終納品物
```

## 推奨外部統合
- `figma@claude-plugins-official` — Figma 連携

## 検証習慣（運用 Tips Tip 2 / 13）
- 出力 HTML/SVG は **ブラウザでスクリーンショット** を撮って提示（`playwright@claude-plugins-official` / `chrome-devtools@claude-plugins-official` プラグイン）
- バリエーション 3 案は **同一画面サイズ・同一視点** で並べて比較できるよう出力
- アクセシビリティ（コントラスト比、フォーカス順）は実環境で確認、推測しない
