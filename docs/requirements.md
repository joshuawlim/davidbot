# DavidBot PRD (Prototype on Telegram → Migrate to Twilio)

## Overview
DavidBot recommends altar call songs in real time from short prompts by prioritizing thematic lyric match and tempo/energy fit, returning 3–5 results as separate messages per request. Each song recommendation is delivered as an individual message to enable direct feedback reactions. The prototype runs on Telegram using long polling from a personal computer, then migrates to Twilio AU SMS for live service use. [1][2]

## Goals
- Primary: Maximize thematic match to sermon keywords and fit to altar-call tempo/energy, defaulting to worship‑slow when unspecified. [2][3]
- Secondary: Fast, low-friction live use; minimal admin overhead via Google Sheets; easy migration to Twilio later. [1][4]

## Users
- Worship leaders, music directors, pastors; prototype on Telegram; later live use via AU SMS long code. [1][3]

## Scope
- MVP: Telegram chat input with multiple keywords; returns 3–5 song picks as individual messages with compact metadata and a short rationale; supports follow-up modifiers; direct feedback via emoji reactions on individual song messages. [1][2]
- Next: Learn-to-rank from feedback, NLP auto-tagging of lyrics, optional Planning Center export, Twilio SMS channel. [1][5]

## Channels and Sessions
- Prototype channel: Telegram Bot API via long polling; can run locally without public URL/SSL. Webhook deployment is optional later. [1][6]
- Session window: Per-user 60-minute rolling context to support follow-ups like “more,” “slower,” “female lead,” and “key D.” [1][7]
- Migration target: Twilio AU SMS with inbound webhook to n8n; maintain concise, single‑segment responses where possible. [3][2]

## Functional Requirements

### Inputs
- Free-text prompt: “find songs on x, y, z.” Bot prompts for lead (male/female) and pace (praise/fast or worship/slow; default worship‑slow). [1][2]
- Follow-ups: "more," "slower," "faster," "male/female," "key G," within 60‑minute session. Feedback via direct emoji reactions (👍/👎) on individual song messages. [1][7]

### Outputs
- 3–5 individual messages, one song per message: Title — Artist | Suggested Key | BPM | tags: … | link: MultiTracks/YouTube | rationale: matched 'keywords', slow. [2][1]
- Each message formatted for direct feedback reactions (👍/👎) to enable precise learning loops
- SMS migration consideration: Multiple messages increase segment costs; may require combined format for SMS channel. [2][8]

### Data and Admin
- Source of truth: Google Sheets. Sheets: Songs, Lyrics, Feedback, MessageLog. Single admin edits directly. [4][9]
- Songs: SongID, Title, Artist, OriginalKey, BPM, BoyKey(s), GirlKey(s), Tags (lyric + style), ResourceLink (MultiTracks/YouTube), CCLI (optional). [10][11]
- Lyrics: SongID, FullLyrics, Sections, Language. [10][12]
- Feedback: Timestamp, UserID (hashed), SessionID, SongID, Action (thumbs_up/thumbs_down), ContextKeywords, MessageID (for direct reaction tracking). [4][9]

### Recommendation Logic
- Matching priority: lyrics/tag semantic match > BPM/energy fit > key fit; default altar‑call bias to slow unless “praise/fast.” [2][3]
- Key selection: default OriginalKey; if male/female provided, prefer BoyKey/GirlKey where available. [10][11]
- Fallbacks: relax BPM/energy first, then expand tags; always return up to 3–5 with rationale. [1][7]

### Learning
- Record direct emoji reactions (👍/👎) and "used" messages to Feedback; track specific MessageID for precise song-feedback mapping; apply per‑song score boost/penalty for future rankings. [4][1]

## Non‑Functional Requirements
- Latency: near‑instant replies; local Telegram long polling is sufficient for prototype. [1][6]
- Reliability: retry Google Sheets operations on transient errors; append-only logs with unique SongID. [4][9]
- Privacy/licensing: personal, non‑commercial; store minimal identifiers; lyrics retained for research only. [3][13]

## Architecture

### Prototype (Telegram)
- BotFather issues token; local runner uses long polling to receive updates and respond. No public URL/SSL needed. [14][1]
- Orchestration: n8n optional; a simple script or worker can call Google Sheets API and implement matching/feedback. [1][4]
- State: in‑memory/session KV with 60‑minute TTL keyed by Telegram user ID. [1][7]

### Migration (Twilio SMS)
- Twilio AU long code; inbound webhook to n8n workflow; replicate matching and feedback; comply with sender ID and STOP handling. [3][15]
- SMS formatting: keep results to one segment when possible to control costs. [2][16]

