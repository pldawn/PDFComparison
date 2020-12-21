import re
import jieba
from jieba import posseg
import Levenshtein as edit
from collections import OrderedDict
from pdfminer.pdfparser import PDFParser as mPDFParser, PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams
from CSS import get_css


jieba.load_userdict("userdict.txt")


class PDFParser:
    def __init__(self):
        self.__resources_manager = PDFResourceManager()
        self.__params_manager = LAParams()
        self.__aggregator = PDFPageAggregator(rsrcmgr=self.__resources_manager, laparams=self.__params_manager)
        self.__interpreter = PDFPageInterpreter(rsrcmgr=self.__resources_manager, device=self.__aggregator)
        self.__analyzer = None

    def parse(self, input_path, password=""):
        result = []

        parser = mPDFParser(open(input_path, "rb"))
        document = PDFDocument()
        parser.set_document(document)
        document.set_parser(parser)
        document.initialize(password=password)

        for page in document.get_pages():
            self.__interpreter.process_page(page)
            layout = self.__aggregator.get_result()

            for out in layout:
                if hasattr(out, 'get_text'):
                    content = out.get_text().strip()
                    content = content.replace('\n', '|')
                    result.append((out.x0, out.height, content))

        return result

    def analyze(self, rule, parse_result):
        if rule == "Monetary Policy Report":
            self.__analyzer = MonetaryPolicyReportAnalyzer()
            result = self.__analyzer.analyze(parse_result)

        else:
            print("rule is invalid, doesn't analyze content")
            return parse_result

        return result


