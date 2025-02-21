web: nix-shell --run "python -m spacy download en_core_web_sm && gunicorn -w 4 -b 0.0.0.0:8080 app:app"
