__license__ = """
NML is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

NML is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with NML; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA."""

from nml.editors import extract_tables

output_file = "nml_kate.xml"

header_text = """\
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE language SYSTEM "language.dtd">
<!--
        This is a syntax highlighter for NML, the NewGRF markup language
        (http://dev.openttdcoop.org/nml) used to write NewGRF
        extensions for OpenTTD (http://www.openttd.org)

        The part on highlighting preprocessor instructions are taken from kate's c++ highlighter
        in the version 1.49 by Sebastian Pipping (webmaster@hartwork.org)
-->
<language name="NML" section="Sources" version="0.01" kateversion="2.4"
      extensions="*.nml;*.pnml;*.tnml"
      mimetype="text/x-nml"
      indenter="cstyle"
      author="Ingo von Borstel"
      license="GPL v2"
      priority="10">

  <highlighting>
    <list name="blockwords">
"""

feature_text = """\
    </list>
    <list name="features">
"""

builtin_text = """\
    </list>
    <list name="builtin">
"""

constant_text = """\
    </list>
    <list name="constants">
"""

tail_text = """\
    </list>

    <contexts>
      <!-- Normal text with the usual keywords and inserts -->
      <context name="Normal" attribute="Normal Text" lineEndContext="#stay">
        <DetectSpaces />
        <DetectChar context="AfterHash" char="#" firstNonSpace="true" lookAhead="true" />
        <keyword attribute="Block" context="#stay" String="blockwords" />
        <keyword attribute="Feature" context="#stay" String="features" />
        <keyword attribute="Built-in Function" context="#stay" String="builtin" />
        <keyword attribute="Constant" context="#stay" String="constants" />
        <DetectChar attribute="String" context="String" char="&quot;"/>
        <Detect2Chars attribute="Comment" context="Comment 1" char="/" char1="/" />
        <Detect2Chars attribute="Comment" context="Comment 2" char="/" char1="*" />
      </context>

      <!-- Strings within quotation marks -->
      <context attribute="String" lineEndContext="#pop" name="String">
        <LineContinue attribute="String" context="#stay"/>
        <HlCStringChar attribute="String Char" context="#stay"/>
        <DetectChar attribute="String" context="#pop" char="&quot;"/>
      </context>

      <!-- Strings starting with // -->
      <context attribute="Comment" lineEndContext="#pop" name="Comment 1">
        <LineContinue attribute="Comment" context="#stay"/>
        <DetectSpaces />
        <IncludeRules context="##Alerts" />
        <DetectIdentifier />
      </context>
      <!-- Multi-line strings like /* ... */ -->
      <context attribute="Comment" lineEndContext="#stay" name="Comment 2">
        <DetectSpaces />
        <Detect2Chars attribute="Comment" context="#pop" char="*" char1="/" endRegion="Comment"/>
        <IncludeRules context="##Alerts" />
        <DetectIdentifier />
      </context>

      <!-- Preprocessor commands starting with a hash - Main switch for preprocessor -->
      <context attribute="Error" lineEndContext="#pop" name="AfterHash">
        <!-- define,elif,else,endif,error,if,ifdef,ifndef,include,include_next,line,pragma,undef,warning -->
        <RegExpr attribute="Preprocessor" context="Preprocessor"
                 String="#\\s*if(?:def|ndef)?(?=\\s+\\S)" insensitive="true" beginRegion="PP" firstNonSpace="true" />
        <RegExpr attribute="Preprocessor" context="Preprocessor"
                 String="#\\s*endif" insensitive="true" endRegion="PP" firstNonSpace="true" />
        <RegExpr attribute="Preprocessor" context="Define"
                 String="#\\s*define.*((?=\\))" insensitive="true" firstNonSpace="true" />
        <RegExpr attribute="Preprocessor" context="Preprocessor"
                 String="#\\s*(?:el(?:se|if)|include(?:_next)?|define|undef|line|error|warning|pragma)"
                 insensitive="true" firstNonSpace="true" />
        <RegExpr attribute="Preprocessor" context="Preprocessor"
                 String="#\\s+[0-9]+" insensitive="true" firstNonSpace="true" />
      </context>
      <!-- Preprocessor instructions -->
      <context attribute="Preprocessor" lineEndContext="#pop" name="Preprocessor">
        <LineContinue attribute="Preprocessor" context="#stay"/>
        <RangeDetect attribute="Prep. Lib" context="#stay" char="&quot;" char1="&quot;"/>
        <RangeDetect attribute="Prep. Lib" context="#stay" char="&lt;" char1="&gt;"/>
        <IncludeRules context="##Doxygen" />
        <Detect2Chars attribute="Comment" context="Comment/Preprocessor" char="/" char1="*" beginRegion="Comment2" />
        <Detect2Chars attribute="Comment" context="Comment 1" char="/" char1="/"/>
      </context>
      <!-- Preprocessor #define -->
      <context attribute="Preprocessor" lineEndContext="#pop" name="Define">
        <LineContinue attribute="Preprocessor" context="#stay"/>
      </context>
      <!-- Preprocessor comments -->
      <context attribute="Comment" lineEndContext="#stay" name="Comment/Preprocessor">
        <DetectSpaces />
        <Detect2Chars attribute="Comment" context="#pop" char="*" char1="/" endRegion="Comment2" />
        <DetectIdentifier />
      </context>

    </contexts>

    <itemDatas>
      <itemData name="Normal Text"       defStyleNum="dsNormal" />
      <itemData name="Block"             defStyleNum="dsKeyword" />
      <itemData name="Feature"           defStyleNum="dsKeyword" color="#0095ff"
                                         selColor="#ffffff" bold="1" italic="0" spellChecking="false"/>
      <itemData name="Built-in Function" defStyleNum="dsDataType" spellChecking="false" />
      <itemData name="String"            defStyleNum="dsString"/>
      <itemData name="Preprocessor"      defStyleNum="dsOthers" spellChecking="false"/>
      <itemData name="Constant"          defStyleNum="dsOthers" color="#006400" italic="1" spellChecking="false" />
      <itemData name="Comment"           defStyleNum="dsComment"/>
    </itemDatas>
  </highlighting>

  <general>
    <comments>
      <comment name="singleLine" start="//" />
      <comment name="multiLine" start="/*" end="*/" region="Comment"/>
    </comments>
    <keywords casesensitive="1" />
  </general>

  </language>
<!--
// kate: space-indent on; indent-width 2; replace-tabs on;
-->
"""


def write_file(fname):
    with open(fname, "w") as file:
        file.write(header_text)
        for word in extract_tables.keywords:
            file.write("      <item> {} </item>\n".format(word))

        file.write(feature_text)
        for word in extract_tables.features:
            file.write("      <item> {} </item>\n".format(word))

        file.write(builtin_text)
        for word in extract_tables.functions:
            file.write("      <item> {} </item>\n".format(word))

        file.write(constant_text)
        for word in extract_tables.callback_names_table:
            file.write("      <item> {} </item>\n".format(word))

        file.write(tail_text)


def run():
    write_file("nml_kate.xml")
