from urllib.parse import parse_qs
import socketio
import uvicorn

"""
requirements - python-socketio, websockets

Create an instance of the asynchronous Socket.IO server
The async_mode parameter allows you to specify the asynchronous framework or mode in which the WebSocket server will run.

“asgi”: Uses ASGI (Asynchronous Server Gateway Interface), which is a more modern and flexible interface for asynchronous web applications. 
ASGI is compatible with ASGI-compatible servers, like uvicorn or daphne.
The choice of async_mode depends on your specific web framework, server, and application requirements.
In this boilerplate 'asgi' is used, indicating an ASGI-compatible setup.

"""
so = socketio.AsyncServer(async_mode = 'asgi', cors_allowed_origins='*')

def authenticate_credentials():
    """
    Placeholder function for user authentication.

    This function is intended to handle user authentication based on tokens or other
    authentication mechanisms.
    """
    # Token authentication example at the end of the file
    pass

@so.event
async def connect(sid,environ):
    """
    Handle a new WebSocket connection.

    Args:
        sid (str): The session ID of the connected client.
        environ (dict): A dictionary containing environment information.

    Note:
        This function is called when a new WebSocket connection is established.

    Example:
        This function can be customized to perform user authentication based on
        'query_string' parameters (e.g., user_id, token, user_name), save session data,
        and emit a 'connected' event to the connected client.

    """
    query_string = environ.get('QUERY_STRING')
    query_params = parse_qs(query_string)

    user_id = query_params.get('user_id', None)
    token = query_params.get('token', None)
    user_name = query_params.get('user_name', None)

    authenticate_credentials()

    # Save user-related data to the session
    data = {'user_name':user_name}
    await so.save_session(sid, data)

    # Save sid somewhere for identifying user's and emitting events to them
    await so.emit('connected',{"message": "connected", "sid": sid}, to = sid)

@so.event
async def disconnect(sid):
    """
    Handle WebSocket disconnection.

    Args:
        sid (str): The session ID of the disconnected client.

    Note:
        This function is called when a WebSocket client disconnects. You can
        perform any necessary cleanup or additional actions here.

    Example:
        You can customize this function to handle cleanup tasks or notify other
        clients about the disconnection event.
    """
    await so.disconnect(sid)

# Example event
@so.event
async def event_name(sid, data):
    """
    event_name Event Handler
    
    This event handler is responsible for processing the 'event_name' event received from a WebSocket client.
    
    Parameters:
    - sid (str): The session ID of the WebSocket client.
    - data (str): The data associated with the 'event_name' event. It is expected to be a JSON-encoded string.

    Behavior:
    - The function first parses the JSON-encoded 'data' into a Python dictionary.
    - It then extracts the 'data' field from the dictionary.
    - The extracted 'data' is used as the payload for a new 'emitted_event' event.
    - The 'emitted_event' event can be emitted to any client identified.

    Example Usage:
    - When a WebSocket client emits an 'event_name' event with the following data:
        {"data": "Hello, WebSocket!"}
      The function will emit an 'emitted_event' event to client with:
        {"data": "Hello, WebSocket!"}

    Notes:
    - This function assumes that the 'data' parameter is a JSON-encoded string containing a dictionary.
    """

    data = json.loads(data)
    await so.emit('emitted_event',{"data": data['data']}, to = sid)


