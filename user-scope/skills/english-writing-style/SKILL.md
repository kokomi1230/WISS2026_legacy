---
name: english-writing-style
description: 英語の論文・申請書・技術文書を執筆する際の文体・構造・表記ルール（plain English、能動態優先、強い動詞、トピックセンテンス、SI 単位、Strunk & White ベース）を Claude に適用させる。学術論文・grant proposal・技術ブログ・README・仕様書を英語で書くときに発火する。Use when writing or editing academic/technical English (papers, grant proposals, technical specs, README, documentation).
---

# 英語文章執筆スタイル (english-writing-style)

このスキルは英語の論文・申請書・技術文書を執筆 / 編集する際の、文体・構造・表記の **強制適用ルール** を提供する。Strunk & White『The Elements of Style』および scientific writing コミュニティの慣行に基づく。

## いつ発火させるか

ユーザーが以下のいずれかに該当する作業を始めたとき、このスキルを自動適用する:

- 英語論文（学会発表 / ジャーナル投稿）の執筆 / 改稿
- 英語の研究費 grant proposal（NIH / NSF / ERC など）
- 英語の技術ブログ / README / API ドキュメント
- 英語の仕様書 / RFC / design doc
- 既存英語ドキュメントの校正
- ユーザーが「英語で書いて」「論文用に整えて」「reword in English」と明示したとき

## 基本理念

**Write to express, not to impress.** わかりやすい英文とは、読者が一度で意味を取れる文である。Strunk & White の core rules を継承:

- Omit needless words.
- Use definite, specific, concrete language.
- Put statements in positive form.
- Use the active voice.
- Keep related words together.
- Express coordinate ideas in similar form.

## 句読点

- カンマ「,」とピリオド「.」（半角、英文標準）
- **Oxford comma**（serial comma）はプロジェクトで方針を統一。論文では推奨、ジャーナリスティック文書では省略するスタイルも可
- セミコロン「;」は独立節を強くつなげる場合のみ
- コロン「:」はリスト / 引用 / 説明の導入
- ダッシュは em-dash 「—」を使用、半角ハイフン「-」で代用しない
- 句点と引用符の順序: American style では `"sentence."` が標準（British style は `"sentence".`）

## 文体・voice

### Tense（時制）

- **Present tense** for established facts and citing prior work
  - "Smith (2020) reports that ..."
  - "This algorithm runs in O(n log n) time."
- **Past tense** for describing your own experiments / methods
  - "We trained the model for 50 epochs."
- **Present perfect** for describing field-wide progress
  - "Researchers have studied this problem for decades."
- 1 段落内で tense を頻繁に切り替えない。論理的に必要な切替のみ

### Active voice 優先

| Passive (避ける) | Active (推奨) |
| --- | --- |
| It was found that | We found that / Our analysis shows that |
| The data were analyzed | We analyzed the data |
| It is believed that | We believe that / Prior work suggests |
| A model was trained | We trained a model |

Methods セクションのみ passive voice が許容される慣行があるが、近年は active voice 推奨が主流（Nature / Science 含む）。

### Plain English principles

| 冗長 (wordy) | 簡潔 (concise) |
| --- | --- |
| in order to | to |
| due to the fact that | because |
| at this point in time | now / currently |
| a large number of | many |
| in the event that | if |
| with regard to | about / regarding |
| it should be noted that | (削除して直接書く) |
| has the ability to | can |
| is responsible for | manages / handles |

### 強い動詞を選ぶ

- 弱い: "make a decision" → 強い: "decide"
- 弱い: "give an explanation" → 強い: "explain"
- 弱い: "be in agreement with" → 強い: "agree with"
- 弱い: "perform an analysis" → 強い: "analyze"

名詞化（nominalization）を動詞に戻すと文が短くなり読みやすくなる。

### 否定形より肯定形

- 避ける: "He was not very often on time."
- 推奨: "He usually came late."
- 避ける: "did not remember"
- 推奨: "forgot"

### Hedging（断定の弱め方）

科学論文では不確実性を明示する。ただし過剰な hedging は主張を弱める。

| 強い断定 | 弱い断定（hedge） |
| --- | --- |
| X causes Y | X may cause Y / X is associated with Y |
| Our method is best | Our method outperforms prior work on benchmark Z |
| (avoid) | suggests, indicates, may, likely, appears to |

