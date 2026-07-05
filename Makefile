.PHONY: setup run clean test

setup:
	pip install -r requirements.txt

run:
	streamlit run app.py

test:
	pytest tests/

clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	rm -f lged_offline_sync.db
