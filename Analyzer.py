import re
from collections import OrderedDict


class IndexNode:
    def __init__(self):
        self.title = ""
        self.paragraphs = []
        self.children = []
        self.parent = "root"
        self.page = 0


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