"""Repository pattern for database access."""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, text

from .models import Song, Lyrics, UserFeedback, SongUsage, ThemeMapping, MessageLog


class SongRepository:
    """Repository for song-related database operations."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_by_id(self, song_id: int) -> Optional[Song]:
        """Get song by ID."""
        return self.session.query(Song).filter(Song.song_id == song_id).first()
    
    def get_by_title_and_artist(self, title: str, artist: str) -> Optional[Song]:
        """Get song by title and artist."""
        return self.session.query(Song).filter(
            and_(Song.title == title, Song.artist == artist)
        ).first()
    
    def get_all_active(self) -> List[Song]:
        """Get all active songs."""
        return self.session.query(Song).filter(Song.is_active == True).all()
    
    def search_by_theme(self, theme: str, limit: int = 10) -> List[Song]:
        """Search songs by theme."""
        return self.session.query(Song).join(ThemeMapping).filter(
            and_(
                ThemeMapping.theme_name.ilike(f"%{theme}%"),
                Song.is_active == True
            )
        ).order_by(ThemeMapping.confidence_score.desc()).limit(limit).all()
    
    def search_by_text(self, query: str, limit: int = 10) -> List[Song]:
        """Search songs by title, artist, or lyrics content."""
        # Simple text search - will be enhanced with FTS5 later
        songs = self.session.query(Song).filter(
            and_(
                or_(
                    Song.title.ilike(f"%{query}%"),
                    Song.artist.ilike(f"%{query}%")
                ),
                Song.is_active == True
            )
        ).limit(limit).all()
        
        return songs
    
    def get_songs_with_lyrics(self, song_ids: List[int]) -> List[Song]:
        """Get songs with their lyrics loaded."""
        return self.session.query(Song).filter(
            Song.song_id.in_(song_ids)
        ).join(Lyrics).all()
    
    def create(self, song_data: Dict[str, Any]) -> Song:
        """Create a new song."""
        song = Song(**song_data)
        self.session.add(song)
        self.session.flush()  # Get the ID without committing
        return song
    
    def update(self, song_id: int, updates: Dict[str, Any]) -> Optional[Song]:
        """Update a song."""
        song = self.get_by_id(song_id)
        if song:
            for key, value in updates.items():
                setattr(song, key, value)
            self.session.flush()
        return song
    
    def delete(self, song_id: int) -> bool:
        """Soft delete a song by setting is_active = False."""
        song = self.get_by_id(song_id)
        if song:
            song.is_active = False
            self.session.flush()
            return True
        return False
    
    def get_popular_by_feedback(self, action: str = "thumbs_up", limit: int = 10) -> List[Song]:
        """Get songs ordered by positive feedback count."""
        from sqlalchemy import func
        
        return self.session.query(Song, func.count(UserFeedback.feedback_id).label('feedback_count')).join(
            UserFeedback
        ).filter(
            and_(
                UserFeedback.action == action,
                Song.is_active == True
            )
        ).group_by(Song.song_id).order_by(
            text('feedback_count DESC')
        ).limit(limit).all()


class LyricsRepository:
    """Repository for lyrics-related database operations."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_by_song_id(self, song_id: int) -> Optional[Lyrics]:
        """Get lyrics for a song."""
        return self.session.query(Lyrics).filter(Lyrics.song_id == song_id).first()
    
    def search_lyrics_content(self, query: str, limit: int = 10) -> List[Lyrics]:
        """Search lyrics by content across first_line, chorus, and bridge."""
        return self.session.query(Lyrics).filter(
            or_(
                Lyrics.first_line.ilike(f"%{query}%"),
                Lyrics.chorus.ilike(f"%{query}%"),
                Lyrics.bridge.ilike(f"%{query}%")
            )
        ).limit(limit).all()
    
    def create(self, lyrics_data: Dict[str, Any]) -> Lyrics:
        """Create lyrics for a song."""
        lyrics = Lyrics(**lyrics_data)
        self.session.add(lyrics)
        self.session.flush()
        return lyrics
    
    def update(self, song_id: int, updates: Dict[str, Any]) -> Optional[Lyrics]:
        """Update lyrics for a song."""
        lyrics = self.get_by_song_id(song_id)
        if lyrics:
            for key, value in updates.items():
                setattr(lyrics, key, value)
            self.session.flush()
        return lyrics
    
    def delete(self, song_id: int) -> bool:
        """Delete lyrics for a song."""
        lyrics = self.get_by_song_id(song_id)
        if lyrics:
            self.session.delete(lyrics)
            self.session.flush()
            return True
        return False


