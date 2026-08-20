# コーディング規約 — 命名規則とコメントの付け方

プロレベルの品質でコードベースを統一するための実用リファレンス。
対象: **言語横断の汎用原則** / **Python** / **JavaScript・TypeScript** / **Java・C#**

---

## 目次

1. [基本方針](#1-基本方針)
2. [言語横断の汎用原則](#2-言語横断の汎用原則)
   - 2.1 命名の普遍原則
   - 2.2 コメントの普遍原則
3. [Python](#3-python)
4. [JavaScript / TypeScript](#4-javascript--typescript)
5. [Java / C#](#5-java--c)
6. [ケース表記チートシート](#6-ケース表記チートシート)
7. [レビュー用チェックリスト](#7-レビュー用チェックリスト)

---

## 1. 基本方針

規約の目的は「個人の好み」を消し、**誰が書いても同じ形になる**ことです。細部の是非より一貫性が優先されます。以下の3つを土台とします。

1. **一貫性 > 正しさ** — 既存コードベースに規約があるなら、たとえ自分の好みと違ってもそれに従う。
2. **名前で語らせ、コメントで補う** — 良い名前はコメントの必要を減らす。まず名前を磨き、それでも伝わらない「なぜ」をコメントにする。
3. **コメントは資産であり負債** — 保守コストを伴う。書くほど良いのではなく、コードで表現できないものだけに絞る。

---

## 2. 言語横断の汎用原則

### 2.1 命名の普遍原則

**意図が読み取れる名前にする。** 名前を見ただけで「何を表すか」「なぜ存在するか」が分かること。

```
# 悪い
d = 30
def calc(x): ...

# 良い
expiration_days = 30
def calculate_monthly_fee(usage): ...
```

**検索可能な名前にする。** マジックナンバーや1文字変数は検索・置換ができない。定数に名前を付ける。

```
# 悪い
if status == 7: ...

# 良い
STATUS_SHIPPED = 7
if status == STATUS_SHIPPED: ...
```

**スコープの長さと名前の長さを比例させる。** ループカウンタの `i` は数行で閉じるなら許容。生存期間が長い変数ほど説明的にする。

**型・単位・意味を名前に埋め込む。** 誤用を防げる。

```
timeout_ms        # 単位を明示（timeout だけだと秒か分か不明）
max_retry_count   # 何の数か明示
is_active         # 真偽値は is / has / can で始める
user_list         # コレクションは複数形
```

**否定形の名前を避ける。** 二重否定は読みにくい。`is_not_valid` より `is_valid` を使う。

**対称的な語彙を統一する。** `get/set`、`open/close`、`begin/end`、`create/destroy` のように対で揃える。同じ概念に `fetch` `get` `retrieve` を混在させない。**1概念1語** を守る。

**略語を乱用しない。** 広く通じるもの（`id` `url` `db` `max`）以外は省略しない。`usr` `calc` `tmp2` は避ける。

### 2.2 コメントの普遍原則

最重要原則: **「何を(what)」ではなく「なぜ(why)」を書く。** コードは what を既に表している。

```python
# 悪い例: コードの逐語的な繰り返し
i = i + 1  # i に 1 を足す

# 良い例: 意図・背景を説明
i = i + 1  # ヘッダー行をスキップするため1行進める
```

**価値の高いコメントの類型**

| 類型 | 内容 | 例 |
|------|------|-----|
| 意図 | なぜこの実装を選んだか | `# パフォーマンス優先のため意図的にキャッシュを共有` |
| 警告 | 変更時の危険・制約 | `# この関数はスレッドセーフではない` |
| 外部参照 | 仕様・チケット・バグへのリンク | `# workaround for FooLib bug #1234` |
| 非自明な根拠 | 定数や式の由来 | `# RFC 5321 によりメールは最大 254 文字` |
| TODO/FIXME | 未完成・既知の問題 | `# TODO(name): ページネーション未対応` |

**避けるべきコメント**

- コードの言い換え（当たり前の説明）
- コメントアウトされた古いコード → バージョン管理があるので**削除する**
- **嘘をつくコメント** — コードを変えたらコメントも必ず更新する。古いコメントは無いより有害。
- 履歴コメント（`# 2024-01 田中 修正`）→ Git blame に任せる

**書式のルール**

- コメントはコードと同じインデントに揃える。
- 文として書く（大文字始まり・句点）。チーム言語（日本語/英語）を統一する。
- コードの右横（行末コメント）は短い補足のみ。長い説明は対象行の**上**に置く。
- 「コメントを書く前に、コメントが不要なコードにできないか」を常に自問する。

---

## 3. Python

準拠: **PEP 8**（スタイル） / **PEP 257**（docstring）。整形は `black`、静的解析は `ruff` / `flake8` を推奨。

### 命名規則

| 対象 | 表記 | 例 |
|------|------|-----|
| 変数・関数・メソッド | `snake_case` | `user_count`, `get_user()` |
| 定数 | `UPPER_SNAKE_CASE` | `MAX_RETRIES` |
| クラス・例外 | `PascalCase` | `UserAccount`, `ValidationError` |
| モジュール・パッケージ | 短い `snake_case` | `http_client` |
| 内部利用（非公開） | 先頭に `_` | `_internal_cache` |
| 名前衝突回避 | 末尾に `_` | `class_`, `type_` |
| 「使わない」変数 | `_` | `for _ in range(3):` |

真偽値は `is_` / `has_` で始める（`is_valid`, `has_permission`）。

### コメント & docstring

行コメントは `#` + 半角スペース1つ。docstring は三重ダブルクオート `"""..."""`。

```python
def fetch_user(user_id: int, *, use_cache: bool = True) -> User:
    """ユーザーを1件取得する。

    Args:
        user_id: 取得対象のユーザーID。
        use_cache: True の場合はローカルキャッシュを優先する。

    Returns:
        該当する User オブジェクト。

    Raises:
        UserNotFoundError: 指定 ID が存在しない場合。
    """
    # DB 負荷を抑えるため、明示的に無効化されない限りキャッシュを見る
    if use_cache and user_id in _cache:
        return _cache[user_id]
    ...
```

公開モジュール・クラス・関数には docstring を付ける（1行要約 → 空行 → 詳細）。スタイルは **Google / NumPy / reStructuredText** のいずれかにチームで統一する。

---

## 4. JavaScript / TypeScript

準拠: 一般的な JS/TS 慣習 + **JSDoc**（JS） / **TSDoc**（TS）。整形は `Prettier`、静的解析は `ESLint`。

### 命名規則

| 対象 | 表記 | 例 |
|------|------|-----|
| 変数・関数 | `camelCase` | `userCount`, `getUser()` |
| クラス・型・インターフェース・enum | `PascalCase` | `UserAccount`, `type UserId` |
| 定数（真の不変値） | `UPPER_SNAKE_CASE` | `MAX_RETRIES` |
| React コンポーネント | `PascalCase` | `function UserCard() {}` |
| ファイル名 | プロジェクト規約に統一 | `userService.ts` / `user-service.ts` |
| プライベート（慣習/構文） | `#field` または `_field` | `#secret`, `_internal` |

- `boolean` は `is` / `has` / `can` / `should` で始める。
- TypeScript のインターフェース名に `I` 接頭辞は付けない（現代の主流）。
- 型は `type` / `interface` とも `PascalCase`。
- 定数でも「単なる再代入不可の変数」は `camelCase`。真に普遍的な設定値だけ `UPPER_SNAKE_CASE`。

### コメント & JSDoc / TSDoc

```typescript
/**
 * ユーザーを1件取得する。
 *
 * @param userId - 取得対象のユーザーID。
 * @param options - 取得オプション。
 * @returns 該当ユーザー。存在しなければ reject する。
 * @throws {UserNotFoundError} 指定 ID が存在しない場合。
 */
async function fetchUser(
  userId: number,
  options: { useCache?: boolean } = {},
): Promise<User> {
  // レートリミット回避のため、明示指定がなければキャッシュを優先
  if (options.useCache !== false && cache.has(userId)) {
    return cache.get(userId)!;
  }
  // ...
}
```

TypeScript では型が引数・戻り値を語るので、JSDoc の `@param {type}` は**書かない**（型注釈と重複するため）。説明が必要な項目だけ `@param name - 説明` を残す。

---

## 5. Java / C#

準拠: **Java** = Oracle コード規約 + Javadoc / **C#** = Microsoft .NET 命名ガイドライン + XML ドキュメントコメント。

### 命名規則

| 対象 | Java | C# |
|------|------|-----|
| クラス・インターフェース・enum | `PascalCase` | `PascalCase` |
| メソッド | `camelCase` | `PascalCase` |
| フィールド・ローカル変数・引数 | `camelCase` | フィールド`camelCase`(先頭`_`可) / ローカル`camelCase` |
| 定数 | `UPPER_SNAKE_CASE` | `PascalCase`（`const`/`static readonly`） |
| プロパティ | (getter/setter) | `PascalCase` |
| パッケージ / 名前空間 | 全小文字 `com.example.app` | `PascalCase` `Company.Product` |
| インターフェース | `PascalCase`（`I` 接頭辞なし） | `I` 接頭辞あり `IRepository` |
| 型パラメータ | `T`, `E`, `K`, `V` | `T`, `TKey`, `TValue` |

boolean を返すメソッドは `is` / `has` / `can`（Java: `isEmpty()`、C#: `IsEmpty`）。

### ドキュメントコメント

**Java (Javadoc):**

```java
/**
 * ユーザーを1件取得する。
 *
 * @param userId   取得対象のユーザーID
 * @param useCache trueの場合はキャッシュを優先する
 * @return 該当するユーザー
 * @throws UserNotFoundException 指定IDが存在しない場合
 */
public User fetchUser(long userId, boolean useCache) {
    // DB負荷を抑えるため、明示的に無効化されない限りキャッシュを見る
    if (useCache && cache.containsKey(userId)) {
        return cache.get(userId);
    }
    // ...
}
```

**C# (XML ドキュメントコメント):**

```csharp
/// <summary>ユーザーを1件取得する。</summary>
/// <param name="userId">取得対象のユーザーID。</param>
/// <param name="useCache">trueの場合はキャッシュを優先する。</param>
/// <returns>該当するユーザー。</returns>
/// <exception cref="UserNotFoundException">指定IDが存在しない場合。</exception>
public User FetchUser(long userId, bool useCache)
{
    // DB負荷を抑えるため、明示的に無効化されない限りキャッシュを見る
    if (useCache && _cache.ContainsKey(userId))
    {
        return _cache[userId];
    }
    // ...
}
```

公開 API（`public` / `protected` メンバ）にはドキュメントコメント必須。内部実装の「なぜ」は通常の `//` コメントで補う。

---

## 6. ケース表記チートシート

| 表記名 | 形 | 主な用途 |
|--------|-----|----------|
| `snake_case` | `user_count` | Python 変数/関数、DBカラム |
| `UPPER_SNAKE_CASE` | `MAX_RETRIES` | 定数（全言語共通） |
| `camelCase` | `userCount` | JS/TS/Java の変数・メソッド |
| `PascalCase` | `UserCount` | クラス・型（全言語共通）、C#メソッド |
| `kebab-case` | `user-count` | ファイル名、URL、CSSクラス |

---

## 7. レビュー用チェックリスト

**命名**

- [ ] 名前だけで意図が読み取れるか（`d` `tmp` `data2` が残っていないか）
- [ ] 言語の標準ケース表記に従っているか（表を参照）
- [ ] boolean は `is`/`has`/`can` で始まっているか
- [ ] マジックナンバーが名前付き定数になっているか
- [ ] 同じ概念に複数の語（get/fetch/retrieve）が混在していないか
- [ ] 略語を乱用していないか

**コメント**

- [ ] 「なぜ」を説明しているか（「何を」の繰り返しになっていないか）
- [ ] コードと矛盾する古いコメントが残っていないか
- [ ] コメントアウトされた死んだコードを削除したか
- [ ] 公開 API にドキュメントコメント（docstring/JSDoc/Javadoc/XML）があるか
- [ ] TODO/FIXME に担当者・文脈が付いているか
- [ ] 名前を改善すれば消せるコメントではないか

---

> **運用のヒント:** この規約は「読むもの」で終わらせず、フォーマッタ（black / Prettier）とリンタ（ruff / ESLint / Checkstyle / .editorconfig）で**自動強制**する。人間のレビューは機械が拾えない「意図の質」に集中させるのが、プロのコードベースの姿。