## Flows

### Query Flow
1) Receive message → parse keywords; if missing lead/tempo, ask: “Male or female lead? Praise (fast) or worship (slow; default)?” [1][7]
2) Retrieve Songs + Lyrics from Sheets → compute scores → return top 3–5 as individual messages with concise metadata and rationale. [4][9]
3) Log each message to MessageLog with unique MessageID; retain context for 60 minutes; store song-to-message mapping for feedback tracking. [4][1]

### Feedback Flow
- Capture direct emoji reactions (👍/👎) on individual song messages → map MessageID to SongID → append Feedback with precise song identification → adjust per‑song score. [4][9]
- Fallback: Parse "used <song_title>" for explicit usage reporting when direct reactions unavailable. [4][9]

### Ingestion Flow
- Add new songs via Google Sheets; lyrics via manual paste or one‑off scrape; optional NLP auto‑tagging that writes Tags back to Songs sheet (admins override via Sheets). [4][9]

## Message Design

Telegram examples
- "Find songs on surrender, repentance, salvation." → Bot: "Lead? Male/female. Pace? Praise/fast or worship/slow (default)." [1][7]
- Result format (3 separate messages):
  Message 1: "O Come to the Altar — Elevation | Key G | 72 BPM | tags: altar-call, reflective | link: … | matched: 'surrender'"
  Message 2: "My Hallelujah — Bethel Music | Key D | 68 BPM | tags: surrender, worship | link: … | matched: 'surrender'"
  Message 3: "Center (Live) — Bethel Music | Key G | 68 BPM | tags: repentance, slow | link: … | matched: 'repentance'" [1][2]
- User reacts with 👍 directly on Message 2 → feedback recorded for "My Hallelujah"

SMS adaptation notes
- Individual messages will increase segment costs significantly; consider reverting to combined format for SMS channel
- Keep lines short; avoid emojis that trigger UCS‑2 unless intended; target one segment per song when possible. [2][17]
- SMS feedback may require fallback to text commands ("used song 1") due to limited reaction capabilities.

## Testing
- Golden set: 20 curated songs with hand tags; verify queries, follow-ups, feedback logging, and key selection behavior. [4][1]
- Individual message delivery: verify each song appears as separate message with unique MessageID
- Direct feedback reactions: test emoji reaction capture and mapping to specific songs
- Session expiry: verify context drops after 60 minutes. [1][7]

## Success Metrics & Acceptance Criteria

### User Story 1: Individual Song Recommendations
**As a** worship leader  
**I want** each song recommendation delivered as a separate message  
**So that** I can easily scan and react to individual songs without confusion  

**Acceptance Criteria:**
- Given user searches for songs with "find songs on surrender"
- When bot returns recommendations
- Then each song appears as a separate message
- And each message contains complete song metadata (title, artist, key, BPM, tags, link, rationale)

### User Story 2: Direct Feedback on Individual Songs  
**As a** worship leader  
**I want** to react with 👍 directly on the song I use  
**So that** the bot learns my preferences precisely without position tracking confusion  

**Acceptance Criteria:**
- Given user has received individual song recommendation messages  
- When user reacts with 👍 emoji on a specific message
- Then feedback is logged with precise song identification (MessageID → SongID mapping)
- And user receives confirmation that feedback was recorded
- And future recommendations are improved based on this precise feedback

### User Story 3: Improved Learning Loop
**As a** worship leader  
**I want** the bot to learn from my specific song choices  
**So that** future recommendations better match my preferences and context  

**Acceptance Criteria:**
- Given user has provided feedback on individual songs via direct reactions
- When user makes subsequent searches with similar themes  
- Then previously liked songs receive ranking boost
- And recommendations become more personalized over time

### Key Performance Indicators
- **Feedback Precision**: % of feedback events with specific song identification (target: >95%)
- **User Engagement**: Average reactions per recommendation set (target: increase from baseline)  
- **Learning Effectiveness**: Improvement in recommendation relevance over time (measured via continued usage)
- **Error Reduction**: Decrease in "wrong song" feedback compared to position-based system

## Technical Implementation Changes

### ResponseFormatter Updates Required
- Change `format_search_result()` to return array of individual messages instead of single concatenated string
- Add MessageID generation and tracking for each song message
- Implement song-to-message mapping storage for feedback correlation

### Bot Handler Updates Required  
- Modify message sending to iterate through individual song messages
- Implement emoji reaction event handling for direct feedback capture
- Update feedback parsing to map MessageID to SongID instead of position-based lookup
- Maintain backward compatibility with text-based feedback as fallback

