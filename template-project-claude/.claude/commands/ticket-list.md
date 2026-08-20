---
description: tasks/ 配下の未完了チケットを一覧表示する。frontmatter から id / title / status / category / estimated_minutes / depends_on を抽出し、表形式で出力。完了済み (tasks/_done/) は件数のみ集計。
allowed-tools: Read, Glob, Bash(ls:*), Bash(python3:*)
argument-hint: "[--all] (完了チケットも含む) / [--status=todo|in-progress|blocked] (絞り込み)"
profile_relevance:
  - meta
---

# /ticket-list

`tasks/T-*.md` を frontmatter ベースでスキャンし、未完了チケットを **表形式で一覧表示** する。`/ticket-create` / `/ticket-run` のペアとして機能する閲覧コマンド。

## 動作

| ステップ | 入力 | 処理 |
|---|---|---|
| 1 | `tasks/T-*.md` (除外: `tasks/_done/`, `tasks/_template.md`, `tasks/_*`) | Glob で列挙 |
| 2 | 各ファイルの frontmatter | Read + 正規表現 / YAML parse |
| 3 | status / category で集計 | 引数フィルタを適用 |
| 4 | `tasks/_done/T-*.md` | 件数のみ集計 |
| 5 | 表形式で出力 | id / status / category / title / estimated / deps |

## 引数

- 引数なし: 未完了（`status != done`）のみ表示
- `--all`: 完了済みも含む
- `--status=<value>`: 指定 status のみ（todo / in-progress / blocked / done）

## 実行

以下の Python スクリプトを直接実行（小規模ロジックなのでインライン）:

```bash
python3 << 'EOF'
import re
from pathlib import Path

TASKS = Path("tasks")
DONE = TASKS / "_done"

def parse_frontmatter(text):
    m = re.match(r'---\n(.*?)\n---', text, re.DOTALL)
    if not m:
        return {}
    out = {}
    for line in m.group(1).splitlines():
        if ':' in line and not line.lstrip().startswith('#'):
            key, _, val = line.partition(':')
            out[key.strip()] = val.strip()
    return out

def collect(root):
    out = []
    if not root.exists():
        return out
    for f in sorted(root.glob("T-*.md")):
        if f.name.startswith("_"):
            continue
        fm = parse_frontmatter(f.read_text(encoding="utf-8"))
        out.append({
            "path": str(f),
            "id": fm.get("id", f.stem.split("-", 2)[0:2] and "-".join(f.stem.split("-")[:2])),
            "title": fm.get("title", "(no title)").strip('"\''),
            "status": fm.get("status", "?"),
            "category": fm.get("category", "-"),
            "estimated": fm.get("estimated_minutes", "-"),
            "deps": fm.get("depends_on", "[]").strip("[]") or "-",
        })
    return out

active = collect(TASKS)
done = collect(DONE)

print(f"# Tickets ({len(active)} active, {len(done)} done)\n")
if active:
    print(f"| ID | Status | Category | Est | Deps | Title |")
    print(f"|---|---|---|---|---|---|")
    for t in active:
        print(f"| {t['id']} | {t['status']} | {t['category']} | {t['estimated']} | {t['deps']} | {t['title']} |")
else:
    print("_未完了チケットはありません。_\n")

print(f"\n## 完了済み (tasks/_done/): {len(done)} 件")
if done:
    print("\n直近 5 件:")
    for t in done[-5:]:
        print(f"- {t['id']}: {t['title']}")
EOF
```

引数フィルタ (`--status=<value>` / `--all`) は Claude が `$ARGUMENTS` を解釈してロジックを切り替える（上記スクリプトに条件分岐を追加）。

## 出力例

```
# Tickets (3 active, 11 done)

| ID    | Status      | Category    | Est | Deps           | Title                                |
|-------|-------------|-------------|-----|----------------|--------------------------------------|
| T-011 | in-progress | command     | 60  | -              | Japanese writing set                 |
| T-012 | todo        | command     | 45  | T-011          | English writing set                  |
| T-013 | todo        | command     | 45  | -              | Template ops commands                |

## 完了済み (tasks/_done/): 11 件

直近 5 件:
- T-007: enabledplugins-reset
- T-008: update-init-project
- T-009: mcp-json-cleanup
- T-010: decisions
- T-010: prune-skills
```

## いつ使うか

- セッション開始時に「今どこに居るか」を把握
- 並行作業中に複数チケットの状況を一覧したい
- `depends_on` で blocked 状態のチケットを発見
- 完了したチケット数を週次振り返りで集計

## 注意

- frontmatter の YAML を簡易 parse（`key: value` ベース）。複雑な構造（ネスト、配列の複数行）には対応しない
- `depends_on: [T-001, T-002]` のような列挙は `T-001, T-002` 形式で表示
- `tasks/_template.md` や `tasks/_*` で始まるファイルは除外
- 完了済みの全件一覧が必要なら `--all` を付ける（古いチケットほど下に表示）
