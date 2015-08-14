# Reddit-Imgur-Mass-Picture-Downloader
  This python script will pull every single post made between two specified dates and then use the URLs in those posts to scrape Imgur for the linked pictures. The resulting photos will be placed in what ever directory the script resides in.
##Requirements:
  BeautifulSoup, PRAW. Python 3.0+
##How To Use:
  When the script is run it will ask what subreddit you with to download from. Simply type it in(case sensitive). The program itself will prompt you for the start and end dates. 
##A Word on Subreddits:
  Keep in mind that the activity of default subreddits is an order of magnitude different from non-default subreddits. Saying you want two weeks of /r/pics material will result in thousands of pictures being downloaded while specifying a two week span for an out of the way non-default subreddit will result in much less.  
