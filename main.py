from Parser import PDFComparer


def main():
    # pdf_input_path = "../Resources/2019Q3.pdf"
    # agent = PDFParser()
    # parse_result = agent.parse(pdf_input_path)
    #
    # with open("result.txt", "w") as f:
    #     for line in parse_result:
    #         f.write(str(line[0]) + '\t' + '%04.1f' % line[1] + '\t' + line[2] + '\n')
    #
    # document = agent.analyze("Monetary Policy Report", parse_result)
    # print(document)
    # agent = PDFComparer()
    # agent.compare_two_pdf("../Resources/2020Q1.pdf", "../Resources/2020Q2.pdf", "Monetary Policy Report")
    # agent.to_markdown("result.md")
    # markdown_to_html("result.md", "result.html")
    # agent.to_html_based_frame("2020Q1_2020Q2.html")

    agent = PDFComparer()
    agent.compare_two_pdf("../Resources/2020Q1.pdf", "../Resources/2020Q2.pdf", "Monetary Policy Report")
    agent.to_html("2020Q1_2020Q2.html")


if __name__ == '__main__':
    main()
