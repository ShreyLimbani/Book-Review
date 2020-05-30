import os
import requests, json
from flask import Flask, session, render_template, request, url_for, redirect
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker


app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key='1q2w3e4r'

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))
Session(app)

@app.route("/",methods=["GET","POST"])
def index():
	if request.method == "POST":
		session.pop("user_id", None)
		session.pop("name", None)
		return render_template('index.html', index=True)
	else:
		if session.get("user_id")==None:
			return render_template('index.html', index=True)
		else:
			return redirect(url_for('login'))

@app.route("/dashboard", methods=["GET","POST"])
def login():
	books = db.execute("SELECT books.id,isbn,title,authors.name,year FROM books join authors on books.author_id=authors.id order by random() limit 21;")
	if request.method == "GET":
		if session.get("user_id")==None:
			#For opening the login page form
			return redirect(url_for('index'))
		else:		
			#yourBooks_id_res = db.execute("SELECT book_id from book_ratings WHERE user_id= :u_id",
			#					{'u_id': session["user_id"]})
			#yourBooks_id = []
			#for y_b in yourBooks_id_res:
			#	yourBooks_id.append(y_b.book_id)
			#print("---Hello EveryOne---(())"+str(yourBooks_id))

			return render_template('dashboard.html', name=session["name"], books=books)
	
	else:
	#For logging into to the account or creating a new user account	
		form_type = request.form.get("form")
		username = request.form.get("username")
		password = request.form.get("password")
		if password=='' or username=='':
			return "Retry with proper username and password"

		if form_type == 'register':
			name = request.form.get("name")	
			dob = request.form.get("dob")
			if db.execute("SELECT * FROM users WHERE username = :username", {"username": username}).rowcount == 1:
				return "Try again with another username...!!"

			db.execute("INSERT INTO users (username, name, password, dateOfBirth) VALUES (:username, :name, :password, :dob)",
				{"username":username,"name": name,"password": password,"dob": dob})
			db.commit()
			session["name"] = name
			session["user_id"] = db.execute("SELECT * FROM users WHERE username = :username", {"username": username}).first().id
			return render_template("dashboard.html", name=name, books =books, index=False) # 
		
		else:
			try:
				user = db.execute("SELECT * FROM users WHERE username = :username and password=	:password", 
				{"username": username, "password": password}).fetchall()
				session["user_id"] = user[0].id
				session["name"] = user[0].name
			except:
				return "Retry with proper username and password"
			if len(user) == 0:
				return "No user found .../n Try registering for a new user"

			#yourBooks_id_res = db.execute("SELECT book_id from book_ratings WHERE user_id= :u_id",
			#					{'u_id': session["user_id"]})
			#yourBooks_id = []
			#for y_b in yourBooks_id_res:
			#	yourBooks_id.append(y_b.book_id)
			#print("---Hello EveryOne---(())"+str(yourBooks_id))
			
			return render_template("dashboard.html", name=session["name"], books = books) #

@app.route("/books/<int:book_id>")
def book(book_id):
	# Make sure book exists.
	book = db.execute("SELECT * FROM books WHERE id = :id", {"id": book_id}).fetchone()
	if book is None:
		return "No such book availble"

	# Get Book Details
	book_details = db.execute("SELECT books.id,isbn,title,authors.name,year FROM books join authors on books.author_id=authors.id WHERE books.id= :book_id;",
							{"book_id": book.id}).fetchone()

	#Getting Data From Goodreads API
	try:
		book = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "Vaf5hBbE54KXyG63wIb3jQ", "isbns": book_details.isbn})
		book = json.loads(book.text)
		goodreads = [book['books'][0].get('average_rating'),book['books'][0].get('ratings_count')]
	except:
		goodreads="None"

	#Getting Reviews From Book_review Table
	reviews = db.execute("SELECT users.id, rating, review, users.name FROM book_ratings JOIN users on book_ratings.user_id=users.id where book_id = :b_id limit 10;",
			{"b_id": book_id}).fetchall()
	stat = db.execute("SELECT round(avg(rating),2), count(*) FROM book_ratings WHERE book_id= :b_id;",
						{'b_id': book_id})

	if len(reviews) == 0:
		reviews = "None"
	#Getting Rev
	book = {'details': book_details, 'goodreads':goodreads, 'reviews': reviews, 'stat': stat.first(), 'yourReview': 'None'}

	#Checking if user has reviewed the book.
	if reviews != "None":
		for review in reviews:
			if review.id==session["user_id"]:
				book['yourReview'] = review
				try:
					reviews.remove(review)
				except:
					pass
				break

	return render_template("book.html",name=session["name"], book=book)

@app.route("/books/<int:book_id>/submitreview", methods=["POST"])
def postReview(book_id):
	rating = request.form.get("rating")
	review = request.form.get("review")

	#Add review to database
	db.execute("INSERT INTO book_ratings (book_id, rating, review, user_id) VALUES (:b_id, :rat, :rev, :u_id)",
				{'b_id':book_id, 'rat':rating, 'rev':review, 'u_id':session["user_id"]})
	db.commit()

	return redirect(url_for('book', book_id=book_id))


@app.route("/search", methods=["POST"])
def search():
	search_string = request.form.get("search_string")
	#Formatting the string in different ways to match different attributes
	search_string = search_string.strip()
	s1 = '%'+search_string.title()+'%'
	s2 = '%'+search_string.capitalize()+'%'
	s3 = '%'+search_string.upper()+'%'
	s = '%'+search_string+'%'
	print(f"s-{s}--------s1-{s1}--------s2-{s2}--------s3-{s3}")
	try:
		query = db.execute("SELECT books.id, isbn, title, name FROM BOOKS join authors on books.author_id=authors.id WHERE ISBN like :s3 or title like :s2 or title like :s1 or title like :s or name like :s1 or name like :s2 or name like :s order by title",
						{'s3': s3, 's2': s2, 's1': s1, 's': s}).fetchall()
		count = len(query)
	except:
		query = []
		count = len(query)

	return render_template('search.html',name=session["name"], search_string=search_string, query=query, count=count)
