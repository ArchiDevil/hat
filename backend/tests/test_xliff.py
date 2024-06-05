from app.xliff import extract_xliff_content


def test_can_parse_simple_xliff():
    content = """
<?xml version="1.0" encoding="utf-8"?>
<xliff version="1.2"
    xmlns:sc="SmartcatXliff"
    xmlns="urn:oasis:names:tc:xliff:document:1.2">
    <file datatype="plaintext" date="2023-11-07T20:56:05.0017382Z" original="99103f5989ba533724dc780c_25" source-language="en" target-language="ru">
        <header>
            <tool tool-name="Smartcat.ai" tool-id="40c7d5b2-da26-4b36-84f1-8305b3aadb03" tool-version="1.0.11.0" />
        </header>
        <body>
            <trans-unit id="675606" approved="no" sc:locked="false" sc:last-modified-date="2023-10-19T18:29:22.711Z">
                <source xml:space="preserve">Regional Effects</source>
                <target state="needs-translation" xml:space="preserve" />
            </trans-unit>
        </body>
    </file>
</xliff>
""".encode()
    data = extract_xliff_content(content)
    assert len(data.segments) == 1
    segment = data.segments[0]
    assert segment.original == "Regional Effects"
    assert segment.translation == ""
    assert not segment.dirty
    assert not segment.approved
    assert segment.id_ == 675606


def test_can_parse_multiple_segments():
    content = """
<?xml version="1.0" encoding="utf-8"?>
<xliff version="1.2"
    xmlns:sc="SmartcatXliff"
    xmlns="urn:oasis:names:tc:xliff:document:1.2">
    <file datatype="plaintext" date="2023-11-07T20:56:05.0017382Z" original="99103f5989ba533724dc780c_25" source-language="en" target-language="ru">
        <header>
            <tool tool-name="Smartcat.ai" tool-id="40c7d5b2-da26-4b36-84f1-8305b3aadb03" tool-version="1.0.11.0" />
        </header>
        <body>
            <trans-unit id="675606" approved="no" sc:locked="false" sc:last-modified-date="2023-10-19T18:29:22.711Z">
                <source xml:space="preserve">Regional Effects</source>
                <target state="needs-translation" xml:space="preserve" />
            </trans-unit>
            <trans-unit id="675607" approved="no" sc:locked="false" sc:last-modified-date="2023-10-19T18:29:22.711Z">
                <source xml:space="preserve">Other Effects</source>
                <target state="needs-translation" xml:space="preserve" />
            </trans-unit>
        </body>
    </file>
</xliff>
""".encode()
    data = extract_xliff_content(content)
    assert len(data.segments) == 2
    assert data.segments[0].original == "Regional Effects"
    assert data.segments[0].translation == ""
    assert not data.segments[0].dirty
    assert not data.segments[0].approved
    assert data.segments[0].id_ == 675606

    assert data.segments[1].original == "Other Effects"
    assert data.segments[1].translation == ""
    assert not data.segments[1].dirty
    assert not data.segments[1].approved
    assert data.segments[1].id_ == 675607


def test_can_parse_segments_with_g_tags():
    content = """
<?xml version="1.0" encoding="utf-8"?>
<xliff version="1.2"
    xmlns:sc="SmartcatXliff"
    xmlns="urn:oasis:names:tc:xliff:document:1.2">
    <file datatype="plaintext" date="2023-11-07T20:56:05.0017382Z" original="99103f5989ba533724dc780c_25" source-language="en" target-language="ru">
        <header>
            <tool tool-name="Smartcat.ai" tool-id="40c7d5b2-da26-4b36-84f1-8305b3aadb03" tool-version="1.0.11.0" />
        </header>
        <body>
            <trans-unit id="678926" approved="no" sc:locked="false" sc:last-modified-date="2023-10-21T10:04:53.395Z">
                <source xml:space="preserve"><g id="1" ctype="x-smartcat">Project Leads:</g> Justice Ramin Arman, F. Wesley Schneider</source>
                <target state="needs-translation" xml:space="preserve"></target>
            </trans-unit>
        </body>
    </file>
</xliff>
""".encode()
    data = extract_xliff_content(content)
    assert len(data.segments) == 1
    segment = data.segments[0]
    assert segment.original == "Project Leads: Justice Ramin Arman, F. Wesley Schneider"
    assert segment.translation == ""
    assert not segment.dirty
    assert not segment.approved
    assert segment.id_ == 678926


