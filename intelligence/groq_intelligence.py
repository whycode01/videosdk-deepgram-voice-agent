from typing import Optional

from groq import Groq

from intelligence.intelligence import Intelligence
from tts.tts import TTS


class GroqIntelligence(Intelligence):
    def __init__(self, api_key: str, tts: TTS, model: Optional[str] = None, system_prompt: Optional[str] = None):
        self.client = Groq(
            api_key=api_key,
        )

        self.tts = tts
        self.chat_history = []
        self.model = model or "openai/gpt-oss-120b"  # Default to GPT OSS 120B model
        self.system_prompt = system_prompt or """You are an experienced Software Development Engineer (SDE) interviewer conducting a technical interview for a software engineering position.

Your role and objectives:
- Assess candidate's technical competency, problem-solving skills, and communication abilities
- Conduct a comprehensive interview covering multiple technical areas
- Provide constructive feedback and maintain a professional, encouraging atmosphere
- Evaluate both technical depth and breadth of knowledge

Interview Structure and Topics:
1. Introduction and Background (5-10 minutes)
   - Welcome and interview overview
   - Candidate's background, experience, and recent projects
   - Career goals and motivations

2. Technical Fundamentals (15-20 minutes)
   - Data structures and algorithms knowledge
   - Programming language proficiency
   - Software engineering principles
   - Code quality and best practices

3. Coding Challenges (20-25 minutes)
   - Start with simple problems, gradually increase complexity
   - Focus on problem-solving approach, not just correct answers
   - Encourage thinking aloud and explaining the reasoning
   - Topics: arrays, strings, linked lists, trees, dynamic programming, etc.

4. System Design Discussion (15-20 minutes)
   - Scalability concepts and trade-offs
   - Database design and considerations
   - API design and microservices
   - Performance optimization strategies

5. Behavioral and Situational Questions (10-15 minutes)
   - Teamwork and collaboration experiences
   - Handling challenging technical problems
   - Learning and adapting to new technologies
   - Leadership and mentoring experiences (if applicable)

6. Candidate Questions and Wrap-up (5-10 minutes)
   - Address candidate's questions about role, team, or technology
   - Provide next steps information

CRITICAL OUTPUT FORMATTING RULES:
- NEVER use asterisks (*) or any markdown formatting in your responses
- NEVER include meta-commentary, stage directions, or notes meant for the LLM
- Speak directly to the candidate as if you are having a natural conversation
- Avoid filler words like "um", "uh", "well", "you know", "basically", "actually", "like"
- No parenthetical comments or asides
- Use natural, conversational language that flows well when spoken aloud
- Keep responses direct and clear without unnecessary qualifiers

Communication Guidelines:
- Maintain a conversational, supportive tone throughout
- Ask clarifying questions to understand thought processes
- Provide gentle guidance if candidate gets stuck
- Give positive reinforcement for good approaches
- Keep responses clear and focused (2-4 sentences typically)
- Adapt difficulty based on candidate's experience level
- Encourage questions and make candidate feel comfortable

Assessment Focus Areas:
- Problem decomposition and analytical thinking
- Code structure, readability, and efficiency
- Understanding of fundamental CS concepts
- Ability to discuss trade-offs and alternatives
- Communication skills and ability to explain complex concepts
- Adaptability when requirements change

Remember: Speak naturally and directly to the candidate. Your responses will be converted to speech, so ensure they sound natural when spoken aloud. Avoid any text formatting or meta-commentary."""

        self.pubsub = None
    
    def set_pubsub(self, pubsub):
        self.pubsub = pubsub

    def build_messages(self, text: str, sender_name: str):
        # Build the message with proper context
        human_message = {
            "role": "user",
            "content": f"Candidate ({sender_name}): {text}",
        }

        # Add message to history
        self.chat_history.append(human_message)

        # Local chat history for context (keep more messages for interview continuity)
        chat_history = []

        # Add system message with interviewer context
        chat_history.append(
            {
                "role": "system",
                "content": self.system_prompt,
            }
        )

        # Add conversation history (last 40 messages for better interview flow and context retention)
        chat_history = chat_history + self.chat_history[-40:]

        # Return local chat history
        return chat_history
    
    def add_response(self, text):
        ai_message = {
            "role": "assistant",
            "content": text,
        }

        self.chat_history.append(ai_message)

    def text_generator(self, response):
        """Generate text chunks from streaming response"""
        for chunk in response:
            content = chunk.choices[0].delta.content
            if content:
                yield content

    def generate(self, text: str, sender_name: str):
        try:
            # build message history
            messages = self.build_messages(text, sender_name=sender_name)

            # generate llm completion using Groq with improved parameters for complete responses
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,  # More controlled temperature for professional responses
                max_completion_tokens=2048,  # Significantly increased for longer, complete responses
                top_p=0.9,  # More focused responses
                reasoning_effort="medium",
                stream=False,  # Use non-streaming for complete responses
                stop=None
            )

            # Extract response text directly from non-streaming response
            response_text = completion.choices[0].message.content.strip()
            
            # Clean the response for TTS
            cleaned_response = self._clean_response_for_tts(response_text)

            if cleaned_response:
                # Generate TTS for the complete response without chunking to preserve context
                # Only chunk if response is extremely long (>500 characters)
                if len(cleaned_response) > 500:
                    chunks = self._split_response_for_tts(cleaned_response, max_chunk_length=400)
                    print(f"[SDE Interviewer]: {cleaned_response}")
                    
                    # Generate TTS for each chunk with slight delay to ensure proper delivery
                    for i, chunk in enumerate(chunks):
                        if chunk.strip():
                            self.tts.generate(text=chunk.strip())
                            # Small delay between chunks for better TTS processing
                            if i < len(chunks) - 1:
                                import time
                                time.sleep(0.1)
                else:
                    # For shorter responses, send as single TTS request
                    print(f"[SDE Interviewer]: {cleaned_response}")
                    self.tts.generate(text=cleaned_response)
                
                # publish message in meeting chat
                if self.pubsub is not None:
                    self.pubsub(message=f"[SDE Interviewer]: {cleaned_response}")

                # add response to history
                self.add_response(cleaned_response)
            else:
                print("No response generated from Groq")
                fallback_text = "Could you please repeat that? I want to make sure I understand your response correctly."
                self.tts.generate(text=fallback_text)
                if self.pubsub is not None:
                    self.pubsub(message=f"[SDE Interviewer]: {fallback_text}")

        except Exception as e:
            print(f"Error generating response with Groq: {e}")
            # Improved fallback response for interviewer context
            fallback_text = "I'm experiencing some technical difficulties. Let's continue with the next question."
            self.tts.generate(text=fallback_text)
            if self.pubsub is not None:
                self.pubsub(message=f"[SDE Interviewer]: {fallback_text}")

    def _split_response_for_tts(self, text: str, max_chunk_length: int = 400):
        """Split long responses into larger chunks for better TTS delivery while preserving context"""
        if len(text) <= max_chunk_length:
            return [text]
        
        # Try to split by paragraphs first (double newlines)
        paragraphs = text.split('\n\n')
        if len(paragraphs) > 1:
            chunks = []
            current_chunk = ""
            
            for paragraph in paragraphs:
                if len(current_chunk + paragraph + '\n\n') <= max_chunk_length:
                    current_chunk += paragraph + '\n\n'
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = paragraph + '\n\n'
            
            if current_chunk:
                chunks.append(current_chunk.strip())
            
            return chunks
        
        # Fallback to sentence splitting with larger chunks
        sentences = text.split('. ')
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk + sentence + '. ') <= max_chunk_length:
                current_chunk += sentence + '. '
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + '. '
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks

    def _clean_response_for_tts(self, text: str) -> str:
        """Clean the response text to make it TTS-friendly"""
        import re
        
        # Remove asterisks and markdown formatting
        text = re.sub(r'\*+', '', text)
        
        # Remove brackets and parenthetical comments that look like stage directions
        text = re.sub(r'\[.*?\]', '', text)
        text = re.sub(r'\(.*?\)', lambda m: '' if any(word in m.group().lower() for word in ['note', 'aside', 'thinking', 'pause', 'meta', 'llm', 'ai']) else m.group(), text)
        
        # Remove common filler words and phrases
        filler_patterns = [
            r'\b(um|uh|er|ah|hmm)\b',
            r'\byou know\b',
            r'\bbasically\b',
            r'\bactually\b(?!\s+implement|coding|working)',  # Keep "actually implement" but remove standalone "actually"
            r'\blike\b(?!\s+this|that)',  # Keep "like this" but remove standalone "like"
            r'\bwell\b(?=\s*[,.])',  # Remove "well" when followed by punctuation
            r'\bso\b(?=\s*[,.])',    # Remove "so" when followed by punctuation
            r'\bokay\b(?=\s*[,.])',  # Remove "okay" when followed by punctuation
        ]
        
        for pattern in filler_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # Remove excessive whitespace and normalize
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # Remove any meta-commentary patterns
        meta_patterns = [
            r'^\*.*?\*\s*',  # Remove leading asterisk comments
            r'\*.*?\*',      # Remove any remaining asterisk comments
            r'\bnow\s+(?:let\'s|let\s+us|we\s+will|we\s+should)\b',  # Remove "now let's" transitions
        ]
        
        for pattern in meta_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # Clean up punctuation issues caused by removals
        text = re.sub(r'\s*,\s*,', ',', text)  # Remove double commas
        text = re.sub(r'\s*\.\s*\.', '.', text)  # Remove double periods
        text = re.sub(r'^[,.\s]+', '', text)  # Remove leading punctuation
        text = re.sub(r'[,.\s]+$', '.', text)  # Ensure proper ending
        
        # Ensure the response ends with proper punctuation
        if text and not text[-1] in '.!?':
            text += '.'
        
        return text.strip()
