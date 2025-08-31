# Complete Song Verification Guide

## Quick Start - Verify All 69 Songs

**Goal**: Verify BPM and key data for all songs against MultiTracks.com

**Time Estimate**: 2-3 hours for complete verification

## Step 1: Generate Verification Tools

```bash
python3 scripts/verify_all_songs.py --csv --urls --summary
```

**This creates**:
- `song_verification_template.csv` - Spreadsheet for data entry
- Batch URLs organized for efficient verification
- Database summary showing current distribution

## Step 2: Systematic Verification Process

### Option A: Batch Verification (Recommended)
1. **Open 10 URLs at once** (use the batch URLs from Step 1)
2. **Use split screen**: CSV on one side, MultiTracks tabs on other
3. **Work in batches**: Complete 10 songs, then next batch
4. **Fill CSV columns**: `verified_key`, `verified_bpm`, `matches_db`

### Option B: Individual Verification
1. Open `song_verification_template.csv` in Excel/Google Sheets
2. For each song, visit the MultiTracks search URL
3. Record verified Key and BPM
4. Mark if current data matches (TRUE/FALSE)

## Step 3: Apply Corrections

### Preview Changes
```bash
python3 scripts/apply_verification_results.py
```

### Apply to Database
```bash
python3 scripts/apply_verification_results.py --apply
```

### Generate Report
```bash
python3 scripts/apply_verification_results.py --report
```

## Database Summary (Current State)

**Total Songs**: 69
- **Slow (≤85 BPM)**: 45 songs (65.2%)
- **Moderate (86-120 BPM)**: 5 songs (7.2%)  
- **Fast (≥121 BPM)**: 18 songs (26.1%)
- **Missing BPM**: 1 song (1.4%)

**Key Distribution**:
- G: 12 songs, C: 11 songs, A: 9 songs, D: 8 songs, E: 8 songs
- Bb: 7 songs, B: 4 songs, Eb: 3 songs, F: 3 songs
- F#: 2 songs, Db: 2 songs

## Verification Tips

### MultiTracks.com Navigation
- **Search**: Use song title first, then add artist if needed
- **Look for**: "Key:" and "BPM:" in song details
- **Prefer**: Original master tracks over covers
- **Note**: Some songs have multiple versions (live vs studio)

### Common Issues
- **No exact match**: Try shortened title or different version
- **Multiple versions**: Note in CSV which version you verified
- **Missing data**: Mark as "VERIFY NEEDED" in notes column
- **Different arrangements**: Use the most common worship arrangement

### CSV Data Entry
- **verified_key**: Use standard notation (A, Bb, C, C#, D, Eb, E, F, F#, G, Ab)
- **verified_bpm**: Whole numbers only
- **matches_db**: TRUE if current data is correct, FALSE if needs updating
- **notes**: Any issues or version differences

## Quality Checks

### Before Applying Changes
- [ ] All critical songs verified (top 20 most requested)
- [ ] Key format is consistent (A, Bb, C#, etc.)
- [ ] BPM values are reasonable (40-200 range)
- [ ] "matches_db" column is filled for all verified songs

### After Applying Changes
- [ ] Run verification report to confirm changes
- [ ] Test filtering with corrected BPM ranges
- [ ] Verify search results include corrected songs

## Known Issues to Watch For

1. **Live vs Studio versions** - Often different BPM
2. **Key transpositions** - MultiTracks may show worship-friendly keys
3. **Arrangement differences** - Acoustic vs full band versions
4. **Missing songs** - Some may not be on MultiTracks

## Success Metrics

**Target Goals**:
- ✅ 100% of active songs verified within 1 week
- ✅ <1% error rate in BPM/key data
- ✅ All core worship songs (top 20) have perfect accuracy
- ✅ Filtering works correctly for slow/fast requests

**Before Verification**:
- ❌ 1+ confirmed major BPM errors (67% error on "I Know That I Know")
- ❌ Unknown accuracy across entire database
- ❌ User filtering issues

**After Verification**:
- ✅ All songs verified against authoritative source
- ✅ Systematic correction process in place
- ✅ Database accuracy suitable for production use

## Emergency Fixes

**If you find a critical error during verification**:
1. Note it in the CSV immediately
2. For urgent fixes, use the single-song correction script:
   ```bash
   python3 scripts/correct_known_errors.py --apply
   ```

## Next Steps After Verification

1. **Test the improvements** with real queries
2. **Monitor user feedback** for remaining issues  
3. **Set up quarterly reviews** to catch new errors
4. **Document verification dates** for future reference
5. **Create process for new song additions**

---

**Start here**: `python3 scripts/verify_all_songs.py --csv --urls --summary`