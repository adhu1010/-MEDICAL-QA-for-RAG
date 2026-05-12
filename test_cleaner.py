class MockGenerator:
    def _clean_meditron_response(self, answer: str) -> str:
        if not answer:
            return ""

        if 'Detailed Answer:' in answer and answer.index('Detailed Answer:') < len(answer) / 2:
            answer = answer.split('Detailed Answer:', 1)[-1].strip()
        elif answer.startswith('Answer:') or ( 'Answer:' in answer and answer.index('Answer:') < 50):
            answer = answer.split('Answer:', 1)[-1].strip()

        if '\nQuestion:' in answer:
            answer = answer.split('\nQuestion:')[0].strip()
        elif '\nQ:' in answer:
            answer = answer.split('\nQ:')[0].strip()

        prompt_echoes = [
            'Provide a clear medical answer:', 'Answer in simple terms:',
            'Provide a helpful medical answer based on the information above:',
            'You are a helpful medical', 'Health Info:', 'Medical Context:'
        ]
        for echo in prompt_echoes:
            if answer.lower().startswith(echo.lower()):
                answer = answer[len(echo):].strip()
            answer = answer.replace(echo, '').strip()

        prompt_echo_patterns = [
            'Based on the provided', 'Based on the context', 'Based on the information',
            'In the context of', 'According to the provided', 'Here is a detailed',
            'Here is the detailed', 'Here is an explanation'
        ]

        lines = answer.split('\n')
        cleaned_lines = []
        skip_mode = True

        for line in lines:
            line_stripped = line.strip()
            
            if not line_stripped:
                continue
                
            if line_stripped.startswith("Question:"):
                if "?" in line_stripped or len(line_stripped) < 100:
                    continue
            
            if line_stripped == "Answer:":
                continue

            if skip_mode and any(p in line_stripped for p in prompt_echo_patterns):
                continue
            
            skip_mode = False
            cleaned_lines.append(line)
                
        answer = ' '.join(cleaned_lines)

        artifacts = [
            "</s>", "<s>", "<|im_end|>", "<|im_start|>",
            "[INST]", "[/INST]", "<<SYS>>", "<</SYS>>",
            "assistant", "Assistant:", "###", "```",
            "# Discussion", "# Conclusions", "# Background", "# Methods",
            "# Results", "# Abstract", "## ", "# "
        ]
        for artifact in artifacts:
            answer = answer.replace(artifact, "")

        return answer.strip()

mock = MockGenerator()
test_input = """- Imerslund-Grasbeck syndrome is a rare condition first described in Finland and Norway; it is estimated to affect 1 in 200,000 people in these regions.
- Explain how the condition was discovered, as well as the symptoms experienced by those who were diagnosed with IGS:
- The condition was first des"""
print("OUTPUT:", repr(mock._clean_meditron_response(test_input)))
