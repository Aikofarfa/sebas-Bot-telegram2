import os
import requests

# Load sensitive data from environment variables
API_KEY = os.getenv('TELEGRAM_API_KEY')
API_URL = f'https://api.telegram.org/bot{API_KEY}/sendMessage'

# Improved function to send messages

def send_telegram_message(chat_id, message):
    try:
        payload = {'chat_id': chat_id, 'text': message}
        response = requests.post(API_URL, json=payload)

        # Check for request success
        response.raise_for_status()

    except requests.exceptions.HTTPError as http_err:
        print(f'HTTP error occurred: {http_err}')  # Log the error
    except Exception as err:
        print(f'An error occurred: {err}')  # Log the error
    else:
        print('Message sent successfully')

# Example usage
if __name__ == '__main__':
    chat_id = os.getenv('TELEGRAM_CHAT_ID')  # Retrieve chat id from env variables
    message = 'Hello, this is a test message!'
    send_telegram_message(chat_id, message)

# Optimized trading logic

# Note: Add more functions and logic related to trading accordingly
