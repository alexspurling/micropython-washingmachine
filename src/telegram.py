from microWebCli import MicroWebCli
import secrets


def get_bot():
    url = f'api.telegram.org/bot{secrets.TELEGRAM_API_KEY}/getMe'
    return MicroWebCli.GETRequest(url)


def send_message(message):
    url = f'https://api.telegram.org/bot{secrets.TELEGRAM_API_KEY}/sendMessage'
    data = {
        'chat_id': secrets.TELEGRAM_CHAT_ID,
        'text': message
    }
    return MicroWebCli.JSONRequest(url, data)


def get_messages():
    # Get the id of the last update that we saw
    last_update_filename = 'lastupdateid.txt'

    try:
        print(f"Opening file {last_update_filename}")
        with open(last_update_filename, 'r') as f:
            print(f"Opened file {last_update_filename}")
            last_update_id = f.readline()
    except Exception as e:
        print(f"Error opening file {last_update_filename}", e)
        last_update_id = None

    print(f'Using last update id: {last_update_id}')

    url = f'https://api.telegram.org/bot{secrets.TELEGRAM_API_KEY}/getUpdates'

    print(f"Using telegram url: {url}")

    data = None
    if last_update_id:
        data = {"offset": int(last_update_id)}

    print(f"Using data: {data}")

    messages = MicroWebCli.JSONRequest(url, data)

    print(f"Got messages: {messages}")

    if messages is None:
        messages = {}

    if messages.get('result'):
        last_message_update_id = messages['result'][-1].get('update_id')
        if last_message_update_id:
            new_last_message_update_id = last_message_update_id + 1
            print('Setting last update id to:', new_last_message_update_id)
            with open(last_update_filename, 'w') as f:
                f.write(str(new_last_message_update_id))
        else:
            print('Did not find update_id in messages')

    return messages
