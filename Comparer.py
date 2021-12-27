import re
from CSS import get_css
from PDFParser import PDFParser
from alignment_methods import align_text


class ReportComparer:
    def __init__(self, rule):
        """
        报告对比，根据rule选择对比的报告类型
        :param rule: str, 目前的有效值：Monetary Report--货币政策执行报告,
                Monetary Committee--货币政策委员会季度例会
        """
        self.rule = rule

        if self.rule == "Monetary Report":
            self.comparer = MonetaryReportComparer()

        elif self.rule == "Monetary Committee":
            self.comparer = MonetaryCommitteeComparer()

        else:
            self.comparer = None

    def compare_report(self, new_report, old_report, **kwargs):
        """
        报告对比，根据rule自动调用不同的对比模块，传入参数根据rule有所变化，具体参考各实际调用接口
        :param new_report: str，新报告
        :param old_report: str，旧报告
        :param kwargs: dict，额外参数
        :return: List[Tuple[str, ..., List[str], List[str]]]
        """
        return self.comparer.compare_report(new_report, old_report, **kwargs)

    def compare_text(self, new_text, old_text):
        """
        对比两个字符串
        :param new_text: str，新的文本
        :param old_text: str，旧的文本
        :return: Tuple[List[str], List[str]]，对比结果，按照句号进行划分，以优化显示效果
        """
        return self.comparer.compare_text(new_text, old_text)


