# -*- coding: utf-8 -*-
"""bounty_list：`items` 元素**非对象**在 **validate 面**与 **render 面**都不崩

被修处（`scripts/bounty_list.py`）：
    - `validate`（fail-closed 判据面，`main()` 里 `if errs: return 2`）—— **既有覆盖**，本件保留；
    - `render`（产物生成面）—— 旧实现 `sorted(doc["items"], key=sort_key)` 直接排，
      元素非对象 ⇒ `sort_key` 的 `it["score"]` 抛 `TypeError` / `KeyError`。

**两个面都必须覆盖**（返工说明，见本件申报件的维护者回执）：
    `main()` 顺序是 `load → validate（errs 即 return 2） → render → --check/--write`。
    `validate` 是 `bounty_list.py --check` 这道门禁的 fail-closed 判据面；
    `render` 是产物生成面。**只覆盖其中一个 = 覆盖面转移，不是扩展。**

判据分组：
  A validate：四类非对象元素 ⇒ 不抛 + 点名「非对象条目」
  B validate：零行为变更（合法条目 / 空 items）
  C validate：反向证明（形状判据锚点 + 旧形态已不在源码里）
  D render：四类非对象元素 ⇒ 不抛 + 合法那条仍渲染出来
  E render：零行为变更（全合法 ⇒ 首行不变）
  F render：反向证明（过滤锚点 + 旧形态已不在源码里）
"""
import sys
import os
import copy
import json

sys.stdout.reconfigure(encoding='utf-8')
_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.dirname(_HERE)
_IMPL = os.path.join(_REPO, "scripts", "bounty_list.py")
sys.path.insert(0, os.path.join(_REPO, "scripts"))

pass_n = fail_n = 0


def check(name, ok, detail=""):
    global pass_n, fail_n
    if ok:
        pass_n += 1
    else:
        fail_n += 1
    print(f'[{"OK " if ok else "NG "}] {name}{" — " + detail if detail else ""}')


import bounty_list as bl

# 真实真源（构造测试 doc 时只替换 items —— 不猜字段）
_SRC = json.load(open(os.path.join(_REPO, "docs", "bounty", "悬赏.json"), encoding="utf-8"))
_GOOD = copy.deepcopy(_SRC["items"][0])
BAD = (("字符串", "oops"), ("数字", 5), ("null", None), ("数组", [1]))

print('— A validate：非对象条目 ⇒ 不崩、且被点名 —')
for label, val in BAD:
    try:
        errs = bl.validate({"items": [val]})
        check(f'A items=[{label}] ⇒ 不抛', True, str(errs[:1])[:56])
        check(f'A items=[{label}] ⇒ 点名「非对象条目」', any("非对象条目" in e for e in errs),
              str(errs)[:60])
    except Exception as exc:
        check(f'A items=[{label}] ⇒ 不抛', False, f'{type(exc).__name__}: {exc}')

print('— B validate：零行为变更 —')
_e = bl.validate({"items": [copy.deepcopy(_GOOD)]})
check('B 合法条目无「非对象」错误', not any("非对象条目" in x for x in _e), str(_e)[:60])
check('B 空 items 仍报缺失', any("缺失或为空" in x for x in bl.validate({"items": []})), '')

print('— C validate：反向证明 —')
_SRC_TXT = open(_IMPL, encoding="utf-8").read()
check('C0 形状判据锚点命中', _SRC_TXT.count('if not isinstance(it, dict):') == 1, '')
check('C 旧实现直接 `it.get("id", "?")` ⇒ 非对象必抛 AttributeError（已不在源码里）',
      'for it in doc.get("items", []):\n        i = it.get("id", "?")' not in _SRC_TXT, '')

print('— D render：非对象条目 ⇒ 不崩、合法那条仍渲染 —')
for label, val in BAD:
    doc = copy.deepcopy(_SRC)
    doc["items"] = [val, copy.deepcopy(_GOOD)]
    try:
        out = bl.render(doc)
        check(f'D render(items=[{label}, 合法]) ⇒ 不抛', True, out[:26].replace("\n", " "))
        check(f'D 合法那条仍渲染出来', _GOOD["id"] in out, '')
    except Exception as exc:
        check(f'D render(items=[{label}]) ⇒ 不抛', False, f'{type(exc).__name__}: {str(exc)[:30]}')

print('— E render：零行为变更 —')
_d2 = copy.deepcopy(_SRC)
_d2["items"] = [copy.deepcopy(_GOOD)]
_out2 = bl.render(_d2)
check('E 全合法 ⇒ 首行仍 `# 灵枢悬赏 · 任务清单`',
      _out2.startswith("# 灵枢悬赏 · 任务清单"), _out2[:30])

print('— F render：反向证明 —')
check('F0 形状过滤锚点命中', "_good = [it for it in _items if isinstance(it, dict)]" in _SRC_TXT, '')
check('F 旧实现直接 `sorted(doc["items"], key=sort_key)` ⇒ 非对象必抛（已不在源码里）',
      'items = sorted(doc["items"], key=sort_key)' not in _SRC_TXT, '')
check('F `sort_key` 的 `it["score"]` 对非对象必然抛 TypeError/KeyError（既有实现证据）',
      'return (-it["score"], it["id"])' in _SRC_TXT, '')

print(f'\n通过 {pass_n} / 失败 {fail_n}')
sys.exit(0 if fail_n == 0 else 1)