Grant proposal では断定的に書く（"We will demonstrate..."）。論文では証拠に応じた hedging を使う。

## 文の構造

### Sentence length

- 1 文: 15〜25 words が読みやすい範囲。30 words を超えると分解検討
- 短い文（5-10 words）を時折挟むとリズムが生まれる
- 1 文に独立節は 2 つまで（and / but / so で接続）

### Parallel structure（並列構造）

リストや列挙では文法構造を揃える:

- NG: "We collected data, then the analysis was done, and finally writing the paper."
- OK: "We collected data, analyzed it, and wrote the paper."

### Misplaced modifiers

修飾語は被修飾語の近くに置く:

- NG: "She almost drove her kids to school every day." (almost が drove を修飾)
- OK: "She drove her kids to school almost every day."

## パラグラフ構造

### Topic sentence + supporting + closing

各パラグラフは 1 つの主題を扱い、以下の構造を持つ:

1. **Topic sentence**: 段落の主題を 1 文で端的に提示
2. **Supporting sentences**: 主題を裏付ける詳細・例・データ
3. **Closing sentence**（任意）: 次段落へつなぐ / 段落の含意を述べる

### Paragraph length

- 学術論文: 3〜8 sentences / 段落
- Grant proposal: 3〜5 sentences / 段落（簡潔）
- 技術ブログ: 2〜5 sentences / 段落（読みやすさ優先）

### Transition words

| 関係 | 代表例 |
| --- | --- |
| Addition | moreover, furthermore, in addition |
| Contrast | however, conversely, in contrast |
| Cause/effect | therefore, consequently, as a result |
| Example | for example, for instance, specifically |
| Conclusion | in summary, in conclusion, to summarize |

接続詞は段落間 / 文間の論理を明示するが、すべての文に必要ではない。前文の情報を次文の主語にする「information flow」が機能していれば transition word を省ける。

## 表記ルール

### Numbers and units

- 0〜9 はスペルアウト（"three samples"）、10 以上は数字（"42 samples"）
- ただし、文頭の数字は常にスペルアウト（"Forty-two samples were collected.")
- 4 桁以上は thousands separator「,」を使う（10,000、ただし year には付けない: 2026）
- SI 単位を優先、unit と数値の間に半角スペース（"100 Hz", "10 ms"）
- パーセントは数値の場合 `%` を直接（"42%"）、文中では "42 percent" もある

### Capitalization

- Title case: 主要単語の頭文字を大文字化（"A Study of Deep Learning Models"）
- Sentence case: 文頭と固有名詞のみ大文字（"A study of deep learning models"）
- ジャーナルや学会のスタイルガイドに従う
- 章タイトル内のハイフネーション語: 両方の単語を大文字化（"State-of-the-Art Methods"）

### Abbreviations and acronyms

- 初出時に full term + abbreviation を併記
  - "Electroencephalography (EEG)"
  - "Long Short-Term Memory (LSTM) networks"
- 2 回目以降は abbreviation のみ
- アブストラクトと本文は別カウント（abstract で初出 → 本文でも再度初出扱い）

### Italics

- 強調: sparingly（多用しない）
- 専門用語の初出（時に）
- 書籍 / ジャーナル名
- ラテン語句（"in vivo", "et al."）
- 数学変数

### Citation

- スタイル: APA / IEEE / ACM / Nature / Science など投稿先に従う
- LaTeX: `\cite{key}` または `\citep{key}` / `\citet{key}`
- 文末の citation は句点の前: "...result \cite{smith2020}."
- 著者複数: 2 名 "Smith and Jones" / 3 名以上 "Smith et al."

## 論文執筆特有のルール

### Section organization (IMRaD)

論文は以下の構造（Introduction-Methods-Results-and-Discussion）が基本:

1. **Abstract**: 250-300 words、研究の motivation / methods / results / conclusion を 1 段落
2. **Introduction**: 課題の背景 → 先行研究のレビュー → 課題のギャップ → 本研究の貢献
3. **Methods**: 再現可能なレベルの実験手順
4. **Results**: データと統計を客観的に提示（解釈は最小限）
5. **Discussion**: 結果の意味、限界、今後の展望
6. **Conclusion**: 主要な発見を 1〜2 段落で要約

