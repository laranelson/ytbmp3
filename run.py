from server import app

if __name__ == "__main__":
    app.run(app, host="0.0.0.0", port=5000, debug=False)