def test_can_write_xml():
    content = """<?xml version='1.0' encoding='UTF-8'?>
<xliff xmlns:sc="SmartcatXliff" xmlns="urn:oasis:names:tc:xliff:document:1.2" version="1.2">
    <file datatype="plaintext" date="2023-11-07T20:56:05.0017382Z" original="99103f5989ba533724dc780c_25" source-language="en" target-language="ru">
        <header>
            <tool tool-name="Smartcat.ai" tool-id="40c7d5b2-da26-4b36-84f1-8305b3aadb03" tool-version="1.0.11.0"/>
        </header>
        <body>
            <trans-unit id="675606" approved="no" sc:locked="false" sc:last-modified-date="2023-10-19T18:29:22.711Z">
                <source xml:space="preserve">Regional Effects</source>
                <target state="needs-translation" xml:space="preserve"/>
            </trans-unit>
        </body>
    </file>
</xliff>
""".encode()
    data = extract_xliff_content(content)
    result = data.write()
    result.seek(0)
    assert result.read() == content


def test_can_write_xml_after_segment_update():
    content = """<?xml version='1.0' encoding='UTF-8'?>
<xliff xmlns:sc="SmartcatXliff" xmlns="urn:oasis:names:tc:xliff:document:1.2" version="1.2">
    <file datatype="plaintext" date="2023-11-07T20:56:05.0017382Z" original="99103f5989ba533724dc780c_25" source-language="en" target-language="ru">
        <header>
            <tool tool-name="Smartcat.ai" tool-id="40c7d5b2-da26-4b36-84f1-8305b3aadb03" tool-version="1.0.11.0"/>
        </header>
        <body>
            <trans-unit id="675606" approved="no" sc:locked="false" sc:last-modified-date="2023-10-19T18:29:22.711Z">
                <source xml:space="preserve">Regional Effects</source>
                <target state="needs-translation" xml:space="preserve"/>
            </trans-unit>
        </body>
    </file>
</xliff>
""".encode()
    data = extract_xliff_content(content)
    data.segments[0].translation = "Some translation"
    data.commit()
    result = data.write()
    result.seek(0)
    assert "Some translation" in result.read().decode("utf-8")


def test_can_write_xml_with_g_tags_after_segment_update():
    content = """
<?xml version="1.0" encoding="utf-8"?>
<xliff version="1.2"
    xmlns:sc="SmartcatXliff"
    xmlns="urn:oasis:names:tc:xliff:document:1.2">
    <file datatype="plaintext" date="2023-11-07T20:56:05.0017382Z" original="99103f5989ba533724dc780c_25" source-language="en" target-language="ru">
        <header>
            <tool tool-name="Smartcat.ai" tool-id="40c7d5b2-da26-4b36-84f1-8305b3aadb03" tool-version="1.0.11.0" />
        </header>
        <body>
            <trans-unit id="678926" approved="no" sc:locked="false" sc:last-modified-date="2023-10-21T10:04:53.395Z">
                <source xml:space="preserve"><g id="1" ctype="x-smartcat">Project Leads:</g> Justice Ramin Arman, F. Wesley Schneider</source>
                <target state="needs-translation" xml:space="preserve"><g id="1" ctype="x-smartcat">Лидеры проекта:</g> Джастин Рамин Арман, Ф. Уэсли Шнайдер</target>
            </trans-unit>
        </body>
    </file>
</xliff>
""".encode()
    data = extract_xliff_content(content)
    data.segments[0].translation = "Some translation"
    data.commit()
    result = data.write()
    result.seek(0)
    assert (
        '<target state="translated" xml:space="preserve">Some translation</target>'
        in result.read().decode("utf-8")
    )
