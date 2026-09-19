from flask import Blueprint, render_template, abort, redirect, url_for
from app.models import PaperStore

main = Blueprint("main", __name__)
paper_store = PaperStore()

@main.route("/")
def home():
    return render_template("index.html")

@main.route("/reader/<paper_id>")
def reader(paper_id):
    paper = paper_store.get_paper(paper_id)
    if not paper:
        return redirect(url_for("main.home"))
    return render_template("reader.html", paper=paper)

@main.route("/about")
def about():
    return render_template("about.html")