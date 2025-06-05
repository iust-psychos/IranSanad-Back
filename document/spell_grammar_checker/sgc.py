from language_tool_python import LanguageTool


def spell_grammar_check(text):
    """
    Check the spelling and grammar of the given text using LanguageTool.
    """

    tool = LanguageTool("auto")
    matches = tool.check(text)
    spell_correction = {}
    grammar_corrections = {}
    for match in matches:
        if match.category == "GRAMMAR":
            grammar_corrections[match.matchedText] = match.replacements[0]
        elif match.category == "TYPOS":
            spell_correction[match.matchedText] = match.replacements[0]
    return {"Grammar": grammar_corrections, "Spell": spell_correction}
