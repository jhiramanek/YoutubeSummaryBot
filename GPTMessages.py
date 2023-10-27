
def get_makeTag_message(achunk):
    msg = [
        {"role": "system",
         "content": "You are a Technology, finance and business journalist"},
        {"role": "assistant",
         "content": "Output a list of keywords for which to create embeddings.  Present the output in a python list format such as ['item1','item2','item3']"},
        {"role": "user", "content": achunk}]
    return msg


def get_summary_message(achunk):

    message = [
        {"role": "system", "content": "You are a Technology, and business Consultant"},
        {"role": "assistant",
         "content": "Write a concise summary of the key learnings from the following transcript for your client.  Present findings and learnings in a list format with no preamble.  The audience values actionable and insightful information."},
        {"role": "user", "content": achunk}]
    return message
