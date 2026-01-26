.PHONY: clean scrape map sentiment signals run dashboard

clean:
	rm -f data/processed/*.csv
	rm -f data/raw/*.csv

scrape:
	python -m src.scrape.news_rss
	python -m src.scrape.news_api

map:
	python -m src.scrape.map_tickers

sentiment: 
	python -m src.nlp.sentiment

signals:
	python -m src.signals.make_signals

run:
	make scrape
	make map
	make sentiment
	make signals
	
dashboard:
	streamlit run dashboard/app.py
