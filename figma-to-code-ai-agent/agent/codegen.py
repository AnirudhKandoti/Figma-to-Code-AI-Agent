from __future__ import annotations
import json
from typing import Dict, List, Tuple
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from .prompt import SYSTEM_PROMPT, USER_INSTRUCTION

class CodeGen:
    def __init__(self, model_name: str, api_key: str):
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=0.2,
            convert_system_message_to_human=True,
        )

    def _build_chain(self):
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", USER_INSTRUCTION),
        ])
        return prompt | self.llm | StrOutputParser()

    def generate(self, schema: dict) -> str:
        chain = self._build_chain()
        out = chain.invoke({"schema_json": json.dumps(schema, indent=2)})
        return out

    @staticmethod
    def parse_fenced_files(llm_text: str) -> List[Tuple[str,str]]:
        files: List[Tuple[str,str]] = []
        lines = llm_text.splitlines()
        current_name = None
        current_buf: List[str] = []
        in_block = False
        for ln in lines:
            if ln.startswith("```file:"):
                if in_block and current_name:
                    files.append((current_name, "\n".join(current_buf)))
                in_block = True
                current_buf = []
                current_name = ln[len("```file:"):].strip()
                continue
            if in_block and ln.strip() == "```":
                in_block = False
                if current_name:
                    files.append((current_name, "\n".join(current_buf)))
                    current_name = None
                    current_buf = []
                continue
            if in_block:
                current_buf.append(ln)
        return files
