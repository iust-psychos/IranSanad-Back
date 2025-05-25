from openai import OpenAI
from document.spell_grammar_checker.system_prompt import (
    system_spellcheck_content,
    system_grammar_checker,
)


class SpellGrammarChecker:
    def __init__(self, AI_API_KEY, AI_MODEL):
        self.client = OpenAI(api_key=AI_API_KEY)
        self.model = AI_MODEL

    def spell_check(self, text):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_spellcheck_content},
                {"role": "user", "content": "{" + '"text" : ' + f'"{text}"' + "}"},
            ],
            response_format={"type": "text"},
            temperature=1,
            max_completion_tokens=1024,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
        )
        return response.choices[0].message.content

    def grammar_check(self, text):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_grammar_checker},
                {"role": "user", "content": "{" + '"text" : ' + f'"{text}"' + "}"},
            ],
            response_format={"type": "text"},
            temperature=1,
            max_completion_tokens=1024,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
        )
        return response.choices[0].message.content
