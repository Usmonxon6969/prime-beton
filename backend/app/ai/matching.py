"""Name matching that survives Latin/Cyrillic mixes, Uzbek/Russian spelling and typos.

Every name is reduced to a canonical Latin "sound" form (Cyrillic and Latin spellings of the same word meet there), numbers are kept apart and
must agree, and words are compared one by one so word order, suffixes ("sementdan") and missing words do not matter much.
"""
import difflib
import re

CYR = {"а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "yo", "ж": "j", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
       "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u", "ф": "f", "х": "h", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "sh",
       "ъ": "", "ы": "i", "ь": "", "э": "e", "ю": "yu", "я": "ya", "ў": "o", "ғ": "g", "қ": "k", "ҳ": "h", "ҷ": "j", "ӣ": "i", "ү": "u", "ө": "o"}
LOOK = str.maketrans({"a": "а", "b": "в", "c": "с", "e": "е", "h": "н", "k": "к", "m": "м", "o": "о", "p": "р", "t": "т", "x": "х", "y": "у",
                      "A": "А", "B": "В", "C": "С", "E": "Е", "H": "Н", "K": "К", "M": "М", "O": "О", "P": "Р", "T": "Т", "X": "Х", "Y": "У"})
APOS = "ʻʼ‘’`´'ʹ"
_CYR_RE = re.compile("[а-яёўғқҳҷӣүө]", re.I)
_LAT_RE = re.compile("[a-z]", re.I)


def _word(w: str) -> str:
    if _CYR_RE.search(w) and _LAT_RE.search(w):          # mixed scripts in one word: Latin look-alikes are Cyrillic letters
        w = w.translate(LOOK)
    w = "".join(CYR.get(ch, ch) for ch in w.lower())
    w = w.replace("c", "k") if "ts" in w else w
    w = re.sub(r"c(?=[eiy])", "s", w).replace("c", "k")
    w = w.replace("ts", "s").replace("q", "k").replace("x", "h").replace("w", "v").replace("zh", "j").replace("yo", "o").replace("ph", "f")
    w = re.sub(r"(.)\1+", r"\1", w)                      # doubled letters
    return w


def tokens(s: str) -> tuple[list[str], list[str]]:
    """(words, numbers) of a name. Numbers stay apart from words: 2ПК 66*12 -> words [pk], numbers [2, 12, 66]."""
    s = s.lower().replace("ё", "е")
    for a in APOS:
        s = s.replace(a, "")
    s = re.sub(r"(?<=\d)\s*[x×х*]\s*(?=\d)", " ", s)                     # 66*12, 66x12, 66х12
    s = re.sub(r"(?<=\d)[,.](?=\d)", "·", s)                              # 71,5 and 24.4.6 stay one number
    s = re.sub(r"(?<=\d)(?=[^\W\d_])|(?<=[^\W\d_])(?=\d)", " ", s)        # 2пк -> 2 пк
    parts = re.findall(r"[^\W_]+(?:·[^\W_]+)*", s)
    nums = sorted(p.replace("·", ".") for p in parts if p[0].isdigit())
    words = [_word(p) for p in parts if not p[0].isdigit()]
    return [w for w in words if w], nums


def _wscore(a: str, b: str) -> float:
    if a == b:
        return 1.0
    r = difflib.SequenceMatcher(None, a, b).ratio()
    if min(len(a), len(b)) >= 4 and (a.startswith(b) or b.startswith(a)):    # sementdan ~ sement
        r = max(r, 0.92)
    return r


def score(query: str, name: str) -> float:
    qw, qn = tokens(query)
    cw, cn = tokens(name)
    if not (qw or qn) or not (cw or cn):
        return 0.0
    if qw and cw:
        per_q = [max(_wscore(q, c) for c in cw) for q in qw]
        per_c = [max(_wscore(q, c) for q in qw) for c in cw]
        wl = sum(per_q) / len(per_q)
        text = 0.75 * wl + 0.25 * (sum(per_c) / len(per_c))
        whole = difflib.SequenceMatcher(None, " ".join(qw), " ".join(cw)).ratio()
        if wl >= 0.88:                                    # everything written is there: extra words in the catalogue name are fine
            text = max(text, 0.88 if len(per_c) > len(per_q) else wl)
        text = max(text, whole)
    elif qw or cw:
        text = 0.0
    else:
        text = 1.0
    if qn or cn:
        if qn == cn:
            pass
        elif qn and cn and set(qn) <= set(cn):
            text *= 0.85                                  # fewer numbers written than the catalogue name has
        elif qn and cn:
            text *= 0.45                                  # different numbers: 66*12 is not 62*12
        else:
            text *= 0.95
    return round(text, 3)


def best(query: str, pool: dict[int, list[str]], n=5, floor=0.4) -> list[tuple[int, float]]:
    out = []
    for pid, names in pool.items():
        s = max((score(query, v) for v in names if v), default=0.0)
        if s >= floor:
            out.append((pid, s))
    out.sort(key=lambda x: -x[1])
    return out[:n]


def pick(cands: list[tuple[int, float]], accept=0.8, gap=0.05) -> tuple[int | None, bool]:
    """(chosen id or None, ambiguous): a clear winner is chosen; two near-equal strong candidates are left to the user."""
    if not cands or cands[0][1] < accept:
        return None, False
    if len(cands) > 1 and cands[0][1] < 0.999 and cands[1][1] >= accept and cands[0][1] - cands[1][1] < gap:
        return None, True
    return cands[0][0], False
