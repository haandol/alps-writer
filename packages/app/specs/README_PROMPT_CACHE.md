# Prompt Cache for Claude 3.7

## Overview

This feature implements a prompt caching system for Claude 3.7, which allows efficient reuse of context from long-running conversations. The system creates cache points at strategic points in the conversation, which helps maintain continuity while reducing token usage.

## Features

- Automatically creates cache points when accumulated tokens since the last cache point exceed 2000 tokens
- Manages up to 4 cache points using FIFO (First In, First Out) strategy
- Stores cache point indices in the user session
- Recovers cache points when building new messages for continued conversations

## Implementation Details

### Key Components

1. **PromptCacheService**: Main service that handles cache creation, storage, and retrieval
2. **Token Counter**: Utility for counting tokens in messages
3. **LLMCowriterService Integration**: Updated to use cache points when building messages

### Cache Point Logic

- A cache point is created when the total tokens since the last cache point exceed 2000 tokens
- The system measures all accumulated tokens from the last cache point to the current message
- Cache points are added to specific messages in the history
- When building a new message, the system includes these cache points to maintain context
- During chat resume, the system evaluates all restored messages and creates a cache point if needed

## Usage

The prompt cache system works automatically behind the scenes:

1. User sends a message
2. LLM generates a response
3. System calculates total tokens since the last cache point
4. If total tokens exceed 2000, a new cache point is created
5. In subsequent interactions, these cache points are used to maintain context

## Technical Implementation

- Cache points are stored as special markers in the message content
- The `{"cachePoint": {"type": "default"}}` structure is recognized by Claude 3.7
- The system maintains indices of where cache points exist in the conversation history
- Token counting considers all messages since the last cache point, not just the latest response

This feature significantly improves the model's context management during extended conversations, especially when discussing technical specifications with many details.