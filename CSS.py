def get_css():
    css = \
        """
        <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
        <style type="text/css">
            body{
                margin: 0 auto;
                font-family: "Microsoft YaHei", arial,sans-serif;
                color: #444444;
                line-height: 1;
                padding: 30px;
            }

            @media screen and (min-width: 768px) {
                body {
                    width: 1000px;
                    margin: 10px auto;
                }
            }

            table {
                border-spacing: 0;
                width: 100%;
            }

            table {
                border: solid #ccc 5px;
                border-radius: 6px;
            }

            table td {
                border-left: 1px solid #ccc;
                border-top: 1px solid #ccc;
                padding: 10px;
            }

            table th {
                border: 1px solid #ccc;
                background-color: #dce9f9;
                text-shadow: 0 1px 0 rgba(255,255,255,.5);
                padding: 5px;
            }

            table th:first-child {
                width: 10%;
            }
        </style>
        """

    return css
