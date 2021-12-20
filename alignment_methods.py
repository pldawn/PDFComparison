import jieba
import Levenshtein as edit
import re


jieba.load_userdict("userdict.txt")


def align_text(paragraph_a, paragraph_b, join=True):
    sent_list_a = re.split("\\W", paragraph_a) if paragraph_a else []
    punc_list_a = re.split("\\w", paragraph_a)[1:-1] if paragraph_a else []
    punc_list_a = [i for i in punc_list_a if i]
    sent_list_b = re.split("\\W", paragraph_b) if paragraph_b else []
    punc_list_b = re.split("\\w", paragraph_b)[1:-1] if paragraph_b else []
    punc_list_b = [i for i in punc_list_b if i]
    alignment_sents = _align_text_list_for_paragraphs(sent_list_a, sent_list_b)

    alignment_ops = []
    for i in range(len(alignment_sents)):
        text_a = sent_list_a[alignment_sents[i][0]] if alignment_sents[i][0] != 100 else ""
        text_b = sent_list_b[alignment_sents[i][1]] if alignment_sents[i][1] != 100 else ""
        alignment_ops.append((_edit_ops(text_a, text_b)))

    char_ops_a, char_ops_b = [], []
    for j in range(len(alignment_ops)):
        if alignment_ops[j][0]:
            char_ops_a.append((alignment_sents[j][0], alignment_ops[j][0]))
        if alignment_ops[j][1]:
            char_ops_b.append((alignment_sents[j][1], alignment_ops[j][1]))

    char_ops_a.sort(key=lambda x: x[0])
    char_ops_b.sort(key=lambda x: x[0])

    cache_ops_a, cache_ops_b = [], []
    for i in range(len(char_ops_a)):
        cache_ops_a.append(char_ops_a[i][1])
        if i < len(char_ops_a) - 1:
            cache_ops_a.append([("equal", punc_list_a[i])])

    for j in range(len(char_ops_b)):
        cache_ops_b.append(char_ops_b[j][1])
        if j < len(char_ops_b) - 1:
            cache_ops_b.append([("equal", punc_list_b[j])])

    ops_a, ops_b = [], []
    for i in cache_ops_a:
        ops_a += i
    for j in cache_ops_b:
        ops_b += j

    if join:
        new_result = _decorate(ops_a, False).replace("。", "<br><br>")
        old_result = _decorate(ops_b, True).replace("。", "<br><br>")
    else:
        new_result = _decorate(ops_a, False).split("。")
        old_result = _decorate(ops_b, True).split("。")

    return new_result, old_result


def _align_text_list_for_paragraphs(list_a, list_b):
    distances = []

    for ind_a in range(len(list_a)):
        str_a = list_a[ind_a]
        first_a = str_a.split("。")[0]
        for ind_b in range(len(list_b)):
            str_b = list_b[ind_b]
            first_b = str_b.split("。")[0]
            try:
                dist1 = edit.distance(str_a, str_b) / ((len(str_a) + len(str_b)) / 2)
                dist2 = edit.distance(first_a, first_b) / ((len(first_a) + len(first_b)) / 2)
                dist = min(dist1, dist2)
            except ZeroDivisionError:
                dist = 0
            distances.append((ind_a, ind_b, dist))

    alignment = _align_distances_for_paragraphs(distances, list_a, list_b)

    for ind in range(len(list_a)):
        not_in = True
        for item in alignment:
            if ind == item[0]:
                not_in = False
        if not_in:
            alignment.append((ind, 100))

    for ind in range(len(list_b)):
        not_in = True
        for item in alignment:
            if ind == item[1]:
                not_in = False
        if not_in:
            alignment.append((100, ind))

    alignment.sort(key=lambda x: x[0])
    alignment.sort(key=lambda x: x[1])

    return alignment


def _align_distances_for_paragraphs(distances, list_a, list_b):
    alignment = []
    alignment_cache = []

    if not distances:
        return alignment

    distances.sort(key=lambda x: x[-1])
    aligned = distances[0]
    ind_a = aligned[0]
    ind_b = aligned[1]

    alignment_cache.append((ind_a, ind_b, aligned[-1]))
    distances = [item for item in distances if item[0] != ind_a and item[1] != ind_b]
    alignment_cache = alignment_cache + _align_distances_for_paragraphs(distances, list_a, list_b)

    for item in alignment_cache:
        if len(item) == 2:
            alignment.append(item)
        elif item[-1] <= 1:
            alignment.append((item[0], item[1]))
        else:
            alignment.append((item[0], 100))
            alignment.append((100, item[1]))

    return alignment


def _edit_ops(text_a, text_b):
    ops_a, ops_b = [], []

    if not text_a and not text_b:
        return ops_a, ops_b

    if text_a and not text_b:
        ops_a.append(("insert", text_a))

        return ops_a, ops_b

    if not text_a and text_b:
        ops_b.append(("delete", text_b))

        return ops_a, ops_b

    mapper = iter("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")

    split_a = jieba.lcut(text_a)
    split_b = jieba.lcut(text_b)

    word_set = set(split_a + split_b)
    word_dict = {}
    word_dict_rev = {}

    for i in word_set:
        if i not in word_dict:
            j = mapper.__next__()
            word_dict[i] = j
            word_dict_rev[j] = i

    text_a = ""
    for tk in split_a:
        text_a += word_dict[tk]

    text_b = ""
    for tk in split_b:
        text_b += word_dict[tk]

    ops = edit.opcodes(text_b, text_a)
    for op in ops:
        op_name = op[0]
        cache_a = text_a[op[3]: op[4]]
        cache_b = text_b[op[1]: op[2]]

        slice_a = ""
        for tk in cache_a:
            slice_a += word_dict_rev[tk]

        slice_b = ""
        for tk in cache_b:
            slice_b += word_dict_rev[tk]

        if _is_numerical(slice_a) and _is_numerical(slice_b):
            op_name = "equal"

        if slice_a:
            ops_a.append((op_name, slice_a))
        if slice_b:
            ops_b.append((op_name, slice_b))

    return ops_a, ops_b


def _decorate(ops, source, delete_color="#32CD32", insert_color="#FF69B4"):
    string = ""
    for op in ops:
        name = op[0]
        text = op[1]

        if name == "equal":
            string += text

        elif name == "replace":
            if source:
                text = ("<font color=%s><s>" % delete_color) + text + "</s></font>"
            else:
                text = ("<font color=%s>" % insert_color) + text + "</font>"
            string += text

        elif name == "delete":
            text = ("<font color=%s><s>" % delete_color) + text + "</s></font>"
            string += text

        elif name == "insert":
            text = ("<font color=%s>" % insert_color) + text + "</font>"
            string += text

        else:
            string += text

    return string


def _is_numerical(text):
    try:
        float(text)
        return True
    except ValueError:
        return False