class MonetaryCommitteeComparer:
    def __init__(self):
        self.tagging_result = []
        self.project_name = []

    def compare_report(self, new_report, old_report, **kwargs):
        """
        对比货币政策委员会例会记录
        :param new_report: List[str]，新报告，按段分割
        :param old_report: List[str]，旧报告，按段分割
        :param kwargs: dict，占位参数，目前包含4个可用参数；
                        to_html：bool, True时，输出html文件路径，反之输出对比结果列表；
                        output_path：str, 当to_html=True时，指定文件保存路径，默认为"./result.html"；
                        new_report_name：str，新报告的名称，如不提供则从报告第一段抽取；
                        old_report_name：str，旧报告的名称，如不提供则从报告第一段抽取；
        :return: List[Tuple[str, List[str], List[str]]]，对比结果每个Tuple是一行对比结果，Tuple中的str
                  是该行的行名，List[str]是新旧报告在该行的对比结果
        """
        self._load_report(new_report, old_report, **kwargs)

        if not kwargs.get("to_html", False):
            comparison_result = [("项目", self.project_name[0], self.project_name[1])]

            # 经济形势
            new_text = self.tagging_result[0]["经济形势"]
            old_text = self.tagging_result[1]["经济形势"]
            comparison = self.compare_text("。".join(new_text), "。".join(old_text))
            comparison_result.append(("经济形势", comparison[0], comparison[1]))

            # 政策基调
            new_text = self.tagging_result[0]["政策基调"]
            old_text = self.tagging_result[1]["政策基调"]
            comparison = self.compare_text("。".join(new_text), "。".join(old_text))
            comparison_result.append(("政策基调", comparison[0], comparison[1]))

            # 货币政策
            new_text = self.tagging_result[0]["货币政策"]
            old_text = self.tagging_result[1]["货币政策"]
            comparison = self.compare_text("。".join(new_text), "。".join(old_text))
            comparison_result.append(("货币政策", comparison[0], comparison[1]))

            # 结构性政策工具
            new_text = self.tagging_result[0]["结构性政策工具"]
            old_text = self.tagging_result[1]["结构性政策工具"]
            comparison = self.compare_text("。".join(new_text), "。".join(old_text))
            comparison_result.append(("结构性政策工具", comparison[0], comparison[1]))

            # 利率
            new_text = self.tagging_result[0]["利率"]
            old_text = self.tagging_result[1]["利率"]
            comparison = self.compare_text("。".join(new_text), "。".join(old_text))
            comparison_result.append(("利率", comparison[0], comparison[1]))

            # 汇率
            new_text = self.tagging_result[0]["汇率"]
            old_text = self.tagging_result[1]["汇率"]
            comparison = self.compare_text("。".join(new_text), "。".join(old_text))
            comparison_result.append(("汇率", comparison[0], comparison[1]))

            # 金融支持实体
            new_text = self.tagging_result[0]["金融支持实体"]
            old_text = self.tagging_result[1]["金融支持实体"]
            comparison = self.compare_text("。".join(new_text), "。".join(old_text))
            comparison_result.append(("金融支持实体", comparison[0], comparison[1]))

            # 双向开放
            new_text = self.tagging_result[0]["双向开放"]
            old_text = self.tagging_result[1]["双向开放"]
            comparison = self.compare_text("。".join(new_text), "。".join(old_text))
            comparison_result.append(("双向开放", comparison[0], comparison[1]))

            # 房地产
            new_text = self.tagging_result[0]["房地产"]
            old_text = self.tagging_result[1]["房地产"]
            comparison = self.compare_text("。".join(new_text), "。".join(old_text))
            comparison_result.append(("房地产", comparison[0], comparison[1]))

            # 总体要求
            new_text = self.tagging_result[0]["总体要求"]
            old_text = self.tagging_result[1]["总体要求"]
            comparison = self.compare_text("。".join(new_text), "。".join(old_text))
            comparison_result.append(("总体要求", comparison[0], comparison[1]))

            return comparison_result

        else:
            self._to_html(kwargs.get("output_path", "./result.html"))

            return kwargs.get("output_path", "./result.html")

    def compare_text(self, new_text, old_text, join=False):
        """
        对比两个字符串
        :param new_text: str，新的文本
        :param old_text: str，旧的文本
        :param join: bool
        :return: Tuple[List[str], List[str]]，对比结果，按照句号进行划分，以优化显示效果
        """
        new_result, old_result = align_text(new_text, old_text, join=join)

        return new_result, old_result

    def _to_html(self, output_path):
        with open(output_path, "w", encoding="utf-8") as f:
            css = get_css()
            f.write(css + "\n")
            f.write("<table>\n")

            f.write(" <tr>\n")
            f.write("  <th>%s</th>\n" % "项目")
            f.write("  <th>%s</th>\n" % self.project_name[0])
            f.write("  <th>%s</th>\n" % self.project_name[1])
            f.write(" </tr>\n")

            # 经济形势
            new_text = self.tagging_result[0]["经济形势"]
            old_text = self.tagging_result[1]["经济形势"]
            comparison = self.compare_text("。".join(new_text), "。".join(old_text), join=True)
            f.write(" <tr>\n")
            f.write("  <th>%s</th>\n" % "经济形势")
            f.write("  <td>%s</td>\n" % comparison[0])
            f.write("  <td>%s</td>\n" % comparison[1])
            f.write(" </tr>\n")

            # 政策基调
            new_text = self.tagging_result[0]["政策基调"]
            old_text = self.tagging_result[1]["政策基调"]
            comparison = self.compare_text("。".join(new_text), "。".join(old_text), join=True)
            f.write(" <tr>\n")
            f.write("  <th>%s</th>\n" % "政策基调")
            f.write("  <td>%s</td>\n" % comparison[0])
            f.write("  <td>%s</td>\n" % comparison[1])
            f.write(" </tr>\n")

            # 货币政策
            new_text = self.tagging_result[0]["货币政策"]
            old_text = self.tagging_result[1]["货币政策"]
            comparison = self.compare_text("。".join(new_text), "。".join(old_text), join=True)
            f.write(" <tr>\n")
            f.write("  <th>%s</th>\n" % "货币政策")
            f.write("  <td>%s</td>\n" % comparison[0])
            f.write("  <td>%s</td>\n" % comparison[1])
            f.write(" </tr>\n")

            # 结构性政策工具
            new_text = self.tagging_result[0]["结构性政策工具"]
            old_text = self.tagging_result[1]["结构性政策工具"]
            comparison = self.compare_text("。".join(new_text), "。".join(old_text), join=True)
            f.write(" <tr>\n")
            f.write("  <th>%s</th>\n" % "结构性政策工具")
            f.write("  <td>%s</td>\n" % comparison[0])
            f.write("  <td>%s</td>\n" % comparison[1])
            f.write(" </tr>\n")

            # 利率
            new_text = self.tagging_result[0]["利率"]
            old_text = self.tagging_result[1]["利率"]
            comparison = self.compare_text("。".join(new_text), "。".join(old_text), join=True)
            f.write(" <tr>\n")
            f.write("  <th>%s</th>\n" % "利率")
            f.write("  <td>%s</td>\n" % comparison[0])
            f.write("  <td>%s</td>\n" % comparison[1])
            f.write(" </tr>\n")

            # 汇率
            new_text = self.tagging_result[0]["汇率"]
            old_text = self.tagging_result[1]["汇率"]
            comparison = self.compare_text("。".join(new_text), "。".join(old_text), join=True)
            f.write(" <tr>\n")
            f.write("  <th>%s</th>\n" % "汇率")
            f.write("  <td>%s</td>\n" % comparison[0])
            f.write("  <td>%s</td>\n" % comparison[1])
            f.write(" </tr>\n")

            # 金融支持实体
            new_text = self.tagging_result[0]["金融支持实体"]
            old_text = self.tagging_result[1]["金融支持实体"]
            comparison = self.compare_text("。".join(new_text), "。".join(old_text), join=True)
            f.write(" <tr>\n")
            f.write("  <th>%s</th>\n" % "金融支持实体")
            f.write("  <td>%s</td>\n" % comparison[0])
            f.write("  <td>%s</td>\n" % comparison[1])
            f.write(" </tr>\n")

            # 双向开放
            new_text = self.tagging_result[0]["双向开放"]
            old_text = self.tagging_result[1]["双向开放"]
            comparison = self.compare_text("。".join(new_text), "。".join(old_text), join=True)
            f.write(" <tr>\n")
            f.write("  <th>%s</th>\n" % "双向开放")
            f.write("  <td>%s</td>\n" % comparison[0])
            f.write("  <td>%s</td>\n" % comparison[1])
            f.write(" </tr>\n")

            # 房地产
            new_text = self.tagging_result[0]["房地产"]
            old_text = self.tagging_result[1]["房地产"]
            comparison = self.compare_text("。".join(new_text), "。".join(old_text), join=True)
            f.write(" <tr>\n")
            f.write("  <th>%s</th>\n" % "房地产")
            f.write("  <td>%s</td>\n" % comparison[0])
            f.write("  <td>%s</td>\n" % comparison[1])
            f.write(" </tr>\n")

            # 总体要求
            new_text = self.tagging_result[0]["总体要求"]
            old_text = self.tagging_result[1]["总体要求"]
            comparison = self.compare_text("。".join(new_text), "。".join(old_text), join=True)
            f.write(" <tr>\n")
            f.write("  <th>%s</th>\n" % "总体要求")
            f.write("  <td>%s</td>\n" % comparison[0])
            f.write("  <td>%s</td>\n" % comparison[1])
            f.write(" </tr>\n")

    def _load_report(self, new_report, old_report, **kwargs):
        self.tagging_result = []
        self.project_name = []

        new_split_report = self._preprocess(new_report)
        new_tagging_result = self._tagging(new_split_report)
        self.tagging_result.append(new_tagging_result)

        if kwargs.get("new_report_name", False):
            new_name = kwargs.get("new_report_name")
        else:
            new_name = re.match("中国人民银行货币政策委员会\\d{4}年第.季度", new_split_report[0][0]).group()
        self.project_name.append(new_name)

        old_split_report = self._preprocess(old_report)
        old_tagging_result = self._tagging(old_split_report)
        self.tagging_result.append(old_tagging_result)

        if kwargs.get("old_report_name", False):
            old_name = kwargs.get("old_report_name")
        else:
            old_name = re.match("中国人民银行货币政策委员会\\d{4}年第.季度", old_split_report[0][0]).group()
        self.project_name.append(old_name)

    def _preprocess(self, report):
        split_report = []
        for paragraph in report:
            split_report.append(paragraph.strip().strip("。").split('。'))

        return split_report

    def _remove_sentence(self, paragraph, tagging_class):
        if len(tagging_class) > 0:
            for item in tagging_class:
                for sentence in paragraph:
                    if item in sentence:
                        paragraph.remove(sentence)
                        break

    def _tagging(self, split_report):
        tagging_result = {}

        # 经济形势
        tagging_result['经济形势'] = []

        paragraph = split_report[1]
        if '会议认为' in paragraph[1]:
            if '经济' in paragraph[1] and '增长' in paragraph[1]:
                tagging_result['经济形势'].append(paragraph[1].replace('会议认为，', ''))
            if '国内' in paragraph[-1] and ('国际' in paragraph[-1] or '世界' in paragraph[-1]):
                tagging_result['经济形势'].append(paragraph[-1])

        paragraph = split_report[2]
        if '会议指出，要' not in paragraph[0]:
            if '，要' in paragraph[0]:
                tagging_result['经济形势'].append(paragraph[0][:paragraph[0].index('，要')].replace('会议指出，', ''))
            else:
                tagging_result['经济形势'].append(paragraph[0].replace('会议指出，', ''))

        # 政策基调
        tagging_result['政策基调'] = []

        if '会议指出，要' in paragraph[0]:
            tagging_result['政策基调'].append(paragraph[0][paragraph[0].index('，要'):].replace('，要', '要'))
        else:
            for sentence in paragraph:
                if '要' == sentence[0]:
                    tagging_result['政策基调'].append(sentence)
                    break
                elif '，要' in sentence:
                    tagging_result['政策基调'].append(sentence[sentence.index('，要'):].replace('，要', '要'))
                    break

        self._remove_sentence(paragraph, tagging_result['政策基调'])

        # 货币政策
        tagging_result['货币政策'] = []

        for sentence in paragraph:
            if ('货币政策' in sentence or '流动性' in sentence) and '企业' not in sentence:
                tagging_result['货币政策'].append(sentence)

                if len(tagging_result["货币政策"]) >= 2:
                    break

        self._remove_sentence(paragraph, tagging_result['货币政策'])

        # 结构性政策工具
        tagging_result['结构性政策工具'] = []

        for sentence in paragraph:
            if '政策工具' in sentence:
                tagging_result['结构性政策工具'].append(sentence)

        self._remove_sentence(paragraph, tagging_result['结构性政策工具'])

        # 汇率
        tagging_result['汇率'] = []

        for sentence in paragraph:
            if '汇率' in sentence:
                tagging_result['汇率'].append(sentence)

        self._remove_sentence(paragraph, tagging_result['汇率'])

        # 利率
        tagging_result['利率'] = []
        tagging_result['金融支持实体'] = []

        for sentence in paragraph:
            if '利率' in sentence and '实体' not in sentence:
                tagging_result['利率'].append(sentence)

            elif '利率' in sentence and '实体' in sentence:
                parts = sentence.split('，')
                for part in parts:
                    if '实体' in part:
                        tagging_result['利率'].append("，".join(parts[:parts.index(part)]))
                        tagging_result['金融支持实体'].append("，".join(parts[parts.index(part):]))
                        break

            elif '利率' not in sentence and '实体' in sentence:
                tagging_result['金融支持实体'].append(sentence)

        # 双向开放
        tagging_result['双向开放'] = []

        for sentence in paragraph:
            if '双向开放' in sentence or '对外开放' in sentence:
                tagging_result['双向开放'].append(sentence)

        self._remove_sentence(paragraph, tagging_result['双向开放'])

        # 房地产
        tagging_result["房地产"] = []

        for sentence in paragraph:
            if "房地产" in sentence or "住房" in sentence:
                tagging_result["房地产"].append(sentence)

        # 总体要求
        tagging_result['总体要求'] = []

        for sentence in split_report[3]:
            tagging_result['总体要求'].append(sentence.replace('会议强调，', ''))

        return tagging_result


