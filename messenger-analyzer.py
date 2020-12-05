import argparse
import json
import os

def parse_chat_directory(chat_directory):
    chat = {
        "title": "",
        "members": {}
    }

    for entry in os.scandir(chat_directory):
        if entry.is_file():
            data = None

            with open(entry.path, "r") as f:
                data = json.load(f)

            chat["title"] = data["title"]

            for message in data["messages"]:
                if "content" not in message or message["type"] != "Generic":
                    continue

                sender = message["sender_name"]

                if sender not in chat["members"]:
                    chat["members"][sender] = {
                        "messages_sent": 0,
                        "messages": {}
                    }

                chat["members"][sender]["messages_sent"] += 1

                content = message["content"].split()
     
                for word in content:
                    if word not in chat["members"][sender]["messages"]:
                        chat["members"][sender]["messages"][word] = 0

                    chat["members"][sender]["messages"][word] += 1

    return chat

def parse_messenger(messenger_directory):
    inbox_dir = os.path.join(messenger_directory, "inbox")
    chats = []

    for entry in os.scandir(inbox_dir):
        if entry.is_dir():
            chats.append(parse_chat_directory(entry.path))

    for chat in chats:
        print(chat["title"])

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse and analyse messenger data")
    parser.add_argument("messenger_directory", help="Path to messenger directory")

    args = parser.parse_args()
    messenger_directory = args.messenger_directory

    parse_messenger(messenger_directory)