@so.event
async def send_message(sid, data):
    """
    send_message Event Handler

    This event handler is responsible for handling and broadcasting chat messages within a specific room.

    Parameters:
    - sid (str): The session ID of the sender WebSocket client.
    - data (str): The data associated with the 'send_message' event, expected to be a JSON-encoded string.

    Behavior:
    - The function first parses the JSON-encoded 'data' into a Python dictionary.
    - It extracts the 'room_slug_id' from the dictionary, which identifies the target room for the message.
    - The sender is added to the specified room using `so.enter_room(sid, room_slug_id)`.
    - The message is emitted to all members of the room (except the sender) using `so.emit`.
    
    Example Usage:
    - When a WebSocket client emits a 'send_message' event with the following data:
        {"room_slug_id": "room123", "message": "Hello, World!"}
      The function will:
      1. Add the sender to the 'room123' room.
      2. Create a message structure: {"message": "Hello, World!"}.
      3. Emit the message to all members of the 'room123' room (excluding the sender).

    Notes:
    - It assumes that the 'data' parameter is a JSON-encoded string containing a dictionary.
    - The 'room_slug_id' parameter is used to target a specific room where members can join.
    - The 'skip_sid' parameter in the emit function ensures the sender does not receive their own message.
    """
    data = json.loads(data)
    room_slug_id = data.get('room_slug_id', None)

    # using socketio, create room spaces where users can connect  
    await so.enter_room(sid, room_slug_id)

    # Create message thread in your model/table
    send_message_data = {'message':data['message']}
    
    # Emit message to the room members
    await so.emit('recevied_message',{"data": send_message_data}, room = room_slug_id, skip_sid = sid)


@so.event
async def retrieve_chat_messages(sid, data):
    data = json.loads(data)
    room_slug_id = data['room_slug_id']

    chat_data = None

    await so.emit('chat_retrieved',{"data": chat_data},to = sid)




"""
Common function to connect to the server, 
used when we want to emit some event to connected clients
"""

# Create an asynchronous Socket.IO client
async def connect():
    """
    Establish a connection to the server using Socket.IO.

    Returns:
        sio_client (socketio.AsyncClient): An asynchronous Socket.IO client.
    """
    sio_client = socketio.AsyncClient()

    # Check if the client is already connected
    if sio_client.connected:
        return sio_client

    # Connect to the server at 127.0.0.1:8000
    await sio_client.connect("127.0.0.1:8000")
    return sio_client

# Send an event to the connected clients
async def send_event(event_name, data, sid):
    """
    Send an event to connected clients through the Socket.IO server.

    Args:
        event_name (str): The name of the event to be emitted.
        data (any): The data to be sent as part of the event.
        sid (str): The session ID of the recipient client.

    Note:
        This function connects to the server if not already connected and emits
        the specified event with the provided data to the specified client.

    Exceptions:
        Any exceptions raised during connection or event emission are caught
        and not propagated, ensuring graceful handling.

    Example:
        await send_event("chat_message", "Hello, World!", "client123")
    """
    try:
        # Establish a connection to the server
        sio_client = await connect()

        # Emit the event with the provided data to the specified client
        await sio_client.emit(event_name, {"data": data, "sid": list(sid)})
    except Exception as e:
        # Handle any exceptions (e.g., connection errors) gracefully
        pass


application = socketio.ASGIApp(so)

"""
The ASGI app instance is an essential component in this setup because it acts as a bridge between the Socket.IO server,
which handles WebSocket connections and events, and ASGI-compatible servers, which serve the web application and 
route WebSocket requests to the appropriate handlers. 
"""


if __name__ == "__main__":
    uvicorn.run("socks.asgi_application:application", reload=True)
"""
ASGI servers, such as Uvicorn, are capable of serving ASGI applications. 
These servers are designed to handle asynchronous web applications and WebSocket connections.
"""



# Token Authentication Example


"""
Parameters:
    key

If the token with the given key does not exist (i.e., the Token.DoesNotExist exception is raised), the function returns False, indicating that the token is not valid.
Finally, the function checks if the user associated with the token is active. If the user is not active (i.e., token.user.is_active is False), the function returns False.
"""
def authenticate_credentials_example(key):
    try:
        token = Token.objects.get(key=key)
    except Token.DoesNotExist:
        return False
    if is_token_expired(key):
        return False
    if not token.user.is_active:
        return False
    return True

"""
Parameters:
    token
accesses the last_login attribute of the user
If the difference between the current date and user_last_login is greater than or equal to seven days, the function returns True, indicating that the token is expired.
"""

def is_token_expired(token):
    user_last_login = Token.objects.get(key=token).user.last_login
    if user_last_login:
        today = timezone.now()
        if (today - user_last_login).days >= 7:
            return True
        else:
            return False
    else:
        return False