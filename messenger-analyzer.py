import argparse
import json
import pytz
import os

from datetime import datetime

def get_message_type(message):
    phrases = {
        "nickname": [
            " set your nickname ",
            " set the nickname for ",
            " cleared the nickname "
        ],
        "poll": [
            " created a poll: ",
            " in the poll.",
            "This poll is no longer available.",
            " poll has multiple updates."
        ],
        "video": [
            " joined the video chat."
        ],
        "group_photo": [
            " changed the group photo."
        ]
    }

    for phrase_type, strings in phrases.items():
        for string in strings:
            if string in message:
                return phrase_type
    
    return "text"

def parse_chat_messages(messages):
    parsed_messages = []

    for message in messages:
        if "content" not in message or message["type"] != "Generic":
            continue

        content = fix_text_encoding(message["content"])
        sender = fix_text_encoding(message["sender_name"])
                    
        parsed_messages.append({
            "sender": sender,
            "content": content,
            "timestamp": message["timestamp_ms"],
            "type": get_message_type(content)
        })

    parsed_messages.sort(key=lambda message: message["timestamp"])

    return parsed_messages

def get_chat_data(chat_directory):
    chat_data = {
        "title": "",
        "messages": []
    }

    for entry in os.scandir(chat_directory):
        if entry.is_dir():
            continue

        with open(entry.path, "r") as f:
            data = json.load(f)

            chat_data["title"] = fix_text_encoding(data["title"])
            chat_data["messages"] += data["messages"]

    return chat_data

def get_members(chat_messages):
    members = set()

    for message in chat_messages:
        if message["type"] != "text":
            continue

        sender = message["sender"]
        members.add(sender)

    return list(members)

def get_members_message_counts(chat_messages):
    members = {}

    for message in chat_messages:
        if message["type"] != "text":
            continue

        sender = message["sender"]

        if sender not in members:
            members[sender] = 0

        members[sender] += 1

    members = { k: v for k, v in sorted(members.items(), key=lambda item: item[1], reverse=True) }

    return members

def get_members_messages(chat_messages):
    members = {}

    for message in chat_messages:
        if message["type"] != "text":
            continue
    
        content = message["content"]
        sender = message["sender"]

        if sender not in members:
            members[sender] = []

        members[sender].append(content)

    return members

def get_members_word_freqs(chat_messages):
    members = {}

    for message in chat_messages:
        if message["type"] != "text":
            continue
    
        content = message["content"]
        sender = message["sender"]

        if sender not in members:
            members[sender] = {}

        content = content.lower()
        content = content.replace(",", "").replace("’", "").replace("'", "")
        words = content.split()

        for word in words:
            if word not in members[sender]:
                members[sender][word] = 0

            members[sender][word] += 1

    for member in members.keys():
        members[member] = { k: v for k, v in sorted(members[member].items(), key=lambda item: item[1], reverse=True) }

    return members

def get_members_average_message_lengths(members_messages):
    members = {}

    for name, messages in members_messages.items():
        members[name] = round(sum(len(message.split()) for message in messages) / len(messages), 2)

    members = { k: v for k, v in sorted(members.items(), key=lambda item: item[1], reverse=True)}
    return members

def get_members_top_word_freqs(members_word_freqs, size):
    word_exclusions = [
        "a", "able", "about", "across", "after", "all", "almost", "also", "am", "among", "an",
        "and", "any", "are", "as", "at", "be", "because", "been", "but", "by", "can", "cannot",
        "could", "did", "do", "does", "either", "else", "ever", "every", "for", "from", "get",
        "got", "had", "has", "have", "he", "her", "hers", "him", "his", "how", "however", "i", "im",
        "if", "in", "into", "is", "it", "its", "just", "least", "let", "like", "likely", "may",
        "me", "might", "most", "must", "my", "neither", "no", "nor", "not", "of", "off", "often",
        "on", "only", "or", "other", "one", "our", "own", "rather", "said", "say", "says", "she", "should",
        "since", "so", "some", "than", "that", "the", "their", "them", "then", "there", "these",
        "they", "this", "tis", "to", "too", "twas", "us", "wants", "was", "we", "were", "what",
        "when", "where", "which", "while", "who", "whom", "why", "will", "with", "would", "yet",
        "you", "your"
    ]

    members = {}

    for name, word_freqs in members_word_freqs.items():
        members[name] = {}
        idx = 0
        
        for word, count in word_freqs.items():
            if word.lower() in word_exclusions:
                continue

            members[name][word] = count
            idx += 1

            if idx >= size:
                break

    return members

