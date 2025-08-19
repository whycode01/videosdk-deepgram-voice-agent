#!/usr/bin/env python3
"""
Test script for SDE Interviewer functionality with improved TTS context
"""
import os
from dotenv import load_dotenv
from intelligence.groq_intelligence import GroqIntelligence

# Mock TTS class for testing
class MockTTS:
    def __init__(self):
        self.generated_texts = []
    
    def generate(self, text):
        self.generated_texts.append(text)
        print(f"[TTS Chunk {len(self.generated_texts)}]: {text}")
        print(f"[TTS Chunk Length]: {len(text)} characters")
        print("-" * 50)

def test_sde_interviewer_improved():
    load_dotenv()
    
    # Create mock TTS
    mock_tts = MockTTS()
    
    # Create SDE interviewer
    interviewer = GroqIntelligence(
        api_key=os.getenv("GROQ_API_KEY"),
        tts=mock_tts,
        model="openai/gpt-oss-120b"
    )
    
    print("Testing Improved SDE Interviewer with Enhanced TTS Context...")
    print("=" * 70)
    
    # Test introduction
    print("\n1. Testing introduction (should be longer response):")
    interviewer.generate("Hello, I'm ready for the interview", "Alex")
    
    # Test technical question with detailed response
    print("
2. Testing technical response (should handle longer content):")
    interviewer.generate("I have 5 years of experience working with Python, JavaScript, React, Node.js, and PostgreSQL. I've built several full-stack applications and worked on microservices architecture.", "Alex")
    
    # Test complex coding question response
    print("
3. Testing coding question response (should maintain context):")
    interviewer.generate("For the two-sum problem, I would use a hash map to store the numbers I've seen so far and their indices. I'd iterate through the array once, and for each number, check if its complement exists in the hash map. This gives us O(n) time complexity and O(n) space complexity.", "Alex")
    
    print(f"
Total TTS chunks generated: {len(mock_tts.generated_texts)}")
    print(f"Total characters processed: {sum(len(text) for text in mock_tts.generated_texts)}")
    print("
Test completed!")

if __name__ == "__main__":
    test_sde_interviewer_improved()
