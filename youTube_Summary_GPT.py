import os

from more_itertools import last
import requests
from bs4 import BeautifulSoup

from RecordJSON import *
from HelperFunctions import *

openai.api_key = os.environ.get('OPEN_AI_API')

if openai.api_key is None:
    print("OPEN_AI_API environment variable not set.  If using Windows, please set variable in System Environment (User) Variables before proceeding.")
    exit(1)

print(openai.api_key)

# read the urls of the videos from the file
url_file_path = os.path.join(os.path.dirname(__file__), 'urls.txt')
with open(url_file_path) as f:
    urls = f.read().splitlines()

# get the first url in the file
url = urls[0]
page = requests.get(url)
print(url)

soup = BeautifulSoup(page.content, 'html.parser')
title = soup.title.text
print(title)

video_id = url.split("=")[1]
# get up to first 5 words of title
title_summ = ' '.join(title.split()[:5])

# create the file name for the Temporary storage of the video transcript chunks
JSON_FILE_PATH = os.path.join(os.path.dirname(
    __file__), f'{title_summ}--{video_id}.json')

# check if temp file exists if so get the max chunk_id
tempFileExists = os.path.exists(JSON_FILE_PATH)
tempFileEmpty = os.stat(JSON_FILE_PATH).st_size == 0

chunk_transcript = get_chunked_transcript(video_id)
number_of_chunks_in_transcript = len(chunk_transcript)

# initialise variables
number_of_processed_chunks = 0
summary = []
areTagsProcessed = False


# if temp file exists and is not empty then start from last chunk_id
# count number of items in chunk_transcript
res = []
if tempFileExists and not tempFileEmpty:
    update = read_summary_from_file(JSON_FILE_PATH)
    summary = update[0]
    areTagsProcessed = update[1]
    number_of_processed_chunks = update[2]

    if number_of_processed_chunks <= number_of_chunks_in_transcript:
        # remove already processed chunks
        chunk_transcript = chunk_transcript[number_of_processed_chunks:]

# Begin Process to get summary
if (len(chunk_transcript) > 0):
    res = process_transcript_using_gpt3(
        summary, title, video_id, number_of_processed_chunks, chunk_transcript, JSON_FILE_PATH)

    summary = res[0]
    number_of_processed_chunks = res[1]
else:
    print("All chunks processed.. moving on to TAGS")

print(summary)
# After getting a summary of all the chunks of the transcript we can now chunk the summary and determine the TAGS
Tags = generate_tags_from_summary(summary)

# Convert the Tags variable to a list of strings
tag_list = Tags.tolist()  # [str(tag) for tag in Tags]


def generate_text_embeddings_from_tags(tags):
    # generate text embedding for Tags using text-embedding-ada-002
    # https://beta.openai.com/docs/api-reference/text-embeddings
    try:
        embeddings = openai.TextEmbedding.create(
            model="text-embedding-ada-002",
            documents=tags
        )
        return embeddings
    except:
        print("Rate Limit Error")
        return None


def update_file_and_close(num_processed_chunks, Tags, embeddings, title, video_id, JSON_FILE_PATH):

    # Get the directory of the temp file
    temp_file_dir = os.path.dirname(JSON_FILE_PATH)
    with open(JSON_FILE_PATH, 'a') as f:
        # Serializing json
        # check if the last character in the file is "]"
        f.seek(f.tell() - 1, os.SEEK_SET)
        last_char = f.read(1)
        if last_char == ']':
            # remove the "]" from the end of the file
            f.seek(f.tell() - 1, os.SEEK_SET)
            f.truncate()
        # add the tag json object to the file

    # Update the Tags and embeddings to the file
    list_of_tag_objs = []
    for tag in tag_list:
        tag_json_obj = get_tags_json(
            num_processed_chunks, "Tag", title, video_id, tag)

        list_of_tag_objs.append(tag_json_obj)

        with open(JSON_FILE_PATH, 'a') as f:

            # add the tag json object to the file
            if (tag == last(tag_list)):
                f.write(tag_json_obj + '\n')
                f.write(']'+'\n')
            else:
                f.write(tag_json_obj + '\n')
                f.write(','+'\n')

            f.close

    # Update the Embeddings to the file

    # Prepare HTML file for output
        # Join the temp file directory with the filename "youtube.html"
        html_file_path = os.path.join(temp_file_dir, "youtube.html")

        # convert summary to markdown
        import markdown
        summary = markdown.markdown(summary)

        # Open the HTML file in "append" mode

        with open(html_file_path, "a") as f:
            # Write the title and video ID to the file
            f.write(f'<h1>{title} {video_id}</h1>')

            # Write the summary and tags to the file
            f.write(f'<h2>Summary</h2><p>{summary}</p>')
            f.write(f'<h3><strong>Tags: </strong>{Tags}</h3>')
            f.write(f'<h3>Full Transcript</h3>')
            f.close


embeddings = generate_text_embeddings_from_tags(Tags)

print(Tags)

print(embeddings)

update_file_and_close(number_of_processed_chunks, tag_list,
                      embeddings, title, video_id, JSON_FILE_PATH)
