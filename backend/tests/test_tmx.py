from app.tmx import extract_tmx_content


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
    assert data[0][0] == '"My anger consumes me.'
    assert data[0][1] == '"Злость поглощает меня.'


def test_can_load_simplest_tmx_1_4():
    content = """
<?xml version="1.0" encoding="utf-8"?>
<tmx version="1.4">
  <header creationtool="Smartcat" creationtoolversion="6.7334.0.0" segtype="sentence" o-tmf="ATM" adminlang="en-US" srclang="en" datatype="plaintext">
  </header>
  <body>
    <tu creationdate="20220703T075919Z" changedate="20220703T075919Z">
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
    assert data[0][0] == "Each character who plays the game makes a Wisdom check"
    assert data[0][1] == "Каждый персонаж, участвующий в игре, делает проверку Мудрости"


def test_can_load_tagged_1_4():
    content = """
<?xml version="1.0" encoding="utf-8"?>
<tmx version="1.4">
<header creationtool="Smartcat" creationtoolversion="6.7334.0.0" segtype="sentence" o-tmf="ATM" adminlang="en-US" srclang="en" datatype="plaintext">
</header>
<body>

    <tu creationdate="20220703T075919Z" changedate="20220703T075919Z">
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
        data[0][0]
        == "Each character who plays the game makes a Wisdom (Stealth) check to hide (see the Player’s Handbook for rules on skills with different abilities)."
    )
    assert (
        data[0][1]
        == "Каждый персонаж, участвующий в игре, делает проверку Мудрости (Скрытность), чтобы спрятаться (правила о навыках с различными способностями см. в Книге Игрока)."
    )


def test_can_load_multiple_segments():
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
    <tu>
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
    assert data[0][0] == '"My anger consumes me.'
    assert data[0][1] == '"Злость поглощает меня.'

    assert data[1][0] == '"The world is my hunting ground.'
    assert data[1][1] == '"Мир - мои охотничьи угодья,'