### Background / Introduction

**避けるべきパターン:**

- "In recent years, ..." (時代依存、根拠が弱い)
- "There is no work on X" (網羅的調査の証明が必要)
- "X has not been established" (反証として弱い、自分が確立できる根拠が必要)

**正しい流れ:**

- "Prior work has addressed A and B [refs]. However, **specific** challenge X remains underexplored because of constraint Y. We address X by introducing Z."

### Methods

- 過去形 + active voice: "We trained ... We collected ..."
- 再現可能な詳細（hyperparameter, software version, hardware）を明記
- 「被験者」は **"participants"** を使う（"subjects" は古く、人間以外を連想させる）

### Results

- 図表で示せるものは本文で繰り返さない
- 統計は p 値だけでなく effect size と confidence interval を併記
- 単に結果を述べ、解釈は Discussion へ

### Discussion

- 結果の解釈
- 限界（limitations）を honest に述べる
- 今後の展望（future work）を 1 段落以内に
- 結論をネガティブで終わらせない

## Grant proposal 特有のルール

### Aims and approach

- 各 aim は **1 文で要約可能** にする
- "We will demonstrate / develop / characterize ..." の能動・断言的な構文
- "may be explored" のような曖昧な未来形は避ける

### Significance and innovation

- **Significance**: なぜこの研究が重要か（社会的意義・科学的意義）
- **Innovation**: 既存研究と何が異なるか（新理論・新手法・新応用）
- 両者を別段落で述べる

### Specific Aims page

- 1 ページに収める
- Aim 1, Aim 2, Aim 3 の 3 つ程度（4 つ以上は過剰）
- 各 aim に 1 段落の説明 + expected outcomes

### Budget justification

- 必要性を明示（"required for X experiment in Aim 2"）
- 既存設備で代替できない理由を書く

## クイックチェックリスト

執筆後、以下を順に確認する:

### Style and grammar

- [ ] Voice is consistent (active preferred, passive minimal)
- [ ] Tense is appropriate (present for facts, past for own work)
- [ ] No unnecessary nominalizations
- [ ] No wordy phrases ("in order to" → "to", etc.)
- [ ] No misplaced modifiers
- [ ] Parallel structure in lists

### Sentences and paragraphs

- [ ] Sentences are 15-25 words on average
- [ ] Each paragraph has a clear topic sentence
- [ ] Each paragraph addresses one main idea
- [ ] Transitions between paragraphs are logical
- [ ] No long sentences (>30 words) without breaking up

### Terminology

- [ ] Acronyms defined at first use
- [ ] Technical terms used consistently
- [ ] Numbers formatted per style (0-9 spelled out, 10+ as digits)
- [ ] SI units used; space between value and unit
- [ ] Punctuation matches style guide (Oxford comma policy)

### Citations and references

- [ ] All claims have citations where needed
- [ ] Citation style is consistent
- [ ] References list is complete and properly formatted
- [ ] In-text citations use correct format ("Smith et al. (2020)" or "[12]")

### Paper-specific

- [ ] Abstract is 250-300 words and self-contained
- [ ] Introduction states the gap and contribution
- [ ] Methods are reproducible
- [ ] Results are objective; interpretation in Discussion
- [ ] Limitations are stated honestly
- [ ] Conclusion is positive but not overstated

### Grant-specific

- [ ] Aims are stated in present/future tense, actively
- [ ] Significance and innovation are separate
- [ ] Budget is justified per item
- [ ] Specific Aims page fits on one page
- [ ] Figures are clear at print size

## 関連ツール

- `english-proofreader` (subagent) — 本スキルのルールに基づく英文校正専門 agent。書き換え案を提示する
- `code-review` plugin — コード断片を含むドキュメントのレビュー
- `mintlify` plugin — API リファレンスの自動生成

## 参考文献

- Strunk, W. Jr. and White, E.B. *The Elements of Style*. 4th ed.
- Williams, J.M. *Style: Lessons in Clarity and Grace*.
- Pinker, S. *The Sense of Style*.
- 投稿先ジャーナルの author guidelines を必ず参照
