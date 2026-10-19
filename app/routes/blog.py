import markdown
from flask import Blueprint, render_template, request
from sqlalchemy import or_, extract
from app.extensions import db
from app.models import Post, Category

blog_bp = Blueprint("blog", __name__, url_prefix="/blog")


@blog_bp.route("")
@blog_bp.route("/")
def index():
    category_slug = request.args.get("categoria", "").strip()
    archive_param = request.args.get("arquivo", "").strip()  # formato YYYY-MM
    q = request.args.get("q", "").strip()

    query = Post.query.filter_by(is_published=True)
    active_category = None

    if category_slug:
        active_category = Category.query.filter_by(slug=category_slug).first()
        if active_category:
            query = query.filter_by(category_id=active_category.id)

    if archive_param and "-" in archive_param:
        try:
            year_str, month_str = archive_param.split("-", 1)
            query = query.filter(
                extract("year", Post.published_at) == int(year_str),
                extract("month", Post.published_at) == int(month_str),
            )
        except ValueError:
            pass

    if q:
        like_q = f"%{q}%"
        query = query.filter(
            or_(
                Post.title.ilike(like_q),
                Post.summary.ilike(like_q),
                Post.content.ilike(like_q),
                Post.tags.ilike(like_q),
            )
        )

    posts = query.order_by(Post.published_at.desc()).all()
    categories = Category.query.order_by(Category.name.asc()).all()

    return render_template(
        "blog/index.html",
        posts=posts,
        categories=categories,
        active_category=active_category,
        archive_param=archive_param,
        q=q,
    )


@blog_bp.route("/<slug>")
def post_detail(slug):
    post = Post.query.filter_by(slug=slug, is_published=True).first_or_404()
    post.views = (post.views or 0) + 1
    db.session.commit()

    html_content = markdown.markdown(
        post.content,
        extensions=["extra", "fenced_code", "tables", "nl2br"],
    )

    related_posts = (
        Post.query.filter(Post.id != post.id, Post.is_published.is_(True))
        .order_by(Post.published_at.desc())
        .limit(3)
        .all()
    )
    categories = Category.query.order_by(Category.name.asc()).all()

    return render_template(
        "blog/detail.html",
        post=post,
        html_content=html_content,
        related_posts=related_posts,
        categories=categories,
    )
