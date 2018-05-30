'''
A twitter script that will grab past 7 days and real time tweets on a certain topic
and its' competitors.
'''
import settings
import tweepy
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import pandas as pd
import matplotlib.pyplot as plt
import datetime

def search_twitter(twitter, sentiment_analyzer):
	'''
		Uses specified queries to search the real time API (standard, 7 day) 

		Input: twitter - the authenticated Twython client 

		Possible queries to twitter: 
				q (required): search query, e.g. @lululemon
				geocode: latitude, longitude, radius(mi or km) e.g. 37 -122 1mi
				lang: given language
				result_type: choose which results you want, 
					"mixed" (popular and real time), "recent" (most recent),
					"popular" (only most popular)
				count: number of tweets per page
				until: tweets before this date e.g. 2015-11-01
				since_id: tweets with an id greater than this
				max_id: tweets with an id smaller than this
				include_entities: boolean, entities should or not be included

	'''

	list_tweets = []
	count_daily_tweets = 0

	my_query = "%20OR%20".join(settings.QUERY)
	numResults = 100

	until_day = datetime.date.today()
	maximum_id = -1

	while True:

		tweets = twitter.search(q=my_query, count=numResults, tweet_mode='extended', until = until_day, max_id = maximum_id)
		
		if tweets:
			for tweet in tweets:
				tweet_text = tweet.full_text
				if tweet_text.startswith("RT"):
					continue
				print tweet_text
				tweet_date = tweet.created_at
				tweet_id = tweet.id
				tweet_fav_count = tweet.favorite_count
				retweet_count = tweet.retweet_count
				sentiment = sentiment_analyzer.polarity_scores(tweet_text)
				list_tweets.append([tweet_text, tweet_date, tweet_id, tweet_fav_count, retweet_count, sentiment['compound']])
				count_daily_tweets += 1
				print count_daily_tweets

			maximum_id = list_tweets[-1][2]
			if count_daily_tweets >= settings.TWEET_COUNT_PER_DAY:
				until_day = until_day - datetime.timedelta(days=1)
				print until_day
				count_daily_tweets = 0

		else:
			break
		
	headers = ["tweet_text", "tweet_date", "tweet_id", "tweet_fav_count", "retweet_count", "sentiment_compound"]
	tweets_df = pd.DataFrame(list_tweets, columns = headers)
	tweets_df["tweet_text"] = tweets_df["tweet_text"].replace({',': ' '}, regex=True)
	tweets_df.to_csv(settings.OUTPUT_CSV, header=True, index=False, encoding="utf-8")
	return tweets_df

def visualize(tweets_df):
	tweets_df['tweet_date'] = tweets_df['tweet_date'].dt.date

	tweets_df['senti_polarity'] = tweets_df['sentiment_compound'].map(lambda x: "pos" if x > 0 else ("neg" if x < 0 else "neutral"))
	
	tweets_df.groupby(['tweet_date', 'senti_polarity']).size().unstack().plot(kind='bar',
													 stacked=True, rot=45, title=settings.NAME_OF_CHART)

	plt.show()
	figureName = "_".join(settings.NAME_OF_CHART) + ".png"
	plt.savefig('figures/' + figureName)

	averages = tweets_df.groupby(['tweet_date'])['sentiment_compound'].mean()
	print averages

	print tweets_df['sentiment_compound'].mean()


def main():

	# Authenticate twitter, keys and tokens are in settings.py file
	# To get a twitter key, you must make an app at apps.twitter.com
	# You'll also need a twitter account
	#
	# To get the ACCESS TOKEN, uncomment the following:
	#
	# twitter = Twython(API_KEY, API_SECRET, oauth_version=2)
	# ACCESS_TOKEN = twitter.obtain_access_token()



	auth = tweepy.AppAuthHandler(settings.API_KEY, settings.API_SECRET)
	twitter = tweepy.API(auth, wait_on_rate_limit=True,
				   wait_on_rate_limit_notify=True)

	sent_analyze = SentimentIntensityAnalyzer()
	tweets_df = search_twitter(twitter, sent_analyze)
	visualize(tweets_df)





	





if __name__ == "__main__":
    main()