import sys

from Parser import PDFComparer, PDFParser
from CSS import get_css
import os


def main():
    pdf_input_path = "Resources/2020Q1.pdf"
    agent = PDFParser()
    parse_result = agent.parse(pdf_input_path)

    with open("Result/result20Q1.txt", "w") as f:
        for line in parse_result:
            f.write(str(line[0]) + '\t' + '%04.1f' % line[1] + '\t' + line[2] + '\n')

    document = agent.analyze("Monetary Policy Report", parse_result)
    print(document)
    #
    # agent = PDFComparer()
    # agent.compare_two_pdf("../Resources/2020Q1.pdf", "../Resources/2020Q2.pdf", "Monetary Policy Report")

    # agent = PDFComparer()
    # agent.compare_two_pdf("Resources/2019Q3.pdf", "Resources/2020Q2.pdf", "Monetary Policy Report")
    # agent.to_html("Result/2019Q3_2020Q2.html")
    #
    # doc = Document("Resources/2019Q4.docx")
    # with open("Result/2019Q4.txt", "w") as f:
    #     for p in doc.paragraphs:
    #         f.write(p.style.style_id + "\t" + p.text + "\n")


def main_xiaolu(argv):
    f1 = argv[1]
    f2 = argv[2]
    output = argv[3]

    agent = PDFComparer()
    ops_1, ops_2 = agent.edit_ops(open(f1).read().strip(), open(f2).read().strip())
    str_1 = agent.decorate(ops_1, True)
    str_1 = str_1.replace("\n", "<br>")
    del ops_1
    str_2 = agent.decorate(ops_2, False)
    str_2 = str_2.replace("\n", "<br>")
    del ops_2

    with open(output, "w") as f:
        css = get_css()
        f.write(css + "\n")
        f.write("<table>\n")

        agent.write_to_frame(f, "file_name", "", os.path.basename(f1).split(".")[0], os.path.basename(f2).split(".")[0])
        agent.write_to_frame(f, "content", "", str_1, str_2)


if __name__ == '__main__':
    main_xiaolu(sys.argv)
