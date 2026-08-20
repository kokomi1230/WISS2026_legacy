---
name: unity-development
description: Unity Editor を MCP（unityMCP / AnkleBreaker unity-mcp, 268 tools）経由で操作する際のワークフロー規約を Claude に適用させる。C# スクリプトは unity_script_create→unity_get_compilation_errors でコンパイル確認してから新型を使用、新規 scene は Camera + Directional Light を必須、関連 mutation は unity_execute_code でまとめ、パスは Assets/ 相対・forward slash、変更前に unity_editor_state など read 系で現状を確認。Unity / VR / AR / 物理シミュレーションのシーン構築・スクリプト編集・ビルド・デバッグ時に発火する。Use when building or editing Unity scenes, scripts, prefabs, or running Unity via the MCP bridge.
---

# Unity 開発スタイル (unity-development)

このスキルは Unity Editor を MCP ブリッジ（`unityMCP` = AnkleBreaker unity-mcp, `mcp__unityMCP__unity_*`, 268 tools）経由で
操作するときの **強制適用ワークフロー** を提供する。ゲーム・VR/AR・物理シミュレーションのシーン構築、C# スクリプト編集、
prefab/asset 管理、ビルド、デバッグを安全かつ高速に進めるための規約。

## いつ発火させるか

- Unity の scene / GameObject / component を作成・編集する
- C# (MonoBehaviour / ScriptableObject / Editor 拡張) を Unity プロジェクトに追加・修正する
- prefab / material / texture / shader / animation など asset を扱う
- play mode・physics・profiler・build を操作する
- 「Unity で〜」「シーンに〜」「VR / 物理シミュレーションを〜」と明示されたとき

## 前提（接続）

- Unity 側に **MCP for Unity プラグイン（AnkleBreaker `unity-mcp-plugin`, UPM Git URL）** を導入し Editor を起動しておく
  （HTTP ブリッジ既定 port `7890`）
- `.mcp.json` に `unityMCP`（`npx -y anklebreaker-unity-mcp@latest`, env `UNITY_HUB_PATH` / `UNITY_BRIDGE_PORT` / `UNITY_BRIDGE_HOST`）
  が登録済み
- 複数 Unity インスタンス接続時は `unity_list_instances` で確認し `unity_select_instance` で固定する
- Editor 未起動・ブリッジ未接続の疑いがあれば `unity_editor_ping` で疎通を先に確認する
- **ツールはティア制**: コア約 79 tools が `mcp__unityMCP__unity_*` として直接公開され、残り（高度な terrain / shadergraph / amplify / mppm / uma など）は **`unity_advanced_tool` ゲートウェイ経由**で呼び出す。直接見当たらないツールはまず `unity_advanced_tool` で探す

## 基本理念

**read 系で読み、mutation 系で書く。変更前に必ず現状を確認する。** 状態取得（`unity_editor_state` / `unity_project_info` /
`unity_get_project_context` / `unity_scene_info`）を先に行い、その上で mutation（`unity_*_create` / `_set_*` / `_update` 系）を実行する。

## 強制ルール

### 1. スクリプト編集はコンパイル確認とセット
- `unity_script_create` / `unity_script_update` で C# を作成・変更したら、**必ず** `unity_get_compilation_errors`
  （加えて `unity_console_log` の Error/Warning フィルタ）でコンパイル結果を確認する
- `unity_editor_state` の `isCompiling` が false になるまでポーリングし、domain reload 完了を待つ
- **コンパイル成功後にのみ** 新しい型・component を他の操作で参照する（未コンパイルの型を使うと失敗する）

### 2. 新規シーンには Camera + Directional Light を必ず置く
- `unity_scene_new` は **既定で Main Camera + Directional Light を含むシーン**を生成する（説明文の "empty" とは異なる）。作成直後に `unity_scene_hierarchy` で構成を確認し、**重複追加を避ける**。欠けていれば `unity_gameobject_create`（名前を "Main Camera" / "Directional Light" にすると Camera / Light component が自動付与される）で補う
- scene の open / query は `unity_scene_open` / `unity_scene_info` / `unity_scene_hierarchy`。`unity_scene_new` 直後の無題シーンは `unity_scene_save` でパス指定保存できない（保存先未確定で `success:false`）。永続化が必要なら先に Editor 側で名前を付けるか、保存対象の既存 scene を `unity_scene_open` してから作業する

### 3. 再利用は prefab 化
- 繰り返し使う GameObject は `unity_asset_create_prefab` で prefab を作成し、`unity_prefab_*`（add/remove component・variant・override）で編集する
- 生成物は使い回しを前提に `Assets/` 配下へ整理して配置する

