# DavidBot Enhanced Features PRD
## Version 2.0 Product Requirements Document

### Executive Summary

DavidBot v1.0 has successfully delivered basic worship song recommendations with Telegram integration and Ollama/Mistral LLM intelligence. This PRD defines the roadmap for v2.0, integrating new worship leader requirements while maintaining the ministry-focused value proposition. The enhanced system will provide comprehensive song management, intelligent filtering, and robust session context to serve worship leaders in live service preparation.

---

## Problem Statement

**Current State:** DavidBot v1.0 provides basic song recommendations but lacks critical worship leader functionality:
- No BPM-based filtering for tempo requests ("slow songs", "upbeat praise")  
- No key suggestions for male/female vocals
- Limited feedback mechanisms and no database editing capabilities
- Missing musical tag taxonomy separate from lyrical content
- Poor session memory and no recently recommended history
- No familiarity score management

**Future State:** A comprehensive worship preparation assistant that understands musical context, learns from feedback, and provides database management tools for ongoing ministry needs.

---

## Goals & Success Criteria

### Primary Goals
1. **Enhanced Musical Intelligence**: 90% accuracy on tempo/BPM filtering requests
2. **Complete Feedback Loop**: Worship leaders can rate songs and edit database entries
3. **Session Context Mastery**: 60-minute rolling context with recommendation history
4. **Musical Tag Taxonomy**: Separate system for musical vs lyrical characteristics

### Success Metrics
- **User Engagement**: 40% increase in follow-up queries per session
- **Recommendation Accuracy**: 85% positive feedback on tempo-filtered results
- **Database Quality**: 200+ songs with complete musical tag coverage
- **Session Effectiveness**: Average 8+ recommendations per worship leader session

### Guardrails
- **Ministry Focus**: All features must serve live worship preparation
- **Performance**: Sub-2 second response times maintained
- **Simplicity**: No feature complexity that impedes live service use
- **Backward Compatibility**: Existing v1.0 functionality preserved

---

## Out-of-Scope

**Explicitly excluded from v2.0:**
- Planning Center integration (deferred to v3.0)
- Multi-church/tenant architecture  
- Advanced music theory analysis (chord progression matching)
- Lyrics copyright content display
- Web dashboard (limited to CLI management tools)
- Real-time service integration beyond recommendations

---

## User Personas

### Primary: Live Worship Leader
**Context**: Preparing song flow 30 minutes before service
**Pain Points**: 
- Needs tempo-appropriate songs quickly
- Must consider vocal range for team members
- Requires familiarity scoring for congregation engagement
**Goals**: Fast, accurate song selection with minimal friction

### Secondary: Music Director  
**Context**: Weekly service planning and database maintenance
**Pain Points**:
- Database inconsistencies in tags and scoring
- No bulk editing capabilities
- Limited analytics on song usage patterns
**Goals**: Maintain accurate song database and usage insights

---

## Enhanced User Journeys

### Journey 1: Tempo-Specific Song Request
```
Worship Leader: "find slow songs for altar call"
DavidBot: Parses "slow" → filters BPM <80 → returns 5 songs with rationale
Follow-up: "even slower" → re-filters BPM <65
Result: Perfect tempo match for ministry moment
```

### Journey 2: Vocal Range Optimization
```
Worship Leader: "upbeat songs for female lead in key of G"
DavidBot: Filters BPM >110, prefers GirlKey fields, suggests G/Am/C
Follow-up: "👍 #3" → logs positive feedback for song #3
Result: Future recommendations boosted for similar requests
```

### Journey 3: Database Management
```
Music Director: "edit song 'Goodness of God'"
DavidBot: Shows current tags and familiarity score
Music Director: "add tag: building bridge, set familiarity 8"
DavidBot: Updates database, confirms changes
Result: Improved future recommendations with accurate metadata
```

---

## Feature Specifications

### Feature 1: BPM-Based Tempo Filtering

**User Story**: As a worship leader, I want to request "fast" or "slow" songs so that the bot returns appropriate tempo matches for the worship moment.

**Acceptance Criteria**:
- Given user requests "slow songs on surrender"
- When bot processes request
- Then songs returned have BPM <80 
- And rationale includes "slow tempo match"
- And follow-up "slower" re-filters to BPM <65

**Technical Implementation**:
```python
class TempoFilter:
    TEMPO_RANGES = {
        "slow": (40, 80),
        "medium": (80, 120), 
        "fast": (120, 200)
    }
    
    def filter_by_tempo(self, songs: List[Song], tempo: str) -> List[Song]:
        min_bpm, max_bpm = self.TEMPO_RANGES[tempo]
        return [s for s in songs if min_bpm <= s.bpm <= max_bpm]
```

### Feature 2: Vocal Range Key Suggestions

**User Story**: As a worship leader, I want key suggestions for male/female vocals so I can select songs in appropriate ranges for my team.

**Acceptance Criteria**:
- Given user specifies "male lead"
- When bot returns recommendations  
- Then BoyKey values are prioritized in suggested keys
- And rationale includes "optimized for male vocals"
- And fallback to OriginalKey if BoyKey missing

