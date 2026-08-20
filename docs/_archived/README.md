# 退避済みドキュメント

役目を終えた資料の置き場。`.claude/{skills,agents,commands,profiles}/_archived/` と同じ規約で、削除ではなく退避している（当時の判断根拠を辿れるようにするため）。**現行の運用でこれらを参照しない。**

| ファイル | 退避理由 | 現行の置き換え先 |
|---|---|---|
| `INSTALL_PLAN.md` | プラグインの手動 install 手順を列挙した資料。本文自身が「一括導入は `setup-plugins.sh` を正とする」と述べており、マニフェスト方式へ移行して不要になった | `.claude/plugins-user-scope.json` + `.claude/scripts/setup-plugins.sh` |
| `PLUGIN_AND_SKILL_CATALOG.md` | 旧 2 資料（プラグイン 36 選 / スキル 72 選）の統合版。統合カタログへ一本化して被参照 0 になった | `docs/CATALOG.md`（source of truth）と `docs/CATALOG.html` |
| `STANDALONE_SKILLS.md` | 72 スキルの導入区分表。`INSTALL_PLAN.md` からのみ参照されており、同時に役目を終えた | `docs/CATALOG.md` の `kind: skill` エントリ |

`/doctor` のリンクチェックは `_archived/` を走査対象から外している。