### 4. 関連する複数操作はまとめる
- AnkleBreaker には CoplayDev の汎用 `batch_execute` 相当が無い。関連する複数の処理は **`unity_execute_code`（C# を Editor で直接実行）** でまとめて往復を削減する
- **ただし `unity_execute_code` は Roslyn（Microsoft.CodeAnalysis）に依存**し、Roslyn 非搭載の Unity ビルドでは `"Roslyn ... is not available"` エラーで使えない。その場合は `unity_gameobject_*` / `unity_component_*` など個別ツールで代替する
- component の参照配線は `unity_component_batch_wire` で一括する

### 5. パス規約
- パスは特記なき限り **`Assets/` 相対**、区切りは **forward slash (`/`)**（クロスプラットフォーム互換）

### 6. play mode / physics / build
- play 開始・停止・状態取得は `unity_play_mode`
- 物理は `unity_physics_*`（raycast / overlap / set_gravity / set_collision_layer / collision_matrix）と `unity_settings_physics`、
  プロファイリングは `unity_profiler_*` / `unity_memory_*`、ビルドは `unity_build`

## 推奨ワークフロー

### A. シーン構築
1. `unity_editor_state` / `unity_scene_info`（query）で現状把握
2. `unity_scene_new` で scene 作成 → `unity_gameobject_create` で Camera + Directional Light を配置
3. `unity_gameobject_*` / `unity_component_*` で構成、再利用物は `unity_asset_create_prefab` で prefab 化
4. `unity_play_mode` で play して挙動確認 → `unity_console_log` でエラー確認

### B. スクリプト追加
1. `unity_script_create` で C# 追加（`Assets/` 相対パス）
2. `unity_get_compilation_errors` + `unity_editor_state.isCompiling` でコンパイル成功を確認
3. 成功後に `unity_component_add` で GameObject へアタッチ
4. 失敗時は `unity-debugger` subagent に診断を依頼

### C. VR / 物理シミュレーション
- `unity_physics_*` / `unity_settings_physics` でシミュレーション条件を設定、`unity_profiler_*` / `unity_memory_*` で性能計測
- shader は `unity_shadergraph_*` / `unity_amplify_*`、地形は `unity_terrain_*`、ナビは `unity_navmesh_*`、
  マルチプレイ検証は `unity_mppm_*` を利用

## 主要ツール早見（AnkleBreaker `unity_*`）

| 目的 | tool |
| --- | --- |
| 疎通・状態 | `unity_editor_ping`, `unity_editor_state`, `unity_project_info`, `unity_get_project_context` |
| インスタンス | `unity_list_instances`, `unity_select_instance` |
| コンソール | `unity_console_log`, `unity_console_clear`, `unity_get_compilation_errors` |
| シーン | `unity_scene_info`, `unity_scene_open`, `unity_scene_save`, `unity_scene_new`, `unity_scene_hierarchy`, `unity_scene_stats` |
| GameObject | `unity_gameobject_create`/`_delete`/`_info`/`_duplicate`/`_reparent`/`_set_active`/`_set_transform` |
| Component | `unity_component_add`/`_remove`/`_get_properties`/`_set_property`/`_set_reference`/`_batch_wire` |
| 検索 | `unity_search_by_name`/`_component`/`_layer`/`_tag`/`_shader`, `unity_search_assets`, `unity_search_missing_references` |
| スクリプト | `unity_script_create`, `unity_script_read`, `unity_script_update`, `unity_execute_code` |
| アセット/prefab | `unity_asset_list`/`_import`/`_create_prefab`/`_instantiate_prefab`, `unity_prefab_*` |
| マテリアル/描画 | `unity_material_create`, `unity_renderer_set_material`, `unity_texture_*`, `unity_shader_*`, `unity_shadergraph_*`, `unity_amplify_*` |
| 実行・物理 | `unity_play_mode`, `unity_physics_*`, `unity_settings_physics`, `unity_profiler_*`, `unity_memory_*`, `unity_build` |
| その他領域 | `unity_terrain_*`, `unity_navmesh_*`, `unity_particle_*`, `unity_lighting_*`, `unity_ui_*`, `unity_vfx_*`, `unity_mppm_*`, `unity_uma_*`, `unity_testing_*` |

## 連携

- デバッグ: `unity-debugger` subagent（read 専用でコンパイルエラー・例外・シーン不整合を診断）
- MCP 候補比較: `docs/CATALOG.md`（anklebreaker-unity-mcp[標準] / coplay-unity-mcp / ivanmurzak-unity-mcp）
- プロファイル: `system-dev`（開発）/ `research`（VR・物理シミュレーション研究）

## 注意

- 未コンパイルの型を参照しない（必ず `unity_get_compilation_errors` でコンパイル成功を確認してから使う）
- 破壊的操作（削除・上書き）の前に read 系で対象の現状を確認する
- 取り消しは `unity_undo` / `unity_redo` / `unity_undo_history` を活用する
- プロジェクト固有規約が CLAUDE.md にある場合はそちらを優先する