class FeedbackRepository:
    """Repository for feedback-related database operations."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create(self, feedback_data: Dict[str, Any]) -> UserFeedback:
        """Record user feedback."""
        feedback = UserFeedback(**feedback_data)
        self.session.add(feedback)
        self.session.flush()
        return feedback
    
    def get_by_user_and_song(self, user_id: str, song_id: int) -> List[UserFeedback]:
        """Get feedback for a specific user and song."""
        return self.session.query(UserFeedback).filter(
            and_(
                UserFeedback.user_id == user_id,
                UserFeedback.song_id == song_id
            )
        ).all()
    
    def get_feedback_stats(self, song_id: int) -> Dict[str, int]:
        """Get feedback statistics for a song."""
        from sqlalchemy import func
        
        results = self.session.query(
            UserFeedback.action,
            func.count(UserFeedback.feedback_id).label('count')
        ).filter(
            UserFeedback.song_id == song_id
        ).group_by(UserFeedback.action).all()
        
        return {action: count for action, count in results}
    
    def get_user_feedback_history(self, user_id: str, limit: int = 50) -> List[UserFeedback]:
        """Get user's feedback history."""
        return self.session.query(UserFeedback).filter(
            UserFeedback.user_id == user_id
        ).order_by(UserFeedback.timestamp.desc()).limit(limit).all()


