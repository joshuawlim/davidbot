# DavidBot Enhancement Roadmap

**Current Status**: v1.0 Complete ✅  
**Next Phase**: Database and Integration for Analytics

## Overview

DavidBot v1.0 is successfully deployed with:
- ✅ Telegram bot with individual song recommendations
- ✅ 69 worship songs with familiarity scoring
- ✅ Theme-based search with popularity boosting
- ✅ Usage tracking and baseline familiarity system
- ✅ Clean message formatting without link previews

The next phase focuses on building an analytics and feedback layer and adding advanced features for worship leaders.

---

## Sprint 1: Database and Integration for Analytics 🗄️
**Duration**: 3-4 days  
**Priority**: High  
**Effort**: Medium

### Goal
Integrate feedback loop from Telegram logs into davidbot.db database storage for user feedback and message logs, enabling better analytics and faster queries.

### Current State
- MessageLog and FeedbackEvent schema tables have been created
- Queries, outputs, and likes on DavidBot messages from Telegram aren't being stored in the underlying tables
- likes from DavidBot should add to familiarity score for songs

### Deliverables

#### 1.1 Enhanced Database Schema
- **MessageLog Table**: Store all user interactions with full context
  ```sql
  message_logs (
    log_id, timestamp, user_id, session_id, message_type,
    user_message, bot_response, context_keywords, songs_returned,
    error_occurred, processing_time_ms, created_at
  )
  ```

- **FeedbackEvent Table Enhancement**: Expand current user_feedback table
  ```sql
  user_feedback (
    feedback_id, timestamp, user_id, session_id, song_id,
    feedback_type, message_id, context_data, created_at
  )
  ```

#### 1.2 Database Tools
- Repository classes: `MessageLogRepository`, `FeedbackRepository`
- Database indexing for performance on analytics queries

#### 1.3 Analytics CLI Commands
```bash
# Usage analytics
python -m davidbot.manage analytics --period 30d
python -m davidbot.manage user-activity --user-id 123456

# Popular search terms
python -m davidbot.manage search-trends --top 10

# Error monitoring
python -m davidbot.manage errors --since yesterday
```

### Acceptance Criteria
- [ ] A full query, response, and like on a recommendation is logged
- [ ] Analytics queries run <1 second on 10k+ records  
- [ ] CLI commands provide actionable insights

### Technical Approach
- SQLAlchemy models with proper relationships
- Batch processing for large data migrations  
- Background logging with error recovery
- Indexed queries for common analytics patterns

---

## Sprint 2: Web Interface for Database Management 🌐
**Duration**: 7-10 days  
**Priority**: High  
**Effort**: High

### Goal
Create a user-friendly web interface for managing songs, viewing analytics, and configuring the bot without requiring CLI access.

### Deliverables

#### 2.1 FastAPI Web Application
- **Technology Stack**: FastAPI + SQLAlchemy + Jinja2 templates
- **Authentication**: Simple token-based auth for worship leaders
- **Responsive Design**: Mobile-friendly for tablet/phone use

#### 2.2 Song Management Interface
- **Song Listing**: Paginated table with search and filters
- **Bulk Operations**:
  - Import songs from CSV/JSON
  - Batch edit tags, keys, BPMs
  - Mass artist corrections