**Technical Implementation**:
```python
class KeySuggester:
    def suggest_key(self, song: Song, vocal_type: str) -> str:
        if vocal_type == "male" and song.boy_key:
            return song.boy_key
        elif vocal_type == "female" and song.girl_key:
            return song.girl_key
        return song.original_key
```

### Feature 3: Feedback Processing & Database Editing

**User Story**: As a worship leader, I want to rate songs and edit their information so the bot improves and maintains accurate data.

**Acceptance Criteria**:
- Given user responds "👍 #2" to recommendation list
- When bot processes feedback
- Then familiarity score increases for song #2
- And positive feedback logged with context
- And future searches boost this song's ranking

**Database Editing Criteria**:
- Given user requests "edit song 'Amazing Grace'"  
- When bot shows current metadata
- Then user can modify tags, familiarity score, keys, BPM
- And changes persist to database
- And confirmation message displays updated values

### Feature 4: Musical Tags System

**User Story**: As a music director, I want to tag songs with musical characteristics separate from lyrical themes so recommendations consider both aspects.

**Acceptance Criteria**:
- Given song has lyrical_tags ["surrender", "worship"] and musical_tags ["building_bridge", "6/8", "call_response"]
- When user searches "songs with building bridges"
- Then bot matches musical_tags for recommendation
- And rationale distinguishes musical vs lyrical matches

**Schema Enhancement**:
```sql
ALTER TABLE songs ADD COLUMN musical_tags TEXT;
-- Example: "building_bridge,6/8,call_response,key_change"
```

### Feature 5: Session Context & History

**User Story**: As a worship leader, I want to see what songs were recently recommended so I avoid repetition and track my session progress.

**Acceptance Criteria**:
- Given user has received 12 recommendations in current session
- When user requests "show recent songs"
- Then bot displays last 10 recommendations with timestamps
- And excludes these from new searches unless explicitly requested
- And session context clears after 60 minutes

### Feature 6: Enhanced Familiarity Management  

**User Story**: As a music director, I want to bulk-edit familiarity scores so I can reflect actual congregation knowledge accurately.

**Acceptance Criteria**:
- Given user requests "show songs with familiarity < 5"
- When bot lists low-familiarity songs
- Then user can bulk-update scores: "set familiarity 7 for songs 1,3,5"
- And changes reflect immediately in future recommendations

---

## Revised Sprint Roadmap

### Sprint 1A: Core Musical Intelligence (3-4 days)
**Priority**: Critical - Foundation for all musical features

**Deliverables**:
1. **BPM Tempo Filtering**
   - Parse tempo keywords ("slow", "fast", "upbeat", "ballad")
   - Implement filtering logic with configurable ranges
   - Add tempo rationale to response formatting

2. **Vocal Range Key Suggestions**  
   - Extend Song model with BoyKey/GirlKey fields
   - Database migration for key data
   - Key suggestion logic in recommendation engine

3. **Musical Tags Schema**
   - Add musical_tags column to songs table
   - Populate initial musical characteristics for 69 songs
   - Separate matching logic for musical vs lyrical tags

**Acceptance Criteria**:
- [ ] "slow songs" returns only BPM <80 matches
- [ ] "male lead" prioritizes BoyKey suggestions  
- [ ] "building bridge" matches musical_tags field
- [ ] All existing functionality preserved

### Sprint 1B: Feedback & Database Management (2-3 days)
**Priority**: High - Enables learning and maintenance

**Deliverables**:
1. **Feedback Processing Enhancement**
   - Parse thumbs up/down with position tracking
   - Update familiarity scores based on feedback
   - Log detailed feedback context

2. **Database Editing Interface**
   - CLI commands for song metadata editing
   - Bulk familiarity score updates  
   - Tag addition/removal functionality

3. **Validation & Safety**
   - Input validation for BPM, keys, familiarity scores
   - Backup functionality before bulk operations
   - Error recovery for invalid operations

**Acceptance Criteria**:
- [ ] "👍 #3" increases familiarity score for song #3
- [ ] "edit song 'Amazing Grace'" allows metadata modification
- [ ] Bulk operations handle 50+ songs without errors
- [ ] All changes logged for audit trail

### Sprint 2: Session Intelligence & History (2-3 days)  
**Priority**: Medium - Improves user experience

**Deliverables**:
1. **Enhanced Session Management**
   - 60-minute rolling context with song history
   - Recently recommended exclusion logic
   - Session-based recommendation memory

2. **History Display**
   - "show recent songs" command implementation
   - Timestamp tracking for recommendations
   - Session summary functionality

3. **Context-Aware Filtering**
   - Exclude recently recommended unless requested
   - Session preference learning (tempo, keys, themes)
   - Smart follow-up suggestions

**Acceptance Criteria**:  
- [ ] Session tracks 20+ recommendations with timestamps
- [ ] Recently recommended songs excluded from new searches
- [ ] "show recent" displays last 10 recommendations
- [ ] Session context expires after 60 minutes inactivity

### Sprint 3: Database Analytics & Tools (2-3 days)
**Priority**: Low - Administrative efficiency  

