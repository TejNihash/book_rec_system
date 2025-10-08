import ast
import pandas as pd
import gradio as gr
import random
from typing import List, Dict, Tuple, Optional

# =============================================================================
# CONFIGURATION CONSTANTS
# =============================================================================
class Config:
    """Configuration constants for the application"""
    DATA_FILE = "data_mini_books.csv"
    BOOKS_PER_LOAD = 12
    PLACEHOLDER_IMAGE = "https://via.placeholder.com/150x220/444/fff?text=No+Image"
    DEFAULT_RATING_RANGE = (3.5, 4.8)
    DEFAULT_YEAR_RANGE = (1990, 2023)
    DEFAULT_PAGES_RANGE = (150, 600)

# =============================================================================
# DATA MANAGEMENT
# =============================================================================
class DataManager:
    """Handles data loading and preprocessing"""
    
    @staticmethod
    def load_and_prepare_data() -> pd.DataFrame:
        """Load and prepare the book dataset"""
        try:
            df = pd.read_csv(Config.DATA_FILE)
        except FileNotFoundError:
            # Create sample data if file doesn't exist
            print("⚠️ Data file not found, creating sample data...")
            return DataManager._create_sample_data()
        
        # Ensure ID column exists
        if "id" not in df.columns:
            df["id"] = df.index.astype(str)
        
        # Parse list columns
        df = DataManager._parse_list_columns(df)
        
        # Fill missing columns with realistic defaults
        df = DataManager._fill_missing_columns(df)
        
        return df
    
    @staticmethod
    def _create_sample_data() -> pd.DataFrame:
        """Create sample data for testing/demo purposes"""
        sample_data = {
            'id': [str(i) for i in range(24)],
            'title': [f'Sample Book {i+1}' for i in range(24)],
            'authors': [[f'Author {chr(65 + (i % 5))}'] for i in range(24)],
            'genres': [[['Fiction', 'Fantasy'], ['Non-Fiction', 'Science'], ['Mystery', 'Thriller']][i % 3] for i in range(24)],
            'image_url': [f'https://via.placeholder.com/150x220/444/fff?text=Book+{i+1}' for i in range(24)],
            'description': ['This is a sample book description for demonstration purposes in the Book Discovery Hub application.' for _ in range(24)],
            'rating': [round(random.uniform(3.5, 4.8), 1) for _ in range(24)],
            'year': [random.randint(1990, 2023) for _ in range(24)],
            'pages': [random.randint(150, 600) for _ in range(24)]
        }
        return pd.DataFrame(sample_data)
    
    @staticmethod
    def _parse_list_columns(df: pd.DataFrame) -> pd.DataFrame:
        """Parse string representations of lists into actual lists"""
        for column in ["authors", "genres"]:
            if column in df.columns:
                df[column] = df[column].apply(
                    lambda x: ast.literal_eval(x) if isinstance(x, str) else x or []
                )
        return df
    
    @staticmethod
    def _fill_missing_columns(df: pd.DataFrame) -> pd.DataFrame:
        """Fill missing columns with realistic default values"""
        n_rows = len(df)
        
        defaults = {
            "rating": [random.uniform(*Config.DEFAULT_RATING_RANGE) for _ in range(n_rows)],
            "year": [random.randint(*Config.DEFAULT_YEAR_RANGE) for _ in range(n_rows)],
            "pages": [random.randint(*Config.DEFAULT_PAGES_RANGE) for _ in range(n_rows)],
            "description": ["No description available" for _ in range(n_rows)]
        }
        
        for column, default_values in defaults.items():
            if column not in df.columns:
                df[column] = default_values
                
        return df

