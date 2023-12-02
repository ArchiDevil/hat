import app.tmx as tmx


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

    data = tmx.extract_tmx_content(content)
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

    data = tmx.extract_tmx_content(content)
    assert len(data) == 1
    assert data[0][0] == "Each character who plays the game makes a Wisdom check"
    assert data[0][1] == "Каждый персонаж, участвующий в игре, делает проверку Мудрости"