**Deliverables**:
1. **Song Statistics**
   - Most/least recommended songs
   - Familiarity score distributions
   - Tag usage analytics

2. **Database Health Monitoring**
   - Missing metadata detection
   - Duplicate song identification  
   - Data quality reporting

3. **Management Tools**
   - Export/import functionality
   - Database backup/restore
   - Bulk tag operations

**Acceptance Criteria**:
- [ ] Analytics commands show usage patterns
- [ ] Health check identifies data gaps
- [ ] Export/import handles complete song database
- [ ] Tools support database maintenance workflows

---

## Technical Architecture

### Enhanced Data Models

```python
@dataclass  
class Song:
    title: str
    artist: str
    original_key: str
    boy_key: Optional[str] = None
    girl_key: Optional[str] = None
    bpm: int
    lyrical_tags: List[str] = field(default_factory=list)
    musical_tags: List[str] = field(default_factory=list)
    familiarity_score: int = 5
    url: str = ""
    last_recommended: Optional[datetime] = None

@dataclass
class UserSession:
    user_id: str
    recommendation_history: List[RecommendationEntry]
    last_activity: datetime
    session_preferences: Dict[str, Any]  # tempo, key preferences
    
@dataclass
class RecommendationEntry:
    song: Song
    timestamp: datetime
    context_keywords: List[str]
    rationale: str
```

### Core Engine Enhancements

```python
class EnhancedRecommendationEngine:
    def __init__(self):
        self.tempo_filter = TempoFilter()
        self.key_suggester = KeySuggester()
        self.musical_matcher = MusicalTagMatcher()
        self.session_manager = SessionManager()
    
    def recommend(self, query: str, user_id: str) -> List[Song]:
        # Parse tempo, vocal, and musical requirements
        context = self.parse_musical_context(query)
        session = self.session_manager.get_session(user_id)
        
        # Filter by musical criteria
        candidates = self.get_candidate_songs(query)
        candidates = self.tempo_filter.apply(candidates, context.tempo)
        candidates = self.exclude_recent(candidates, session)
        
        # Rank and suggest keys
        ranked = self.rank_by_relevance(candidates, context)
        for song in ranked:
            song.suggested_key = self.key_suggester.suggest_key(
                song, context.vocal_type
            )
            
        return ranked[:5]
```

---

## Risk Assessment & Mitigation

### Technical Risks

**Risk**: Database migration complexity with 69+ existing songs
**Mitigation**: Phased migration with rollback capability, extensive testing

**Risk**: Performance degradation with enhanced filtering 
**Mitigation**: Database indexing, query optimization, caching layer

**Risk**: Session state memory consumption
**Mitigation**: TTL-based cleanup, configurable session limits

### User Experience Risks  

**Risk**: Feature complexity overwhelming worship leaders
**Mitigation**: Progressive disclosure, simple defaults, extensive testing

**Risk**: Backward compatibility breaking existing workflows
**Mitigation**: Feature flags, gradual rollout, parallel testing

### Data Quality Risks

**Risk**: Inconsistent musical tag taxonomy
**Mitigation**: Standardized tag vocabulary, validation rules, bulk editing tools

---

## Success Metrics & Validation

### Quantitative Metrics
- **Feature Adoption**: 70% of queries use enhanced filtering within 30 days
- **Session Length**: Average session time increases 50% due to context
- **Recommendation Accuracy**: 85% positive feedback on tempo-filtered results
- **Database Quality**: 95% of songs have complete musical tag coverage

### Qualitative Validation
- **User Interviews**: Monthly sessions with 3-5 worship leaders
- **Usage Pattern Analysis**: Query complexity and follow-up behavior  
- **Error Analysis**: Common failure modes and edge cases
- **Ministry Impact**: Feedback on service preparation improvement

---

## Implementation Timeline

**Week 1**: Sprint 1A (Musical Intelligence)
- Days 1-2: BPM filtering and tempo parsing
- Days 3-4: Vocal key suggestions and musical tags

**Week 2**: Sprint 1B (Feedback & Database Management)  
- Days 1-2: Enhanced feedback processing
- Days 2-3: Database editing interface

**Week 3**: Sprint 2 (Session Intelligence)
- Days 1-2: Session management enhancement
- Day 3: History and context features

**Week 4**: Sprint 3 (Analytics & Tools)
- Days 1-2: Database analytics
- Day 3: Management tools and documentation

---

## Conclusion

This enhanced PRD maintains DavidBot's core value proposition while addressing critical worship leader needs. The phased approach ensures stable delivery of high-impact features without compromising existing functionality. Success depends on maintaining the ministry focus while building robust technical foundations for future growth.

The roadmap prioritizes musical intelligence and feedback loops as the foundation for all worship leader workflows, followed by session context to improve live service preparation, and finally administrative tools for ongoing database maintenance.

**Next Action**: Begin Sprint 1A with BPM filtering implementation and musical tags schema design.

---

*Document Version*: 1.0  
*Last Updated*: 2025-01-15  
*Next Review*: After Sprint 1A Completion  
*Stakeholders*: Worship Leaders, Music Directors, Development Team