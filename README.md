# Book-Review

A Flask based web-app for book reviews and ratings.

# API Access: 

If users make a GET request to the website’s /api/<isbn> route, where <isbn> is an ISBN number, api website returns a JSON response containing the book’s title, author, publication date, ISBN number, review count, and average score.
The resulting JSON format is:
{
    "title": "Memory",
    "author": "Doug Lloyd",
    "year": 2015,
    "isbn": "1632168146",
    "review_count": 28,
    "average_score": 5.0
}
If the requested ISBN number isn’t in our database, our website returns a 404 error.
