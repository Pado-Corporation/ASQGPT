from flask import Flask, send_file

app = Flask(__name__)


@app.route("/download.pdf")
def download():
    return send_file("my-document.pdf", as_attachment=True)


if __name__ == "__main__":
    app.run()
