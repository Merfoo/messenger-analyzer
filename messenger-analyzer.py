import argparse
import json
import os

def parse_chat_directory(chat_directory):
    title = ""
    members = {}

    for entry in os.scandir(chat_directory):
        if entry.is_dir():
            continue

        chat_data = None

        with open(entry.path, "r") as f:
            chat_data = json.load(f)

        title = chat_data["title"]

        for message in chat_data["messages"]:
            if "content" not in message or message["type"] != "Generic":
                continue

            sender = message["sender_name"]

            if sender not in members:
                members[sender] = {
                    "messages_sent": 0,
                    "messages": {}
                }

            members[sender]["messages_sent"] += 1

            content = message["content"].split()
    
            for word in content:
                if word not in members[sender]["messages"]:
                    members[sender]["messages"][word] = 0

                members[sender]["messages"][word] += 1

    return {
        "title": title,
        "members": members
    }

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
