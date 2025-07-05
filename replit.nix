language = "python3"
run = "python run_elma_app.py"

[nix]
channel = "stable-22_11"

[deployment]
run = ["sh", "-c", "python run_elma_app.py"]