def get_members_message_times(chat_messages):
    time_keys = [military_to_standard(i) for i in range(24)]
    members = {}

    for message in chat_messages:
        if message["type"] != "text":
            continue
    
        sender = message["sender"]
        timestamp = message["timestamp"]

        if sender not in members:
            members[sender] = { time_key: 0 for time_key in time_keys }

        time = get_pst_from_utc_timestamp(timestamp)
        members[sender][military_to_standard(time.hour)] += 1

    return members

def get_members_message_times_percentage(chat_messages):
    time_keys = [military_to_standard(i) for i in range(24)]
    time_sums = { time_key: 0 for time_key in time_keys }
    members = {}

    for message in chat_messages:
        if message["type"] != "text":
            continue
    
        sender = message["sender"]
        timestamp = message["timestamp"]

        if sender not in members:
            members[sender] = { time_key: 0 for time_key in time_keys }

        time = get_pst_from_utc_timestamp(timestamp)
        time_key = military_to_standard(time.hour)

        members[sender][time_key] += 1
        time_sums[time_key] += 1

    for time_key in time_keys:
        for data in members.values():
            if time_sums[time_key]:
                data[time_key] = (data[time_key] / time_sums[time_key]) * 100

    return members

def get_pst_from_utc_timestamp(timestamp):
    date = datetime.fromtimestamp(timestamp / 1000)

    return date.astimezone(pytz.timezone("US/Pacific"))

def military_to_standard(hour):
    if hour == 0:
        return "12am"

    elif hour < 12:
        return f'{hour}am'

    elif hour == 12:
        return "12pm"

    return f'{hour - 12}pm'

def process_chat_data(chat_data):
    chat_title = fix_text_encoding(chat_data["title"])
    chat_messages = parse_chat_messages(chat_data["messages"])

    members = get_members(chat_messages)
    message_counts = get_members_message_counts(chat_messages)
    messages = get_members_messages(chat_messages)
    word_freqs = get_members_word_freqs(chat_messages)
    average_message_lengths = get_members_average_message_lengths(messages)
    top_word_freqs = get_members_top_word_freqs(word_freqs, 10)
    message_times = get_members_message_times(chat_messages)
    message_times_percentage = get_members_message_times_percentage(chat_messages)

    return {
        "title": chat_title,
        "members": members,
        "message_counts": message_counts,
        "messages": messages,
        "word_freqs": word_freqs,
        "average_message_lengths": average_message_lengths,
        "top_word_freqs": top_word_freqs,
        "message_times": message_times,
        "message_times_percentage": message_times_percentage
    }

def parse_messenger(messenger_directory, chat_title):
    inbox_dir = os.path.join(messenger_directory, "inbox")
    chat = None

    for entry in os.scandir(inbox_dir):
        if entry.is_dir():
            chat_data = get_chat_data(entry.path)

            if chat_data["title"] == chat_title:
                chat = process_chat_data(chat_data)
                break

    if chat is None:
        print(f'Chat "{chat_title}" not found')
        return

    chat_filename = "-".join(chat["title"].split())
    members = chat["members"]

    for prop in ["message_counts", "average_message_lengths"]:
        member_data = { name: data for name, data in chat[prop].items() }
        save_singular_csv(f'{chat_filename}_{prop}.csv', chat["title"], member_data)
        
    for name in members:
        name_filename = "_".join(name.split())
        filename_prefix = f'{chat_filename}--{name_filename}'

        for prop in ["word_freqs", "top_word_freqs"]:
            save_singular_csv(f'{filename_prefix}_{prop}.csv', name, chat[prop][name])

        with open(f'{filename_prefix}_messages.txt', "w", encoding="utf-8") as f:
            for message in chat["messages"][name]:
                f.write(message + " ")

    for prop in ["message_times", "message_times_percentage"]:
        message_times = chat[prop]

        with open(f'{chat_filename}_{prop}.csv', "w", encoding="utf-8") as f:
            f.write(f',{",".join(military_to_standard(i) for i in range(24))}\n')

            for member, data in message_times.items():
                f.write(f'{member},{",".join([str(val) for val in data.values()])}\n')

    print(chat["message_counts"])

def save_singular_csv(filename, rowname, data):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f',{",".join(data.keys())}\n')
        f.write(f'{rowname},{",".join([str(val) for val in data.values()])}\n')

def fix_text_encoding(text):
    """Fixes text encoding, see https://stackoverflow.com/questions/50008296/facebook-json-badly-encoded"""
    return text.encode('latin1').decode('utf8')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse and analyse messenger data")
    parser.add_argument("messenger_directory", help="Path to messenger directory")
    parser.add_argument("chat_title", help="Title of the messenger chat")

    args = parser.parse_args()
    messenger_directory = args.messenger_directory
    chat_title = args.chat_title

    parse_messenger(messenger_directory, chat_title)