### Data Schema Extensions
- Add MessageID field to Feedback table for precise reaction tracking
- Extend MessageLog to store song-to-message relationships
- Consider indexed MessageID→SongID lookup for performance

### Migration Considerations
- Telegram implementation: Full individual message support with reaction handling
- SMS implementation: Evaluate cost impact; may require channel-specific formatting (combined vs individual)
- Maintain session context across multiple outbound messages

## Rollout
- Phase 0: Local Telegram long polling prototype with individual message delivery. [1][6]
- Phase 1: Deploy Telegram webhook on a small VPS for 24/7 uptime with reaction handling. [1][6]
- Phase 2: Enable Twilio AU SMS; evaluate individual vs combined message format based on cost analysis; implement fallback feedback mechanisms. [3][2]

## Open Items
- Synonym bootstrapping for themes (e.g., surrender ~ repentance/response). [1][7]
- Optional Planning Center export in later phase. [5][1]

Appendix

### Why Telegram first
- Long polling works locally without a domain/SSL; zero per‑message cost; rapid iteration ideal for personal projects. [1][6]

### Migration tips to Twilio
- Configure AU long code; set Messaging webhook; handle STOP/UNSUBSCRIBE; be mindful of 160/70 limits and segment billing. [3][15]
- Consider keeping the same core matching logic and Sheets schema to minimize channel differences. [4][9]

Sources
[1] Long Polling vs. Webhooks https://grammy.dev/guide/deployment-types
[2] Messaging Character Limits - Twilio https://www.twilio.com/docs/glossary/what-sms-character-limit
[3] Australia: SMS Guidelines | Twilio https://www.twilio.com/en-us/guidelines/au/sms
[4] Automate Google Sheets with n8n: A Practical Guide https://ryanandmattdatascience.com/n8n-google-sheets/
[5] Twilio integrations | Workflow automation with n8n https://n8n.io/integrations/twilio/
[6] Difference Between Polling and Webhook in Telegram Bots https://hostman.com/tutorials/difference-between-polling-and-webhook-in-telegram-bots/
[7] What's the use of Telegram webhooks? https://stackoverflow.com/questions/63062298/whats-the-use-of-telegram-webhooks
[8] Does Twilio support concatenated SMS messages or messages ... https://help.twilio.com/articles/223181508-Does-Twilio-support-concatenated-SMS-messages-or-messages-over-160-characters-
[9] How to append multiple rows in google sheet at once? - Questions https://community.n8n.io/t/how-to-append-multiple-rows-in-google-sheet-at-once/134943
[10] Manual | Metadata - OnSong https://onsongapp.com/docs/features/formats/onsong/metadata/
[11] What is Metadata & How Should I Fill it Out? - School of DISCO https://school.disco.ac/article/what-is-metadata-and-how-should-i-fill-it-out
[12] Database design for a lyrics site [closed] - Stack Overflow https://stackoverflow.com/questions/1442805/database-design-for-a-lyrics-site
[13] Chatbot Product Requirements Document (PRD) - GM-RKB https://www.gabormelli.com/RKB/Chatbot_Product_Requirements_Document_(PRD)
[14] A Beginner Guide to Telegram Bot API https://apidog.com/blog/beginners-guide-to-telegram-bot-api/
[15] Receive an inbound SMS | Twilio https://www.twilio.com/docs/serverless/functions-assets/quickstart/receive-sms
[16] SMS Pricing in Australia for Text Messaging https://www.twilio.com/en-us/sms/pricing/au
[17] What is UCS-2 Character Encoding? - Twilio https://www.twilio.com/docs/glossary/what-is-ucs-2-character-encoding
[18] project-nashenas-telegram-bot/Long Polling vs. Webhook. ... https://github.com/pytopia/project-nashenas-telegram-bot/blob/main/Long%20Polling%20vs.%20Webhook.md
[19] [Q] - Polling vs. Webhook : r/TelegramBots https://www.reddit.com/r/TelegramBots/comments/525s40/q_polling_vs_webhook/
[20] Telegram Bot Creation Handbook https://dev.to/simplr_sh/telegram-bot-creation-handbook-g5g
[21] How to Migrate from Bandwidth to Twilio Programmable SMS https://www.twilio.com/en-us/lp/bandwidth-to-twilio-sms-migration-guide/chapter-3
[22] Webhooks vs Long Polling | Svix Resources https://www.svix.com/resources/faq/webhooks-vs-long-polling/
[23] Get Set Up: Migrate from Bandwidth to Twilio SMS API https://www.twilio.com/en-us/lp/bandwidth-to-twilio-sms-migration-guide/chapter-1
