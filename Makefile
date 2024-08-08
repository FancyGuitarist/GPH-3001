VENV=venv
TARGET=mir

.PHONY: run test setup clean
AUDIO_FILE := "./song&samples/gamme_C.wav"

run: $(VENV)/bin/activate
	./$(VENV)/bin/python3 $(TARGET) monophonic -f $(AUDIO_FILE)

test: $(VENV)
	PYTHONWARNINGS=ignore $(VENV)/bin/python3 -m unittest mir/Test/testBasic.py mir/Test/testPartition.py mir/Test/testChordIdentifier.py

coverage: $(VENV)
	coverage html -d Test/coverage_html && open Test/coverage_html/index.html

setup:
	python3.11 -m venv $(VENV)
	./$(VENV)/bin/pip install -r requirements.txt

clean:
	# remove __paycache and venv
	rm -rf __pycache__ $(VENV)
