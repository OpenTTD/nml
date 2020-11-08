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

# Define parts of np++ xml file
string1 = """\
<NotepadPlus>
    <UserLang name="nml" ext="nml pnml">
        <Settings>
            <Global caseIgnored="no" />
            <TreatAsSymbol comment="no" commentLine="yes" />
            <Prefix words1="no" words2="no" words3="no" words4="no" />
        </Settings>
        <KeywordLists>
            <Keywords name="Delimiters">000000</Keywords>
            <Keywords name="Folder+">{</Keywords>
            <Keywords name="Folder-">}</Keywords>
            <Keywords name="Operators">( ) , : ; [ ]</Keywords>
            <Keywords name="Comment">1/* 2*/ 0//</Keywords>
            <!-- blocks, functions and units -->
            <Keywords name="Words1">"""

string2 = """\
</Keywords>
            <!-- properties and variables-->
            <Keywords name="Words2">"""

string3 = """\
</Keywords>
            <!-- features -->
            <Keywords name="Words3">"""

string4 = """\
</Keywords>
            <!-- callbacks and constants -->
            <Keywords name="Words4">"""

string5 = """\
</Keywords>
        </KeywordLists>
        <Styles>
            <WordsStyle name="DEFAULT" styleID="11" fgColor="000000" bgColor="FFFFFF" fontName="" fontStyle="0" />
            <WordsStyle name="FOLDEROPEN" styleID="12" fgColor="000080" bgColor="FFFFFF" fontName="" fontStyle="1" />
            <WordsStyle name="FOLDERCLOSE" styleID="13" fgColor="000080" bgColor="FFFFFF" fontName="" fontStyle="1" />
            <WordsStyle name="KEYWORD1" styleID="5" fgColor="0000FF" bgColor="FFFFFF" fontName="" fontStyle="0" />
            <WordsStyle name="KEYWORD2" styleID="6" fgColor="800000" bgColor="FFFFFF" fontName="" fontStyle="0" />
            <WordsStyle name="KEYWORD3" styleID="7" fgColor="D1802E" bgColor="FFFFFF" fontName="" fontStyle="1" />
            <WordsStyle name="KEYWORD4" styleID="8" fgColor="008040" bgColor="FFFFFF" fontName="" fontStyle="0" />
            <WordsStyle name="COMMENT" styleID="1" fgColor="FF9900" bgColor="FFFFFF" fontName="" fontStyle="0" />
            <WordsStyle name="COMMENT LINE" styleID="2" fgColor="FF9900" bgColor="FFFFFF" fontName="" fontStyle="0" />
            <WordsStyle name="NUMBER" styleID="4" fgColor="000000" bgColor="FFFFFF" fontName="" fontStyle="0" />
            <WordsStyle name="OPERATOR" styleID="10" fgColor="000080" bgColor="FFFFFF" fontName="" fontStyle="1" />
            <WordsStyle name="DELIMINER1" styleID="14" fgColor="000000" bgColor="FFFFFF" fontName="" fontStyle="0" />
            <WordsStyle name="DELIMINER2" styleID="15" fgColor="000000" bgColor="FFFFFF" fontName="" fontStyle="0" />
            <WordsStyle name="DELIMINER3" styleID="16" fgColor="000000" bgColor="FFFFFF" fontName="" fontStyle="0" />
        </Styles>
    </UserLang>
</NotepadPlus>
"""


# Build np++ xml file
def write_file(fname):
    with open(fname, "w") as file:
        file.write(string1)
        file.write(" ".join(extract_tables.block_names_table))
        file.write(string2)
        file.write(" ".join(extract_tables.variables_names_table))
        file.write(string3)
        file.write(" ".join(extract_tables.feature_names_table))
        file.write(string4)
        file.write(" ".join(extract_tables.callback_names_table))
        file.write(string5)


def run():
    write_file("nml_notepadpp.xml")
