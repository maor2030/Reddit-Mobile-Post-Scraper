# Reddit-Mobile-Post-Scraper
A Python tool that fetches and extracts data from the latest 100 posts of any subreddit using Reddit's mobile GraphQL API.

- Features

Collects post metadata:

Author names
Post titles

Posting timestamps

Number of comments

- More to know:
  
Uses the same data endpoints as the official Reddit mobile app

Automatically saves data to a JSON file

No login required

Minimal dependencies (only requires 'requests' library)

# Quick Start
- Just modify the subreddit name in main()
- subreddit = "Steam"  # Change this to any subreddit you want
- target_count = 100   # Number of posts to collect
-  posts = collect_posts(subreddit, target_count) # Run the collector

# The script will:
 1. Collect 100 posts from r/Steam
 2. Print first and last post details
 3. Save all posts to 'reddit_posts_Steam.json'

# Output Example
Final collection: 100 posts

- First post:

Title: Steam Winter Sale 2024

Author: SteamUser123

Comments: 45

Created: 2024-12-18T08:20:02.812000+0000

- Last post:

Title: Need game recommendations

Author: Gamer456

Comments: 12

Created: 2024-12-17T14:15:30.421000+0000

Saved 100 posts to reddit_posts_Steam.json

# Installation
pip install requests

# Important Note
This is an unofficial tool that uses Reddit's mobile app API endpoints. It may stop working if Reddit updates their mobile API structure.