class MonetaryPolicyReportAnalyzer:
    def __init__(self):
        self.pages = OrderedDict()
        self.index_tree = IndexNode()
        self.most_height = 0
        self.most_x0 = 0
        self.title_max_length = 30
        self.pdf_name = ""

    def analyze(self, parse_result):
        self.pages = self.divide_to_pages(parse_result)
        self.pdf_name = self.get_pdf_name(self.pages)
        self.most_height = self.get_most_height(self.pages)
        self.pages = self.delete_non_text_part(self.pages)
        self.most_x0 = self.get_most_x0(self.pages)
        self.pages = self.merge_continuous_paragraph(self.pages)
        plain_text = self.concat_pages_to_plain_text(self.pages)
        self.index_tree = self.convert_to_tree(plain_text)

        return self.index_tree

    def get_most_height(self, pages_dict):
        contents = []
        for value in pages_dict.values():
            contents += value

        heights = [item[1] for item in contents]
        freq_dict = {}

        for height in heights:
            freq_dict[height] = freq_dict.setdefault(height, 0) + 1

        heights = [(k, v) for k, v in freq_dict.items()]
        heights.sort(key=lambda x: x[1])

        most_height = heights[-1][0]

        return most_height

    def get_most_x0(self, pages_dict):
        contents = []
        for value in pages_dict.values():
            contents += value

        x0s = [item[0] for item in contents]
        freq_dict = {}

        for x0 in x0s:
            freq_dict[x0] = freq_dict.setdefault(x0, 0) + 1

        x0s = [(k, v) for k, v in freq_dict.items()]
        x0s.sort(key=lambda x: x[1])

        most_x0 = x0s[-1][0]

        return most_x0

    def get_pdf_name(self, pages_dict):
        first_path_content = pages_dict['O']
        pdf_name = first_path_content[0][-1] + first_path_content[1][-1]

        return pdf_name

    def divide_to_pages(self, parse_result):
        cache = []
        in_page = False
        pages_dict = OrderedDict()
        parse_result = parse_result + [(0, 0, '')]

        for ind in range(len(parse_result)):
            line = parse_result[ind]
            content = line[-1]

            if content.strip() == "":
                if not in_page:
                    continue
                else:
                    page_index = cache[-1][-1].strip()
                    page_content = cache[:-1]

                    if not (page_index.isnumeric() or re.match('[IVX]+', page_index)):
                        # 首页
                        if not pages_dict:
                            page_index = 'O'
                            page_content = cache
                        else:
                            page_index = cache[0][-1].strip()
                            page_content = cache[1:]

                    pages_dict[page_index] = page_content
                    in_page = False
                    cache = []
            else:
                if not in_page:
                    in_page = True
                cache.append(line)

        return pages_dict

    def delete_non_text_part(self, pages_dict):
        in_table, match_table_ending, in_figure, in_column = False, False, False, False

        for page_index, pages_content in pages_dict.items():
            if not page_index.isnumeric():
                continue

            tables, figures, columns = [], [], []

            for ind in range(len(pages_content)):
                line = pages_content[ind]
                (_, height, content) = line

                if not (in_table or in_figure or in_column):
                    if re.match('专栏 \\d+ ', content):
                        in_column = True
                        columns.append(ind)

                    elif re.match('表 \\d+ ', content):
                        in_table = True
                        tables.append(ind)
                        match_table_ending = False

                    elif re.match('数据来源：[^。]+?。', content):
                        figures.append(ind)

                        if not re.match('.+?图 \\d+ ', content):
                            in_figure = True
                    continue

                if in_column:
                    if height > min(14, self.most_height) and self.check_chinese(content) and "数据来源" not in content:
                        in_column = False

                        if not (in_table or in_figure or in_column):
                            if re.match('专栏 \\d+ ', content):
                                in_column = True
                                columns.append(ind)

                            elif re.match('表 \\d+ ', content):
                                in_table = True
                                tables.append(ind)
                                match_table_ending = False

                            elif re.match('数据来源：[^。]+?。', content):
                                figures.append(ind)

                                if not re.match('.+?图 \\d+ ', content):
                                    in_figure = True

                    else:
                        columns.append(ind)
                    continue

                if in_table:
                    if re.match('.*?数据来源：[^。]+?。', content):
                        match_table_ending = True
                        tables.append(ind)
                        continue

                    if match_table_ending and height > min(14, self.most_height) and self.check_chinese(content):
                        in_table = False

                        if not (in_table or in_figure or in_column):
                            if re.match('专栏 \\d+ ', content):
                                in_column = True
                                columns.append(ind)

                            elif re.match('表 \\d+ ', content):
                                in_table = True
                                tables.append(ind)
                                match_table_ending = False

                            elif re.match('数据来源：[^。]+?。', content):
                                figures.append(ind)

                                if not re.match('.+?图 \\d+ ', content):
                                    in_figure = True

                    else:
                        if re.match('表 \\d+ {1,2}', content):
                            match_table_ending = False
                        tables.append(ind)
                    continue

                if in_figure:
                    if re.match('图 \\d+ {1,2}', content):
                        in_figure = False

                        if not (in_table or in_figure or in_column):
                            if re.match('专栏 \\d+ ', content):
                                in_column = True
                                columns.append(ind)

                            elif re.match('表 \\d+ ', content):
                                in_table = True
                                tables.append(ind)
                                match_table_ending = False

                            elif re.match('数据来源：[^。]+?。', content):
                                figures.append(ind)

                                if not re.match('.+?图 \\d+ ', content):
                                    in_figure = True

                    figures.append(ind)
                    continue

            cache = [item for item in pages_content if pages_content.index(item) not in (tables + figures + columns)]
            pages_dict[page_index] = cache

        return pages_dict

    def check_chinese(self, text):
        if re.search("[\u4e00-\u9fa5]", text):
            return True

        return False

    def merge_continuous_paragraph(self, pages_dict):
        for page_index, page_content in pages_dict.items():
            if not page_index.isnumeric() or not page_content:
                continue

            cache_page_content = []
            cache_content = ""
            cache_height = []
            cache_x0 = 0

            for ind in range(len(page_content)):
                (x0, height, content) = page_content[ind]

                if abs(x0 - self.most_x0) >= 5:
                    if cache_content:
                        cache_mean_height = sum(cache_height) / len(cache_height)
                        cache_page_content.append((cache_x0, cache_mean_height, cache_content))

                        cache_content = ""
                        cache_height = []

                    cache_content += content
                    cache_height.append(height)
                    cache_x0 = x0
                else:
                    cache_content += content
                    cache_height.append(height)

                    if ind == 0:
                        cache_x0 = x0

            cache_mean_height = sum(cache_height) / len(cache_height)
            cache_page_content.append((cache_x0, cache_mean_height, cache_content))

            pages_dict[page_index] = cache_page_content

        return pages_dict

    def concat_pages_to_plain_text(self, pages_dict):
        plain_text = []

        for page_index, page_content in pages_dict.items():
            if not page_index.isnumeric() or not page_content:
                continue

            for (x0, height, content) in page_content:
                if abs(x0 - self.most_x0) >= 5:
                    plain_text.append([page_index, x0, height, content])
                else:
                    plain_text[-1][2] = (plain_text[-1][1] + height) / 2
                    plain_text[-1][3] += content

        return plain_text

    def get_index_token(self, text):
        pattern = re.compile('第[一二三四五六七八九十]{1,2}部分')
        result = re.match(pattern, text)
        if result:
            return 'A'

        pattern = re.compile('([一二三四五六七八九十]{1,2})([.、])')
        result = re.match(pattern, text)
        if result:
            return 'B'

        pattern = re.compile('[（(][一二三四五六七八九十0-9]{1,2}[)）]')
        result = re.match(pattern, text)
        if result:
            return 'C'

        pattern = re.compile('([0-9]{1,2})([.、])')
        result = re.match(pattern, text)
        if result:
            return 'D'

        return None

    def convert_to_tree(self, plain_text):
        root_node = IndexNode()
        root_node.title = self.pdf_name
        parent_stack = [('root', root_node)]

        for (page_index, x0s, height, content) in plain_text:
            index_token = self.get_index_token(content.replace(" ", ""))

            if len(content) <= self.title_max_length and index_token is not None:
                new_node = IndexNode()
                new_node.page = page_index
                new_node.title = content
                is_added = False

                # 与上一标题行平级
                for i in range(len(parent_stack), 0, -1):
                    ind = i - 1
                    if parent_stack[ind][0] == index_token:
                        while len(parent_stack) > ind:
                            parent_stack.pop()
                        parent_stack[-1][1].children.append(new_node)
                        new_node.parent = parent_stack[-1][1]
                        parent_stack.append((index_token, new_node))
                        is_added = True
                        break

                if not is_added:
                    parent_stack[-1][1].children.append(new_node)
                    new_node.parent = parent_stack[-1][1]
                    parent_stack.append((index_token, new_node))

            else:
                parent_stack[-1][1].paragraphs.append(content.replace(" ", ""))

        return root_node


