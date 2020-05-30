import csv
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(os.getenv("DATABASE_URL")) 
# database engine object from SQLAlchemy that manages connections to the database
# DATABASE_URL is an environment variable that indicates where the database lives
db = scoped_session(sessionmaker(bind=engine))

f = open('books.csv')
reader = csv.reader(f)
header = next(reader)

for isbn, title, author, year in reader:
	author_entry = db.execute("SELECT * FROM AUTHORS WHERE NAME= :AUTHOR",{"AUTHOR":author})
	if author_entry.rowcount == 0:
		db.execute("INSERT INTO AUTHORS (name) values ( :name)",{"name": author})
		db.execute("INSERT INTO books (isbn, title, author_id, year) values (:isbn, :title, :author_id, :year)",
			{"isbn": isbn, "title": title,
			"author_id": db.execute("SELECT * FROM AUTHORS WHERE NAME= :AUTHOR",{"AUTHOR":author}).first().id, 
			"year": year})
	else:
		db.execute("INSERT INTO books (isbn, title, author_id, year) values (:isbn, :title, :author_id, :year)",
			{"isbn": isbn, "title": title,"author_id": author_entry.first().id, "year": year})
	print("Done")
db.commit()