class MonetaryReportComparer:
    def __init__(self):
        self.report = []

    def compare_report(self, new_report, old_report, **kwargs):
        """
        对比货币政策执行报告
        :param new_report: str, 新报告的路径
        :param old_report: str, 旧报告的路径
        :param kwargs: 占位参数，目前包含2个可用参数；
                        to_html：bool, True时，输出html文件路径，反之输出对比结果列表；
                        output_path：str, 当to_html=True时，指定文件保存路径，默认为"./result.html"
        :return: Union[str, List[Tuple[str, str, str, str]]],
                 当to_html=True时，输出html文件路径；反之，输出对比结果列表
        """
        self._load_report(new_report, old_report, **kwargs)

        if kwargs.get("to_html", False):
            self._to_html(kwargs.get("output_path", "./result.html"))
            return kwargs.get("output_path", "./result.html")

        else:
            return self._to_stdout()

    def compare_text(self, new_text, old_text, join=False):
        """
        对比两个字符串
        :param new_text: str，新的文本
        :param old_text: str，旧的文本
        :param join: bool
        :return: Tuple[List[str], List[str]]，对比结果，按照句号进行划分，以优化显示效果
        """
        new_result, old_result = align_text(new_text, old_text, join=join)

        return new_result, old_result

    def _load_report(self, new_report, old_report, **kwargs):
        self.report = []

        parser_a = PDFParser()
        parse_new_result = parser_a.parse(new_report, kwargs.get("password_a", ""))
        new_index_tree = parser_a.analyze("Monetary Report", parse_new_result)
        self.report.append(new_index_tree)

        parser_b = PDFParser()
        parse_old_result = parser_b.parse(old_report, kwargs.get("password_b", ""))
        old_index_tree = parser_b.analyze("Monetary Report", parse_old_result)
        self.report.append(old_index_tree)

    def _to_stdout(self):
        comparison_result = []

        # title
        path = [["t"]]
        new_ctt = self._find_content(self.report[0], path)[0].replace(" ", "").strip("。")
        old_ctt = self._find_content(self.report[1], path)[0].replace(" ", "").strip("。")
        comparison_result.append(("项目", "", new_ctt, old_ctt))

        # 总体基调
        path = [["c5"], ["c1"], ["p2"]]
        new_ctt, old_ctt = self._align_continuous_text([path], join=False)
        comparison_result.append(("总体基调", "", new_ctt, old_ctt))

        # 货币政策展望
        ## 流动性基调
        path = [["c5"], ["c2"], ["ps1", "p1s-1"]]
        new_ctt, old_ctt = self._align_discrete_text([path], ["稳健的货币政策", "大水漫灌", "货币政策稳定性"], join=False)
        comparison_result.append(("货币政策展望", "流动性", new_ctt, old_ctt))

        ## 风险防控
        path = [["c5"], ["c2"], ["ps1"]]
        new_ctt, old_ctt = self._align_discrete_text([path], ["金融风险"], join=False)
        comparison_result.append(("货币政策展望", "风险防控", new_ctt, old_ctt))

        ## 房地产
        path = [["c5"], ["c2"], ["ps-1"]]
        new_ctt, old_ctt = self._align_discrete_text([path], ["房子"], join=False)
        comparison_result.append(("货币政策展望", "房地产", new_ctt, old_ctt))

        ## 信贷总量
        path = [["c5"], ["c2"], ["p3"]]
        new_ctt, old_ctt = self._align_discrete_text([path], ["再贷款", "再贴现", "信贷", "工具", "总闸门"], join=False)
        comparison_result.append(("货币政策展望", "信贷总量", new_ctt, old_ctt))

        ## 信贷结构
        path = [["c5"], ["c2"], ["p4"]]
        new_ctt, old_ctt = self._align_discrete_text([path], ["再贷款", "再贴现", "信贷", "工具", "总闸门"], join=False)
        comparison_result.append(("货币政策展望", "信贷结构", new_ctt, old_ctt))

        ## 汇率
        path = [["c5"], ["c2"], ["ps1"]]
        new_ctt, old_ctt = self._align_discrete_text([path], ["汇率"], join=False)
        comparison_result.append(("货币政策展望", "汇率", new_ctt, old_ctt))

        # 货币政策回顾
        ## 流动性
        path = [["c1"], ["c"], ["t"]]
        new_ctt, old_ctt = self._align_discrete_text([path], ["流动性"], join=False)
        comparison_result.append(("货币政策回顾", "流动性", new_ctt, old_ctt))

        ## 政策工具
        path = [["c2"], ["c"], ["t"]]
        new_ctt, old_ctt = self._align_discrete_text([path], ["操作", "便利", "货币信贷", "准备金率"], join=False)
        comparison_result.append(("货币政策回顾", "政策工具", new_ctt, old_ctt))

        ## 宏观审慎
        path = [["c2"], ["c"], ["t"]]
        new_ctt, old_ctt = self._align_discrete_text([path], ["宏观审慎"], join=False)
        comparison_result.append(("货币政策回顾", "宏观审慎", new_ctt, old_ctt))

        ## 信贷
        path = [["c2"], ["c"], ["t"]]
        new_ctt, old_ctt = self._align_discrete_text([path], ["信贷政策"], join=False)
        comparison_result.append(("货币政策回顾", "信贷", new_ctt, old_ctt))

        ## 汇率
        path1 = [["c1"], ["c"], ["t"]]
        path2 = [["c2"], ["c"], ["p1s1"]]
        new_ctt, old_ctt = self._align_discrete_text([path1, path2], ["汇率"], join=False)
        comparison_result.append(("货币政策回顾", "汇率", new_ctt, old_ctt))

        ## 本外币存款
        path = [["c1"], ["c2"], ["t"]]
        new_ctt, old_ctt = self._align_discrete_text([path], ["贷款", "存款"], join=False)
        comparison_result.append(("货币政策回顾", "本外币存款", new_ctt, old_ctt))

        ## 社融
        path = [["c1"], ["c"], ["t"]]
        new_ctt, old_ctt = self._align_discrete_text([path], ["社会融资"], join=False)
        comparison_result.append(("货币政策回顾", "社融", new_ctt, old_ctt))

        ## 风险处置
        path = [["c2"], ["c"], ["t"]]
        new_ctt, old_ctt = self._align_discrete_text([path], ["金融风险"], join=False)
        comparison_result.append(("货币政策回顾", "风险处置", new_ctt, old_ctt))

        # 世界经济形势
        ## 经济增速
        path = [["c4"], ["c1"], ["c1"], ["p1s1"]]
        new_ctt, old_ctt = self._align_discrete_text([path], join=False)
        comparison_result.append(("世界经济形势", "经济增速", new_ctt, old_ctt))

        # 国内经济形势
        ## 经济增速
        path1 = [["c4"], ["c2"], ["p1s1"]]
        path2 = [["c4"], ["c1"], ["p1s1", "p2s1", "p3s1"]]
        new_ctt, old_ctt = self._align_discrete_text([path1, path2], join=False)
        comparison_result.append(("国内经济形势", "经济增速", new_ctt, old_ctt))

        # 消费
        path = [["c4"], ["c2"], ["c1"], ["p1s1"]]
        new_ctt, old_ctt = self._align_discrete_text([path], join=False)
        comparison_result.append(("国内经济形势", "消费", new_ctt, old_ctt))

        # 投资
        path = [["c4"], ["c2"], ["c1"], ["p2s1"]]
        new_ctt, old_ctt = self._align_discrete_text([path], join=False)
        comparison_result.append(("国内经济形势", "投资", new_ctt, old_ctt))

        # 进出口
        path = [["c4"], ["c2"], ["c1"], ["p3s1"]]
        new_ctt, old_ctt = self._align_discrete_text([path], join=False)
        comparison_result.append(("国内经济形势", "进出口", new_ctt, old_ctt))

        # 农业
        path = [["c4"], ["c2"], ["c2"], ["p2s1"]]
        new_ctt, old_ctt = self._align_discrete_text([path], join=False)
        comparison_result.append(("国内经济形势", "农业", new_ctt, old_ctt))

        # 工业
        path = [["c4"], ["c2"], ["c2"], ["p3s1"]]
        new_ctt, old_ctt = self._align_discrete_text([path], join=False)
        comparison_result.append(("国内经济形势", "工业", new_ctt, old_ctt))

        # 服务业
        path = [["c4"], ["c2"], ["c2"], ["p4s1"]]
        new_ctt, old_ctt = self._align_discrete_text([path], join=False)
        comparison_result.append(("国内经济形势", "服务业", new_ctt, old_ctt))

        # 财政收支
        path = [["c4"], ["c2"], ["c4"], ["t"]]
        new_ctt, old_ctt = self._align_discrete_text([path], join=False)
        comparison_result.append(("国内经济形势", "财政与就业", new_ctt, old_ctt))

        # 价格形势
        ## 总体趋势
        path = [["c5"], ["c1"], ["p4s1"]]
        new_ctt, old_ctt = self._align_discrete_text([path], join=False)
        comparison_result.append(("价格形势", "总体趋势", new_ctt, old_ctt))

        ## CPI
        path = [["c4"], ["c2"], ["c3"], ["p1s1"]]
        new_ctt, old_ctt = self._align_discrete_text([path], join=False)
        comparison_result.append(("价格形势", "CPI", new_ctt, old_ctt))

        ## PPI
        path = [["c4"], ["c2"], ["c3"], ["p2s1"]]
        new_ctt, old_ctt = self._align_discrete_text([path], join=False)
        comparison_result.append(("价格形势", "PPI", new_ctt, old_ctt))

        # 金融市场运行回顾
        ## 货币市场
        path = [["c3"], ["c1"], ["c1"], ["t"]]
        new_ctt, old_ctt = self._align_discrete_text([path], join=False)
        comparison_result.append(("金融市场运行回顾", "货币市场", new_ctt, old_ctt))

        ## 债券市场
        path = [["c3"], ["c1"], ["c2"], ["t"]]
        new_ctt, old_ctt = self._align_discrete_text([path], join=False)
        comparison_result.append(("金融市场运行回顾", "债券市场", new_ctt, old_ctt))

        ## 票据市场
        path = [["c3"], ["c1"], ["c3"], ["t"]]
        new_ctt, old_ctt = self._align_discrete_text([path], join=False)
        comparison_result.append(("金融市场运行回顾", "票据市场", new_ctt, old_ctt))

        ## 股票市场
        path = [["c3"], ["c1"], ["c4"], ["t"]]
        new_ctt, old_ctt = self._align_discrete_text([path], join=False)
        comparison_result.append(("金融市场运行回顾", "股票市场", new_ctt, old_ctt))

        ## 保险市场
        path = [["c3"], ["c1"], ["c5"], ["t"]]
        new_ctt, old_ctt = self._align_discrete_text([path], join=False)
        comparison_result.append(("金融市场运行回顾", "保险市场", new_ctt, old_ctt))

        ## 外汇市场
        path = [["c3"], ["c1"], ["c6"], ["t"]]
        new_ctt, old_ctt = self._align_discrete_text([path], join=False)
        comparison_result.append(("金融市场运行回顾", "外汇市场", new_ctt, old_ctt))

        ## 黄金市场
        path = [["c3"], ["c1"], ["c7"], ["t"]]
        new_ctt, old_ctt = self._align_discrete_text([path], join=False)
        comparison_result.append(("金融市场运行回顾", "黄金市场", new_ctt, old_ctt))

        return comparison_result

    def _to_html(self, output_path):
        if not self.report:
            raise AttributeError("haven't call load_report interface.")

        with open(output_path, "w", encoding="utf-8") as f:
            css = get_css()
            f.write(css + "\n")
            f.write("<table>\n")

            # title
            path = [["t"]]
            new_ctt = self._find_content(self.report[0], path)[0].replace(" ", "").strip("。")
            old_ctt = self._find_content(self.report[1], path)[0].replace(" ", "").strip("。")
            self._write_to_frame(f, "项目", "", new_ctt, old_ctt, header=True)

            # 总体基调
            path = [["c5"], ["c1"], ["p2"]]
            new_ctt, old_ctt = self._align_continuous_text([path])
            self._write_to_frame(f, "总体基调", "", new_ctt, old_ctt)

            # 货币政策展望
            ## 流动性基调
            path = [["c5"], ["c2"], ["ps1", "p1s-1"]]
            new_ctt, old_ctt = self._align_discrete_text([path], ["稳健的货币政策", "大水漫灌", "货币政策稳定性"])
            self._write_to_frame(f, "货币政策展望", "流动性", new_ctt, old_ctt, 6)

            ## 风险防控
            path = [["c5"], ["c2"], ["ps1"]]
            new_ctt, old_ctt = self._align_discrete_text([path], ["金融风险"])
            self._write_to_frame(f, "", "风险防控", new_ctt, old_ctt)

            ## 房地产
            path = [["c5"], ["c2"], ["ps-1"]]
            new_ctt, old_ctt = self._align_discrete_text([path], ["房子"])
            self._write_to_frame(f, "", "房地产", new_ctt, old_ctt)

            ## 信贷总量
            path = [["c5"], ["c2"], ["p3"]]
            new_ctt, old_ctt = self._align_discrete_text([path], ["再贷款", "再贴现", "信贷", "工具", "总闸门"])
            self._write_to_frame(f, "", "信贷总量", new_ctt, old_ctt)

            ## 信贷结构
            path = [["c5"], ["c2"], ["p4"]]
            new_ctt, old_ctt = self._align_discrete_text([path], ["再贷款", "再贴现", "信贷", "工具", "总闸门"])
            self._write_to_frame(f, "", "信贷结构", new_ctt, old_ctt)

            ## 汇率
            path = [["c5"], ["c2"], ["ps1"]]
            new_ctt, old_ctt = self._align_discrete_text([path], ["汇率"])
            self._write_to_frame(f, "", "汇率", new_ctt, old_ctt)

            # 货币政策回顾
            ## 流动性
            path = [["c1"], ["c"], ["t"]]
            new_ctt, old_ctt = self._align_discrete_text([path], ["流动性"])
            self._write_to_frame(f, "货币政策回顾", "流动性", new_ctt, old_ctt, 8)

            ## 政策工具
            path = [["c2"], ["c"], ["t"]]
            new_ctt, old_ctt = self._align_discrete_text([path], ["操作", "便利", "货币信贷", "准备金率"])
            self._write_to_frame(f, "", "政策工具", new_ctt, old_ctt)

            ## 宏观审慎
            path = [["c2"], ["c"], ["t"]]
            new_ctt, old_ctt = self._align_discrete_text([path], ["宏观审慎"])
            self._write_to_frame(f, "", "宏观审慎", new_ctt, old_ctt)

            ## 信贷
            path = [["c2"], ["c"], ["t"]]
            new_ctt, old_ctt = self._align_discrete_text([path], ["信贷政策"])
            self._write_to_frame(f, "", "信贷", new_ctt, old_ctt)

            ## 汇率
            path1 = [["c1"], ["c"], ["t"]]
            path2 = [["c2"], ["c"], ["p1s1"]]
            new_ctt, old_ctt = self._align_discrete_text([path1, path2], ["汇率"])
            self._write_to_frame(f, "", "汇率", new_ctt, old_ctt)

            ## 本外币存款
            path = [["c1"], ["c2"], ["t"]]
            new_ctt, old_ctt = self._align_discrete_text([path], ["贷款", "存款"])
            self._write_to_frame(f, "", "本外币存贷款", new_ctt, old_ctt)

            ## 社融
            path = [["c1"], ["c"], ["t"]]
            new_ctt, old_ctt = self._align_discrete_text([path], ["社会融资"])
            self._write_to_frame(f, "", "社融", new_ctt, old_ctt)

            ## 风险处置
            path = [["c2"], ["c"], ["t"]]
            new_ctt, old_ctt = self._align_discrete_text([path], ["金融风险"])
            self._write_to_frame(f, "", "风险处置", new_ctt, old_ctt)

            # 世界经济形势
            ## 经济增速
            path = [["c4"], ["c1"], ["c1"], ["p1s1"]]
            new_ctt, old_ctt = self._align_discrete_text([path])
            self._write_to_frame(f, "世界经济形势", "经济增速", new_ctt, old_ctt)

            # 国内经济形势
            ## 经济增速
            path1 = [["c4"], ["c2"], ["p1s1"]]
            path2 = [["c4"], ["c1"], ["p1s1", "p2s1", "p3s1"]]
            new_ctt, old_ctt = self._align_discrete_text([path1, path2])
            self._write_to_frame(f, "国内经济形势", "经济增速", new_ctt, old_ctt, 8)

            # 消费
            path = [["c4"], ["c2"], ["c1"], ["p1s1"]]
            new_ctt, old_ctt = self._align_discrete_text([path])
            self._write_to_frame(f, "", "消费", new_ctt, old_ctt)

            # 投资
            path = [["c4"], ["c2"], ["c1"], ["p2s1"]]
            new_ctt, old_ctt = self._align_discrete_text([path])
            self._write_to_frame(f, "", "投资", new_ctt, old_ctt)

            # 进出口
            path = [["c4"], ["c2"], ["c1"], ["p3s1"]]
            new_ctt, old_ctt = self._align_discrete_text([path])
            self._write_to_frame(f, "", "进出口", new_ctt, old_ctt)

            # 农业
            path = [["c4"], ["c2"], ["c2"], ["p2s1"]]
            new_ctt, old_ctt = self._align_discrete_text([path])
            self._write_to_frame(f, "", "农业", new_ctt, old_ctt)

            # 工业
            path = [["c4"], ["c2"], ["c2"], ["p3s1"]]
            new_ctt, old_ctt = self._align_discrete_text([path])
            self._write_to_frame(f, "", "工业", new_ctt, old_ctt)

            # 服务业
            path = [["c4"], ["c2"], ["c2"], ["p4s1"]]
            new_ctt, old_ctt = self._align_discrete_text([path])
            self._write_to_frame(f, "", "服务业", new_ctt, old_ctt)

            # 财政收支
            path = [["c4"], ["c2"], ["c4"], ["t"]]
            new_ctt, old_ctt = self._align_discrete_text([path])
            self._write_to_frame(f, "", "财政与就业", new_ctt, old_ctt)

            # 价格形势
            ## 总体趋势
            path = [["c5"], ["c1"], ["p4s1"]]
            new_ctt, old_ctt = self._align_discrete_text([path])
            self._write_to_frame(f, "价格形势", "总体趋势", new_ctt, old_ctt, 3)

            ## CPI
            path = [["c4"], ["c2"], ["c3"], ["p1s1"]]
            new_ctt, old_ctt = self._align_discrete_text([path])
            self._write_to_frame(f, "", "CPI", new_ctt, old_ctt)

            ## PPI
            path = [["c4"], ["c2"], ["c3"], ["p2s1"]]
            new_ctt, old_ctt = self._align_discrete_text([path])
            self._write_to_frame(f, "", "PPI", new_ctt, old_ctt)

            # 金融市场运行回顾
            ## 货币市场
            path = [["c3"], ["c1"], ["c1"], ["t"]]
            new_ctt, old_ctt = self._align_discrete_text([path])
            self._write_to_frame(f, "金融市场运行回顾", "货币市场", new_ctt, old_ctt, 7)

            ## 债券市场
            path = [["c3"], ["c1"], ["c2"], ["t"]]
            new_ctt, old_ctt = self._align_discrete_text([path])
            self._write_to_frame(f, "", "债券市场", new_ctt, old_ctt)

            ## 票据市场
            path = [["c3"], ["c1"], ["c3"], ["t"]]
            new_ctt, old_ctt = self._align_discrete_text([path])
            self._write_to_frame(f, "", "票据市场", new_ctt, old_ctt)

            ## 股票市场
            path = [["c3"], ["c1"], ["c4"], ["t"]]
            new_ctt, old_ctt = self._align_discrete_text([path])
            self._write_to_frame(f, "", "股票市场", new_ctt, old_ctt)

            ## 保险市场
            path = [["c3"], ["c1"], ["c5"], ["t"]]
            new_ctt, old_ctt = self._align_discrete_text([path])
            self._write_to_frame(f, "", "保险市场", new_ctt, old_ctt)

            ## 外汇市场
            path = [["c3"], ["c1"], ["c6"], ["t"]]
            new_ctt, old_ctt = self._align_discrete_text([path])
            self._write_to_frame(f, "", "外汇市场", new_ctt, old_ctt)

            ## 黄金市场
            path = [["c3"], ["c1"], ["c7"], ["t"]]
            new_ctt, old_ctt = self._align_discrete_text([path])
            self._write_to_frame(f, "", "黄金市场", new_ctt, old_ctt)

            f.write("</table>\n")

    def _align_discrete_text(self, path_list, keywords=None, join=True):
        new_result, old_result = [], []

        for path in path_list:
            text_a_list = self._find_content(self.report[0], path, keywords)
            text_b_list = self._find_content(self.report[1], path, keywords)

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

            paragraph_a = "".join(text_a_list)
            paragraph_b = "".join(text_b_list)

            res_a, res_b = align_text(paragraph_a, paragraph_b, join)

            if join:
                new_result.append(res_a)
                old_result.append(res_b)
            else:
                new_result += res_a
                old_result += res_b

        new_result = [i for i in new_result if i]
        old_result = [i for i in old_result if i]

        if join:
            new_result = "<br><br>".join(new_result)
            old_result = "<br><br>".join(old_result)

        return new_result, old_result

    def _align_continuous_text(self, path_list, join=True):
        paragraph_a = self._find_content(self.report[0], path_list[0])[0]
        paragraph_b = self._find_content(self.report[1], path_list[0])[0]
        new_result, old_result = align_text(paragraph_a, paragraph_b)

        if not join:
            new_result = new_result.split("<br><br>")
            old_result = old_result.split("<br><br>")

        return new_result, old_result

    def _find_content(self, tree, path, keywords=None):
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

    def _write_to_frame(self, f, str1, str2, new_ctt, old_ctt, rowspan1=1, rowspan2=1, header=False, reverse=False):
        if reverse:
            new_ctt, old_ctt = old_ctt, new_ctt

        if str1 and str2:
            f.write(" <tr>\n")
            f.write("  <th rowspan='%s'>%s</th>\n" % (rowspan1, str1))
            f.write("  <th rowspan='%s'>%s</th>\n" % (rowspan2, str2))
            f.write("  <td>%s</td>\n" % new_ctt)
            f.write("  <td>%s</td>\n" % old_ctt)
            f.write(" </tr>\n")

        elif str1 and not str2:
            if header:
                f.write(" <tr>\n")
                f.write("  <th colspan='2'>%s</th>\n" % str1)
                f.write("  <th>%s</th>\n" % new_ctt)
                f.write("  <th>%s</th>\n" % old_ctt)
                f.write(" </tr>\n")
            else:
                f.write(" <tr>\n")
                f.write("  <th colspan='2'>%s</th>\n" % str1)
                f.write("  <td>%s</td>\n" % new_ctt)
                f.write("  <td>%s</td>\n" % old_ctt)
                f.write(" </tr>\n")

        elif not str1 and str2:
            f.write(" <tr>\n")
            f.write("  <th rowspan='%s'>%s</th>\n" % (rowspan2, str2))
            f.write("  <td>%s</td>\n" % new_ctt)
            f.write("  <td>%s</td>\n" % old_ctt)
            f.write(" </tr>\n")

        elif not str1 and not str2:
            f.write(" <tr>\n")
            f.write("  <td>%s</td>\n" % new_ctt)
            f.write("  <td>%s</td>\n" % old_ctt)
            f.write(" </tr>\n")


if __name__ == '__main__':
    # agent = MonetaryReportComparer()
    # # my_result = agent.compare_text("新的一年继续落实和发挥好结构性货币政策工具的牵引带动作用。保持再贷款、再贴现政策稳定性，继续对涉农、小微企业、民营企业提供普惠性、持续性的资金支持。", "继续落实和发挥好结构性货币政策工具的牵引带动作用,运用好碳减排支持工具推动绿色低碳发展。保持再贷款、再贴现政策稳定性，实施好两项直达实体经济货币政策工具的延期工作，继续对涉农、小微企业、民营企业提供普惠性、持续性的资金支持。")
    # my_result = agent.compare_report("Resources/2021Q3.pdf", "Resources/2021Q2.pdf", to_html=True, output_path="Result/2021Q2_2021Q3.html")
    # print(my_result)

    my_report1 = open("Resources/2021Q4Committee.txt").readlines()
    my_report2 = open("Resources/2021Q3Committee.txt").readlines()
    agent = MonetaryCommitteeComparer()
    my_result = agent.compare_report(my_report1, my_report2, to_html=True, output_path="Result/Committee2021Q4_2021Q3.html")
    print(my_result)
