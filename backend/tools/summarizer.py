"""
tools/summarizer.py - Text Summarizer Tool
============================================
This tool condenses long text into a short, readable summary.

Why is this needed?
  When the Search tool returns a Wikipedia article, it might be very long.
  The Summarizer takes that long text and creates a shorter version,
  so the final answer is concise and easy to read.

Two modes:
  1. Simple (no LLM): Uses extractive summarization — picks the most
     important sentences based on word frequency. Fast and works offline.
     
  2. LLM-powered: Uses the OpenAI model to write an intelligent summary.
     Produces better results but requires an API key and costs tokens.

The agent uses whichever mode is configured.
"""

import re
from collections import Counter
from typing import Optional


class TextSummarizerTool:
    """
    Summarizes long text into a concise, readable summary.
    
    The agent uses this tool when:
    - A Wikipedia article is too long to include fully
    - The user asks "summarize this text: ..."
    - Research results need to be condensed before final answering
    
    Usage:
        summarizer = TextSummarizerTool()
        result = summarizer.run("Very long text here...")
        # Returns a shorter summary
    """

    # Tool metadata
    name: str = "TextSummarizer"
    description: str = (
        "Summarizes long text into a concise, readable summary. "
        "Use this when you have a large block of text that needs to be shortened. "
        "Input should be the text you want to summarize, "
        "optionally followed by the desired summary length."
    )

    def run(self, text: str, max_sentences: int = 4) -> str:
        """
        Summarize the given text.
        
        Args:
            text: The text to summarize
            max_sentences: How many sentences to include in the summary
            
        Returns:
            A shorter summary of the input text
        """
        # Clean up input
        text = text.strip()

        if not text:
            return "Error: No text provided to summarize."

        # If text is already short, no need to summarize
        word_count = len(text.split())
        if word_count < 50:
            return f"Text is already concise ({word_count} words):\n\n{text}"

        try:
            # Use extractive summarization (no API needed)
            summary = self._extractive_summarize(text, max_sentences)

            # Add metadata
            original_words = word_count
            summary_words = len(summary.split())
            reduction = round((1 - summary_words / original_words) * 100)

            return (
                f"📝 Summary ({summary_words} words, {reduction}% reduction):\n\n"
                f"{summary}\n\n"
                f"Original length: {original_words} words"
            )

        except Exception as e:
            # If summarization fails, return a truncated version
            words = text.split()
            truncated = " ".join(words[:100]) + "..."
            return f"Summary (truncated): {truncated}"

    def _extractive_summarize(self, text: str, max_sentences: int) -> str:
        """
        Extractive summarization: picks the most important sentences.
        
        Algorithm:
        1. Split text into sentences
        2. Count word frequencies (common words = important topic words)
        3. Score each sentence based on the words it contains
        4. Pick the top N highest-scoring sentences
        5. Return them in their original order
        
        This approach doesn't require an AI model — it's pure logic!
        """
        # Step 1: Split into sentences
        # We split on . ! ? followed by a space or end of string
        sentences = re.split(r'(?<=[.!?])\s+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]

        if not sentences:
            return text[:500] + "..."

        if len(sentences) <= max_sentences:
            return " ".join(sentences)

        # Step 2: Build word frequency map
        # Remove common "stop words" that don't carry meaning
        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to",
            "for", "of", "with", "by", "from", "is", "are", "was", "were",
            "be", "been", "being", "have", "has", "had", "do", "does", "did",
            "will", "would", "could", "should", "may", "might", "shall",
            "it", "its", "this", "that", "these", "those", "i", "you", "he",
            "she", "we", "they", "what", "which", "who", "when", "where",
            "how", "why", "as", "if", "then", "than", "so", "also", "can",
            "not", "no", "more", "one", "two", "about", "up", "into", "just"
        }

        # Get all words from the full text, lowercase
        all_words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        # Remove stop words
        meaningful_words = [w for w in all_words if w not in stop_words]
        # Count frequency of each word
        word_freq = Counter(meaningful_words)

        # Step 3: Score each sentence
        sentence_scores = {}
        for i, sentence in enumerate(sentences):
            words_in_sentence = re.findall(r'\b[a-zA-Z]{3,}\b', sentence.lower())
            score = 0
            for word in words_in_sentence:
                if word not in stop_words and word in word_freq:
                    score += word_freq[word]
            # Normalize by sentence length to avoid bias toward long sentences
            if words_in_sentence:
                score = score / len(words_in_sentence)
            # Give slight bonus to first sentence (often introductory/important)
            if i == 0:
                score *= 1.2
            sentence_scores[i] = score

        # Step 4: Pick top N sentences by score
        top_indices = sorted(
            sentence_scores.keys(),
            key=lambda i: sentence_scores[i],
            reverse=True
        )[:max_sentences]

        # Step 5: Return sentences in their ORIGINAL ORDER (not by score)
        top_indices_sorted = sorted(top_indices)
        summary_sentences = [sentences[i] for i in top_indices_sorted]

        return " ".join(summary_sentences)

    def summarize_bullet_points(self, text: str, num_points: int = 5) -> str:
        """
        Create a bullet-point summary instead of paragraph form.
        Useful for structured responses.
        
        Args:
            text: Text to summarize
            num_points: Number of bullet points to generate
            
        Returns:
            Bullet-point formatted summary
        """
        summary = self._extractive_summarize(text, num_points)
        sentences = re.split(r'(?<=[.!?])\s+', summary)

        bullet_points = "\n".join(
            f"• {sentence.strip()}"
            for sentence in sentences
            if sentence.strip()
        )

        return f"Key Points:\n{bullet_points}"

    def get_tool_info(self) -> dict:
        """Return tool metadata as a dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "example_inputs": [
                "Summarize this: [long text here]",
                "Give me the key points from this article: [text]",
                "Condense this into 3 sentences: [text]"
            ]
        }
