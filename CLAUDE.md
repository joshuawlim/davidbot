# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DavidBot is a Telegram-to-Twilio worship song recommendation system that helps worship leaders find altar call songs in real-time. The bot matches sermon themes with appropriate songs based on lyrics, tempo, and energy levels.

**Key Architecture:**
- **Phase 0**: Telegram Bot using long polling (prototype on personal computer)
- **Phase 1**: Telegram webhook deployment on VPS
- **Phase 2**: Migration to Twilio AU SMS with n8n orchestration

**Data Source**: Google Sheets as single source of truth with sheets for Songs, Lyrics, Feedback, and MessageLog.

## Core Functional Requirements

### Input Processing
- Free-text prompts: "find songs on surrender, repentance, salvation"
- Follow-up modifiers: "more," "slower," "faster," "male/female," "key G," "used <#>," "👍 <#>," "👎 <#>"
- Session context: 60-minute rolling window per user

### Output Format
- 3-5 songs per response
- Format: `Title — Artist | Suggested Key | BPM | tags: ... | link: MultiTracks/YouTube | rationale: matched 'keywords', slow`
- SMS constraint: Keep under 160 GSM-7/70 UCS-2 characters per segment

### Recommendation Logic Priority
1. Lyrics/tag semantic match (highest priority)
2. BPM/energy fit
3. Key fit
4. Default altar-call bias to slow tempo unless "praise/fast" specified

## Data Schema

### Songs Sheet
- SongID, Title, Artist, OriginalKey, BPM, BoyKey(s), GirlKey(s), Tags (lyric + style), ResourceLink, CCLI

### Lyrics Sheet  
- SongID, FullLyrics, Sections, Language

### Feedback Sheet
- Timestamp, UserID (hashed), SessionID, SongID, Action, ContextKeywords, Params

## Development Constraints

- **No build/test commands**: This is a requirements/design document repository only
- **Deployment**: Local Telegram long polling initially, no public URL/SSL needed
- **State Management**: In-memory/session KV with 60-minute TTL keyed by Telegram user ID
- **Privacy**: Personal, non-commercial use; minimal identifiers stored

## Migration Considerations

When implementing Twilio SMS phase:
- Configure AU long code with inbound webhook
- Handle STOP/UNSUBSCRIBE compliance  
- Maintain single-segment responses where possible (cost control)
- Preserve core matching logic and Sheets schema for consistency

## Testing Strategy

- **Golden set**: 20 curated songs with hand tags
- **Test coverage**: Queries, follow-ups, feedback logging, key selection behavior
- **Session validation**: Context expiry after 60 minutes