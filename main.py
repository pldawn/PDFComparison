import sys

from Parser import PDFComparer, PDFParser
from CSS import get_css
import os


def main():
    # pdf_input_path = "Resources/2020Q1.pdf"
    # agent = PDFParser()
    # parse_result = agent.parse(pdf_input_path)
    #
    # with open("Result/result20Q1.txt", "w") as f:
    #     for line in parse_result:
    #         f.write(str(line[0]) + '\t' + '%04.1f' % line[1] + '\t' + line[2] + '\n')
    #
    # document = agent.analyze("Monetary Policy Report", parse_result)
    # print(document)
    #
    agent = PDFComparer()
    agent.compare_two_pdf("Resources/2021Q2.pdf", "Resources/2021Q3.pdf", "Monetary Policy Report")
    agent.to_html("Result/2021Q2_2021Q3.html")
    #
    # doc = Document("Resources/2019Q4.docx")
    # with open("Result/2019Q4.txt", "w") as f:
    #     for p in doc.paragraphs:
    #         f.write(p.style.style_id + "\t" + p.text + "\n")


if __name__ == '__main__':
    main()
