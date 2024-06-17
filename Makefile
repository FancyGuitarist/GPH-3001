VENV=venv
TARGET=main.py

.PHONY: run test setup clean
AUDIO_FILE := "./song\&samples/gamme_C.wav"

run: $(VENV)/bin/activate
	./$(VENV)/bin/python3 $(TARGET) $(AUDIO_FILE)

test: $(VENV)
	PYTHONWARNINGS=ignore $(VENV)/bin/python3 -m unittest Test/test.py

setup: $(VENV)
	$(VENV): requirements.txt
	python3.11 -m venv $(VENV)
	./$(VENV)/bin/pip install -r requirements.txt

clean:
	rm -rf __pycache__ $(VENV)
