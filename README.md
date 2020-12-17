# Messenger Analyzer
Extract some neat information from chats in messenger!

## Install

[Python 3.6+](https://www.python.org/downloads/) is required alongside the [pytz](https://pypi.org/project/pytz/) package.

## Usage

```
python messenger-analyzer <messenger_directory> <chat_title>
```

### Required Arguments

messenger_directory - Path to "messages" directory of data downloaded from Facebook

chat_title - Title of chat to extract information from

### Result

Output files for the chat and for each chat participant will be created in the current
directory that the command was ran in.

xxx = Chat title

yyy = Participant

#### Output Files

xxx_average_message_lengths.csv - Average message length (# of words) for all chat participants

xxx_message_counts.csv - Number of messages sent by each chat participant

xxx_message_monthly_counts.csv - Number of messages sent by each participant per month

xxx_message_times_percentage.csv - Percentage of each hour's messages sent by a chat participant

xxx_message_times.csv - Total number of messages sent in each hour by a chat participant

xxx-yyy_messages.txt - Contains all messages this participant sent to the chat

xxx-yyy_top_word_freqs.csv - Top 10 words and their frequencies exluding some common words for this participant

xxx-yyy_word_freqs.csv - All words and their frequencies for this participant 

## Contributing

PRs accepted :)

## License

GNU GPL v3.0