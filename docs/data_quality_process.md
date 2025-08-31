# DavidBot Data Quality Process

## Overview

Accurate BPM and key data is **critical** for DavidBot's filtering and recommendation features. This document outlines the process for maintaining high-quality musical data.

## Critical Issue Discovered

**Problem**: "I Know That I Know" by The Belonging Co
- **Database**: 85 BPM ❌  
- **MultiTracks**: 142 BPM ✅
- **Impact**: 67% error causing complete filtering failure

## Data Quality Standards

### Required Accuracy
- **BPM**: ±2 BPM tolerance (must match authoritative source)
- **Key**: Exact match (A, Bb, B, C, C#, D, Eb, E, F, F#, G, Ab)
- **Source**: Must be verifiable against MultiTracks.com or equivalent

### Priority Verification Order
1. **Core Songs** (17 most requested) - verify first
2. **High Familiarity** (familiarity score >7) - verify second  
3. **Frequently Requested** (based on search logs) - ongoing
4. **New Additions** - verify before adding

## Verification Process

### 1. Manual Verification (Current)
```bash
python3 scripts/verify_core_songs.py --checklist
```

**Steps:**
1. Visit MultiTracks.com for each song
2. Record correct Key and BPM values
3. Add to `VERIFIED_DATA` in verification script
4. Run correction script to update database

### 2. Correction Application
```bash
python3 scripts/correct_known_errors.py --apply
```

### 3. Verification Report
```bash
python3 scripts/verify_core_songs.py
```

## Data Source Hierarchy

**Primary Sources** (in order of preference):
1. **MultiTracks.com** - Most reliable for contemporary worship
2. **Official Artist Recordings** - Original studio versions
3. **PraiseCharts** - Secondary verification
4. **CCLI** - License info but limited musical data

**Avoid:**
- YouTube covers (inconsistent)
- Lyric websites (often wrong musical data)
- Crowdsourced databases (unverified)

## Quality Checks

### Automated Validation
- BPM range: 40-200 (flag outliers)
- Key format: Standard notation only
- Missing data: Flag songs without BPM/key

### Manual Review Triggers
- User reports incorrect filtering results
- New song additions
- BPM/key changes in authoritative sources
- Seasonal review (quarterly)

## Known Data Issues

### Confirmed Errors
1. **I Know That I Know** - The Belonging Co: 85→142 BPM

### Patterns to Watch
- **Live vs Studio versions**: Often different BPM
- **Key transpositions**: MultiTracks may show preferred worship key
- **Song variations**: "(Live)", "(Acoustic)" versions

## Database Schema Enhancements

### Future Improvements
```sql
-- Add verification tracking
ALTER TABLE songs ADD COLUMN verified_date DATE;
ALTER TABLE songs ADD COLUMN verification_source VARCHAR(100);
ALTER TABLE songs ADD COLUMN confidence_level INTEGER; -- 1-5 scale

-- Add alternative versions
ALTER TABLE songs ADD COLUMN studio_bpm INTEGER;
ALTER TABLE songs ADD COLUMN live_bpm INTEGER;
```

## Workflow for New Songs

### Before Adding to Database
1. ✅ Verify on MultiTracks.com
2. ✅ Record source and date
3. ✅ Check for multiple versions (live/studio)
4. ✅ Add to verification tracking

### Template for New Entries
```python
{
    "title": "Song Title",
    "artist": "Artist Name", 
    "correct_key": "G",
    "correct_bpm": 128,
    "source": "MultiTracks.com verified 2025-08-31",
    "notes": "Studio version, live version is 132 BPM"
}
```

## Quality Metrics

### Target Goals
- **Core Songs**: 100% verification within 1 week
- **All Active Songs**: 95% verification within 1 month
- **New Additions**: 100% verified before activation
- **Error Rate**: <1% BPM/key errors in active database

### Monitoring
- Monthly verification report
- User feedback tracking
- Filter accuracy metrics
- Search result relevance scores

## Emergency Response

### When Data Errors are Found
1. **Immediate**: Add to known corrections list
2. **Within 24h**: Apply correction to database  
3. **Within 48h**: Verify related songs from same artist
4. **Weekly**: Review verification process

### Communication
- Log all corrections in commit messages
- Update verification scripts
- Document lessons learned
- Share findings with team

## Tools Created

1. **verify_core_songs.py** - Check core song data accuracy
2. **correct_known_errors.py** - Apply verified corrections
3. **verify_musical_data.py** - Automated web verification (future)

## Success Metrics

**Before Data Quality Process:**
- ❌ 1+ confirmed major errors (67% BPM error)
- ❌ Unknown accuracy of core songs
- ❌ No verification tracking

**After Data Quality Process:**
- ✅ All core songs verified against authoritative sources
- ✅ Systematic correction process
- ✅ Ongoing quality maintenance
- ✅ User confidence in filtering accuracy

---

**Next Action**: Complete manual verification of 16 core songs using generated checklist.