# Claude Code ベストプラクティス（統合版）

> 本ドキュメントは旧 docs/ 配下の以下 3 件を統合したもの。元ファイルの章タイトル・著者注釈は原文のまま保持し、見出しレベルのみ降格（H1 → H2 等）して章間構造を整えている。
>
> - `CLAUDE_CODE_PRACTICE.md`（松尾研究所による実践ガイド）
> - `CLAUDE_CODE_BORIS_30TIPS.md`（Claude Code 開発者 Boris Cherny の 30 Tips）
> - `CLAUDE_CODE_TOKEN_SAVING_GUIDE.md`（Miles Deutscher 流トークン節約ガイド）

## 目次

- [PART 1: 並列開発と Markdown 運用（松尾研究所）](#part-1-並列開発と-markdown-運用松尾研究所)
- [PART 2: Boris Cherny の 30 Tips](#part-2-boris-cherny-の-30-tips)
- [PART 3: トークン節約ガイド（Miles Deutscher）](#part-3-トークン節約ガイドmiles-deutscher)

---

# PART 1: 並列開発と Markdown 運用（松尾研究所）

> **原資料**: `docs/CLAUDE_CODE_PRACTICE.md`

## Claude Code 中心のAIコーディング実務知見まとめ

出典: [AIコーディング前提の開発プロセスを仕組み化（Zenn / 松尾研究所 中川氏）](https://zenn.dev/mkj/articles/868e0723efa060)

### 概要

松尾研究所での実務において、Claude Codeを「補助」ではなく開発プロセスの**中核**として運用するための知見をまとめた記事。小規模体制で開発速度と品質を両立するために、以下の5つを"仕組み"として構築している。

1. 並列化
2. プロンプト運用
3. レビュー自動ループ
4. ナレッジ一元化
5. インストラクション（Skills）

### 開発対象（参考）

- フロントエンド: React + Vite + TypeScript
- バックエンド: FastAPI, 非同期処理ワーカー, イベント駆動関数
- IaC: Terraform
- E2Eテスト: Playwright

---

### 1) 並列開発: git worktreeで「モジュールごとに別窓」を作る

`git worktree` を使って複数の作業ディレクトリを常設し、モジュール単位でAIとの会話（コンテキスト）を分離する。

#### ポイント

- 開発者は1人でも、git worktreeで複数ウィンドウを並列稼働
- 基本は **1モジュール = 1 Claude Code** で実装し、conflictを最小化
- ChatGPT側で外部API調査・設計の壁打ちも並走させ、調査・設計・実装を全並列化
- ChatGPTのThinkingモードは数分かかるため、待ち時間に他作業を進められる

#### トレードオフ

- コンテキストスイッチが重くなり、並列度を上げるほど思考負荷が増大

---

### 2) Markdownでタスクチケット管理（=プロンプトファイル管理）

専用ツールではなく、**Markdownファイル**を中心にタスク管理する。Claude Codeへの指示をそのままMarkdownで書き、ファイルとして渡す。

#### 運用

- 開発中に「あとでやる」を思いついたら即座にmdへメモ（= タスク化）
- 並列稼働させるため、「次にやるタスク（プロンプト）」を常にストック
- SDD（仕様駆動開発）でAI生成された仕様書はレビュー負荷が高いため、開発仕様が決まっている場合は自分でmarkdownを書く方が早い
- Claude Codeに渡すタスク量を自分でコントロールできる

---

### 3) 実装の中核: subagent + custom slash commandで「実装↔レビュー」を強制ループ

#### 運用ステップ

1. **モジュールごとに異なるsubagentを定義**
   - FastAPI用、React用、Playwright用など、技術スタックに合わせて用意
2. **subagentを呼び出すカスタムスラッシュコマンドを用意**
   - subagent呼び出しが簡単になる
3. **コマンド内で「実装subagent ↔ レビューsubagent」を交互に繰り返すよう指示**

#### メリット

- プロンプティングを「コマンド + ファイル指定」に固定
- 実装者が毎回長文指示を書かず、タスクmdに集約
- 実行のたびにオペレーションが一定化される
- 実装とレビューを自動的に交互ループでき、コード品質が向上

#### デメリット

- 実装時間が長くなる
- トークン消費が増える（上限の高いプランが必須）
- 並列開発前提なら実装時間は気にならない

---

### 4) 仕様と実装詳細の一元管理: module/README.mdを育てる

毎回会話で説明するのではなく、**参照すべき仕様を固定化**する方が強い。

#### 運用

- モジュールごとの仕様・実装詳細は `module/README.md` で一元管理
- リポジトリ全体の構成・概要は `CLAUDE.md` で管理
- 機能追加・バグ修正のたびに、README / CLAUDE.md / ユニットテストを拡充する運用を「定期実行」
- コード変更だけでなく、**コード変更に同期したドキュメント・テストの更新もAIに任せる**

---

### 5) CLAUDE.md / subagent.mdで従ってくれないことはSkillsに逃がす

#### 基本方針

- コーディング規約、パッケージ管理、ロギング方法、コメント方針などは書いておく
- Claude Codeの出力癖で不満なことは、とりあえずCLAUDE.mdに記載

#### 著者が定めた禁止事項の例（CLAUDE.md）

```
* 後方互換の名目等で、削除予定・未使用コードを残さない（残骸を検出したら削除）
* 未使用の変数・引数・関数・クラス・コメントアウト・到達不能分岐を残さない
* コメントや README に「実装した／完了」等の進捗・完了宣言を書かない
* 日付や相対時制を書かない（例：いつ実装した、どのバージョンで追加、等）
* 実装状況チェックリストやステータス表のカラムを作らない
```

#### Skillsへの逃がし方

長時間走らせるとCLAUDE.mdの指示に従わなくなることがある。そこで、**長文インストラクションに埋もれてしまう指示はClaude Skillsとして定義**する。

> Skillsは「自然言語でhookタイミングと挙動を定義できる仕組み」

##### 例: skills/quality-check/SKILL.md

```
---
name: quality-check
description: コード実装後に毎回行う品質チェック
---

実装要件に基づいて、コードを以下の観点から検証します：

## コード品質
1. 後方互換の名目等で、削除予定・未使用コードを残さない（残骸を検出したら削除）
2. 未使用の変数・引数・関数・クラス・コメントアウト・到達不能分岐を残さない

## コメント品質
1. コメントや README に「実装した／完了」等の進捗・完了宣言を書かない
2. 日付や相対時制を書かない（例：いつ実装した、どのバージョンで追加、等）
```

#### 注意

- 常にスキルを参照してくれるわけではないため、都度確認が必要

---

### まとめ

| 型 | 内容 |
|----|------|
| 並列化 | git worktreeによる並列開発 |
| プロンプト運用 | Markdown形式によるプロンプト資産化 |
| レビュー自動ループ | subagent + custom slash commandで強制ループ |
| ナレッジ一元化 | README / CLAUDE.mdで仕様・テスト・ドキュメントを固定化 |
| インストラクション | Skillsで守らせる（従わない指示の退避先） |

#### 著者の結論

- これらの工夫により、AIコーディング運用を"仕組み化"し、実案件で開発速度と品質を安定化できている
- 現時点では**ペアプロ的に張り付く運用**は依然必要
- マルチタスクの思考負荷も無視できない
- AIコーディングは「速く書く」以上に、**プロセスを固定化して品質と再現性を上げる用途で効果が出やすい**

---

### 実務に活かすチェックリスト

- [ ] git worktreeでモジュールごとに作業ディレクトリを分離しているか
- [ ] タスクをMarkdownで書き溜めているか
- [ ] モジュールごとのsubagentを定義しているか
- [ ] subagent呼び出し用のカスタムスラッシュコマンドを整備したか
- [ ] 「実装 ↔ レビュー」のループがコマンドに組み込まれているか
- [ ] CLAUDE.md / module/README.md を継続的に更新する運用ができているか
- [ ] AIが従わない指示はSkillsへ切り出しているか

---

**Sources:** [AIコーディング前提の開発プロセスを仕組み化（Zenn）](https://zenn.dev/mkj/articles/868e0723efa060)

---

# PART 2: Boris Cherny の 30 Tips

> **原資料**: `docs/CLAUDE_CODE_BORIS_30TIPS.md`

## Claude Code生みの親「Boris」が実践する30個の最強Tips完全版

> 出典: [@ClaudeCode_love on X](https://x.com/ClaudeCode_love/status/2047992961175277791)
> Claude Codeの生みの親『Boris Cherny』が「これだけは押さえとけ」と言っている運用Tipsを30個まとめた記事の内容。

---

### はじめに

Claude Codeを実戦で強くする運用Tips集。Boris Cherny（Claude Codeを作った人）のX投稿、Anthropicの公式ドキュメント、GitHubの公式リポジトリと公式Actionを中心に、2026年4月23日時点の一次情報を優先して調査・執筆されたもの。

#### よくある悩み

- Claude Codeを使っているけど、毎回同じこと指示している気がする
- 大きめの変更を任せると手戻りばかりで、結局自分で直した方が早かった
- 機能が多すぎて、結局どれから手をつければいいのか分からない
- 会話が長くなると途中から噛み合わなくなる

Claude Codeは、文脈の持たせ方、検証のさせ方、権限の決め方、並列で動かす設計、自動化、このあたりをちゃんと組んで使うと体感がガラッと変わる。

---

### まず押さえてほしい3つの原則

Claude Codeを実戦で強くする最大の要因は、突き詰めると3つしかない。

1. **Plan Modeで「調べる」と「実装する」を分けること**
2. **Claudeに自分の仕事を検証させること**
3. **並列セッションを前提に働くこと**

Borisも以下を繰り返し言っている。

- "Almost always use Plan mode"（ほぼ常にPlan mode使え）
- "give Claude a way to verify its output"（Claudeに自分の出力を検証する手段を持たせろ）
- "3〜5 git worktrees"（worktreeを3〜5本並列で）

---

### 「唯一の正解はない」という考え方

Borisは "there is no one right way to use Claude Code"（使い方に唯一の正解はない）と何度も繰り返している。その前提の上で、一番効くワークフローは以下の通り。

```
Plan Modeで調査・計画
   ↓
実装セッション
   ↓
テスト・スクリーンショット・CLIで自己検証
   ↓
PR作成
   ↓
Code Review / Ultrareview
   ↓
学びをCLAUDE.md・Hook・Skillに還元
```

---

### 30個の運用Tips

#### Tip 1：大きい変更はまずPlan Modeで分離する

調査・計画・実装を分けるだけで、誤実装と手戻りがガッと減る。Borisが何度も "Almost always use Plan mode" と言う理由。

例:

> Plan Modeで src/auth と secrets まわりを読んで。Google OAuth導入で影響するファイル、データの流れ、テストの観点を整理してから実装に入って。

Plan Modeなしでいきなり大規模変更に突っ込むと、途中でcontextが切れたり方向修正が入る。先に全体像を掴ませるだけで、そのあとの実装精度が大きく変わる。

---

#### Tip 2：Claude自身に検証させる

Borisが "single highest-leverage thing"（一番レバレッジが効くやつ）と呼んでいるもの。テスト実行、スクリーンショット確認、CLI出力のチェックをClaude本人にやらせる。

例:

> 修正したあと npm test を走らせて、全テスト通ることを確認してから完了にして。

人間がレビューする前にClaude自身が問題を見つけて直してくれる。検証コマンドが重すぎると時間を食うので、最初は最低限のスモークテストから始めるのがおすすめ。

---

#### Tip 3：3〜5本のgit worktreeを並列で回す

Borisが「最重要の生産性ブースト」と言っている並列worktree運用。

```bash
git worktree add ../repo-auth -b feat/auth
```

複数のworktreeを切って、それぞれで別のclaudeを起動する。待ち時間がほぼゼロになり、独立したタスクを同時進行できる。

最適な本数は環境次第。3〜5本が目安だが、レビューの捌ける量、CPU、頭の切り替えコストによっては、2本がちょうどいい人もいれば6本いける人もいる。自分の環境で実測するのが確実。

---

#### Tip 4：CLAUDE.mdを容赦なく編集し続ける

CLAUDE.mdはプロジェクト固有のルールブック。放置すると古くなり、Claudeが間違った前提で動き始める。

Borisの運用方針:
- "Ruthlessly edit your CLAUDE.md over time"（時間とともに容赦なく編集し続けろ）
- "Add to it when Claude makes the same mistake a second time"（同じミスを2回したら追記しろ）

逆に、いらなくなったルールは消す。膨らみすぎるとcontextを食うので、定期的に棚卸しして簡潔に保つ。

---

#### Tip 5：毎日繰り返す作業はskills化してgitにコミット

繰り返しの手順を毎回会話で説明するのは時間の無駄。`.claude/skills/deploy/SKILL.md` を作っておいて `/deploy staging` で呼べばOK。

Boris: "If you do something more than once a day, turn it into a skill or command"（1日1回以上やることはskillかcommandにしろ）、"costs almost nothing until you need it"（使うまではほぼコストかからない）。

Skillが膨らみすぎると発火タイミングが曖昧になるので、長い参考資料は分割した方が良い。

---

#### Tip 6：チーム共通設定はsettings.jsonに入れてgit管理する

プロジェクト固有の設定をバージョン管理しておけば、チーム全員が同じClaude Code体験を得られる。新メンバーのオンボーディングも速くなり、設定が誰か一人に依存する問題も防げる。

**注意:** 個人のAPIキーやトークンは絶対にコミットしない。`.gitignore`の確認を忘れずに。

---

#### Tip 7：安全な権限は事前承認、危険な領域はdenyする

`allow` / `ask` / `deny` を使い分けると、確認ダイアログ疲れが消える。

```json
{
  "allow": ["Bash(npm test *)"],
  "ask": ["Bash(git push *)"],
  "deny": ["Read(./.env)", "Read(./secrets/**)"]
}
```

Boris: "Pre-approve common permissions"（よく使う権限は事前承認しとけ）
公式Docs: "Rules are evaluated in order: deny… ask… allow"（denyから順に評価）

ワイルドカードを広げすぎると危険。`.env`やsecrets系は明示的にdenyする。

---

#### Tip 8：--add-dirで複数フォルダ・複数repoを跨がせる

モノレポの外にあるドキュメントやライブラリも見せたい場面に。

```bash
CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=1 claude --add-dir ../docs --add-dir ../shared-libs
```

環境変数を有効にしないと、追加したディレクトリのCLAUDE.mdが読み込まれないので注意。

---

#### Tip 9：subagentsを前提に役割分担する

調査・レビュー・デバッグを全部メインのcontextに突っ込むと、文脈がどんどん汚れる。Boris: "I use a few subagents regularly"（いくつかsubagentを常用してる）。各subagentは自分専用のcontext windowで動く。

code-reviewer、debugger、data-scientistなどのsubagentを用意し、descriptionをはっきり書くこと。曖昧だと自動で振り分けが起きにくく、使えるツールの制限設計も必要。

---

#### Tip 10：PostToolUse hookで整形・検査を自動化

Claudeがファイル編集するたびに、formatterやlintを自動で走らせる。

> Write a hook that runs prettier --write after every file edit.

Claudeに頼めば、hookの生成から`.claude/settings.json`への組み込みまでやってくれる。コードスタイル統一が自動化され、レビューでスタイル指摘が消える。

hookが重いとセッション全体が遅くなるので、実行時間の上限は設けておく。

---

#### Tip 11：PRコメントでCLAUDE.mdを更新する

コードだけでなく「これからのルール」もPRで一緒に変える。Boris: "tag @.claude on my coworkers' PRs to add something to the CLAUDE.md"（同僚のPRに@.claudeつけてCLAUDE.mdに追記させることがある）。

例:

> @claude この学びをCLAUDE.mdに追記して。src/billing配下の変更は必ずPlan Modeから始める。

同じ観点の指摘を次回以降減らせる。ただし局所的な事情を全体ルールにしすぎないよう、スコープは必ず明示する。

---

#### Tip 12：status lineで今の状態を常に把握する

画面下に常時表示される情報で、現在の作業状況が一目で分かる。

```
/statusline show model name, git branch, context percentage, cost
```

まずは branch、context%、cost の3つだけで十分。context切れや別branch誤操作に早く気づける。

---

#### Tip 13：Chrome拡張でフロントエンド作業を加速する

Boris: "Use the Chrome extension for frontend work"（フロントエンド作業にはChrome拡張を使え）。

ブラウザのログイン状態を共有できるので、スクリーンショット比較をClaudeに見せてUI確認をさせられる。UI崩れをClaude自身が検出してくれる。

ただしアクセシビリティや体感速度まではスクリーンショットでは測れないので、必要に応じてLighthouseやe2eテストを併用。

---

#### Tip 14：分析タスクもCLI経由でClaudeにやらせる

SQLやCLIをClaudeに使わせると、開発・分析・施策検討が同じ作業面に入る。

> Use the bq CLI to pull last 7 days conversion metrics by channel, summarize anomalies, and suggest hypotheses.

Boris: "Use Claude for data analysis"。開発者だけでなくプロダクト担当者にも効く。データ権限、PII、コストには注意。CLIの認証と出力整形は先に整えておく。

---

#### Tip 15：仕様が曖昧ならまずClaudeにインタビューさせる

公式Docs: "Let Claude interview you"。いきなり実装に入るのではなく、まずClaudeに質問させて要件を引き出す。

仕様の穴が実装前に埋まり、手戻りが圧倒的に減る。特に「何を作るか」がふわっとしてる段階で効果大。

---

#### Tip 16：CLAUDE.mdとauto memoryの役割を分ける

- **CLAUDE.md（人間が書く）**: build/test/conventions
- **auto memory（Claudeが覚える）**: ローカルな学習やデバッグ癖

auto memoryはworking tree単位で読み込み量にも上限があるので、本当に重要なルールは必ずCLAUDE.md側に残す。

---

#### Tip 17：パス別ルールとcompaction挙動を知った上で設計する

monorepoでは「全体ルール」と「局所ルール」を分ける。
- ルートのCLAUDE.md: 全体規約
- src/billing など: 局所規約

`/compact`のあとにサブディレクトリのCLAUDE.mdが読まれなくなる可能性があるので、明示的に再読込を指示する癖をつけておく。

---

#### Tip 18：文脈を積極的に管理する

公式Docs: "Manage context aggressively"（文脈は積極的に管理しろ）。

重要な運用知はCLAUDE.mdやskillへ昇格、`/compact`でcontext windowを定期的に整理、進行中タスクの要点は`/btw`で差し込む。

compactは戻せないので、重要情報は事前にCLAUDE.mdへ退避しておく。

---

#### Tip 19：/rewindとcheckpointsで「怖い変更」を試す

Claude Codeのすべての操作はcheckpointになる。`Esc`を2回、または`/rewind`を開いて、message checkpointから `code only` / `conversation only` / `both` で戻せる。

深いリファクタや代替実装を試すときに「戻せる」安心感があると、探索の幅が広がる。

**注意:** 外部副作用がある作業（DB操作、API呼び出し）はcheckpointでは戻せない。

---

#### Tip 20：MCPサーバーで外部ツールと接続する

Slack、Jira、データベース、社内APIをClaude Codeから直接操作できるようにする。ツール間の移動が激減し、全部が同じ作業面で完結する。

MCP接続先のセキュリティとアクセス権限は事前に整備。

---

#### Tip 21：非対話モード（claude -p）でスクリプト・CIに組み込む

非対話モードはClaude Codeの自動化入口。

```bash
claude -p "List all API endpoints" --output-format json
claude -p "Analyze this log file" --output-format stream-json
```

CI、pre-commit、スクリプト連携が実現する。ただし非対話だと人間の介入がないので、出力形式と許可ツールを明示し、ログは必ず残す。

---

#### Tip 22：大規模移行はclaude -pをファイル単位でfan-outする

1セッションで巨大移行を抱え込むのは無理。横に分散する。

```bash
for file in $(cat files.txt); do
  claude -p "Migrate $file..." --allowedTools "Edit,Bash(git commit *)"
done
```

200〜2000ファイル級の移行でスループット出る。いきなり全量で回さず、まず数ファイルで失敗パターンを洗い出してから全体に展開する。

---

#### Tip 23：課題管理ツールから直接実装させる

GitHub IssueやLinearのチケットをClaudeに読ませて、そのまま実装に入らせる。仕様と実装の距離が一気に縮まる。

**注意:** プロンプトインジェクションのリスクがある。外部入力を直接渡す場合は、内容を事前に検証する。

---

#### Tip 24：例外なく守らせたい規則はhooksで強制する

- **CLAUDE.md**: 「助言」
- **hooks**: 「実行」

例:
> Write a hook that blocks writes to the migrations folder.
> Write a hook that runs eslint after every file edit.

公式Docs: "zero exceptions"（例外ゼロ）、"guarantee the action happens"（その動作が確実に起こるようにする）。

Hookが増えすぎると保守が重くなるので、まず「絶対に守るべき最小集合」から始める。

---

#### Tip 25：/simplifyで最近触ったコードを並列レビューさせる

3つのreview agentが重複・品質・効率を同時にチェックし、修正までやってくれる。

```
/simplify focus on memory efficiency
```

リファクタの見落としが減って、コード品質が底上げされる。

---

#### Tip 26：GitHub Actionで @claude メンションを使う

公式のclaude-code-actionを使えば、PRやIssueで `@claude` とメンションするだけで質問回答やコード変更実装ができる。GitHub上のやりとりだけでClaude Codeの力を使えるのは、チーム運用ではかなり便利。

---

#### Tip 27：PRレビューはCode ReviewとUltrareviewを使い分ける

- **日常的**: Code Reviewを有効化
- **マージ前に深く掘りたいとき**: `/ultrareview` または `/ultrareview 1234`

Boris: "team of agents runs a deep review"（エージェント群が深いレビューを行う）、"fleet of specialized agents"（専門化したエージェント群）。

どちらも研究プレビュー要素があるので、可用性・課金・認証の制約は事前に確認。

---

#### Tip 28：決まった反復運用はRoutines化する

週次整備、APIトリガー、PR連動作業など反復作業はクラウド常駐に寄せる。

```
/schedule daily PR review at 9am
```

公式Docs: "keep working when your laptop is closed"（ラップトップを閉じていても動き続ける）。

研究プレビューで仕様が変わりうる点、GitHub triggerやAPI token管理の設計は別途必要。

---

#### Tip 29：計画が重い案件はUltraplanでクラウドに逃がす

terminalで計画を待つのではなく、ブラウザで章ごとにレビューする。

```
/ultraplan migrate the auth service from sessions to JWTs
```

terminalを塞がずに、より広い画面で計画を検討できる。研究プレビューなので、クラウド実行のコストとセキュリティは事前に検討。

---

#### Tip 30：Remote Controlでクラウドセッションを操作する

ローカルからクラウド上のClaude Codeセッションを制御する機能。研究プレビュー段階で、認証・ネットワーク・課金条件の確認が必要。

---

### まだ固まってない運用ポイント

方向性は見えているが、ベストプラクティスが確立していない領域。

- **Chrome拡張 + Lighthouse + axe + e2eテストの組み合わせ**: スクリーンショット比較がUI崩れには効く一方で、アクセシビリティや体感速度は測れない。段階的に追加しながら、どこまで自動化するか線引きが必要。
- **Stop hooksを使った「days at a time」運用**: 長時間動かした実例はあるものの、障害復旧・再開戦略・監視条件の詳細は明示されていない。まずは1〜2時間のsoak testから始めて、ログ量、停止率、再起動手順、通知条件を決めてから延長するのが現実的。

---

### どこから始めるか

#### 開発者向け（まずこの6つ）

- Tip 1: Plan Mode
- Tip 2: 自己検証
- Tip 4: CLAUDE.md更新
- Tip 7: permissions設計
- Tip 9: subagents
- Tip 18: 文脈整理

これだけでClaude Codeは「その場しのぎのチャット」から「継続的に学習する開発環境」に変わる。

#### プロダクト担当者向け

- Tip 14: 分析タスク
- Tip 15: Interview
- Tip 23: 課題管理連携
- Tip 27: レビュー
- Tip 28: Routines

CLIとMCPでデータ・課題・設計知見を同じ面に集約し、Interviewで仕様を掘って、レビューやRoutineで運用のループまで閉じる。

---

### 週次チェックリスト

- 同じミスを二度指摘していないか → していたらCLAUDE.mdに追記
- Skillやhookで吸収できる反復作業が残っていないか → あればskill化
- context window使用率が高すぎないか → /compactの習慣を見直す
- worktreeの本数は適切か → レビュー帯域とCPUに応じて調整

---

### 結論

Claude Codeを実運用で使いこなす鍵は、**「Plan → Verify → Persist → Automate」**の順に運用構成要素を一つずつ固めること。

1. **Plan Mode**で探索と実装を分離
2. テスト・スクリーンショット・CLIで**Verify**（検証）
3. 学びをCLAUDE.mdやhooksへ**Persist**（還元）
4. Routinesやfan-outで**Automate**（自動化）

この一連の流れが、Anthropic公式のagentic loop説明とBorisの運用発言の交点にある勝ち筋。

「全部盛り」で始める必要はない。まず**Tip 1・2・4**の3つだけでも、Claude Codeとの開発体験は根本から変わる。

---

### Sources

- [@ClaudeCode_love on X](https://x.com/ClaudeCode_love/status/2047992961175277791)

---

# PART 3: トークン節約ガイド（Miles Deutscher）

> **原資料**: `docs/CLAUDE_CODE_TOKEN_SAVING_GUIDE.md`

## トークン消費67%カットを実現する：ClaudeCode「エスカレート式」運用術

> 「うああ今日もClaude Codeの使用制限きた😭ケチ！💢」
> 気持ちはわかります。でも、それあなたの運用方法が悪いのかも？

### はじめに

Claude Codeを使っていて、こんな経験ありませんか？

- プロンプトの途中で突然「使用制限に達しました」と表示される
- $200/月のプランなのに数時間ごとにレート制限に引っかかる
- 制限を気にしながら使うせいで、集中力が途切れて生産性が落ちる
- 制限回避のためにプランをアップグレードすべきか毎月悩んでいる
- 重要な作業の途中で止まるから、結局別のAIに逃げてしまう

海外で67万フォロワーを持つAI活用のトップインフルエンサー **Miles Deutscher（[@milesdeutscher](https://x.com/milesdeutscher)）** が書いた記事が335万いいねの大バズ中。

彼自身も$200/月のAnthropicプランを使いながら、日常的にレート制限に引っかかっていたそう。しかし「Claudeの仕組みを根本から理解し直した」ことで、**過去3週間は一度もトークン制限に到達していない**とのこと。

元ポスト：https://x.com/milesdeutscher/status/2049618781841031551

---

### Step 1：Planning（計画と実行を完全に分離する）

Milesが最初に指摘するのは「**Claude Opusでブレストするな**」という点。

これ、やっている人かなり多いはず。アイデアが浮かんだらとりあえずOpusに投げて壁打ちする。気づいたら30分経っていて、制限に到達。心当たりありませんか？

#### Milesが発見した事実

> 「テキストチャット自体はトークンをそこまで消費しない。本当に消費するのは、コーディング・ビルド・デザインなどの実行系タスク」

つまり、**何を作るかを考えるフェーズ（計画）と、実際に作るフェーズ（実行）を明確に分けるだけで、高コストモデルの消費量が激減する**。

#### 具体的な比較例

同じファイナンス追跡アプリを作る2人の場合：

- **Person A**：計画に2分しか使わず、設計が甘いままビルド開始。結果、3回作り直し
- **Person B**：計画に20分かけて設計を固め、ビルドは1回で完了

Person Bはこのタスク単体で**約67%のトークンを節約**。金額にして$1.50の差。これが1日に何タスクもあると考えると、月単位では数十ドルの差になる。

#### Plan Modeを活用する

Claude Codeを使っている人なら、`Shift+Tab×2`で入れる「**Plan Mode**」がまさにこの思想を体現した機能です。

Plan Modeに入ると、Claudeはコードを書かずに設計・計画に集中する。つまり実行トークンを消費せずに、アーキテクチャや方針を固められる。

さらに、計画フェーズ自体も安いモデルに任せるのがMiles流。Opusで壁打ちする代わりに、**Haiku**で十分。Haikuはブレスト用途なら十分賢く、コストは桁違いに安い。

#### 実践ポイント

- アイデア出し・壁打ち・設計は**Haiku**で行う
- 設計が固まり「あとは作るだけ」になってから**Opus**に切り替える
- Claude CodeならPlan Mode（`Shift+Tab×2`）を毎回使う癖をつける
- 「考える時間」をケチるほど、「作り直す回数」が増えてトータルで損する

---

### Step 2：Chat Length（チャットの長さが全てを支配する）

**長いチャットはサイレントキラー**だとMilesは言います。これは多くの人が見落としている最大の落とし穴。

#### 仕組み

Claudeは毎回メッセージを送るたびに、そのチャット内の全コンテキストを読み直している。つまり：

- チャットが10メッセージの時：10メッセージ分のトークンを読む
- チャットが100メッセージの時：100メッセージ分のトークンを読む

チャットが長くなるほど、1メッセージあたりのコストが**雪だるま式に増えていく**。しかも問題はコストだけじゃない。古い情報が混ざることで、Claudeの**出力品質自体が劣化する**。関係ない過去の文脈に引っ張られて、的外れな回答が増える。

#### 解決策1：Projectsを活用する

繰り返し同じ種類のタスクをやるなら、1つの長大なチャットではなく、**Projectの中に複数のサブチャットを作る**。

Miles自身はX執筆用のProjectを持っていて、新しい記事を書くたびに新規チャットを開いている。Projectの設定（Instructions）は全チャットで共有されるから、毎回「自分はこういう人で、こういうスタイルで書いて」と説明し直す必要がない。

さらに賢いのが、**Project Instructionsにこの1文を入れておくこと**：

```
Be cognisant of the fact I'm trying to save account usage. 
Be concise in your answers, and when appropriate, advise me on when I should start a new chat 
or any other tips that may help me reduce token usage.
```

これだけで、Claude自身がトークン節約のアドバイザーになってくれる。「そろそろ新しいチャットに移った方がいいですよ」と教えてくれるようになる。

#### 解決策2：メガプロンプトで文脈を圧縮引き継ぎ

どうしても今のチャットの文脈を次に持っていきたい場合。チャットの最後にこう言う：

```
I'm moving to a new chat; give me a prompt I can use to restart this session 
without losing any of our context from this conversation.
```

Claudeが全文脈を圧縮した1つのプロンプトを生成してくれる。これを新規チャットの最初に貼るだけで、**文脈ロスなく軽量なチャットで再スタート**できる。

#### 覚えておくべき鉄則

> 「1つの超長チャット」より「3つの短いチャット」の方がトークン効率は圧倒的に良い。
> 迷ったら新しいチャットを開く。これだけで制限に到達する頻度が激減する。

---

### Step 3：Proper Memory（Claudeの記憶を外部ファイルで永続化する）

Claudeの最大の弱点の1つ。それは**文脈を忘れること**です。

デフォルトのClaudeは、あなたの好みや過去の指示をほとんど覚えていない。結果として何が起きるか：

- 毎回同じ前提条件を説明する → その分トークンを消費
- 過去に修正したミスを繰り返す → 再度修正のやり取りでトークンを消費
- 好みを忘れて不要な出力をする → リテイクでトークンを消費

#### やり方

PCのデスクトップにフォルダを1つ作り、中に**2つのMarkdownファイル**を置く。

##### Instructions.MD（指示書）

Claudeへの恒久的なルールと指示を書くファイル。

構成例：

- `## Who you are` → 自分の役割・専門性
- `## What you do` → Claudeに期待する振る舞い
- `## Rules` → 絶対に守らせたいルール

そして**最も重要な1行**をここに入れる：

```
Update Memory.MD with my preferences over time.
```

この指示があることで、Claudeが会話の中で学んだあなたの好みや修正を、自動的に2つ目のファイルに書き込んでくれる。

##### Memory.MD（記憶ファイル）

Claudeの「**第二の脳**」として機能するファイル。使えば使うほど賢くなっていく。

構成例：

- `## Preferences` → 好みのスタイル、フォーマット
- `## Corrections` → 過去に修正された事項
- `## Patterns` → 繰り返し使うパターン

**具体例**：あなたが「emダッシュを使わないで」と一度言えば、Claudeがこのファイルに記録する。次回以降、何も言わなくてもemダッシュは出てこなくなる。「見出しは#じゃなくて■を使って」と言えば、それも記録される。

このフォルダをClaude Code/Coworkにアタッチするだけで設定完了。フォルダの中身はClaudeが毎回読み込むので、**チャットをまたいでも文脈が保持される**。

一度使い始めたら、もう元には戻れないとMilesは言っています。再説明にかかっていたトークンがゼロになるのは、体感としてかなり大きい。

---

### Step 4：Model Stacking & Selection（モデルの使い分けで90%を節約）

> 「Opus 4.7を全てに使うのは完全な無駄遣い」

多くの人がやりがちなのは、「一番賢いモデルを常に使えば間違いない」という思考。でもこれは「**近所のコンビニに行くのにフェラーリを出す**」ようなもの。

#### エスカレート方式

Milesが実践しているのは「エスカレート方式」。

```
Haiku（軽いタスク） → Sonnet（中程度のタスク） → Opus（重いタスク・最終仕上げ）
```

この順番で始めて、本当に能力が足りない時だけ上のモデルに切り替える。実感として、**90%のタスクはOpus以外で十分**に処理でき、Opusが本当に必要なのは残り10%だけだとのこと。

#### さらに細かいチューニング

- **Extended Thinking**：普段はオフにしておく。複雑な推論や数学的タスクの時だけオン。オンにするとトークン消費が跳ね上がるので、本当に必要な場面だけ
- **Styles（スタイル設定）**：Claudeのホーム画面から「Concise」スタイルに切り替えられる。これだけで回答が短く簡潔になり、出力トークンが大幅に減る。多くの人がこの機能の存在すら知らない
- **Low Effort**：Claude Codeでは「Low」エフォートモードを選択可能。簡単なタスクならこれで十分で、処理速度も上がる

#### Claude以外も使う

そしてClaude以外の選択肢も忘れないこと。**ニュース検索、リサーチ、要約のような単純タスクには、KimiやDeepSeekなどの無料・安価なオープンソースモデルで十分対応できる**。Claudeの枠は「Claudeでしかできないこと」に温存する。

---

### Step 5：Tool Splitting（ツールごとの使用枠を戦略的に使い分ける）

ほとんどの人が気づいていない事実。**Claudeの各ツールには、それぞれ独立した使用パラメータが存在します**。

#### 具体的な仕組み

- **Claude Code / Claude Chat** → 同じプランの使用枠を共有
- **Claude Design** → 完全に別枠

この仕組みを知らないと何が起きるか。例えば、Claude Codeの中でUIデザインのモックアップを作らせる。これはCode/Chatの枠を消費する。でもClaude Designという別ツールには未使用の枠が丸々残っている。**同じデザインタスクをClaude Designでやれば、Code/Chatの枠を一切消費せずに済む**。

#### Milesのルール

- コーディング → **Claude Code**
- デザイン → **Claude Design**
- 対話・分析 → **Claude Chat**
- それぞれのツールが得意なことに使い、苦手なことを無理にやらせない

---

### Bonus Tips（すぐ使える追加テクニック集）

- **追加クレジット購入**：$20→$100のようなプランアップグレードを検討する前に、数ドルだけクレジットを追加購入する選択肢がある。月末にちょっと足りない時はこれで十分
- **Claude Skills**：繰り返しタスクを自動化するスキルを構築しておく。毎回同じ手順を説明する代わりに、スキルとして保存すれば1コマンドで実行できる
- **使用量トラッキング**：定期的に使用状況を確認する習慣をつける。Claude Codeなら `/Usage` コマンドで即座に確認可能。「あと何%使えるか」を把握していれば、使い方を調整できる
- **Overviewセクション**：最近追加された新機能で、使用状況の概要が一目でわかるダッシュボードが見られる
- **制限に近づいたら行動を変える**：残り20%を切ったら、Haikuに切り替える、Extended Thinkingをオフにする、チャットを短く保つ、など意識的にモードを切り替える

---

### まとめ：この方法で3週間、制限ゼロを達成

Milesがこの5ステップを実践してから3週間、一度もトークン制限に引っかかっていないとのこと。**$200/月のプランを変えずに**、です。

#### ポイントを整理

| Step | 内容 | 効果 |
|------|------|------|
| Step 1 | 計画はHaikuで、実行はOpusで。フェーズを分離 | 67%削減 |
| Step 2 | チャットは短く保ち、Projectsで管理 | 3つの短いチャット ＞ 1つの長いチャット |
| Step 3 | Memory.MDで記憶を外部化 | 再説明コストをゼロに |
| Step 4 | エスカレート方式で90%をOpus以外に回す | Styles・Effort設定も活用 |
| Step 5 | ツールごとの使用枠の違いを把握 | 適材適所で使い分ける |

#### 最後に

AIの利用コストが今後安くなる見込みは正直薄い。むしろモデルが高性能化するほど、トークン単価は上がる傾向にある。だからこそ、**今のうちに「正しい使い方」を身につけておくことが、長期的な節約に直結**します。

Milesも言っている通り、問題は「プランが安いこと」ではなく「使い方が間違っていること」。**正しく使えば、今のプランのままで制限に引っかからない生活は十分に実現可能**です。

---

### 参考リンク

- 元記事: https://x.com/ClaudeCode_love/status/2051287112864223572
- Miles Deutscherの元ポスト: https://x.com/milesdeutscher/status/2049618781841031551
