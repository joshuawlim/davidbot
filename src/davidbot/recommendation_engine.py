"""Recommendation engine with hardcoded song dataset."""

from typing import List, Optional
from .models import Song, SearchResult


class RecommendationEngine:
    """Engine for finding song recommendations from hardcoded dataset."""
    
    def __init__(self):
        """Initialize with hardcoded song dataset."""
        self.songs = self._load_hardcoded_songs()
    
    def _load_hardcoded_songs(self) -> List[Song]:
        """Load hardcoded song dataset."""
        return [
            # Surrender theme songs
            Song("I Surrender All", "Judson W. Van DeVenter", "G", 72, ["altar-call"], 
                 "https://example.com/surrender-all", ["surrender"]),
            Song("All to Jesus I Surrender", "Judson W. Van DeVenter", "F", 78, ["surrender", "commitment"], 
                 "https://example.com/all-to-jesus", ["surrender"]),
            Song("Nothing but the Blood", "Robert Lowry", "A", 86, ["blood", "cleansing"], 
                 "https://example.com/nothing-but-blood", ["surrender"]),
            Song("Take My Life and Let It Be", "Frances R. Havergal", "D", 82, ["consecration"], 
                 "https://example.com/take-my-life", ["surrender"]),
            Song("Have Thine Own Way", "Adelaide A. Pollard", "Bb", 76, ["surrender", "will"], 
                 "https://example.com/have-thine-own-way", ["surrender"]),
            Song("More Love to Thee", "Elizabeth P. Prentiss", "G", 80, ["love", "surrender"], 
                 "https://example.com/more-love-to-thee", ["surrender"]),
                 
            # Worship theme songs  
            Song("How Great Thou Art", "Carl Boberg", "G", 90, ["praise", "majesty"], 
                 "https://example.com/how-great-thou-art", ["worship"]),
            Song("Holy, Holy, Holy", "Reginald Heber", "Eb", 88, ["holiness", "trinity"], 
                 "https://example.com/holy-holy-holy", ["worship"]),
            Song("Amazing Grace", "John Newton", "D", 84, ["grace", "salvation"], 
                 "https://example.com/amazing-grace", ["worship"]),
            Song("Come Thou Fount", "Robert Robinson", "A", 95, ["blessing", "streams"], 
                 "https://example.com/come-thou-fount", ["worship"]),
            Song("Be Thou My Vision", "Eleanor H. Hull", "F", 78, ["vision", "heart"], 
                 "https://example.com/be-thou-my-vision", ["worship"]),
            Song("Crown Him with Many Crowns", "Matthew Bridges", "D", 96, ["crowns", "king"], 
                 "https://example.com/crown-him", ["worship"]),
            Song("Praise to the Lord, the Almighty", "Joachim Neander", "G", 100, ["praise", "almighty"], 
                 "https://example.com/praise-to-lord", ["worship"]),
            Song("All Hail the Power of Jesus' Name", "Edward Perronet", "F", 88, ["power", "name"], 
                 "https://example.com/all-hail-power", ["worship"]),
            Song("Immortal, Invisible", "Walter Chalmers Smith", "Bb", 85, ["immortal", "invisible"], 
                 "https://example.com/immortal-invisible", ["worship"]),
                 
            # Grace theme songs
            Song("Grace Greater Than Our Sin", "Julia H. Johnston", "G", 86, ["grace", "forgiveness"], 
                 "https://example.com/grace-greater", ["grace"]),
            Song("Marvelous Grace of Our Loving Lord", "Julia H. Johnston", "C", 82, ["grace", "love"], 
                 "https://example.com/marvelous-grace", ["grace"]),
            Song("'Tis So Sweet to Trust in Jesus", "Louisa M. R. Stead", "F", 75, ["trust", "grace"], 
                 "https://example.com/tis-so-sweet", ["grace"]),
                 
            # Hope theme songs
            Song("Blessed Hope", "Fanny J. Crosby", "F", 82, ["hope", "future"], 
                 "https://example.com/blessed-hope", ["hope"]),
            Song("My Hope Is Built", "Edward Mote", "G", 90, ["hope", "foundation"], 
                 "https://example.com/my-hope-is-built", ["hope"]),
            Song("We Have an Anchor", "Priscilla J. Owens", "Bb", 78, ["hope", "anchor"], 
                 "https://example.com/we-have-anchor", ["hope"]),
            Song("Hope of the World", "Georgia Harkness", "C", 88, ["hope", "world"], 
                 "https://example.com/hope-of-world", ["hope"]),
            Song("Living Hope", "Phil Wickham", "D", 94, ["hope", "living"], 
                 "https://example.com/living-hope", ["hope"]),
            Song("Resurrection Hope", "Traditional", "G", 85, ["hope", "resurrection"], 
                 "https://example.com/resurrection-hope", ["hope"]),
                 
            # Faith theme songs
            Song("Faith of Our Fathers", "Frederick W. Faber", "G", 86, ["faith", "fathers"], 
                 "https://example.com/faith-of-fathers", ["faith"]),
            Song("My Faith Looks Up to Thee", "Ray Palmer", "F", 80, ["faith", "trust"], 
                 "https://example.com/my-faith-looks-up", ["faith"]),
            Song("Only Trust Him", "John H. Stockton", "D", 92, ["faith", "trust"], 
                 "https://example.com/only-trust-him", ["faith"]),
            Song("Faith Is the Victory", "John H. Yates", "C", 96, ["faith", "victory"], 
                 "https://example.com/faith-is-victory", ["faith"]),
            Song("Have Faith in God", "B. B. McKinney", "F", 84, ["faith", "god"], 
                 "https://example.com/have-faith-in-god", ["faith"]),
            Song("Walk by Faith", "Keith Getty", "G", 88, ["faith", "walk"], 
                 "https://example.com/walk-by-faith", ["faith"]),
                 
            # Peace theme songs  
            Song("It Is Well with My Soul", "Horatio G. Spafford", "C", 76, ["peace", "comfort"], 
                 "https://example.com/it-is-well", ["peace"]),
            Song("Peace Like a River", "Traditional", "G", 84, ["peace", "flowing"], 
                 "https://example.com/peace-like-river", ["peace"]),
            Song("Blessed Assurance", "Fanny J. Crosby", "D", 88, ["assurance", "peace"], 
                 "https://example.com/blessed-assurance", ["peace"]),
            Song("Perfect Peace", "Laura S. Copenhaver", "F", 80, ["peace", "perfect"], 
                 "https://example.com/perfect-peace", ["peace"]),
            Song("Peace, Perfect Peace", "Edward H. Bickersteth", "Bb", 82, ["peace", "perfect"], 
                 "https://example.com/peace-perfect-peace", ["peace"]),
            Song("Like a River Glorious", "Frances R. Havergal", "C", 86, ["peace", "river"], 
                 "https://example.com/like-river-glorious", ["peace"]),
                 
            # Love theme songs
            Song("Love Divine, All Loves Excelling", "Charles Wesley", "F", 84, ["love", "divine"], 
                 "https://example.com/love-divine", ["love"]),
            Song("The Love of God", "Frederick M. Lehman", "G", 78, ["love", "eternal"], 
                 "https://example.com/love-of-god", ["love"]),
            Song("Jesus Loves Me", "Anna B. Warner", "C", 88, ["love", "children"], 
                 "https://example.com/jesus-loves-me", ["love"]),
            Song("O Love That Will Not Let Me Go", "George Matheson", "D", 85, ["love", "unfailing"], 
                 "https://example.com/o-love-that-will-not", ["love"]),
            Song("Love Lifted Me", "James Rowe", "G", 90, ["love", "lifted"], 
                 "https://example.com/love-lifted-me", ["love"]),
            Song("Great Is Thy Faithfulness", "Thomas O. Chisholm", "F", 82, ["love", "faithfulness"], 
                 "https://example.com/great-is-thy-faithfulness", ["love"]),
                 
            # Joy theme songs
            Song("Joy to the World", "Isaac Watts", "D", 120, ["joy", "celebration"], 
                 "https://example.com/joy-to-world", ["joy"]),
            Song("Joyful, Joyful We Adore Thee", "Henry van Dyke", "G", 110, ["joy", "adoration"], 
                 "https://example.com/joyful-joyful", ["joy"]),
            Song("This Joy That I Have", "Shirley Caesar", "C", 96, ["joy", "inner"], 
                 "https://example.com/this-joy", ["joy"]),
                 
            # Love theme songs
            Song("Love Divine, All Loves Excelling", "Charles Wesley", "F", 84, ["love", "divine"], 
                 "https://example.com/love-divine", ["love"]),
            Song("The Love of God", "Frederick M. Lehman", "G", 78, ["love", "eternal"], 
                 "https://example.com/love-of-god", ["love"]),
            Song("Jesus Loves Me", "Anna B. Warner", "C", 88, ["love", "children"], 
                 "https://example.com/jesus-loves-me", ["love"]),
        ]
    
    def search(self, query: str, excluded_songs: Optional[List[str]] = None) -> Optional[SearchResult]:
        """Search for songs matching the query."""
        if excluded_songs is None:
            excluded_songs = []
            
        # Extract search term from query
        query_lower = query.lower()
        
        # Find matching term
        matched_term = None
        for song in self.songs:
            for search_term in song.search_terms:
                if search_term in query_lower:
                    matched_term = search_term
                    break
            if matched_term:
                break
        
        if not matched_term:
            return None
            
        # Find all songs matching this term, excluding already returned ones
        matching_songs = []
        for song in self.songs:
            if (matched_term in song.search_terms and 
                song.title not in excluded_songs):
                matching_songs.append(song)
        
        if not matching_songs:
            return None
            
        # Return up to 3 songs
        selected_songs = matching_songs[:3]
        
        return SearchResult(
            songs=selected_songs,
            matched_term=matched_term,
            theme=matched_term
        )