# =============================================================================
# FAVORITES MANAGEMENT
# =============================================================================
class FavoritesManager:
    """Manages favorite books functionality"""
    
    def __init__(self):
        self.favorites: List[Dict] = []
    
    def add_to_favorites(self, book_data: Dict) -> Tuple[bool, str]:
        """Add a book to favorites"""
        if not any(fav['id'] == book_data['id'] for fav in self.favorites):
            self.favorites.append(book_data.copy())  # Use copy to avoid reference issues
            print(f"✅ Added '{book_data['title']}' to favorites")
            return True, f"❤️ Added '{book_data['title']}' to favorites!"
        return False, "⚠️ Already in favorites!"
    
    def remove_from_favorites(self, book_id: str) -> Tuple[bool, str]:
        """Remove a book from favorites"""
        for fav in self.favorites:
            if fav['id'] == book_id:
                book_title = fav['title']
                self.favorites = [fav for fav in self.favorites if fav['id'] != book_id]
                print(f"❌ Removed '{book_title}' from favorites")
                return True, f"💔 Removed '{book_title}' from favorites!"
        return False, "❌ Book not found in favorites!"
    
    def toggle_favorite(self, book_data: Dict) -> Tuple[bool, str]:
        """Toggle favorite status for a book"""
        book_id = book_data['id']
        if any(fav['id'] == book_id for fav in self.favorites):
            return self.remove_from_favorites(book_id)
        else:
            return self.add_to_favorites(book_data)
    
    def is_favorite(self, book_id: str) -> bool:
        """Check if a book is in favorites"""
        return any(fav['id'] == book_id for fav in self.favorites)
    
    def get_favorites_dataframe(self) -> pd.DataFrame:
        """Get favorites as DataFrame"""
        return pd.DataFrame(self.favorites) if self.favorites else pd.DataFrame()

# =============================================================================
# UI COMPONENTS
# =============================================================================
class UIComponents:
    """Generates HTML components for the UI"""
    
    @staticmethod
    def create_book_card_html(book: Dict, is_favorite: bool = False) -> str:
        """Create HTML for a book card"""
        rating = book.get("rating", 0)
        stars = UIComponents._generate_stars(rating)
        favorite_indicator = "❤️ " if is_favorite else ""
        
        # Escape quotes in text to prevent HTML issues
        title = book['title'].replace('"', '&quot;')
        authors = ', '.join(book['authors']).replace('"', '&quot;')
        genres = ', '.join(book['genres']).replace('"', '&quot;')
        description = book.get('description', 'No description').replace('"', '&quot;')
        
        return f"""
        <div class='book-card' 
             data-id='{book["id"]}' 
             data-title="{title}" 
             data-authors="{authors}" 
             data-genres="{genres}" 
             data-img="{book['image_url']}" 
             data-desc="{description}"
             data-rating="{rating}" 
             data-year="{book.get('year', 'N/A')}" 
             data-pages="{book.get('pages', 'N/A')}">
            
            <div class='book-image-container'>
                <img src="{book['image_url']}" 
                     onerror="this.src='{Config.PLACEHOLDER_IMAGE}'">
                <div class='book-badge'>{book.get('year', 'N/A')}</div>
            </div>
            
            <div class='book-info'>
                <div class='book-title' title="{title}">
                    {favorite_indicator}{book['title']}
                </div>
                <div class='book-authors'>by {', '.join(book['authors'])}</div>
                <div class='book-rating'>{stars} ({rating:.1f})</div>
                <div class='book-meta'>
                    <span class='book-pages'>{book.get('pages', 'N/A')} pages</span>
                    <span class='book-genres'>
                        {', '.join(book['genres'][:2])}
                        {'...' if len(book['genres']) > 2 else ''}
                    </span>
                </div>
            </div>
        </div>
        """
    
    @staticmethod
    def _generate_stars(rating: float) -> str:
        """Generate star rating HTML"""
        full_stars = int(rating)
        half_star = rating % 1 >= 0.5
        empty_stars = 5 - full_stars - (1 if half_star else 0)
        
        stars = "⭐" * full_stars
        if half_star:
            stars += "⭐"
            empty_stars -= 1
        stars += "☆" * empty_stars
        
        return stars
    
    @staticmethod
    def build_books_grid_html(books_df: pd.DataFrame, is_favorites_section: bool = False, favorites_manager: Optional['FavoritesManager'] = None) -> str:
        """Build HTML grid for books"""
        if books_df.empty:
            return UIComponents._get_empty_state_message(is_favorites_section)
        
        cards_html = []
        for _, book in books_df.iterrows():
            book_dict = book.to_dict()
            is_favorite = favorites_manager.is_favorite(book_dict['id']) if favorites_manager else False
            cards_html.append(UIComponents.create_book_card_html(book_dict, is_favorite))
        
        return f"<div class='books-grid'>{''.join(cards_html)}</div>"
    
    @staticmethod
    def _get_empty_state_message(is_favorites_section: bool) -> str:
        """Get message for empty state"""
        if is_favorites_section:
            return """
            <div style='text-align: center; padding: 40px; color: #888; font-size: 16px;'>
                No favorite books yet. Click the favorite button in book details to add some!
            </div>
            """
        return "<div style='text-align: center; padding: 40px; color: #888;'>No books found</div>"
    
    @staticmethod
    def create_favorites_header(favorites_count: int) -> str:
        """Create favorites section header"""
        return f"""
        <div style="display: flex; align-items: center; margin-bottom: 12px;">
            <h2 style="margin: 0; color: #fff; border-left: 4px solid #ed8936; padding-left: 10px;">
                ⭐ Favorites
            </h2>
            <div class="favorites-count">
                {favorites_count} book{'s' if favorites_count != 1 else ''}
            </div>
        </div>
        """

