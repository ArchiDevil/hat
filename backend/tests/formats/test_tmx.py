from datetime import datetime

from app.formats.tmx import extract_tmx_content

# pylint: disable=C0116


def test_can_load_simplest_tmx_1_1():
    content = """
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE tmx SYSTEM "tmx11.dtd">
<tmx version="1.1">
  <header creationtool="OmegaT" o-tmf="OmegaT TMX" adminlang="EN-US" datatype="plaintext" creationtoolversion="6.0.0_0_1bf1729c" segtype="sentence" srclang="en"/>
  <body>
<!-- Default translations -->
    <tu>
      <tuv lang="en">
        <seg>"My anger consumes me.</seg>
      </tuv>
      <tuv lang="ru">
        <seg>"Злость поглощает меня.</seg>
      </tuv>
    </tu>
  </body>
</tmx>
""".encode()

    data = extract_tmx_content(content)
    assert len(data) == 1
    assert data[0].original == '"My anger consumes me.'
    assert data[0].translation == '"Злость поглощает меня.'
    assert not data[0].creation_date
    assert not data[0].change_date


def test_can_load_simplest_tmx_1_4():
    content = """
<?xml version="1.0" encoding="utf-8"?>
<tmx version="1.4">
  <header creationtool="Smartcat" creationtoolversion="6.7334.0.0" segtype="sentence" o-tmf="ATM" adminlang="en-US" srclang="en" datatype="plaintext">
  </header>
  <body>
    <tu creationdate="20220703T075919Z" changedate="20220703T075920Z">
      <tuv xml:lang="en">
        <seg>Each character who plays the game makes a Wisdom check</seg>
      </tuv>
      <tuv xml:lang="ru">
        <seg>Каждый персонаж, участвующий в игре, делает проверку Мудрости</seg>
      </tuv>
    </tu>
  </body>
</tmx>
""".encode()

    data = extract_tmx_content(content)
    assert len(data) == 1
    assert data[0].original == "Each character who plays the game makes a Wisdom check"
    assert (
        data[0].translation
        == "Каждый персонаж, участвующий в игре, делает проверку Мудрости"
    )
    assert data[0].creation_date == datetime(2022, 7, 3, 7, 59, 19)
    assert data[0].change_date == datetime(2022, 7, 3, 7, 59, 20)


def test_can_load_tagged_1_4():
    content = """
<?xml version="1.0" encoding="utf-8"?>
<tmx version="1.4">
<header creationtool="Smartcat" creationtoolversion="6.7334.0.0" segtype="sentence" o-tmf="ATM" adminlang="en-US" srclang="en" datatype="plaintext">
</header>
<body>

    <tu creationdate="20220703T075919Z" changedate="20220703T075920Z">
      <tuv xml:lang="en">
        <seg>Each character who plays the game makes a Wisdom (<bpt i="0" type="structure-only" x="0" />Stealth<ept i="0" />) check to hide (see the <bpt i="2" type="structure-only" x="1" />Player’s Handbook<ept i="2" /> for rules on skills with different abilities).</seg>
      </tuv>
      <tuv xml:lang="ru">
        <seg>Каждый персонаж, участвующий в игре, делает проверку Мудрости (<bpt i="0" type="structure-only" x="0" />Скрытность<ept i="0" />), чтобы спрятаться (правила о навыках с различными способностями см. в <bpt i="2" type="structure-only" x="1" />Книге Игрока<ept i="2" />).</seg>
      </tuv>
    </tu>

  </body>
</tmx>
""".encode()

    data = extract_tmx_content(content)
    assert len(data) == 1
    assert (
        data[0].original
        == "Each character who plays the game makes a Wisdom (Stealth) check to hide (see the Player’s Handbook for rules on skills with different abilities)."
    )
    assert (
        data[0].translation
        == "Каждый персонаж, участвующий в игре, делает проверку Мудрости (Скрытность), чтобы спрятаться (правила о навыках с различными способностями см. в Книге Игрока)."
    )
    assert data[0].creation_date == datetime(2022, 7, 3, 7, 59, 19)
    assert data[0].change_date == datetime(2022, 7, 3, 7, 59, 20)


def test_can_load_multiple_segments():
    content = """
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE tmx SYSTEM "tmx11.dtd">
<tmx version="1.1">
  <header creationtool="OmegaT" o-tmf="OmegaT TMX" adminlang="EN-US" datatype="plaintext" creationtoolversion="6.0.0_0_1bf1729c" segtype="sentence" srclang="en"/>
  <body>
<!-- Default translations -->
    <tu creationdate="20210730T051133Z" changedate="20210730T051134Z">
      <tuv lang="en">
        <seg>"My anger consumes me.</seg>
      </tuv>
      <tuv lang="ru">
        <seg>"Злость поглощает меня.</seg>
      </tuv>
    </tu>
    <tu creationdate="20210730T051133Z" changedate="20210730T051134Z">
      <tuv lang="en">
        <seg>"The world is my hunting ground.</seg>
      </tuv>
      <tuv lang="ru">
        <seg>"Мир - мои охотничьи угодья,</seg>
      </tuv>
    </tu>
""".encode()

    data = extract_tmx_content(content)
    assert len(data) == 2
    assert data[0].original == '"My anger consumes me.'
    assert data[0].translation == '"Злость поглощает меня.'
    assert data[0].creation_date == datetime(2021, 7, 30, 5, 11, 33)
    assert data[0].change_date == datetime(2021, 7, 30, 5, 11, 34)

    assert data[1].original == '"The world is my hunting ground.'
    assert data[1].translation == '"Мир - мои охотничьи угодья,'
    assert data[1].creation_date == datetime(2021, 7, 30, 5, 11, 33)
    assert data[1].change_date == datetime(2021, 7, 30, 5, 11, 34)
