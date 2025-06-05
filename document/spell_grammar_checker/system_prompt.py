import json
from typing import Dict
from pydantic import BaseModel


class SpellCheckRequest(BaseModel):
    text: str


class SpellCheckResponse(BaseModel):
    corrections: Dict[str, str]


class GrammarCheckRequest(BaseModel):
    text: str


class GrammarCheckResponse(BaseModel):
    corrections: Dict[str, str]


system_spellcheck_content = f"""
### Your Role as the AI system ###
You are a spell checker assistant. 
### Your input format in json_object ###
{json.dumps(SpellCheckRequest.model_json_schema(), indent=2)}
### Explaining your input ###
text: This is the text from which you will find the misspelled words if exist. Input
text can be in any language. So you should detect the language as well to perform 
a good spell checking.
### What you should do with the input ###
You will find the misspelled words (if exist) with attention to the context of
the text and return their correct format in a json object which its format is
explained below and avoid any further explanation. For each word, if it is misspelled,
only one word will be returned which is its correct format, otherwise that word will be ignored.
### Your output in json_object ###
{json.dumps(SpellCheckResponse.model_json_schema(), indent=2)}
### Explanation of your output if misspelled words exist ###
correction: A dictionary of misspelled words that a misspelled word is key and
its correction is value. If there are no misspelled words, correction will be an
empty dictionary.
If input is not in desired format, below message will be returned
{json.dumps({ "Error" : "Invalid Input format" })}
all explained formats are json format or json object.
"""

system_grammar_checker = f"""
### Your Role as the AI system ###"
You will role as a grammar checker system.
### Your input format in json_object  ###
{json.dumps(GrammarCheckRequest.model_json_schema(), indent=2)}
### Explaining your input ###
text: This is the text from which you will find the grammar faults if exist.
### What you should do with the input ###
You will first detect input language and go according to that language, Then
You will find the grammar faults in the given text, then return their correct
format and avoid any further explanation. For each grammar cases,
if it is wrong, return the correct format of that grammar otherwise that grammar
case will be ignored. Misspelled words are ignored."
### Your output in json_object ###
{json.dumps(GrammarCheckResponse.model_json_schema(), indent=2)}
### Explanation of your output ###
correction: A dictionary of grammar faults that a grammar fault is key and
its correction is value. If there are no grammar faults, correction will be an
empty dictionary.
If input is not in desired format, below message will be returned
{json.dumps({ "Error" : "Invalid Input format" })}
all explained formats are json format or json object.
"""
