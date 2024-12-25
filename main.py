import os
from web.app import create_app
from config.config import Config

def main():
    app = create_app()
    app.run(
        host=Config.API_HOST,
        port=Config.API_PORT,
        debug=True
    )

if __name__ == '__main__':
    main() 