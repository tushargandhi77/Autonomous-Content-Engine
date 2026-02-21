"""
ace_config.py — Runtime Configuration Bridge
app.py sets os.environ values before each generation call.
ACE_backend.py imports from here — reads env at property-access time → always fresh.
"""
import os


class AceConfig:

    @property
    def gemini_api_key(self) -> str:
        return os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY", "")

    @property
    def output_type(self) -> str:
        return os.environ.get("ACE_OUTPUT_TYPE", "Study Guide")

    @property
    def section_count(self) -> int:
        """Number of sections — set directly by user (3-10)."""
        return int(os.environ.get("ACE_SECTION_COUNT", "5"))

    @property
    def words_per_section(self) -> int:
        """Target words per section — set directly by user (100-1000)."""
        return int(os.environ.get("ACE_WORDS_PER_SECTION", "300"))

    @property
    def total_word_target(self) -> int:
        """Derived total = sections x words_per_section."""
        return self.section_count * self.words_per_section

    @property
    def depth_level(self) -> str:
        return os.environ.get("ACE_DEPTH_LEVEL", "Balanced")

    @property
    def tone(self) -> str:
        return os.environ.get("ACE_TONE", "Educational")

    @property
    def extra_instruction(self) -> str:
        return os.environ.get("ACE_EXTRA_INSTRUCTION", "")

    @property
    def needs_web_research(self) -> bool:
        return self.depth_level in ("Balanced", "Deep", "Exhaustive")

    def router_hint(self) -> dict:
        depth = self.depth_level
        if depth == "Quick":
            return {"mode": "closed_book", "needs_research": False}
        elif depth == "Balanced":
            return {"mode": "hybrid", "needs_research": True}
        else:
            return {"mode": "open_book", "needs_research": True}

    def build_system_prompt(self) -> str:
        output_instructions = {
            "Study Guide": (
                "You are an expert educator creating a comprehensive STUDY GUIDE. "
                "Structure content with clear definitions, worked examples, key concepts in bold, "
                "mnemonics where useful, practice questions at the end, and a summary box."
            ),
            "Blog Post": (
                "You are a skilled content writer creating an engaging BLOG POST. "
                "Use a compelling hook, clear narrative flow, subheadings for scannability, "
                "real-world examples, and a strong conclusion with a call to action."
            ),
            "Deep Research": (
                "You are a research analyst producing an in-depth RESEARCH DOCUMENT. "
                "Cover multiple perspectives, include evidence and citations, address counterarguments, "
                "use precise academic language, and provide a thorough bibliography section."
            ),
            "Quick Summary": (
                "You are a summarization expert creating a QUICK REFERENCE SUMMARY. "
                "Be extremely concise. Use bullet points for key facts and a Key Takeaways section."
            ),
        }
        tone_instructions = {
            "Educational":  "Use clear, accessible language with helpful analogies. Define jargon when used.",
            "Academic":     "Use formal academic language, precise terminology, and structured argumentation.",
            "Casual":       "Write in a friendly, conversational tone. Use contractions and relatable examples.",
            "Professional": "Be precise, structured, and business-appropriate. Avoid filler phrases.",
            "Socratic":     "Frame content as questions that lead to understanding. Pose rhetorical questions.",
        }
        depth_instructions = {
            "Quick":      f"Write ~{self.words_per_section} words per section. Be concise, hit only essential points.",
            "Balanced":   f"Write ~{self.words_per_section} words per section. Balance breadth and depth.",
            "Deep":       f"Write ~{self.words_per_section} words per section. Go into significant depth, include nuance.",
            "Exhaustive": f"Write ~{self.words_per_section} words per section. Be exhaustive, cover every angle.",
        }
        parts = [
            output_instructions.get(self.output_type, output_instructions["Study Guide"]),
            "",
            f"TONE: {tone_instructions.get(self.tone, tone_instructions['Educational'])}",
            "",
            f"LENGTH: {depth_instructions.get(self.depth_level, depth_instructions['Balanced'])}",
            f"SECTIONS: Produce exactly {self.section_count} sections.",
            f"TOTAL TARGET: ~{self.total_word_target} words across all sections.",
            "",
            "FORMAT: Always output clean Markdown. Use ## for section headers, ### for subsections. "
            "Use **bold** for key terms. Use code blocks for code/formulas. "
            "Use > blockquotes for important callouts.",
        ]
        if self.extra_instruction:
            parts += ["", f"SPECIAL INSTRUCTIONS: {self.extra_instruction}"]
        return "\n".join(parts)

    def __repr__(self):
        return (
            f"AceConfig(output_type={self.output_type!r}, sections={self.section_count}, "
            f"words_per_section={self.words_per_section}, depth={self.depth_level!r}, tone={self.tone!r})"
        )


cfg = AceConfig()