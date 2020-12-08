import argparse
import json
import os

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
        ]
    }

    for phrase_type, strings in phrases.items():
        for string in strings:
            if string in message:
                return phrase_type
    
    return "text"

def get_top_freq_words(word_count, size):
    top_freq_words = {}
    idx = 0

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

    for word, count in word_count.items():
        if word.lower() in word_exclusions:
            continue

        top_freq_words[word] = count
        idx += 1

        if idx >= size:
            break

    return top_freq_words

def get_average_message_length(messages):
    length = 0

    for message in messages:
        length += len(message.split())

    return round(length / len(messages), 2)

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
    chat_data = []

    for entry in os.scandir(chat_directory):
        if entry.is_dir():
            continue

        with open(entry.path, "r") as f:
            chat_data.append(json.load(f))

    return chat_data

def parse_chat_directory(chat_directory):
    title = ""
    members = {}

    for chat_data in get_chat_data(chat_directory):
        title = fix_text_encoding(chat_data["title"])
        messages = parse_chat_messages(chat_data["messages"])

        for message in messages:
            if message["type"] != "text":
                continue
        
            content = message["content"]
            sender = message["sender"]

            if sender not in members:
                members[sender] = {
                    "messages_sent": 0,
                    "messages": [],
                    "word_count": {}
                }

            members[sender]["messages_sent"] += 1
            members[sender]["messages"].append(content)

            content = content.lower()
            content = content.replace(",", "").replace("’", "").replace("'", "")
            words = content.split()
    
            for word in words:
                if word not in members[sender]["word_count"]:
                    members[sender]["word_count"][word] = 0

                members[sender]["word_count"][word] += 1

    for name in members.keys():
        member_data = members[name]

        member_data["average_message_length"] = get_average_message_length(member_data["messages"])
        member_data["word_count"] = { k: v for k, v in sorted(member_data["word_count"].items(), key=lambda item: item[1], reverse=True) }
        member_data["top_freq_words"] = get_top_freq_words(member_data["word_count"], 10)

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
        if chat["title"] == "":
            chat_filename = "-".join(chat["title"].split())
            members = chat["members"]

            average_message_length = { name: data["average_message_length"] for name, data in members.items() }
            save_singular_csv(f'{chat_filename}_average_message_length.csv', chat["title"], average_message_length)
            
            messages_sent = { name: data["messages_sent"] for name, data in members.items() }
            save_singular_csv(f'{chat_filename}_messages_sent.csv', chat["title"], messages_sent)

            for name, data in members.items():
                name_filename = "_".join(name.split())
                filename_prefix = f'{chat_filename}--{name_filename}'

                save_singular_csv(f'{filename_prefix}_top_freq_words.csv', name, data["top_freq_words"])
                save_singular_csv(f'{filename_prefix}_word_count.csv', name, data["word_count"])

                with open(f'{filename_prefix}_messages.txt', "w", encoding="utf-8") as f:
                    for message in data["messages"]:
                        f.write(message + " ")

            print(messages_sent)

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

    args = parser.parse_args()
    messenger_directory = args.messenger_directory

    parse_messenger(messenger_directory)