class IndexNode:
    def __init__(self):
        self.title = ""
        self.paragraphs = []
        self.children = []
        self.parent = "root"
        self.page = 0


class PDFComparer:
    def __init__(self):
        self.pdfs = []

    def compare_two_pdf(self, pdf_a_path, pdf_b_path, rule, password_a="", password_b=""):
        self.pdfs = []

        parser_a = PDFParser()
        parse_result_a = parser_a.parse(pdf_a_path, password_a)
        index_tree_a = parser_a.analyze(rule, parse_result_a)
        self.pdfs.append(index_tree_a)

        parser_b = PDFParser()
        parse_result_b = parser_b.parse(pdf_b_path, password_b)
        index_tree_b = parser_b.analyze(rule, parse_result_b)
        self.pdfs.append(index_tree_b)

        return self.pdfs

    def to_html(self, output_path):
        if not self.pdfs:
            raise AttributeError("haven't call compare_two_pdf interface.")

        with open(output_path, "w", encoding="utf-8") as f:
            css = get_css()
            f.write(css + "\n")
            f.write("<table>\n")

            # title
            path = [["t"]]
            str3, str4 = self.align_text([path])
            self.write_to_frame(f, "项目", "", str3, str4, header=True)

            # 总体基调
            path = [["c5"], ["c1"], ["p2"]]
            str3, str4 = self.align_paragraphs([path])
            self.write_to_frame(f, "总体基调", "", str3, str4)

            # 货币政策展望
            ## 流动性基调
            path = [["c5"], ["c2"], ["ps1"]]
            str3, str4 = self.align_text([path], ["稳健的货币政策"])
            self.write_to_frame(f, "货币政策展望", "流动性", str3, str4, 5)

            ## 风险防控
            path = [["c5"], ["c2"], ["ps1"]]
            str3, str4 = self.align_text([path], ["金融风险"])
            self.write_to_frame(f, "", "风险防控", str3, str4)

            ## 房地产
            path = [["c5"], ["c2"], ["ps-1"]]
            str3, str4 = self.align_text([path], ["房子"])
            self.write_to_frame(f, "", "房地产", str3, str4)

            ## 信贷
            path = [["c5"], ["c2"], ["ps1"]]
            str3, str4 = self.align_text([path], ["再贷款", "再贴现", "信贷", "工具"])
            self.write_to_frame(f, "", "信贷", str3, str4)

            ## 汇率
            path = [["c5"], ["c2"], ["ps1"]]
            str3, str4 = self.align_text([path], ["汇率"])
            self.write_to_frame(f, "", "汇率", str3, str4)

            # 货币政策回顾
            ## 流动性
            path = [["c1"], ["c"], ["t"]]
            str3, str4 = self.align_text([path], ["流动性"])
            self.write_to_frame(f, "货币政策回顾", "流动性", str3, str4, 8)

            ## 政策工具
            path = [["c2"], ["c"], ["t"]]
            str3, str4 = self.align_text([path], ["操作", "便利", "货币信贷", "准备金率"])
            self.write_to_frame(f, "", "政策工具", str3, str4)

            ## 宏观审慎
            path = [["c2"], ["c"], ["t"]]
            str3, str4 = self.align_text([path], ["宏观审慎"])
            self.write_to_frame(f, "", "宏观审慎", str3, str4)

            ## 信贷
            path = [["c2"], ["c"], ["t"]]
            str3, str4 = self.align_text([path], ["信贷政策"])
            self.write_to_frame(f, "", "信贷", str3, str4)

            ## 汇率
            path1 = [["c1"], ["c"], ["t"]]
            path2 = [["c2"], ["c"], ["p1s1"]]
            str3, str4 = self.align_text([path1, path2], ["汇率"])
            self.write_to_frame(f, "", "汇率", str3, str4)

            ## 本外币存款
            path = [["c1"], ["c2"], ["t"]]
            str3, str4 = self.align_text([path], ["贷款", "存款"])
            self.write_to_frame(f, "", "本外币存贷款", str3, str4)

            ## 社融
            path = [["c1"], ["c"], ["t"]]
            str3, str4 = self.align_text([path], ["社会融资"])
            self.write_to_frame(f, "", "社融", str3, str4)

            ## 风险处置
            path = [["c2"], ["c"], ["t"]]
            str3, str4 = self.align_text([path], ["金融风险"])
            self.write_to_frame(f, "", "风险处置", str3, str4)

            # 世界经济形势
            ## 经济增速
            path = [["c4"], ["c1"], ["c1"], ["p1s1"]]
            str3, str4 = self.align_text([path])
            self.write_to_frame(f, "世界经济形势", "经济增速", str3, str4)

            # 国内经济形势
            ## 经济增速
            path1 = [["c4"], ["c2"], ["p1s1"]]
            path2 = [["c4"], ["c1"], ["p1s1", "p2s1", "p3s1"]]
            str3, str4 = self.align_text([path1, path2])
            self.write_to_frame(f, "国内经济形势", "经济增速", str3, str4, 8)

            # 消费
            path = [["c4"], ["c2"], ["c1"], ["p1s1"]]
            str3, str4 = self.align_text([path])
            self.write_to_frame(f, "", "消费", str3, str4)

            # 投资
            path = [["c4"], ["c2"], ["c1"], ["p2s1"]]
            str3, str4 = self.align_text([path])
            self.write_to_frame(f, "", "投资", str3, str4)

            # 进出口
            path = [["c4"], ["c2"], ["c1"], ["p3s1"]]
            str3, str4 = self.align_text([path])
            self.write_to_frame(f, "", "进出口", str3, str4)

            # 农业
            path = [["c4"], ["c2"], ["c2"], ["p2s1"]]
            str3, str4 = self.align_text([path])
            self.write_to_frame(f, "", "农业", str3, str4)

            # 工业
            path = [["c4"], ["c2"], ["c2"], ["p3s1"]]
            str3, str4 = self.align_text([path])
            self.write_to_frame(f, "", "工业", str3, str4)

            # 服务业
            path = [["c4"], ["c2"], ["c2"], ["p4s1"]]
            str3, str4 = self.align_text([path])
            self.write_to_frame(f, "", "服务业", str3, str4)

            # 财政收支
            path = [["c4"], ["c2"], ["c4"], ["t"]]
            str3, str4 = self.align_text([path])
            self.write_to_frame(f, "", "财政与就业", str3, str4)

            # 价格形势
            ## 总体趋势
            path = [["c5"], ["c1"], ["p4s1"]]
            str3, str4 = self.align_text([path])
            self.write_to_frame(f, "价格形势", "总体趋势", str3, str4, 3)

            ## CPI
            path = [["c4"], ["c2"], ["c3"], ["p1s1"]]
            str3, str4 = self.align_text([path])
            self.write_to_frame(f, "", "CPI", str3, str4)

            ## PPI
            path = [["c4"], ["c2"], ["c3"], ["p2s1"]]
            str3, str4 = self.align_text([path])
            self.write_to_frame(f, "", "PPI", str3, str4)

            # 金融市场运行回顾
            ## 货币市场
            path = [["c3"], ["c1"], ["c1"], ["t"]]
            str3, str4 = self.align_text([path])
            self.write_to_frame(f, "金融市场运行回顾", "货币市场", str3, str4, 7)

            ## 债券市场
            path = [["c3"], ["c1"], ["c2"], ["t"]]
            str3, str4 = self.align_text([path])
            self.write_to_frame(f, "", "债券市场", str3, str4)

            ## 票据市场
            path = [["c3"], ["c1"], ["c3"], ["t"]]
            str3, str4 = self.align_text([path])
            self.write_to_frame(f, "", "票据市场", str3, str4)

            ## 股票市场
            path = [["c3"], ["c1"], ["c4"], ["t"]]
            str3, str4 = self.align_text([path])
            self.write_to_frame(f, "", "股票市场", str3, str4)

            ## 保险市场
            path = [["c3"], ["c1"], ["c5"], ["t"]]
            str3, str4 = self.align_text([path])
            self.write_to_frame(f, "", "保险市场", str3, str4)

            ## 外汇市场
            path = [["c3"], ["c1"], ["c6"], ["t"]]
            str3, str4 = self.align_text([path])
            self.write_to_frame(f, "", "外汇市场", str3, str4)

            ## 黄金市场
            path = [["c3"], ["c1"], ["c7"], ["t"]]
            str3, str4 = self.align_text([path])
            self.write_to_frame(f, "", "黄金市场", str3, str4)

            f.write("</table>\n")

    def align_text(self, path_list, keywords=None):
        result_a, result_b = [], []

        for path in path_list:
            text_a_list = self.find_content(self.pdfs[0], path, keywords)
            text_b_list = self.find_content(self.pdfs[1], path, keywords)

            if len(text_a_list) > 1:
                text_a_list.sort(key=lambda x: -len(x))

                for i in range(len(text_a_list)):
                    i = len(text_a_list) - 1 - i

                    for j in range(i):
                        if text_a_list[i].strip("。") in text_a_list[j]:
                            text_a_list.pop(i)
                            break

            if len(text_b_list) > 1:
                text_b_list.sort(key=lambda x: -len(x))

                for i in range(len(text_b_list)):
                    i = len(text_b_list) - 1 - i

                    for j in range(i):
                        if text_b_list[i].strip("。") in text_b_list[j]:
                            text_b_list.pop(i)
                            break

            paragraph_a = "。".join(text_a_list)
            paragraph_b = "。".join(text_b_list)

            res_a, res_b = self.align_paragraphs_core(paragraph_a, paragraph_b)

            result_a.append(res_a)
            result_b.append(res_b)

            # text = zip(text_a_list, text_b_list)
            #
            # for text_a, text_b in text:
            #     (ops_a, ops_b) = self.edit_ops(text_a.strip("。"), text_b.strip("。"))
            #     result_a.append(self.decorate(ops_a, True))
            #     result_b.append(self.decorate(ops_b, False))

        result_a = "<br><br>".join(result_a)
        result_a = result_a.replace("<br><br><br><br>", "<br><br>")
        result_b = "<br><br>".join(result_b)
        result_b = result_b.replace("<br><br><br><br>", "<br><br>")

        return result_a, result_b

    def align_paragraphs(self, path_list):
        paragraph_a = self.find_content(self.pdfs[0], path_list[0])[0]
        paragraph_b = self.find_content(self.pdfs[1], path_list[0])[0]
        result_a, result_b = self.align_paragraphs_core(paragraph_a, paragraph_b)

        return result_a, result_b

    def align_paragraphs_core(self, paragraph_a, paragraph_b):
        sent_list_a = re.split("\\W", paragraph_a) if paragraph_a else []
        punc_list_a = re.split("\\w", paragraph_a)[1:-1] if paragraph_a else []
        punc_list_a = [i for i in punc_list_a if i]
        sent_list_b = re.split("\\W", paragraph_b) if paragraph_b else []
        punc_list_b = re.split("\\w", paragraph_b)[1:-1] if paragraph_b else []
        punc_list_b = [i for i in punc_list_b if i]
        alignment_sents = self.align_text_list_for_paragraphs(sent_list_a, sent_list_b)

        alignment_ops = []
        for i in range(len(alignment_sents)):
            text_a = sent_list_a[alignment_sents[i][0]] if alignment_sents[i][0] != 100 else ""
            text_b = sent_list_b[alignment_sents[i][1]] if alignment_sents[i][1] != 100 else ""
            alignment_ops.append((self.edit_ops(text_a, text_b)))

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

        result_a = self.decorate(ops_a, True).replace("。", "<br><br>")
        result_b = self.decorate(ops_b, False).replace("。", "<br><br>")

        return result_a, result_b

    def align_text_list_for_paragraphs(self, list_a, list_b):
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

        alignment = self.align_distances_for_paragraphs(distances, list_a, list_b)

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

    def align_distances_for_paragraphs(self, distances, list_a, list_b):
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
        alignment_cache = alignment_cache + self.align_distances_for_paragraphs(distances, list_a, list_b)

        for item in alignment_cache:
            if len(item) == 2:
                alignment.append(item)
            elif item[-1] <= 1:
                alignment.append((item[0], item[1]))
            else:
                alignment.append((item[0], 100))
                alignment.append((100, item[1]))

        return alignment

    def edit_ops(self, text_a, text_b):
        ops_a, ops_b = [], []

        if not text_a and not text_b:
            return ops_a, ops_b

        if text_a and not text_b:
            ops_a.append(("delete", text_a))

            return ops_a, ops_b

        if not text_a and text_b:
            ops_b.append(("insert", text_b))

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

        ops = edit.opcodes(text_a, text_b)
        for op in ops:
            op_name = op[0]
            cache_a = text_a[op[1]: op[2]]
            cache_b = text_b[op[3]: op[4]]

            slice_a = ""
            for tk in cache_a:
                slice_a += word_dict_rev[tk]

            slice_b = ""
            for tk in cache_b:
                slice_b += word_dict_rev[tk]

            if self.is_numerical(slice_a) and self.is_numerical(slice_b):
                op_name = "equal"

            # if len(slice_a) == 1 or len(slice_b) == 1:
            #     op_name = "equal"

            if slice_a:
                ops_a.append((op_name, slice_a))
            if slice_b:
                ops_b.append((op_name, slice_b))

        return ops_a, ops_b

    def find_content(self, tree, path, keywords=None):
        # path = [[c1], [c2], [t], [p1s1s2, p2]]
        path = path.copy()
        result = [tree]
        cache = []

        while path:
            route = path.pop(0)
            for ind in range(len(result)):
                tree = result[ind]

                for r in route:
                    if r.startswith("c"):
                        if r == "c":
                            for c in tree.children:
                                cache.append(c)
                        else:
                            index = int(r[1:]) - 1
                            try:
                                position = tree.children[index]
                                cache.append(position)
                            except IndexError:
                                pass
                    elif r.startswith("t"):
                        try:
                            position = tree.title
                            head = position[:4]
                            if "、" in head:
                                start = head.index("、") + 1
                            elif "）" in head:
                                start = head.index("）") + 1
                            elif "." in head:
                                start = head.index(".") + 1
                            else:
                                start = 0
                            position = position[start:]
                            cache.append(position + "。")
                        except IndexError:
                            pass
                    elif r.startswith("p"):
                        if "s" in r:
                            first_s = r.index("s")
                            if r[:first_s] == "p":
                                for paragraphs in tree.paragraphs:
                                    try:
                                        sents = r[first_s + 1:].split("s")
                                        paragraphs = re.split("[。？！]", paragraphs)
                                        for s in sents:
                                            try:
                                                position = paragraphs[int(s) - 1]
                                                head = position[:3]
                                                if "是" in head:
                                                    start = position.index("是") + 1
                                                else:
                                                    start = 0
                                                position = position[start:]
                                                cache.append(position + "。")
                                            except IndexError:
                                                pass
                                    except IndexError:
                                        pass

                            else:
                                index = int(r[1:first_s]) - 1
                                try:
                                    sents = r[first_s + 1:].split("s")
                                    paragraphs = re.split("[。？！]", tree.paragraphs[index])
                                    for s in sents:
                                        try:
                                            position = paragraphs[int(s) - 1]
                                            head = position[:3]
                                            if "是" in head:
                                                start = position.index("是") + 1
                                            else:
                                                start = 0
                                            position = position[start:]
                                            cache.append(position + "。")
                                        except IndexError:
                                            pass
                                except IndexError:
                                    pass

                        else:
                            if r == "p":
                                for position in tree.paragraphs:
                                    try:
                                        head = position[:3]
                                        if "是" in head:
                                            start = position.index("是") + 1
                                        else:
                                            start = 0
                                        position = position[start:]
                                        cache.append(position + "。")
                                    except IndexError:
                                        pass

                            else:
                                index = int(r[1:]) - 1
                                try:
                                    position = tree.paragraphs[index]
                                    head = position[:3]
                                    if "是" in head:
                                        start = position.index("是") + 1
                                    else:
                                        start = 0
                                    position = position[start:]
                                    cache.append(position + "。")
                                except IndexError:
                                    pass
                    else:
                        raise ValueError("find_content")

            result = cache
            cache = []

        if keywords:
            cache = result
            result = []

            for res in cache:
                score = 0
                for kw in keywords:
                    if kw in res:
                        score += 1

                if score / len(keywords) >= 0.1:
                    result.append(res)

        return result

    def write_to_frame(self, f, str1, str2, str3, str4, rowspan1=1, rowspan2=1, header=False, reverse=True):
        if reverse:
            cache = str3
            str3 = str4
            str4 = cache

        if str1 and str2:
            f.write(" <tr>\n")
            f.write("  <th rowspan='%s'>%s</th>\n" % (rowspan1, str1))
            f.write("  <th rowspan='%s'>%s</th>\n" % (rowspan2, str2))
            f.write("  <td>%s</td>\n" % str3)
            f.write("  <td>%s</td>\n" % str4)
            f.write(" </tr>\n")

        elif str1 and not str2:
            if header:
                f.write(" <tr>\n")
                f.write("  <th colspan='2'>%s</th>\n" % str1)
                f.write("  <th>%s</th>\n" % str3)
                f.write("  <th>%s</th>\n" % str4)
                f.write(" </tr>\n")
            else:
                f.write(" <tr>\n")
                f.write("  <th colspan='2'>%s</th>\n" % str1)
                f.write("  <td>%s</td>\n" % str3)
                f.write("  <td>%s</td>\n" % str4)
                f.write(" </tr>\n")

        elif not str1 and str2:
            f.write(" <tr>\n")
            f.write("  <th rowspan='%s'>%s</th>\n" % (rowspan2, str2))
            f.write("  <td>%s</td>\n" % str3)
            f.write("  <td>%s</td>\n" % str4)
            f.write(" </tr>\n")

        elif not str1 and not str2:
            f.write(" <tr>\n")
            f.write("  <td>%s</td>\n" % str3)
            f.write("  <td>%s</td>\n" % str4)
            f.write(" </tr>\n")

    def decorate(self, ops, source, delete_color="#FF69B4", insert_color="#32CD32"):
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

    def is_numerical(self, text):
        try:
            float(text)
            return True
        except ValueError:
            return False
