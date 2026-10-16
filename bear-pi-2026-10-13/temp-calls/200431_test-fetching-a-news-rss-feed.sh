# 2026-10-13T20:04:31.189196Z UTC  agent=main  (verbatim command from transcript; secrets REDACTED)
# result head: 'Top stories - Google News\nGoogle News\nTrump fires ambassador to Greece Guilfoyle after reports of misconduct - Reuters\nCornell Bans Fraternity Parties and Adds Sexual Assault Investigators - The New York Times\nSix Flags closes nine rides across country after man dies falling off roller coaster in Ge'
curl -s -m 10 "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en" | grep -o '<title>[^<]*</title>' | head -12 | sed 's/<[^>]*>//g'
