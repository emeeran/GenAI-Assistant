import logging

logging.basicConfig(level=logging.INFO)

def process_message(user_input, chat_history):
    """
    Process the user input and return the AI response.

    Args:
        user_input (str): The text sent by the user.
        chat_history (list): List of previous chat messages.

    Returns:
        str: The response text.
    """
    # ...integrate AI/logic here...
    response = f"Echo: {user_input}"
    logging.info("Processed message: %s", user_input)
    return response