# =============================================================================
# APPLICATION LOGIC
# =============================================================================
class BookDiscoveryApp:
    """Main application class"""
    
    def __init__(self):
        self.df = DataManager.load_and_prepare_data()
        self.favorites_manager = FavoritesManager()
        self.ui_components = UIComponents()
    
    def load_more_books(self, loaded_books: pd.DataFrame, display_books: pd.DataFrame, 
                       page_idx: int, is_favorites: bool = False) -> Tuple[pd.DataFrame, dict, dict, int]:
        """Load more books for pagination"""
        start = page_idx * Config.BOOKS_PER_LOAD
        end = start + Config.BOOKS_PER_LOAD
        new_books = loaded_books.iloc[start:end]
        
        if new_books.empty:
            html = self.ui_components.build_books_grid_html(
                display_books, is_favorites, self.favorites_manager
            )
            return display_books, gr.update(value=html), gr.update(visible=False), page_idx
        
        combined = pd.concat([display_books, new_books], ignore_index=True)
        html = self.ui_components.build_books_grid_html(
            combined, is_favorites, self.favorites_manager
        )
        return combined, gr.update(value=html), gr.update(visible=True), page_idx + 1
    
    def shuffle_random_books(self, loaded_books: pd.DataFrame, display_books: pd.DataFrame) -> Tuple:
        """Shuffle and display random books"""
        shuffled = loaded_books.sample(frac=1).reset_index(drop=True)
        initial_books = shuffled.iloc[:Config.BOOKS_PER_LOAD]
        html = self.ui_components.build_books_grid_html(
            initial_books, False, self.favorites_manager
        )
        return shuffled, initial_books, html, 1
    
    def handle_favorite_click(self, book_index: int) -> Tuple:
        """Handle favorite button clicks"""
        if book_index >= len(self.df):
            return self._get_error_response("Book not found")
        
        book = self.df.iloc[book_index]
        success, message = self.favorites_manager.toggle_favorite(book.to_dict())
        
        # Update favorites display
        favorites_df = self.favorites_manager.get_favorites_dataframe()
        favorites_html = self.ui_components.build_books_grid_html(
            favorites_df, True, self.favorites_manager
        )
        load_more_visible = len(self.favorites_manager.favorites) > Config.BOOKS_PER_LOAD
        header_html = self.ui_components.create_favorites_header(len(self.favorites_manager.favorites))
        
        # Update button text
        is_fav = self.favorites_manager.is_favorite(book['id'])
        new_btn_text = self._get_favorite_button_text(book['title'], is_fav)
        
        # Create feedback
        feedback_html = self._create_feedback_html(message, success)
        
        return favorites_df, favorites_html, gr.update(visible=load_more_visible), header_html, gr.update(value=new_btn_text), feedback_html
    
    def _get_error_response(self, message: str) -> Tuple:
        """Create error response"""
        feedback_html = self._create_feedback_html(message, False)
        return (
            self.favorites_manager.get_favorites_dataframe(),
            gr.update(),
            gr.update(visible=False),
            self.ui_components.create_favorites_header(len(self.favorites_manager.favorites)),
            gr.update(),
            feedback_html
        )
    
    def _get_favorite_button_text(self, title: str, is_favorite: bool) -> str:
        """Generate favorite button text"""
        action = "💔" if is_favorite else "❤️"
        shortened_title = title[:15] + "..." if len(title) > 15 else title
        return f"{action} {shortened_title}"
    
    def _create_feedback_html(self, message: str, success: bool) -> str:
        """Create feedback toast HTML"""
        color = "#48bb78" if success else "#f56565"
        return f"""
        <div class="feedback-toast" style="background: {color}">
            {message}
        </div>
        """
    
    def initial_load(self, books_df: pd.DataFrame) -> Tuple[pd.DataFrame, str, int]:
        """Initial load of books"""
        initial_books = books_df.iloc[:Config.BOOKS_PER_LOAD]
        html = self.ui_components.build_books_grid_html(
            initial_books, False, self.favorites_manager
        )
        return initial_books, html, 1

