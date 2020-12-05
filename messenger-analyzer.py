import argparse
import json
import os

def parse_chat_directory(chat_directory):
    title = ""
    members = {}
    message_lengths = {}

    for entry in os.scandir(chat_directory):
        if entry.is_dir():
            continue

        chat_data = None

        with open(entry.path, "r") as f:
            chat_data = json.load(f)

        chat_data["title"] = fix_text_encoding(chat_data["title"])
        
        title = chat_data["title"]

        for message in chat_data["messages"]:
            if "content" not in message or message["type"] != "Generic":
                continue

            sender = fix_text_encoding(message["sender_name"])
            content = fix_text_encoding(message["content"])
            
            if sender not in members:
                members[sender] = {
                    "messages_sent": 0,
                    "messages": [],
                    "word_count": {}
                }

                message_lengths[sender] = 0

            members[sender]["messages_sent"] += 1
            members[sender]["messages"].append(content)

            words = []

            for word in content.split():
                word = word.lower()
                word = word.replace(",", "")
                word = word.replace("’", "")
                word = word.replace("'", "")

                words.append(word)

            message_lengths[sender] += len(words)
    
            for word in words:
                if word not in members[sender]["word_count"]:
                    members[sender]["word_count"][word] = 0

                members[sender]["word_count"][word] += 1

    for name in members.keys():
        avg_msg_len = message_lengths[name] / members[name]["messages_sent"]
        members[name]["average_message_length"] = round(avg_msg_len, 2)
        
        members[name]["word_count"] = { k: v for k, v in sorted(members[name]["word_count"].items(), key=lambda item: -item[1]) }

        word_count = { message: count for message, count in members[name]["word_count"].items() }
        word_count = { k: v for k, v in sorted(word_count.items(), key=lambda item: -item[1]) }

        top_freq_words = {}
        top_freq_words_len = 10
        idx = 0

        word_exclusions = [
            "a", "able", "about", "across", "after", "all", "almost", "also", "am", "among", "an",
            "and", "any", "are", "as", "at", "be", "because", "been", "but", "by", "can", "cannot",
            "could", "did", "do", "does", "either", "else", "ever", "every", "for", "from", "get",
            "got", "had", "has", "have", "he", "her", "hers", "him", "his", "how", "however", "i", "im",
            "if", "in", "into", "is", "it", "its", "just", "least", "let", "like", "likely", "may",
            "me", "might", "most", "must", "my", "neither", "no", "nor", "not", "of", "off", "often",
            "on", "only", "or", "other", "our", "own", "rather", "said", "say", "says", "she", "should",
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

            if idx >= top_freq_words_len:
                break

        members[name]["top_freq_words"] = top_freq_words

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
            save_singular_csv(f'{chat_filename}_avg_msg_len.csv', chat["title"], average_message_length)
            
            messages_sent = { name: data["messages_sent"] for name, data in members.items() }
            save_singular_csv(f'{chat_filename}_messages_sent.csv', chat["title"], messages_sent)

            for name, data in members.items():
                name_filename = "_".join(name.split())
                filename_prefix = f'{chat_filename}--{name_filename}'

                save_singular_csv(f'{filename_prefix}_top_freq_words.csv', name, data["top_freq_words"])
                save_singular_csv(f'{filename_prefix}_messages.csv', name, data["word_count"])

                with open(f'{filename_prefix}_word_cloud.txt', "w", encoding="utf-8") as f:
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
