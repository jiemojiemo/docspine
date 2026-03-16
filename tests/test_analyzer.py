from docling_progressive.analyzer import build_outline_tree, slugify


def test_build_outline_tree_groups_content_under_headings():
    markdown = "\n".join(
        [
            "# Annual Report",
            "Intro paragraph.",
            "## Business Overview",
            "Business content.",
            "## Risk Factors",
            "Risk content.",
        ]
    )

    root = build_outline_tree(markdown)

    assert root.title == "Annual Report"
    assert [child.title for child in root.children] == [
        "Business Overview",
        "Risk Factors",
    ]


def test_build_outline_tree_uses_meaningful_non_heading_title_for_real_pdf_markdown():
    markdown = "\n".join(
        [
            "<!-- image -->",
            "2021 年 08 月 29 日",
            "开源证券",
            "券商金股的内部收益结构",
            "金融工程团队",
            "",
            "1 、 新进金股与重复金股的整体差异",
            "正文第一段。",
        ]
    )

    root = build_outline_tree(markdown)

    assert root.title == "券商金股的内部收益结构"


def test_build_outline_tree_uses_first_non_noise_markdown_heading_as_root_title():
    markdown = "\n".join(
        [
            "## 金融工程研究团队",
            "## 魏建榕（首席分析师）",
            "## 相关研究报告",
            "## 券商金股的内部收益结构",
            "## 2.1 、 事件收益视角的差异",
            "正文第一段。",
        ]
    )

    root = build_outline_tree(markdown)

    assert root.title == "券商金股的内部收益结构"


def test_build_outline_tree_deduplicates_repeated_chinese_section_slugs():
    markdown = "\n".join(
        [
            "券商金股的内部收益结构",
            "1 、 第一部分",
            "内容 1",
            "1 、 第一部分",
            "内容 2",
        ]
    )

    root = build_outline_tree(markdown)

    assert [child.slug for child in root.children] == [
        "1-第一部分",
        "1-第一部分-2",
    ]


def test_build_outline_tree_detects_numbered_chinese_sections():
    markdown = "\n".join(
        [
            "券商金股的内部收益结构",
            "2.1 、 事件收益视角的差异",
            "内容 A",
            "图 1 ：月度数量",
            "内容 B",
        ]
    )

    root = build_outline_tree(markdown)

    assert [child.title for child in root.children] == [
        "2.1 、 事件收益视角的差异",
        "图 1 ：月度数量",
    ]


def test_slugify_keeps_chinese_text_and_numbers():
    assert slugify("2.1 、 事件收益视角的差异") == "2-1-事件收益视角的差异"


def test_build_outline_tree_prefers_toc_sections_for_annual_report_structure():
    markdown = "\n".join(
        [
            "## 深圳迈瑞生物医疗电子股份有限公司 2024 年年度报告",
            "## 第一节 重要提示、目录和释义",
            "前言内容。",
            "## 目 录",
            "| 第一节  重要提示、目录和释义  ........  6  第二节  公司简介和主要财务指标  ........  20  第三节  管理层讨论与分析  ........  24 |",
            "|---|",
            "## 第一节 重要提示、目录和释义",
            "第一节正文。",
            "## 第二节 公司简介和主要财务指标",
            "第二节正文。",
            "## 第三节 管理层讨论与分析",
            "第三节正文。",
        ]
    )

    root = build_outline_tree(markdown)

    assert root.title == "深圳迈瑞生物医疗电子股份有限公司 2024 年年度报告"
    assert [child.title for child in root.children] == [
        "第一节 重要提示、目录和释义",
        "第二节 公司简介和主要财务指标",
        "第三节 管理层讨论与分析",
    ]


def test_build_outline_tree_uses_toc_matches_to_assign_section_content():
    markdown = "\n".join(
        [
            "## 年度报告",
            "## 目 录",
            "| 第一节  重要提示、目录和释义  ........  6  第二节  公司简介和主要财务指标  ........  20 |",
            "|---|",
            "## 第一节 重要提示、目录和释义",
            "第一节正文。",
            "## 第二节 公司简介和主要财务指标",
            "第二节正文。",
        ]
    )

    root = build_outline_tree(markdown)

    assert root.children[0].content == "第一节正文。"
    assert root.children[1].content == "第二节正文。"


def test_build_outline_tree_prefers_pdf_outline_metadata_over_text_toc():
    markdown = "\n".join(
        [
            "## 年度报告",
            "## 目 录",
            "| 第一节  重要提示、目录和释义  ........  6  第二节  公司简介和主要财务指标  ........  20 |",
            "|---|",
            "## 第一节 重要提示、目录和释义",
            "第一节正文。",
            "## 第二节 公司简介和主要财务指标",
            "第二节正文。",
        ]
    )

    root = build_outline_tree(
        markdown,
        metadata={
            "outline": [
                {"title": "第二节 公司简介和主要财务指标", "level": 1, "page": 20},
                {"title": "第一节 重要提示、目录和释义", "level": 1, "page": 6},
            ]
        },
    )

    assert [child.title for child in root.children] == [
        "第二节 公司简介和主要财务指标",
        "第一节 重要提示、目录和释义",
    ]


def test_build_outline_tree_builds_nested_tree_from_pdf_outline_metadata():
    markdown = "\n".join(
        [
            "## 年度报告",
            "## 第一节 重要提示、目录和释义",
            "第一节正文。",
            "## 第二节 公司简介和主要财务指标",
            "第二节正文。",
            "## 一、公司信息",
            "公司信息正文。",
            "## 二、联系人和联系方式",
            "联系人正文。",
        ]
    )

    root = build_outline_tree(
        markdown,
        metadata={
            "outline": [
                {"title": "第一节 重要提示、目录和释义", "level": 1, "page": 6},
                {"title": "第二节 公司简介和主要财务指标", "level": 1, "page": 20},
                {"title": "一、公司信息", "level": 2, "page": 20},
                {"title": "二、联系人和联系方式", "level": 2, "page": 20},
            ]
        },
    )

    assert [child.title for child in root.children] == [
        "第一节 重要提示、目录和释义",
        "第二节 公司简介和主要财务指标",
    ]
    assert [child.title for child in root.children[1].children] == [
        "一、公司信息",
        "二、联系人和联系方式",
    ]