# =============================================================================
# GRADIO INTERFACE
# =============================================================================
class GradioInterface:
    """Handles Gradio interface setup"""
    
    CSS = """
    /* Your existing CSS remains the same */
    .books-section { border:1px solid #555; border-radius:12px; padding:16px; height:500px; overflow-y:auto; margin-bottom:20px; background:#222; }
    .books-grid { display:grid; grid-template-columns:repeat(6,1fr); gap:16px; }
    .book-card { background:#333; border-radius:12px; padding:10px; box-shadow:0 3px 10px rgba(0,0,0,0.5); cursor:pointer; text-align:left; transition:all 0.3s ease; border:1px solid #555; height:100%; display:flex; flex-direction:column; color:#eee; }
    .book-card:hover { transform:translateY(-4px) scale(1.02); box-shadow:0 8px 20px rgba(0,0,0,0.7); border-color:#667eea; }
    .book-image-container { position:relative; margin-bottom:10px; }
    .book-card img { width:100%; height:180px; object-fit:cover; border-radius:8px; border:1px solid #666; }
    .book-badge { position:absolute; top:8px; right:8px; background:rgba(102,126,234,0.9); color:white; padding:2px 6px; border-radius:10px; font-size:10px; font-weight:bold;}
    .book-info { flex-grow:1; display:flex; flex-direction:column; gap:4px; }
    .book-title { font-size:13px; font-weight:700; color:#fff; line-height:1.3; overflow:hidden; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; margin-bottom:2px; }
    .book-authors { font-size:11px; color:#88c; font-weight:600; overflow:hidden; display:-webkit-box; -webkit-line-clamp:1; -webkit-box-orient:vertical; margin-bottom:3px;}
    .book-rating { font-size:10px; color:#ffa500; margin-bottom:4px; }
    .book-meta { display:flex; flex-direction:column; gap:2px; margin-top:auto; font-size:10px; color:#ccc; }

    .load-more-btn { background:linear-gradient(135deg,#667eea 0%,#764ba2 100%); color:white; border:none; padding:10px 25px; border-radius:20px; font-weight:600; cursor:pointer; transition:all 0.3s ease; box-shadow:0 4px 12px rgba(102,126,234,0.3); font-size:12px; }
    .load-more-btn:hover { transform:translateY(-2px); box-shadow:0 6px 16px rgba(102,126,234,0.4); }

    .favorite-btn { background:linear-gradient(135deg,#ed8936 0%,#dd6b20 100%); color:white; border:none; padding:12px 24px; border-radius:20px; font-weight:600; cursor:pointer; transition:all 0.3s ease; box-shadow:0 4px 12px rgba(237,137,54,0.3); font-size:14px; margin:10px 0; }
    .favorite-btn:hover { transform:translateY(-2px); box-shadow:0 6px 16px rgba(237,137,54,0.4); }
    .favorite-btn.remove { background:linear-gradient(135deg,#f56565 0%,#e53e3e 100%); }

    .favorites-count { background:#ed8936; color:white; padding:4px 12px; border-radius:16px; font-size:12px; font-weight:600; margin-left:10px; }

    .feedback-toast { position:fixed; top:20px; right:20px; background:#48bb78; color:white; padding:12px 20px; border-radius:8px; z-index:100000; box-shadow:0 4px 12px rgba(0,0,0,0.5); font-weight:600; }

    /* Popup Styles */
    .popup-overlay { display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.8); backdrop-filter:blur(5px); z-index:99998; }
    .popup-container { display:none; position:fixed; top:50%; left:50%; transform:translate(-50%,-50%); background:#111; border-radius:16px; padding:24px; max-width:700px; width:90%; max-height:80vh; overflow-y:auto; box-shadow:0 20px 60px rgba(0,0,0,0.7); border:2px solid #667eea; z-index:99999; color:#eee; }
    .popup-close { position:absolute; top:12px; right:16px; cursor:pointer; font-size:24px; font-weight:bold; color:#fff; background:#222; border-radius:50%; width:32px; height:32px; display:flex; align-items:center; justify-content:center; box-shadow:0 2px 6px rgba(0,0,0,0.5); transition:all 0.2s ease; }
    .popup-close:hover { background:#667eea; color:white; }
    .popup-content { line-height:1.6; }
    .description-scroll { max-height:200px; overflow-y:auto; padding-right:8px; margin-top:10px; background:#222; border-radius:6px; padding:12px; border:1px solid #444; font-size:14px; line-height:1.5; }
    .detail-stats { display:grid; grid-template-columns:repeat(3,1fr); gap:10px; margin:15px 0; padding:15px; background:#1a1a1a; border-radius:8px; border:1px solid #333; }
    .detail-stat { text-align:center; }
    .detail-stat-value { font-size:16px; font-weight:bold; color:#667eea; }
    .detail-stat-label { font-size:11px; color:#888; margin-top:4px; }
    .favorite-action-section { margin-top:20px; padding-top:15px; border-top:2px solid #ed8936; text-align:center; }

    /* Scrollbar */
    .description-scroll::-webkit-scrollbar { width:6px; }
    .description-scroll::-webkit-scrollbar-track { background:#333; border-radius:3px; }
    .description-scroll::-webkit-scrollbar-thumb { background:#667eea; border-radius:3px; }
    .description-scroll::-webkit-scrollbar-thumb:hover { background:#5a6fd8; }
    """
    
    def __init__(self, app: BookDiscoveryApp):
        self.app = app
        self.demo = self._create_interface()
    
    def _create_interface(self) -> gr.Blocks:
        """Create the Gradio interface"""
        with gr.Blocks(css=self.CSS) as demo:
            # Header
            gr.Markdown("# 📚 Dark Book Discovery Hub")
            gr.Markdown("### Explore our curated collection of amazing books")
            
            # Feedback component
            feedback = gr.HTML("")
            
            # Random Books Section
            gr.Markdown("## 🎲 Random Books")
            random_books_container = gr.HTML(elem_classes="books-section")
            with gr.Row():
                random_load_more_btn = gr.Button("📚 Load More Random Books", elem_classes="load-more-btn")
                shuffle_btn = gr.Button("🔀 Shuffle Books", elem_classes="load-more-btn")
            
            # Popular Books Section
            gr.Markdown("## 📈 Popular Books")
            popular_books_container = gr.HTML(elem_classes="books-section")
            popular_load_more_btn = gr.Button("📚 Load More Popular Books", elem_classes="load-more-btn")
            
            # Favorites Section
            with gr.Column():
                favorites_header = gr.HTML(
                    self.app.ui_components.create_favorites_header(0)
                )
                favorites_container = gr.HTML(
                    elem_classes="books-section",
                    value=self.app.ui_components._get_empty_state_message(True)
                )
                favorites_load_more_btn = gr.Button(
                    "📚 Load More Favorites", 
                    elem_classes="load-more-btn", 
                    visible=False
                )
            
            # Quick Favorites Section
            gr.Markdown("### ⭐ Quick Favorites")
            with gr.Row():
                favorite_buttons = []
                for i in range(min(6, len(self.app.df))):
                    book = self.app.df.iloc[i]
                    is_fav = self.app.favorites_manager.is_favorite(book['id'])
                    btn_text = self.app._get_favorite_button_text(book['title'], is_fav)
                    btn = gr.Button(btn_text, elem_classes="favorite-btn", size="sm")
                    favorite_buttons.append(btn)
            
            # States
            random_books_state = gr.State(self.app.df.sample(frac=1).reset_index(drop=True))
            random_display_state = gr.State(pd.DataFrame())
            random_index_state = gr.State(0)

            popular_books_state = gr.State(self.app.df.copy())
            popular_display_state = gr.State(pd.DataFrame())
            popular_index_state = gr.State(0)

            favorites_state = gr.State(pd.DataFrame())
            favorites_display_state = gr.State(pd.DataFrame())
            favorites_index_state = gr.State(0)
            
            # Event handlers - FIXED: Use the actual button variables, not state dictionary
            random_load_more_btn.click(
                self.app.load_more_books,
                [random_books_state, random_display_state, random_index_state],
                [random_display_state, random_books_container, random_load_more_btn, random_index_state]
            )
            
            shuffle_btn.click(
                self.app.shuffle_random_books,
                [random_books_state, random_display_state],
                [random_books_state, random_display_state, random_books_container, random_index_state]
            )
            
            popular_load_more_btn.click(
                self.app.load_more_books,
                [popular_books_state, popular_display_state, popular_index_state],
                [popular_display_state, popular_books_container, popular_load_more_btn, popular_index_state]
            )
            
            favorites_load_more_btn.click(
                lambda lb, db, idx: self.app.load_more_books(lb, db, idx, True),
                [favorites_state, favorites_display_state, favorites_index_state],
                [favorites_display_state, favorites_container, favorites_load_more_btn, favorites_index_state]
            )
            
            # Connect favorite buttons
            for i, btn in enumerate(favorite_buttons):
                btn.click(
                    lambda x=i: self.app.handle_favorite_click(x),
                    outputs=[
                        favorites_state, favorites_container, 
                        favorites_load_more_btn, favorites_header,
                        btn, feedback
                    ]
                )
            
            # Initial load
            def initialize_interface():
                # Random books
                random_display, random_html, random_idx = self.app.initial_load(random_books_state.value)
                # Popular books  
                popular_display, popular_html, popular_idx = self.app.initial_load(popular_books_state.value)
                
                return (
                    random_display, gr.update(value=random_html), random_idx,
                    popular_display, gr.update(value=popular_html), popular_idx,
                    pd.DataFrame(), gr.update(), 0
                )
            
            demo.load(
                initialize_interface,
                outputs=[
                    random_display_state, random_books_container, random_index_state,
                    popular_display_state, popular_books_container, popular_index_state,
                    favorites_state, favorites_container, favorites_index_state
                ]
            )
            
            # JavaScript for popup (simplified version)
            gr.HTML("""
            <script>
            document.addEventListener('click', function(e) {
                const card = e.target.closest('.book-card');
                if (card) {
                    alert('Book details for: ' + card.dataset.title + '\\nClick favorite buttons above to add to favorites!');
                }
            });
            </script>
            """)
            
        return demo
    
    def launch(self, **kwargs):
        """Launch the application"""
        self.demo.launch(**kwargs)

# =============================================================================
# MAIN EXECUTION
# =============================================================================
def main():
    """Main function to run the application"""
    try:
        app = BookDiscoveryApp()
        interface = GradioInterface(app)
        print("🚀 Starting Book Discovery Hub...")
        interface.launch(share=True)  # share=True for public access if needed
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        raise

if __name__ == "__main__":
    main()