- **Individual Song Editing**:
  - Form validation for keys (A, B♭, C#, etc.)
  - Tag autocomplete from existing tags
  - BPM validation (40-200 range)
  - URL validation for MultiTracks links

#### 2.3 Usage Analytics Dashboard
- **Real-time Metrics**:
  - Search queries per day/week/month
  - Most popular songs and themes
  - User engagement statistics
  - Error rates and response times
- **Interactive Charts**: Usage trends, familiarity scores over time
- **Export Functionality**: CSV export for external analysis

#### 2.4 Familiarity Management
- **Usage Recording**: Quick interface to log service usage
- **Baseline Setting**: Bulk familiarity score management
- **Popular Song Trending**: Visual familiarity score tracking

#### 2.5 Search Preview & Testing
- **Live Search Testing**: Test search queries and see results
- **Theme Management**: Add/edit/merge themes
- **Result Ranking**: Preview how familiarity scoring affects results

### Acceptance Criteria
- [ ] Worship leaders can manage 100+ songs in <10 minutes
- [ ] Analytics load in <3 seconds with 6 months of data
- [ ] Mobile interface works on tablets during services
- [ ] Search preview matches bot results exactly
- [ ] Bulk operations handle 500+ songs without timeout
- [ ] User authentication prevents unauthorized access

### Technical Approach
- FastAPI with async request handling
- SQLAlchemy with connection pooling
- Client-side validation + server-side verification
- Progressive loading for large datasets
- WebSocket updates for real-time analytics

---

## Sprint 3: Enhanced Bot Intelligence 🤖
**Duration**: 5-7 days  
**Priority**: Medium  
**Effort**: Medium

### Goal
Explore use of an LLM or otherwise to add natural language processing and conversational intelligence to make DavidBot more intuitive and natural for users.

### Deliverables

#### 3.1 Natural Language Query Processing
- **Flexible Search Patterns**:
  ```
  "upbeat songs for celebration" → BPM >120 + celebration tags
  "slow songs about grace" → BPM <80 + grace theme
  "something like Goodness of God" → similarity matching
  "songs we haven't used lately" → low recent usage
  ```

- **Context Understanding**:
  - Understand relative terms: "faster," "slower," "similar"
  - Parse compound requests: "praise songs in G that aren't too long"
  - Handle typos and alternative spellings

#### 3.2 Conversational Context Awareness
- **Follow-up Processing**:
  ```
  User: "find songs on surrender" 
  Bot: [3 songs]
  User: "the second one was perfect"
  Bot: Understands reference to song #2, logs positive feedback
  ```

- **Session Memory**: Remember previous searches within session
- **Smart Suggestions**: "You might also like..." based on selections

#### 3.3 Advanced Filtering
- **Multi-criteria Search**:
  - BPM ranges with theme matching
  - Key signatures with familiarity thresholds
  - Exclude recently used songs automatically
  
- **Smart Defaults**:
  - Morning service: brighter keys, moderate BPM
  - Evening service: introspective themes, varied tempo
  - Altar call: surrender/response themes prioritized

#### 3.4 Worship Leader Personality
- **Context-Aware Responses**:
  - Urgent requests get quick, confident suggestions
  - Exploratory requests get detailed explanations
  - Error states provide helpful alternatives

- **Ministry-Focused Language**:
  - "For this season of worship..." 
  - "These songs invite response..."
  - "Perfect for altar call ministry..."

### Acceptance Criteria
- [ ] 90% of natural language queries return relevant results
- [ ] Context awareness works across 3+ message exchanges
- [ ] Response time stays <2 seconds for complex queries
- [ ] Worship leaders report improved ease of use
- [ ] Bot personality feels appropriate for ministry context
- [ ] Bot is brief and straight to the point

### Technical Approach
- spaCy or NLTK for natural language processing
- Fuzzy string matching for typo tolerance
- Session state management with TTL
- Rule-based classification for worship contexts
- A/B testing for personality variations

---

## Sprint 4: Lyrical Sections Display 📝
**Duration**: 3-5 days  
**Priority**: Low  
**Effort**: Low

### Goal
Populate the first_line, chorus, and bridge columns with brief, copyright-safe excerpts to help worship leaders quickly identify and preview songs.

### Deliverables

#### 4.1 Copyright-Safe Content Strategy
- **Identification Excerpts**: Brief phrases for song recognition
- **Fair Use Compliance**: Short excerpts for identification purposes
- **Manual Curation**: Hand-selected content to ensure appropriateness

#### 4.2 Lyrical Content Management
- **Database Population**:
  - First line: Opening words for immediate recognition
  - Chorus: Key hook phrase (4-6 words max)
  - Bridge: Distinctive bridge identifier if applicable

- **Management Interface**: Web form for editing lyrical excerpts
- **Bulk Import Tools**: CSV import for batch content updates

#### 4.3 Search Integration
- **Enhanced Results**: Show relevant song sections in results
  ```
  Goodness Of God - Bethel Music
  Key F# | 68 BPM
  Tags: Goodness, Faithfulness, Testimony, Worship
  Opening: "I love You Lord, oh Your mercy..."
  Link: <https://multitracks.com/...>
  ```

- **Section-Based Search**: Find songs by lyrical content
- **Preview Mode**: Quick lyrical preview before recommending

#### 4.4 Content Guidelines & Tools
- **Style Guide**: Consistent formatting for excerpts
- **Legal Review Checklist**: Copyright compliance verification
- **Quality Assurance**: Validation for accuracy and appropriateness

### Acceptance Criteria
- [ ] 80% of songs have first_line populated with recognizable excerpts
- [ ] 60% of songs have chorus hooks for quick identification  
- [ ] Zero copyright violations in excerpt selection
- [ ] Web interface supports efficient batch editing
- [ ] Search results help worship leaders recognize songs instantly
- [ ] Content is appropriate for worship ministry context

### Technical Approach
- Manual content curation with legal review
- CSV import/export for bulk operations
- Database migrations for content updates
- Integration with existing search formatting
- Content validation scripts

---

## Implementation Strategy

### Phase Approach
**Immediate (Sprint 1)**: Foundation - Database migration
**Near-term (Sprint 2)**: High Impact - Web interface  
**Medium-term (Sprint 3)**: Enhancement - Bot intelligence
**Long-term (Sprint 4)**: Polish - Lyrical content

### Risk Mitigation
- **Sprint boundaries**: Each sprint delivers independent value
- **Rollback plans**: Database migrations preserve existing functionality
- **User testing**: Worship leader feedback at each sprint completion
- **Scope control**: Kill features that don't prove immediate value

### Success Metrics
- **Sprint 1**: Analytics queries 10x faster than Sheets
- **Sprint 2**: Song management time reduced by 75%
- **Sprint 3**: User satisfaction scores >8/10
- **Sprint 4**: Song recognition time improved by 50%

---

## Technology Stack

### Current Foundation
- **Backend**: Python 3.11, SQLAlchemy, SQLite
- **Bot**: Telegram Bot API with async handling
- **Data**: 69 songs, usage tracking, familiarity scoring
- **Management**: CLI tools for all operations

### Sprint Additions
- **Web Framework**: FastAPI with Jinja2 templates
- **Frontend**: HTML5, CSS3, vanilla JavaScript
- **NLP**: spaCy for natural language processing
- **Analytics**: SQLAlchemy with optimized queries
- **Authentication**: JWT tokens for web access

### Infrastructure
- **Database**: SQLite (sufficient for single-church deployment)  
- **Deployment**: Single server with systemd service
- **Backup**: Daily database snapshots
- **Monitoring**: Built-in error logging and metrics

---

## Getting Started

### Sprint 1 Next Actions
1. **Design database schema** for MessageLog and FeedbackEvent tables
2. **Create migration scripts** to preserve existing Google Sheets data
3. **Build repository classes** for database operations
4. **Implement analytics CLI commands** for immediate value
5. **Test data migration** with validation scripts

### Prerequisites
- Current DavidBot v1.0 running successfully
- Access to existing Google Sheets data
- Backup strategy for current database

### Execution Timeline
- **Week 1**: Sprint 1 (Database Migration)
- **Week 2-3**: Sprint 2 (Web Interface)  
- **Week 4**: Sprint 3 (Bot Intelligence)
- **Week 5**: Sprint 4 (Lyrical Sections)

---

*Last Updated: 2025-01-15*  
*Next Review: After Sprint 1 Completion*