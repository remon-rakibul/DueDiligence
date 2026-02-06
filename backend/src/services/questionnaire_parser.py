import re
from dataclasses import dataclass
from typing import List
from src.utils.loaders import get_file_type, load_documents_from_file_sync

@dataclass
class ParsedQuestion:
    section_id: str
    section_title: str
    question_text: str
    order_index: int

def _parse_content(full_text: str) -> List[ParsedQuestion]:
    out: List[ParsedQuestion] = []
    current_section_id, current_section_title, order = "0", "General", 0

    # Normalize: collapse whitespace but keep single newlines for line-based parsing
    full_text = re.sub(r"[ \t]+", " ", full_text)
    full_text = re.sub(r"\n{3,}", "\n\n", full_text)

    blocks = re.split(r"\n\s*\n", full_text)
    for block in blocks:
        block = block.strip()
        if not block or len(block) < 5:
            continue
        block_single_line = " ".join(block.split("\n"))
        # Short block without "?" -> treat as section header
        if len(block_single_line) < 80 and "?" not in block_single_line:
            current_section_title = block_single_line[:200]
            current_section_id = str(len(out))
            continue
        # Numbered pattern at start: 1. / 1) / Q1. / Question 1.
        q_match = re.match(
            r"^(?:Q(?:uestion)?\s*)?(\d+(?:\.\d+)*)[\.\)]\s*(.+)$",
            block_single_line,
            re.DOTALL | re.IGNORECASE,
        )
        if q_match:
            num, rest = q_match.group(1), q_match.group(2).strip()
            current_section_id = num.split(".")[0] if "." in num else num
            text = rest or block_single_line
            if len(text) > 2:
                out.append(
                    ParsedQuestion(
                        section_id=current_section_id,
                        section_title=current_section_title,
                        question_text=text,
                        order_index=order,
                    )
                )
                order += 1
            continue
        # Any block containing "?" -> treat as question
        if "?" in block_single_line:
            out.append(
                ParsedQuestion(
                    section_id=current_section_id,
                    section_title=current_section_title,
                    question_text=block_single_line,
                    order_index=order,
                )
            )
            order += 1
            continue
        # Line-by-line: look for lines starting with number. or number)
        for line in block.split("\n"):
            line = line.strip()
            if not line or len(line) < 5:
                continue
            line_match = re.match(
                r"^(?:Q(?:uestion)?\s*)?(\d+(?:\.\d+)*)[\.\)]\s*(.+)$",
                line,
                re.IGNORECASE,
            )
            if line_match:
                num, rest = line_match.group(1), line_match.group(2).strip()
                current_section_id = num.split(".")[0] if "." in num else num
                if len(rest) > 2:
                    out.append(
                        ParsedQuestion(
                            section_id=current_section_id,
                            section_title=current_section_title,
                            question_text=rest,
                            order_index=order,
                        )
                    )
                    order += 1
    return out

def parse_questionnaire_file(file_path: str, filename: str) -> List[ParsedQuestion]:
    docs = load_documents_from_file_sync(file_path, get_file_type(filename))
    return _parse_content("\n\n".join(d.page_content for d in docs))