class ThemeMappingRepository:
    """Repository for theme mapping operations."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_themes_for_song(self, song_id: int) -> List[ThemeMapping]:
        """Get all themes for a song."""
        return self.session.query(ThemeMapping).filter(
            ThemeMapping.song_id == song_id
        ).order_by(ThemeMapping.confidence_score.desc()).all()
    
    def get_songs_for_theme(self, theme_name: str, limit: int = 10) -> List[ThemeMapping]:
        """Get songs for a theme."""
        return self.session.query(ThemeMapping).filter(
            ThemeMapping.theme_name.ilike(f"%{theme_name}%")
        ).order_by(ThemeMapping.confidence_score.desc()).limit(limit).all()
    
    def create(self, mapping_data: Dict[str, Any]) -> ThemeMapping:
        """Create a theme mapping."""
        mapping = ThemeMapping(**mapping_data)
        self.session.add(mapping)
        self.session.flush()
        return mapping
    
    def update_confidence(self, song_id: int, theme_name: str, new_confidence: float) -> Optional[ThemeMapping]:
        """Update confidence score for a theme mapping."""
        mapping = self.session.query(ThemeMapping).filter(
            and_(
                ThemeMapping.song_id == song_id,
                ThemeMapping.theme_name == theme_name
            )
        ).first()
        
        if mapping:
            mapping.confidence_score = new_confidence
            self.session.flush()
        
        return mapping
    
    def delete(self, song_id: int, theme_name: str) -> bool:
        """Delete a theme mapping."""
        mapping = self.session.query(ThemeMapping).filter(
            and_(
                ThemeMapping.song_id == song_id,
                ThemeMapping.theme_name == theme_name
            )
        ).first()
        
        if mapping:
            self.session.delete(mapping)
            self.session.flush()
            return True
        
        return False
    
    def get_all_themes(self) -> List[str]:
        """Get list of all unique themes."""
        from sqlalchemy import func
        
        results = self.session.query(
            func.distinct(ThemeMapping.theme_name)
        ).all()
        
        return [result[0] for result in results]


class SongUsageRepository:
    """Repository for song usage tracking operations."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def record_usage(self, song_id: int, service_type: str = 'worship', notes: str = None) -> SongUsage:
        """Record that a song was used in service."""
        usage = SongUsage(
            song_id=song_id,
            service_type=service_type,
            notes=notes
        )
        self.session.add(usage)
        self.session.flush()
        return usage
    
    def get_usage_history(self, song_id: int, limit: int = 10) -> List[SongUsage]:
        """Get usage history for a specific song."""
        return self.session.query(SongUsage).filter(
            SongUsage.song_id == song_id
        ).order_by(SongUsage.used_date.desc()).limit(limit).all()
    
    def get_recent_usage(self, days: int = 90) -> List[SongUsage]:
        """Get all song usage in the last N days."""
        from datetime import datetime, timedelta
        cutoff_date = datetime.now() - timedelta(days=days)
        
        return self.session.query(SongUsage).filter(
            SongUsage.used_date >= cutoff_date
        ).order_by(SongUsage.used_date.desc()).all()
    
    def get_usage_count(self, song_id: int, days: int = 365) -> int:
        """Get number of times a song was used in the last N days."""
        from datetime import datetime, timedelta
        cutoff_date = datetime.now() - timedelta(days=days)
        
        return self.session.query(SongUsage).filter(
            and_(
                SongUsage.song_id == song_id,
                SongUsage.used_date >= cutoff_date
            )
        ).count()
    
    def calculate_familiarity_score(self, song_id: int) -> float:
        """
        Calculate familiarity score based on usage history.
        More recent usage weighted higher. Score decays over time.
        Returns score between 0.0 (never used) and 10.0 (very familiar).
        """
        from datetime import datetime, timedelta
        import math
        
        now = datetime.now()
        usage_records = self.session.query(SongUsage).filter(
            SongUsage.song_id == song_id
        ).order_by(SongUsage.used_date.desc()).limit(20).all()
        
        if not usage_records:
            return 0.0
        
        total_score = 0.0
        
        for usage in usage_records:
            # Calculate days since usage
            days_ago = (now - usage.used_date).days
            
            # Exponential decay: recent usage worth more
            # Base score of 1.0, decays by half every 60 days
            decay_factor = math.exp(-days_ago / 86.4)  # ~60 day half-life
            score_contribution = 1.0 * decay_factor
            
            total_score += score_contribution
        
        # Cap at 10.0 and round to 1 decimal place
        return min(round(total_score, 1), 10.0)
    
    def get_most_familiar_songs(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get songs with highest familiarity scores."""
        # Get all songs with their usage
        songs_with_scores = []
        
        songs = self.session.query(Song).filter(Song.is_active == True).all()
        for song in songs:
            score = self.calculate_familiarity_score(song.song_id)
            if score > 0:  # Only include songs that have been used
                songs_with_scores.append({
                    'song': song,
                    'familiarity_score': score
                })
        
        # Sort by familiarity score descending
        songs_with_scores.sort(key=lambda x: x['familiarity_score'], reverse=True)
        
        return songs_with_scores[:limit]
    
    def set_baseline_familiarity(self, song_id: int, baseline_score: float) -> None:
        """
        Set a baseline familiarity score by creating historical usage records.
        This simulates past usage to establish familiarity for popular songs.
        """
        from datetime import datetime, timedelta
        import math
        
        if not (0.0 <= baseline_score <= 10.0):
            raise ValueError("Baseline score must be between 0.0 and 10.0")
        
        if baseline_score == 0.0:
            return  # No usage records needed
        
        # Calculate how many usage records we need to create to achieve target score
        # Using reverse calculation from familiarity scoring algorithm
        # Target score = sum of (1.0 * exp(-days_ago / 86.4)) for each usage
        
        # For simplicity, we'll create usage records at strategic intervals
        # to achieve the desired baseline score
        now = datetime.now()
        usage_records_needed = []
        
        if baseline_score <= 2.0:
            # 1-2 recent uses
            usage_records_needed = [7, 30]  # 1 week ago, 1 month ago
        elif baseline_score <= 4.0:
            # 3-4 moderate uses
            usage_records_needed = [3, 14, 45, 75]  # Recent and some older
        elif baseline_score <= 6.0:
            # 4-6 regular uses
            usage_records_needed = [2, 7, 21, 35, 60, 90]
        elif baseline_score <= 8.0:
            # 6-8 frequent uses
            usage_records_needed = [1, 5, 14, 28, 42, 60, 80, 120]
        else:
            # 8+ very frequent uses (mega popular songs)
            usage_records_needed = [1, 3, 7, 14, 21, 35, 49, 70, 90, 120, 150]
        
        # Create the usage records
        for days_ago in usage_records_needed:
            usage_date = now - timedelta(days=days_ago)
            
            # Check if we already have a usage record near this date
            existing = self.session.query(SongUsage).filter(
                and_(
                    SongUsage.song_id == song_id,
                    SongUsage.used_date >= usage_date - timedelta(days=1),
                    SongUsage.used_date <= usage_date + timedelta(days=1)
                )
            ).first()
            
            if not existing:
                usage = SongUsage(
                    song_id=song_id,
                    used_date=usage_date,
                    service_type='worship',
                    notes=f'baseline_familiarity_{baseline_score}'
                )
                self.session.add(usage)
        
        self.session.flush()
        
        # Verify the achieved score
        actual_score = self.calculate_familiarity_score(song_id)
        print(f"Set baseline familiarity: target={baseline_score}, actual={actual_score}")
    
    def set_popular_songs_baseline(self) -> None:
        """Set baseline familiarity for well-known popular worship songs."""
        # Define popular songs and their estimated familiarity scores
        # Based on general knowledge of popular contemporary worship songs
        popular_songs = {
            # Mega hits (9-10 score) - songs virtually every church knows
            ("What A Beautiful Name", "Hillsong Worship"): 9.5,
            ("Goodness Of God", "Bethel Music"): 9.0,
            ("Way Maker", "Sinach"): 9.5,  # Not in our DB but example
            
            # Very popular (7-8 score) - widely known songs
            ("Holy Forever", "Chris Tomlin"): 8.0,
            ("Firm Foundation (He Won't)", "Maverick City Music"): 7.5,
            ("Praise", "Elevation Worship"): 7.0,
            ("Forever YHWH", "Elevation Worship"): 7.5,
            
            # Popular (5-6 score) - known by many churches
            ("Champion", "Bethel Music"): 6.0,
            ("Build My Life", "Pat Barrett"): 6.5,
            ("Great Are You Lord", "All Sons & Daughters"): 6.0,
            ("See A Victory", "Elevation Worship"): 5.5,
            
            # Moderately known (3-4 score) - growing in popularity
            ("House Of Miracles", "Brandon Lake"): 4.0,
            ("Same God", "Elevation Worship"): 4.5,
            ("The Joy", "Maverick City Music"): 3.5,
            ("I've Witnessed It", "Maverick City Music"): 3.0,
            
            # Newer/emerging (1-2 score) - some familiarity
            ("Worthy Of It All", "CeCe Winans"): 2.5,
            ("At The Altar", "Elevation Rhythm"): 2.0,
            ("Come Alive", "Planetshakers"): 2.0,
        }
        
        updated_count = 0
        
        for (title, artist), baseline_score in popular_songs.items():
            # Find the song in database
            song = self.session.query(Song).filter(
                and_(
                    Song.title.ilike(f"%{title}%"),
                    Song.artist.ilike(f"%{artist}%"),
                    Song.is_active == True
                )
            ).first()
            
            if song:
                # Only set baseline if song has no existing usage history
                existing_usage = self.session.query(SongUsage).filter(
                    SongUsage.song_id == song.song_id
                ).count()
                
                if existing_usage == 0:
                    self.set_baseline_familiarity(song.song_id, baseline_score)
                    updated_count += 1
                    print(f"✅ Set baseline for: {song.title} by {song.artist} (score: {baseline_score})")
                else:
                    print(f"⚠️ Skipped {song.title} - already has usage history ({existing_usage} records)")
            else:
                print(f"❌ Not found: {title} by {artist}")
        
        self.session.commit()
        print(f"\n🎵 Updated baseline familiarity for {updated_count} songs")


class MessageLogRepository:
    """Repository for message logging operations."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create(self, log_data: Dict[str, Any]) -> MessageLog:
        """Create a message log entry."""
        message_log = MessageLog(**log_data)
        self.session.add(message_log)
        self.session.flush()
        return message_log
    
    def get_user_message_history(self, user_id: str, limit: int = 50) -> List[MessageLog]:
        """Get message history for a specific user."""
        return self.session.query(MessageLog).filter(
            MessageLog.user_id == user_id
        ).order_by(MessageLog.timestamp.desc()).limit(limit).all()
    
    def get_message_type_stats(self, days: int = 30) -> Dict[str, int]:
        """Get message type statistics for the last N days."""
        from datetime import datetime, timedelta
        from sqlalchemy import func
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        results = self.session.query(
            MessageLog.message_type,
            func.count(MessageLog.log_id).label('count')
        ).filter(
            MessageLog.timestamp >= cutoff_date
        ).group_by(MessageLog.message_type).all()
        
        return {msg_type: count for msg_type, count in results}
    
    def get_active_users_count(self, days: int = 30) -> int:
        """Get count of unique active users in the last N days."""
        from datetime import datetime, timedelta
        from sqlalchemy import func
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        result = self.session.query(
            func.count(func.distinct(MessageLog.user_id))
        ).filter(
            MessageLog.timestamp >= cutoff_date
        ).scalar()
        
        return result or 0
    
    def get_recent_activity(self, limit: int = 100) -> List[MessageLog]:
        """Get recent bot activity across all users."""
        return self.session.query(MessageLog).order_by(
            MessageLog.timestamp.desc()
        ).limit(limit).all()