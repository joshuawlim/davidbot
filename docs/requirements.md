# DavidBot PRD (Prototype on Telegram → Migrate to Twilio)

## Overview
DavidBot recommends altar call songs in real time from short prompts by prioritizing thematic lyric match and tempo/energy fit, returning 3–5 concise results per request. The prototype runs on Telegram using long polling from a personal computer, then migrates to Twilio AU SMS for live service use. [1][2]

## Goals
- Primary: Maximize thematic match to sermon keywords and fit to altar-call tempo/energy, defaulting to worship‑slow when unspecified. [2][3]
- Secondary: Fast, low-friction live use; minimal admin overhead via Google Sheets; easy migration to Twilio later. [1][4]

## Users
- Worship leaders, music directors, pastors; prototype on Telegram; later live use via AU SMS long code. [1][3]

## Scope
- MVP: Telegram chat input with multiple keywords; returns 3–5 song picks with compact metadata and a short rationale; supports follow-up modifiers; simple feedback (“👍/👎/used”). [1][2]
- Next: Learn-to-rank from feedback, NLP auto-tagging of lyrics, optional Planning Center export, Twilio SMS channel. [1][5]

## Channels and Sessions
- Prototype channel: Telegram Bot API via long polling; can run locally without public URL/SSL. Webhook deployment is optional later. [1][6]
- Session window: Per-user 60-minute rolling context to support follow-ups like “more,” “slower,” “female lead,” and “key D.” [1][7]
- Migration target: Twilio AU SMS with inbound webhook to n8n; maintain concise, single‑segment responses where possible. [3][2]

## Functional Requirements

### Inputs
- Free-text prompt: “find songs on x, y, z.” Bot prompts for lead (male/female) and pace (praise/fast or worship/slow; default worship‑slow). [1][2]
- Follow-ups: “more,” “slower,” “faster,” “male/female,” “key G,” “used <#>,” “👍 <#>,” “👎 <#>,” within 60‑minute session. [1][7]

### Outputs
- 3–5 items, one per line: Title — Artist | Suggested Key | BPM | tags: … | link: MultiTracks/YouTube | rationale: matched ‘keywords’, slow. [2][1]
- Keep under one segment on SMS later: 160 GSM-7/70 UCS‑2; segmenting increases cost and may split messages. [2][8]

### Data and Admin
- Source of truth: Google Sheets. Sheets: Songs, Lyrics, Feedback, MessageLog. Single admin edits directly. [4][9]
- Songs: SongID, Title, Artist, OriginalKey, BPM, BoyKey(s), GirlKey(s), Tags (lyric + style), ResourceLink (MultiTracks/YouTube), CCLI (optional). [10][11]
- Lyrics: SongID, FullLyrics, Sections, Language. [10][12]
- Feedback: Timestamp, UserID (hashed), SessionID, SongID, Action, ContextKeywords, Params. [4][9]

### Recommendation Logic
- Matching priority: lyrics/tag semantic match > BPM/energy fit > key fit; default altar‑call bias to slow unless “praise/fast.” [2][3]
- Key selection: default OriginalKey; if male/female provided, prefer BoyKey/GirlKey where available. [10][11]
- Fallbacks: relax BPM/energy first, then expand tags; always return up to 3–5 with rationale. [1][7]

### Learning
- Record “👍/👎/used” to Feedback; apply simple per‑song score boost/penalty for future rankings. [4][1]

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
2) Retrieve Songs + Lyrics from Sheets → compute scores → return top 3–5 with concise metadata and rationale. [4][9]
3) Log interaction to MessageLog; retain context for 60 minutes. [4][1]

### Feedback Flow
- Parse “used <n>,” “👍 <n>,” “👎 <n>” → map n to SongID from last response → append Feedback → adjust per‑song score. [4][9]

### Ingestion Flow
- Add new songs via Google Sheets; lyrics via manual paste or one‑off scrape; optional NLP auto‑tagging that writes Tags back to Songs sheet (admins override via Sheets). [4][9]

## Message Design

Telegram examples
- “Find songs on surrender, repentance, salvation.” → Bot: “Lead? Male/female. Pace? Praise/fast or worship/slow (default).” [1][7]
- Result lines: “O Come to the Altar — Elevation | Key G | 72 BPM | tags: altar-call, reflective | link: … | matched: ‘surrender’” [1][2]

SMS adaptation notes
- Keep lines short; avoid emojis that trigger UCS‑2 unless intended; target one segment. [2][17]

## Testing
- Golden set: 20 curated songs with hand tags; verify queries, follow-ups, feedback logging, and key selection behavior. [4][1]
- Session expiry: verify context drops after 60 minutes. [1][7]

## Rollout
- Phase 0: Local Telegram long polling prototype on a laptop/desktop. [1][6]
- Phase 1: Deploy Telegram webhook on a small VPS for 24/7 uptime. [1][6]
- Phase 2: Enable Twilio AU SMS; configure webhook to n8n; verify STOP handling and single‑segment formatting. [3][2]

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
