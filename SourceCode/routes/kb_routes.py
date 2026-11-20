from flask import Blueprint, render_template, request, jsonify
from database import get_db

kb_bp = Blueprint('kb', __name__)

@kb_bp.route('/kb', strict_slashes=False)
def list_articles():
    db = get_db()
    search_query = request.args.get('q', '').strip()
    category_id = request.args.get('category', '').strip()

    query = """
        SELECT k.*, c.name AS category_name
        FROM kb_articles k
        JOIN categories c ON k.category_id = c.category_id
        WHERE 1=1
    """
    params = []

    if search_query:
        query += " AND (k.title LIKE ? OR k.content LIKE ? OR k.tags LIKE ?)"
        like_term = f"%{search_query}%"
        params.extend([like_term, like_term, like_term])

    if category_id:
        query += " AND k.category_id = ?"
        params.append(category_id)

    query += " ORDER BY k.created_at DESC"
    articles = db.execute(query, params).fetchall()
    categories = db.execute("SELECT * FROM categories ORDER BY name").fetchall()

    return render_template('kb/list.html',
                           articles=articles,
                           categories=categories,
                           search_query=search_query,
                           selected_category=category_id)

@kb_bp.route('/kb/<int:article_id>')
def article_detail(article_id):
    db = get_db()
    article = db.execute("""
        SELECT k.*, c.name AS category_name
        FROM kb_articles k
        JOIN categories c ON k.category_id = c.category_id
        WHERE k.article_id = ?
    """, (article_id,)).fetchone()

    if not article:
        return "Knowledge base article not found.", 404

    # Related articles in same category
    related = db.execute("""
        SELECT article_id, title FROM kb_articles
        WHERE category_id = ? AND article_id != ?
        LIMIT 4
    """, (article['category_id'], article_id)).fetchall()

    return render_template('kb/detail.html', article=article, related=related)

@kb_bp.route('/api/kb/search')
def api_search():
    """AJAX endpoint used by ticket submission form for ticket deflection."""
    query = request.args.get('q', '').strip()
    if not query or len(query) < 3:
        return jsonify([])

    db = get_db()
    results = db.execute("""
        SELECT article_id, title, substr(content, 1, 140) AS snippet
        FROM kb_articles
        WHERE title LIKE ? OR content LIKE ? OR tags LIKE ?
        LIMIT 4
    """, (f"%{query}%", f"%{query}%", f"%{query}%")).fetchall()

    data = [dict(r) for r in results]
    return jsonify(data)
